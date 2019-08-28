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
    install_requires=['requests==2.21.0',
                      'python_dateutil==2.6.0',
                      'CacheControl==0.12.5',
                      'lockfile==0.12.2',
                      'databaker==2.0.0',
                      'ipython==7.2.0',
                      'pandas==0.24.2',
                      'pyexcel==0.5.13',
                      'pyexcel-io==0.5.17',
                      'pyexcel-xls==0.5.8',
                      'pyexcel-ods3==0.5.3',
                      'xypath==1.1.1',
                      'html2text==2018.1.9',
                      'rdflib==4.2.2',
                      'rdflib-jsonld==0.4.0',
                      'messytables==0.15.1',
                      'lxml==4.2.5',
                      'unidecode==1.0.23',
                      'argparse',
                      'wheel'],
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
