#
# Copyright (c) 2014, 2016, 2018, 2020 LexisNexis Risk Data Management Inc.
#
# This file is part of the RadSSH software package.
#
# RadSSH is free software, released under the Revised BSD License.
# You are permitted to use, modify, and redsitribute this software
# according to the Revised BSD License, a copy of which should be
# included with the distribution as file LICENSE.txt
#

"""
RadSSH Module
Simplified Paramiko interface for managing clustered SSH interaction
"""

import os
import getpass
import threading
import socket
import time
import uuid
import fnmatch
import mitogen.master
import mitogen.ssh
import re
import logging
import queue

from .authmgr import AuthManager
from .streambuffer import StreamBuffer
from .dispatcher import Dispatcher, UnfinishedJobs
from .console import RadSSHConsole, user_password
from . import config

# The known_hosts logic was tied to paramiko and is not used by Mitogen
# from . import known_hosts

# Mitogen handles its own keepalive, so this is no longer needed.
# from .keepalive import KeepAlive, ServerNotResponding

class MitogenConnection:
    """A wrapper to make Mitogen contexts compatible with the existing structure."""
    def __init__(self, context):
        self.context = context
        self.is_authenticated_flag = True

    def is_active(self):
        return self.context.is_active()

    def is_authenticated(self):
        return self.is_authenticated_flag

    def get_username(self):
        return self.context.remote_username

    def getpeername(self):
        return (self.context.hostname, self.context.port)
    
    def close(self):
        self.is_authenticated_flag = False
        self.context.shutdown(wait=True)

    @property
    def remote_version(self):
        # Mitogen doesn't expose the raw SSH banner easily, returning a placeholder
        return "Mitogen-SSH"


# If main thread gets KeyboardInterrupt, use this to signal
# running background threads to terminate prior to command completion
user_abort = threading.Event()

FILTER_TTY_ATTRS_RE = re.compile(b"\x1b\\[(\d)+(;(\d+))*m")

# Map ssh_config LogLevels to Python logging module levels
# This may need some future adjustment, as the labels don't quite line up
sshconfig_loglevels = {
    "QUIET": 0,
    "FATAL": logging.CRITICAL,
    "ERROR": logging.ERROR,
    "INFO": logging.WARNING,
    "VERBOSE": logging.INFO,
    "DEBUG": logging.DEBUG,
    "DEBUG1": logging.DEBUG,
    "DEBUG2": logging.DEBUG,
    "DEBUG3": logging.DEBUG,
}


def filter_tty_attrs(line):
    """Handle the attributes for colors, etc."""
    return FILTER_TTY_ATTRS_RE.sub(b"", line)


class Quota(object):
    """Quota values for auto-termination of in-flight commands"""

    def __init__(self, defaults={}):
        self.time_limit = int(defaults.get("quota.time", 0))
        self.byte_limit = int(defaults.get("quota.bytes", 0))
        self.line_limit = int(defaults.get("quota.lines", 0))

    def settings(self):
        return self.time_limit, self.byte_limit, self.line_limit

    def time_exceeded(self, elapsed_time):
        if self.time_limit and elapsed_time > self.time_limit:
            return True
        else:
            return False

    def bytes_exceeded(self, bytes):
        if self.byte_limit and bytes > self.byte_limit:
            return True
        else:
            return False

    def lines_exceeded(self, lines):
        if self.line_limit and lines > self.line_limit:
            return True
        else:
            return False


class CommandResult(object):
    """Generic object to save a bunch of fields"""

    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            self.__setattr__(k, v)

    def __repr__(self):
        return '%s "%s" : [%s]' % (self.status, self.command, self.return_code)


class Chunker(object):
    """Allow list of host connections to be chunkified into sublists"""

    def __init__(self, grouping=10, delay=30):
        self.data = [[]]
        self.grouping = grouping
        self.delay = delay

    def add(self, *args):
        for x in args:
            if self.grouping and len(self.data[-1]) >= self.grouping:
                self.data.append([])
            self.data[-1].append(x)

    def __len__(self):
        return sum([len(x) for x in self.data])

    def __iter__(self):
        for x in self.data[:-1]:
            yield x
            if self.delay:
                try:
                    time.sleep(self.delay)
                except KeyboardInterrupt:
                    print("<Ctrl-C> in chunk mode delay")
        # Yield the last one without adding a delay, since it is the last
        yield self.data[-1]


def mitogen_connection_worker(host, conn, auth, sshconfig={}, router=None):
    """Establish a connection using the Mitogen router."""
    if not router:
        raise ValueError("Mitogen router not provided")

    hostname = sshconfig.get("hostname", conn or host)
    port = int(sshconfig.get("port", 22))
    username = sshconfig.get("user", auth.default_user)

    try:
        # For this refactoring, we are simplifying some aspects like strict
        # host key checking to get the core functionality working.
        context = router.ssh(
            hostname=hostname,
            port=port,
            username=username,
            python_path='python3',
            check_host_keys='ignore' 
        )
        return MitogenConnection(context)
    except Exception as e:
        logging.getLogger("radssh").error(
            "Mitogen connection failed for %s: %s", host, e, exc_info=True
        )
        return e

def mitogen_exec_command(host, m_conn, cmd, quota, streamQ, encoding="UTF-8"):
    """Execute a command using a Mitogen context."""
    if not isinstance(m_conn, MitogenConnection) or not m_conn.is_authenticated():
        return CommandResult(
            command=cmd,
            return_code=None,
            status="*** Skipped ***",
            stdout=b"",
            stderr=b"",
        )

    context = m_conn.context
    try:
        # Use Mitogen's API to execute the command.
        # This is a simplified synchronous call for the refactoring.
        call = context.call(subprocess.run, cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        stdout = call.stdout
        stderr = call.stderr
        return_code = call.returncode

        if streamQ:
            if stdout:
                streamQ.put(((str(host), False), stdout.decode(encoding, 'replace')))
            if stderr:
                streamQ.put(((str(host), True), stderr.decode(encoding, 'replace')))

        return CommandResult(
            command=cmd,
            return_code=return_code,
            status="*** Complete ***",
            stdout=stdout,
            stderr=stderr,
        )
    except Exception as e:
        logging.getLogger("radssh").error("Mitogen exec failed for %s: %s", host, e)
        return CommandResult(
            command=cmd,
            return_code=-1,
            status=f"*** Mitogen Error: {e} ***",
            stdout=b"",
            stderr=str(e).encode(),
        )

def mitogen_sftp_thread(host, m_conn, srcfile, dstfile=None, attrs=None):
    """Placeholder for SFTP, as it requires a different approach with Mitogen."""
    logging.getLogger("radssh").warning("SFTP is not supported in this Mitogen version.")
    return CommandResult(
        command=f"SFTP {srcfile} -> {dstfile}",
        return_code=-1,
        status="*** SFTP Not Supported ***",
        stdout=b"",
        stderr=b"SFTP functionality is not available with the Mitogen backend.",
    )

def mitogen_close_connection(m_conn, k, signoff=""):
    """Close a Mitogen connection."""
    if isinstance(m_conn, MitogenConnection):
        m_conn.close()


class Cluster(object):
    """SSH Cluster"""

    def __init__(
        self,
        hostlist,
        auth=None,
        console=None,
        mux={},
        defaults={},
        commandline_options={},
        start_threads=True,
    ):
        """Create a Cluster object from a list of host entries"""
        if auth:
            self.auth = auth
        else:
            self.auth = AuthManager()
        self.start_threads = start_threads
        if console:
            self.console = console
        else:
            outQ = queue.Queue(min(100, 4 * len(hostlist)))
            if start_threads:
                self.console = RadSSHConsole(outQ)
                self.console.quiet(True)
            else:
                class _NoopConsole:
                    def __init__(self, q):
                        self.q = q
                    def quiet(self, *a, **k): return False
                    def progress(self, *a, **k): pass
                    def message(self, *a, **k): pass
                    def status(self, *a, **k): pass
                    def join(self, *a, **k): return
                    def replay_recent(self, *a, **k): return
                self.console = _NoopConsole(outQ)

        if defaults:
            self.defaults = defaults
        else:
            self.defaults = config.load_default_settings()
        
        self.router = mitogen.master.Router()
        self.log_out = self.defaults.get("log_out", "out.log").strip()
        self.log_err = self.defaults.get("log_err", "err.log").strip()
        thread_count = min(int(self.defaults.get("max_threads")), len(hostlist))
        self.dispatcher = Dispatcher(outQ=queue.Queue(), threadpool_size=thread_count)
        self.pending = {}
        self.uuid = uuid.uuid1()
        self.connections = {}
        self.connect_timings = {}
        self.mux = {}
        self.reverse_port = {}
        self.disabled = set()
        self.last_result = None
        self.user_vars = {}
        self.quota = Quota(self.defaults)
        self.chunk_size = None
        self.chunk_delay = 0
        self.output_mode = self.defaults["output_mode"]
        self.ordered_placeholder = self.defaults["ordered_placeholder"]

        for label, conn in hostlist:
            ssh_cfg = self.get_ssh_config(label, conn)
            if mux:
                for idx, mux_var in enumerate(mux.get(label, [])):
                    mux_label = f"{label}:{idx}"
                    self.pending[
                        self.dispatcher.submit(
                            mitogen_connection_worker, mux_label, conn, self.auth, ssh_cfg, router=self.router
                        )
                    ] = label
                    self.mux[mux_label] = mux_var
            else:
                self.pending[
                    self.dispatcher.submit(
                        mitogen_connection_worker, label, conn, self.auth, ssh_cfg, router=self.router
                    )
                ] = label
        self.update_connections()
        if start_threads:
            self.dispatcher.start_threads(len(self.connections))

    def update_connections(self):
        """Pull completed transport creations and save in connections dict"""
        while self.pending:
            try:
                for pid, summary in self.dispatcher.async_results(5):
                    host = self.pending.pop(pid)
                    connection = summary.result
                    self.connections[host] = connection
                    self.connect_timings[host] = summary.end_time - summary.start_time
                    if isinstance(connection, MitogenConnection) and connection.is_authenticated():
                        self.console.progress(".")
                        logging.getLogger("radssh.connection").info(
                            "Authenticated to %s" % host
                        )
                    else:
                        self.console.progress("X")
                        logging.getLogger("radssh.connection").warning(
                            "Failed to connect to %s: %s" % (host, str(connection))
                        )
                break 
            except UnfinishedJobs as e:
                self.console.message(e.message, "STALLED")
            except KeyboardInterrupt:
                self.console.message("Aborting connections...", "Ctrl-C")
                self.dispatcher.terminate()
                break
        self.console.progress("\n")
        self.console.status("Ready")

    def reauth(self, user):
        """Re-authentication logic needs to be adapted for Mitogen or simplified."""
        self.console.message("Re-authentication is not fully supported with Mitogen backend.", "INFO")

    def get_ssh_config(self, label, connection_spec=None):
        """Build a dictionary of SSH options for the given host."""
        config = {}
        if isinstance(connection_spec, str):
            host_spec = connection_spec
        else:
            host_spec = label

        if "@" in host_spec:
            supplied_user, host_spec = host_spec.split("@", 1)
            config["user"] = supplied_user

        if ":" in host_spec:
            host_spec, supplied_port = host_spec.rsplit(":", 1)
            config["port"] = supplied_port
        
        config["hostname"] = host_spec

        if "loglevel" not in config:
            config["loglevel"] = self.defaults.get("loglevel", "INFO").upper()
        return config

    def run_command(self, template):
        """Execute a command line (template) string across all enabled host connections"""
        result = {}
        chunker = Chunker(self.chunk_size, self.chunk_delay)
        for k in self:
            if k in self.disabled:
                continue
            chunker.add(k)

        total = len(chunker)
        for chunk in chunker:
            for k in chunk:
                t = self.connections[k]
                cmd = self.prep_command(template, k)
                if not cmd:
                    continue
                
                stream_q = self.console.q if self.output_mode == "stream" else None
                self.pending[
                    self.dispatcher.submit(
                        mitogen_exec_command,
                        k, t, cmd, self.quota, stream_q, self.defaults["character_encoding"],
                    )
                ] = k
            
            while self.pending:
                try:
                    self.console.status(f"Completed on {len(result)}/{total} hosts")
                    for pid, summary in self.dispatcher.async_results():
                        host = self.pending.pop(pid)
                        result[host] = summary
                except UnfinishedJobs:
                    pass
                except KeyboardInterrupt:
                    self.console.message("Command aborted by user.", "Ctrl-C")
                    user_abort.set()
                    break
            if user_abort.is_set():
                break

        self.console.status("Ready")
        self.console.join(True)
        user_abort.clear()
        self.last_result = result
        return result

    def sftp(self, src, dst=None, attrs=None):
        """SFTP a file (put) to all nodes"""
        for k in self:
            t = self.connections[k]
            if k in self.disabled or not isinstance(t, MitogenConnection):
                continue
            self.pending[self.dispatcher.submit(mitogen_sftp_thread, k, t, src, dst, attrs)] = k
        
        total = len(self.pending)
        result = {}
        while self.pending:
            try:
                for pid, summary in self.dispatcher.async_results():
                    host = self.pending.pop(pid)
                    result[host] = summary
                    if not summary.completed:
                        self.console.message(f"{host} - {summary.result!r}", "EXCEPTION")
                self.console.status(f"Completed on {len(result)}/{total} hosts")
            except UnfinishedJobs:
                pass
        self.last_result = result
        self.console.status("Ready")
        return result

    def status(self):
        """Return a combined list of connection status text messages"""
        good = []
        bad = []
        for k in self:
            t = self.connections[k]
            connect_time = self.connect_timings.get(k, -1)
            if isinstance(t, MitogenConnection):
                if t.is_authenticated():
                    status_str = f"({connect_time:7.3f}s) Authenticated as {t.get_username()} to {t.getpeername()[0]}"
                    if k in self.disabled:
                        status_str += " (Disabled)"
                    good.append((k, status_str))
                else:
                    bad.append((k, f"({connect_time:7.3f}s) Not authenticated"))
            else:
                bad.append((k, f"({connect_time:8.3f}s) {t}"))
        return good + bad

    def close_connections(self):
        """Disconnect from all remote hosts and shut down the router."""
        for k in list(self.connections):
            t = self.connections.pop(k)
            self.dispatcher.submit(mitogen_close_connection, t, k)
        self.dispatcher.wait()
        if self.router:
            self.router.broker.shutdown()
            self.router = None

    # Other methods like locate, __iter__, etc. can remain largely the same
    def locate(self, s):
        if s in self.connections:
            return s
        for k in self.connections:
            if str(k) == s:
                return k
        return None

    def __iter__(self):
        def hybrid_key(x):
            return (str(type(x)), x)
        return iter(sorted(self.connections.keys(), key=hybrid_key))
    
    def prep_command(self, cmd, target):
        # This method for variable substitution can remain as is.
        vars = set(re.findall("%[a-zA-Z_]+%", cmd))
        if not vars:
            return cmd
        t = self.connections[target]
        auto_vars = {
            "%host%": str(target),
            "%ip%": t.getpeername()[0] if isinstance(t, MitogenConnection) else "0.0.0.0",
            "%ssh_version%": t.remote_version if isinstance(t, MitogenConnection) else "No Connection",
            "%uuid%": str(self.uuid),
        }
        if self.mux:
            auto_vars["%mux%"] = self.mux.get(target, "")

        for v in vars:
            if v in auto_vars:
                cmd = cmd.replace(v, auto_vars[v])
            elif v in self.user_vars:
                cmd = cmd.replace(v, self.user_vars[v])
            else:
                val = input(f"Missing variable setting for {v}\nEnter value : ")
                self.user_vars[v] = val
                cmd = cmd.replace(v, val)
        return cmd
    
    def enable(self, enable_list=None):
        self.disabled = set()
        if enable_list is None:
            self.console.q.put((("ENABLED", True), f"All {len(self.connections)} hosts currently enabled"))
            return
        if isinstance(enable_list, str):
            enable_list = [enable_list]

        enabled = set()
        for pattern in enable_list:
            if self.locate(pattern):
                enabled.add(self.locate(pattern))
            else:
                for host in self.connections:
                    if fnmatch.fnmatch(str(host), pattern):
                        enabled.add(host)
        
        self.disabled = set(self.connections.keys()) - enabled
        self.console.q.put((("ENABLED", True), f"{len(enabled)} hosts currently enabled"))

    def log_result(self, logdir=None, command_header=True, encoding="UTF-8"):
        if logdir and self.last_result:
            for k, job in self.last_result.items():
                v = job.result
                if isinstance(v, CommandResult):
                    with open(os.path.join(logdir, str(k) + ".log"), "ab") as f:
                        if command_header:
                            header = f'=== "{v.command}" {v.status} [{v.return_code}] ===\n'
                            f.write(header.encode(encoding))
                        f.write(v.stdout)
                        f.write(b"\n")
                    if v.stderr:
                        with open(os.path.join(logdir, str(k) + ".stderr"), "ab") as f:
                            f.write(v.stderr)
                            f.write(b"\n")

    def connection_summary(self):
        ready = disabled = failed_auth = failed_connect = dropped = 0
        for k, t in self.connections.items():
            if isinstance(t, MitogenConnection) and t.is_authenticated():
                if k in self.disabled:
                    disabled += 1
                else:
                    ready += 1
            else:
                failed_connect += 1
        return (ready, disabled, failed_auth, failed_connect, dropped)
