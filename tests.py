import unittest

class FakeWrapper(object):
    readers = ("areader",)
    writers = ("awriter",)
    logs = []

    def __init__(self, fd, logger):
        self.fd = fd

    def log(self, str, *args, **kwargs):
        pass
        self.logs.append((str, args, kwargs))

class FakeFile(object):
    foo = "foo"
    areader = "untouched"
    awriter = "untouched"

    def log(self, str, *args, **kwargs):
        pass
    
    def read(self, size=-1):
        return "a fake read"

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

if __name__ == "__main__":
    unittest.main()
