import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="gssutils",
    version_format='{tag}.dev{commitcount}+{gitsha}',
    author="Alex Tucker",
    author_email="alex@floop.org.uk",
    description="Common functions used by GSS data transformations",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/ONS-OpenData/gss-utils",
    packages=setuptools.find_packages(),
    setup_requires=['setuptools-git-version'],
    install_requires=['requests',
                      'python_dateutil',
                      'CacheControl',
                      'lockfile',
                      'databaker',
                      'ipython',
                      'pandas',
                      'pyexcel',
                      'pyexcel-xls',
                      'pyexcel-ods3',
                      'xypath',
                      'html2text',
                      'rdflib',
                      'rdflib-jsonld',
                      'messytables==0.15.1',
                      'lxml',
                      'unidecode',
                      'argparse',
                      'wheel'],
    tests_require=['behave', 'parse', 'nose', 'vcrpy', 'docker'],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: OS Independent",
    ],
    entry_points={
        'console_scripts': ['create-schema=gssutils.schema:main']
    }
)
