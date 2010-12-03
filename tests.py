import unittest

class FakeWrapper(object):
    readers = ("areader",)
    writers = ("awriter",)

    def __init__(self, fd, logger):
        self.fd = fd

class FakeFile(object):
    foo = "foo"
    areader = "untouched"
    awriter = "untouched"

class TestUtils(unittest.TestCase):

    def test_wrapfd(self):
        from cmdlog import wrapfd

        logger = object()
        fd = FakeFile()
        wrapped = wrapfd(fd, logger, FakeWrapper)

        self.assertEqual(wrapped.foo, "foo")
        self.assertEqual(wrapped.areader, "untouched")

if __name__ == "__main__":
    unittest.main()
