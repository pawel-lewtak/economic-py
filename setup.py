from setuptools.command.test import test as TestCommand
import setuptools
import sys


class PyTest(TestCommand):
    user_options = [('pytest-args=', 'a', "Arguments to pass to py.test")]

    def initialize_options(self):
        TestCommand.initialize_options(self)
        self.pytest_args = []

    def finalize_options(self):
        TestCommand.finalize_options(self)
        self.test_args = []
        self.test_suite = True

    def run_tests(self):
        # import here, cause outside the eggs aren't loaded
        import pytest

        errno = pytest.main(self.pytest_args)
        sys.exit(errno)


setuptools.setup(
    name="economic-py",
    version="master",
    url="https://github.com/pawel-lewtak/economic-py",

    author="Pawel Lewtak",

    description="Sync Jira issues and Google Calendar events with e-conomic",
    long_description=open('README.md').read(),

    packages=setuptools.find_packages(),

    tests_require=['pytest'],
    install_requires=[
        "gdata==2.0.18",
        "requests==2.6.2",
        "click==4.0",
        "responses==0.3.0",
        "google-api-python-client==1.4.0"
    ],
    cmdclass={'test': PyTest},

    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Console',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2',
        # 'Programming Language :: Python :: 3',
    ],
)
