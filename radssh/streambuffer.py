"""StreamBuffer Module

Single, clean implementation of StreamBuffer used by radssh.

This file intentionally keeps the implementation small and self-contained.
"""

import queue


class StreamBuffer(object):
    """StreamBuffer Class"""

    def __init__(self, queue=None, tag=None, delimiter=b"\n", blocksize=1024, presplit=False, encoding="utf-8"):
        self.tag = tag if tag else "%d" % id(self)
        self.queue = queue
        self.delimiter = delimiter
        self.blocksize = blocksize
        # Local data: empty buffer with reset marker position
        self.buffer = bytes()
        self.marker = 0
        self.pull_marker = 0
        self.line_count = 0
        self.active = True
        self.discards = 0
        self.pre_split = presplit
        self.encoding = encoding

    def push(self, data):
        """Append data to buffer and enqueue lines when thresholds exceeded."""
        if not self.active:
            raise EOFError
        flush_needed = False
        if not isinstance(data, bytes):
            data = data.encode(self.encoding, "xmlcharrefreplace")
        if data:
            self.buffer += data
            if len(self.buffer) - self.marker > self.blocksize:
                flush_needed = True
        else:
            if len(self.buffer) - self.marker > 0:
                flush_needed = True

        if self.queue and flush_needed:
            pending = self.buffer[self.marker:]
            if self.pre_split:
                lines = pending.split(self.delimiter)
                for x in lines[0:-1]:
                    self.line_count += 1
                    try:
                        self.queue.put_nowait((self.tag, x.decode(self.encoding, "replace")))
                    except queue.Full:
                        self.discards += 1
                self.marker = len(self.buffer) - len(lines[-1])
            else:
                pos = pending.rfind(self.delimiter)
                if pos >= 0:
                    try:
                        self.queue.put_nowait((self.tag, pending[:pos].decode(self.encoding, "replace")))
                    except queue.Full:
                        self.discards += 1
                    self.line_count += pending[:pos].count(self.delimiter)
                    self.marker += 1 + pos

    def pull(self, size=0):
        if not self.active and self.pull_marker == len(self.buffer):
            raise EOFError
        data = self.buffer[self.pull_marker:]
        # If size is zero, return all remaining data
        if size == 0:
            self.pull_marker = len(self.buffer)
            return data
        # If requested size is less than or equal to remaining, return that slice
        if self.pull_marker + size <= len(self.buffer):
            result = data[:size]
            self.pull_marker += size
            return result
        # Otherwise return whatever remains and advance to end
        self.pull_marker = len(self.buffer)
        return data

    def rewind(self, position=0):
        if position < 0 or position > len(self.buffer):
            raise ValueError("Invalid rewind position %d: only range [0:%d] exists" % (position, len(self.buffer)))
        self.pull_marker = position

    def close(self):
        if self.buffer and self.buffer[-1:] == self.delimiter:
            self.buffer = self.buffer[:-1]
        if self.queue and len(self.buffer) > self.marker:
            self.push(b"")
            if len(self.buffer) > self.marker:
                pending = self.buffer[self.marker:]
                try:
                    self.queue.put((self.tag, pending.decode(self.encoding, "replace")))
                except queue.Full:
                    self.discards += 1
                self.line_count += 1
        self.marker = len(self.buffer)
        self.active = False

    def __iter__(self):
        for x in self.buffer.split(self.delimiter):
            yield x.decode(self.encoding, "replace")

    def __len__(self):
        return len(self.buffer)

    def __str__(self):
        return "<%s-%s>" % (self.__class__.__name__, self.tag)

