import unittest

from StringIO import StringIO

class FakeWrapper(object):
    readers = ("areader",)
    writers = ("awriter",)

    def __init__(self, fd, logger):
        self.fd = fd
        self.logs = []

    def log(self, str, *args, **kwargs):
        self.logs.append((str, args, kwargs))

class FakeFile(object):
    foo = "foo"
    areader = "untouched"
    awriter = "untouched"

    def __init__(self):
        self.data = "fake data\nmore fake data\n"
        self.buffer = StringIO(self.data)

    def log(self, str, *args, **kwargs):
        pass
    
    def read(self, size=-1):
        return self.buffer.read(size)

    def write(self, str):
        return self.buffer.write(str)
    
    def close(self):
        pass

class FakeLogger(object):

    def __init__(self):
        self.logs = []

    def log(self, level, msg, *args, **kwargs):
        self.logs.append((level, msg, args, kwargs))

class TestUtils(unittest.TestCase):

    def test_wrapfd(self):
        from prociolog import wrapfd

        logger = object()
        fd = FakeFile()
        wrapped = wrapfd(fd, logger, FakeWrapper)

        self.assertEqual(wrapped.foo, "foo")
        self.assertEqual(wrapped.areader, "untouched")

    def test_reader(self):
        from prociolog import reader

        logger = object()
        fd = FakeFile()
        class TestWrapper(FakeWrapper):
            pass
        TestWrapper.read = reader("read")
        wrapper = TestWrapper(fd, logger)

        result = wrapper.read(-1, "an arg", arg="a kwarg")
        logs = wrapper.logs
        self.assertEqual(len(logs), 1)
        self.assertEqual(logs[0], (result, ("an arg",), {"arg": "a kwarg"}))

        wrapper.logs.pop()
        result = wrapper.read(-1)
        self.assertEqual(result, "")
        self.assertEqual(len(logs), 1)
        self.assertEqual(logs[0], ('', (), {}))

    def test_reader_size(self):
        from prociolog import reader

        logger = object()
        fd = FakeFile()
        class TestWrapper(FakeWrapper):
            pass
        TestWrapper.read = reader("read")
        wrapper = TestWrapper(fd, logger)

        result = wrapper.read(1, "an arg", arg="a kwarg")
        logs = wrapper.logs
        self.assertEqual(len(logs), 1)
        self.assertEqual(logs[0], (result, ("an arg",), {"arg": "a kwarg"}))

        wrapper.logs.pop()
        result = wrapper.read(1)
        self.assertEqual(len(logs), 1)
        self.assertEqual(logs[0], (result, (), {}))

    def test_writer(self):
        from prociolog import writer

        logger = object()
        fd = FakeFile()
        class TestWrapper(FakeWrapper):
            pass
        TestWrapper.write = writer("write")
        wrapper = TestWrapper(fd, logger)

        msg = "a fake write"
        result = wrapper.write(msg, "an arg", arg="a kwarg")
        logs = wrapper.logs
        self.assertEqual(len(logs), 1)
        self.assertEqual(logs[0], (msg, ("an arg",), {"arg": "a kwarg"}))

class TestLoggingFile(unittest.TestCase):

    def instance(self):
        from prociolog import LoggingFile

        logger = FakeLogger()
        fd = FakeFile()
        return LoggingFile(fd, logger)

    def test_log_plain(self):
        from prociolog import LoggingFile

        loggingfile = self.instance()
        msg = "a message"
        loggingfile.log(msg)
        logger = loggingfile.logger
        self.assertEqual(len(logger.logs), 1)
        self.assertEqual(logger.logs[0], (LoggingFile.level, repr(msg), (), {}))

    def test_log_level(self):
        loggingfile = self.instance()

        msg = "a message"
        loggingfile.log(msg, level=20)
        logger = loggingfile.logger
        self.assertEqual(len(logger.logs), 1)
        self.assertEqual(logger.logs[0], (20, repr(msg), (), {}))

    def test_log_kwargs(self):
        loggingfile = self.instance()

        msg = "a message"
        loggingfile.log(msg, "arg", level=20, foo="bar")
        logger = loggingfile.logger
        self.assertEqual(len(logger.logs), 1)
        self.assertEqual(logger.logs[0], (20, repr(msg), ("arg",), {"foo": "bar"}))

class TestLineLoggingFile(unittest.TestCase):

    def instance(self):
        from prociolog import LineLoggingFile

        logger = FakeLogger()
        fd = FakeFile()
        fd.data = """foo\nbar\nbaz\n"""
        fd.buffer.buf = fd.data
        return LineLoggingFile(fd, logger)

    def test_read(self):
        loggingfile = self.instance()
        result = loggingfile.read()
        logger = loggingfile.logger

        self.assertEqual(result, loggingfile.fd.data)
        self.assertEqual(len(logger.logs), 3)
        self.assertEqual(logger.logs[0], (loggingfile.level, repr("foo\n"), (), {}))

    def test_read_empty(self):
        loggingfile = self.instance()
        loggingfile.fd.data = ""
        loggingfile.fd.buffer.buf = loggingfile.fd.data
        result = loggingfile.read()
        logger = loggingfile.logger

        self.assertEqual(result, loggingfile.fd.data)
        self.assertEqual(len(logger.logs), 0)

    def test_read(self):
        loggingfile = self.instance()
        result = loggingfile.read()
        logger = loggingfile.logger

        self.assertEqual(result, loggingfile.fd.data)
        self.assertEqual(len(logger.logs), 3)
        self.assertEqual(logger.logs[0], (loggingfile.level, repr("foo\n"), (), {}))

    def test_read_no_newline_at_end(self):
        loggingfile = self.instance()
        loggingfile.fd.data = loggingfile.fd.data.strip()
        loggingfile.fd.buffer.buf = loggingfile.fd.data
        result = loggingfile.read()
        logger = loggingfile.logger

        self.assertEqual(result, loggingfile.fd.data)
        self.assertEqual(len(logger.logs), 2)

        logger.logs = []
        result = loggingfile.read()
        self.assertEqual(result, "")
        self.assertEqual(len(logger.logs), 0)
        self.assertEqual(len(loggingfile.readbuf), 1)
        self.assertEqual(loggingfile.readbuf[0], "baz")

    def test_read_readbuf(self):
        loggingfile = self.instance()
        loggingfile.readbuf.append("a partial read")
        logs = loggingfile.logger.logs

        result = loggingfile.read()
        self.assertEqual(len(loggingfile.readbuf), 0)
        self.assertEqual(result, loggingfile.fd.data)
        self.assertEqual(len(logs), 3)
        self.assertEqual(logs[0][1], repr("a partial readfoo\n"))

    def test_close(self):
        loggingfile = self.instance()
        logger = loggingfile.logger
        loggingfile.writebuf.append("a partial write")
        loggingfile.readbuf.append("a partial read")

        loggingfile.close()

        level = loggingfile.level
        self.assertEqual(len(logger.logs), 2)
        self.assertEqual(logger.logs[0], 
                (level, "'a partial read'", (), {'extra': {'onclose': 'read'}}))
        self.assertEqual(logger.logs[1], 
                (level, "'a partial write'", (), {'extra': {'onclose': 'write'}}))

    def test_write_empty(self):
        loggingfile = self.instance()
        logs = loggingfile.logger.logs

        result = loggingfile.write("")

        self.assertEqual(len(loggingfile.writebuf), 0)
        self.assertEqual(len(logs), 0)

    def test_write_writebuf(self):
        loggingfile = self.instance()
        loggingfile.writebuf.append("a partial write")
        logs = loggingfile.logger.logs

        result = loggingfile.write("the rest of a write\n")
        loggingfile.fd.buffer.seek(0)

        self.assertEqual(len(loggingfile.writebuf), 0)
        self.assertEqual(loggingfile.fd.buffer.read(), "the rest of a write\n")
        self.assertEqual(len(logs), 1)
        self.assertEqual(logs[0][1], repr("a partial writethe rest of a write\n"))

    def test_writelines(self):
        loggingfile = self.instance()
        logs = loggingfile.logger.logs

        loggingfile.writelines("foo bar baz".split())

        self.assertEqual(len(logs), 0)
        self.assertEqual(len(loggingfile.writebuf), 1)
        self.assertEqual(loggingfile.writebuf[0], "foobarbaz")

    def test_writelines_empty(self):
        loggingfile = self.instance()
        logs = loggingfile.logger.logs

        loggingfile.writelines([])

        self.assertEqual(len(logs), 0)
        self.assertEqual(len(loggingfile.writebuf), 0)


if __name__ == "__main__":
    unittest.main()
