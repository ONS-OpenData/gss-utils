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
    setup_requires=['better-setuptools-git-version'],
    install_requires=['requests',
                      'python_dateutil',
                      'CacheControl',
                      'lockfile',
                      'databaker',
                      'ipython',
                      'jinja2',
                      'pandas',
                      'pyexcel',
                      'pyexcel-io',
                      'pyexcel-xls',
                      'pyexcel-ods3',
                      'xypath==1.1.1',
                      'html2text',
                      'rdflib==4.2.2',
                      'rdflib-jsonld',
                      'messytables',
                      'lxml',
                      'unidecode',
                      'argparse',
                      'wheel',
                      'uritemplate'],
    tests_require=['behave', 'parse', 'nose', 'vcrpy', 'docker'],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: OS Independent",
    ],
    entry_points={
        'console_scripts': ['create-schema=gssutils.csvw:create_schema',
                            'create-transform=gssutils.csvw:create_transform']
    }
)
