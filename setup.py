import sys

from setuptools import setup

meta = dict(
    name="prociolog",
    version="0.1.0",
    description="log communication on a subprocess' input and output pipes",
    author="Will Maier",
    author_email="willmaier@ml1.net",
    py_modules=["prociolog"],
    test_suite="tests",
    install_requires=["setuptools"],
    keywords="logging subprocess io log",
    url="http://packages.python.org/prociolog",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: BSD License",
        "License :: OSI Approved :: MIT License",
        "Natural Language :: English",
        "Programming Language :: Python",
        "Topic :: System :: Logging",
    ],
)

# Automatic conversion for Python 3 requires distribute.
if False and sys.version_info >= (3,):
    meta.update(dict(
        use_2to3=True,
    ))

setup(**meta)
