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
        pass

class FakeLogger(object):

    def __init__(self):
        self.logs = []

    def log(self, level, msg, *args, **kwargs):
        self.logs.append((level, msg, args, kwargs))

class TestUtils(unittest.TestCase):

    def test_wrapfd(self):
        from cmdlog import wrapfd

        logger = object()
        fd = FakeFile()
        wrapped = wrapfd(fd, logger, FakeWrapper)

        self.assertEqual(wrapped.foo, "foo")
        self.assertEqual(wrapped.areader, "untouched")

    def test_reader(self):
        from cmdlog import reader

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
        from cmdlog import reader

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
        from cmdlog import writer

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
        from cmdlog import LoggingFile

        logger = FakeLogger()
        fd = FakeFile()
        return LoggingFile(fd, logger)

    def test_log_plain(self):
        from cmdlog import LoggingFile

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
        from cmdlog import LineLoggingFile

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

if __name__ == "__main__":
    unittest.main()
