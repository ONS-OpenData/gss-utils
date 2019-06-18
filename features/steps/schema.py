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
from rdflib import Graph

from features.environment import BytesIOWrapper
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


@when("I create a CSVW metadata file '{filename}' for base '{base}' and path '{path}'")
def step_impl(context, filename, base, path):
    context.metadata_filename = Path(filename)
    context.metadata_io = StringIO()
    context.csv_io.seek(0)
    context.schema.create_io(
        context.csv_io,
        context.metadata_io,
        str(context.csv_filename.relative_to(context.metadata_filename.parent)),
        with_transform=True,
        base_url=base,
        base_path=path
    )


@then("the metadata is valid JSON-LD")
def step_impl(context):
    g = Graph()
    context.metadata_io.seek(0)
    #g.parse(source=BytesIOWrapper(context.metadata_io), format='json-ld')


@step("cloudfluff/csv2rdf generates RDF")
def step_impl(context):
    client = docker.from_env()
    csv2rdf = client.containers.create(
        'cloudfluff/csv2rdf',
        command=f'csv2rdf -m annotated -o /tmp/output.ttl -t /tmp/{context.csv_filename} -u /tmp/{context.metadata_filename}'
    )
    archive = BytesIO()
    context.metadata_io.seek(0, SEEK_END)
    metadata_size = context.metadata_io.tell()
    context.metadata_io.seek(0)
    context.csv_io.seek(0, SEEK_END)
    csv_size = context.csv_io.tell()
    context.csv_io.seek(0)
    with TarFile(fileobj=archive, mode='w') as t:
        tis = TarInfo(str(context.metadata_filename))
        tis.size = metadata_size
        tis.mtime = time.time()
        t.addfile(tis, BytesIO(context.metadata_io.getvalue().encode('utf-8')))
        tic = TarInfo(str(context.csv_filename))
        tic.size = csv_size
        tic.mtime = time.time()
        t.addfile(tic, BytesIO(context.csv_io.getvalue().encode('utf-8')))
    archive.seek(0)
    csv2rdf.put_archive('/tmp/', archive)
    csv2rdf.start()
    response = csv2rdf.wait()
    sys.stdout.write(csv2rdf.logs().decode('utf-8'))
    assert_equal(response['StatusCode'], 0)
    output_stream, output_stat = csv2rdf.get_archive('/tmp/output.ttl')
    output_archive = BytesIO()
    for line in output_stream:
        output_archive.write(line)
    output_archive.seek(0)
    with TarFile(fileobj=output_archive, mode='r') as t:
        output_ttl = t.extractfile('output.ttl')
        context.turtle = output_ttl.read()
