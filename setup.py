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


if __name__ == "__main__":
    setuptools.setup(
            name="economic-py",
            description="Sync Jira issues and Google Calendar events with e-conomic",
            license='MIT',
            url="https://github.com/pawel-lewtak/economic-py",
            version="0.9",
            author="Pawel Lewtak",
            maintainer='Pawel Lewtak',
            long_description='',
            packages=setuptools.find_packages(),

            tests_require=['pytest'],
            install_requires=[
                "gdata==2.0.18",
                "requests==2.9.1",
                "click==6.2",
                "responses==0.5.1",
                "google-api-python-client==1.4.2"
            ],
            cmdclass={'test': PyTest},
            classifiers=[
                'Development Status :: 5 - Production/Stable',
                'Environment :: Console',
                'Intended Audience :: Developers',
                'License :: OSI Approved :: MIT License',
                'Programming Language :: Python',
                'Programming Language :: Python :: 2',
                'Programming Language :: Python :: 2.7',
                # 'Programming Language :: Python :: 3',
            ],
    )
