import setuptools

setuptools.setup(
    name="economic-py",
    version="master",
    url="https://github.com/pawel-lewtak/economic-py",

    author="Pawel Lewtak",

    description="Sync Jira issues and Google Calendar events with e-conomic",
    long_description=open('README.md').read(),

    packages=setuptools.find_packages(),

    install_requires=[
        "gdata==2.0.18",
        "requests==2.5.3",
        "click==3.3",
        "responses==0.3.0",
        "google-api-python-client==1.4.0"
    ],

    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Console',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 3',
    ],
)
