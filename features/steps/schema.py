import sys
import csv
import json
import tempfile
import time
from io import BytesIO, SEEK_END, StringIO, TextIOWrapper
from pathlib import Path
from tarfile import TarFile, TarInfo

import docker as docker
from behave import *
from docker.errors import NotFound
from nose.tools import *

from gssutils import CSVWSchema


@given("table2qb configuration at '{url}'")
def step_impl(context, url):
    context.schema = CSVWSchema(url)


@step("a CSV file '{filename}'")
def step_impl(context, filename):
    context.csv_filename = Path(filename)
    context.csv_io = StringIO()
    writer = csv.writer(context.csv_io)
    writer.writerow(context.table.headings)
    for row in context.table:
        writer.writerow(row)


@when("I create a CSVW schema '{filename}'")
def step_impl(context, filename):
    context.schema_filename = Path(filename)
    context.schema_io = StringIO()
    context.csv_io.seek(0)
    context.schema.create_io(
        context.csv_io,
        context.schema_io,
        str(context.csv_filename.relative_to(context.schema_filename.parent))
    )


@then("The schema is valid JSON")
def step_impl(context):
    context.schema_io.seek(0)
    json.load(context.schema_io)


@step("cloudfluff/csvlint validates ok")
def step_impl(context):
    client = docker.from_env()
    csvlint = client.containers.create(
        'cloudfluff/csvlint',
        command=f'csvlint -s /tmp/{context.schema_filename}'
    )
    archive = BytesIO()
    context.schema_io.seek(0, SEEK_END)
    schema_size = context.schema_io.tell()
    context.schema_io.seek(0)
    context.csv_io.seek(0, SEEK_END)
    csv_size = context.csv_io.tell()
    context.csv_io.seek(0)
    with TarFile(fileobj=archive, mode='w') as t:
        tis = TarInfo(str(context.schema_filename))
        tis.size = schema_size
        tis.mtime = time.time()
        t.addfile(tis, BytesIO(context.schema_io.getvalue().encode('utf-8')))
        tic = TarInfo(str(context.csv_filename))
        tic.size = csv_size
        tic.mtime = time.time()
        t.addfile(tic, BytesIO(context.csv_io.getvalue().encode('utf-8')))
    archive.seek(0)
    csvlint.put_archive('/tmp/', archive)
    csvlint.start()
    response = csvlint.wait()
    sys.stdout.write(csvlint.logs().decode('utf-8'))
    assert_equal(response['StatusCode'], 0)


@when("I create a CSVW metadata file '{filename}'")
def step_impl(context, filename):
    context.metadata_filename = Path(filename)
    context.metadata_io = StringIO()
    context.csv_io.seek(0)
    context.schema.create_io(
        context.csv_io,
        context.metadata_io,
        str(context.csv_filename.relative_to(context.schema_filename.parent)),
        with_transform=True
    )


@then("the metadata is valid JSON-LD")
def step_impl(context):
    """
    :type context: behave.runner.Context
    """
    raise NotImplementedError(u'STEP: Then the metadata is valid JSON-LD')


@step("cloudfluff/csv2rdf generates RDF")
def step_impl(context):
    """
    :type context: behave.runner.Context
    """
    raise NotImplementedError(u'STEP: And cloudfluff/csv2rdf generates RDF')


