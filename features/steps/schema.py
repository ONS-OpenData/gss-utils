import sys
import csv
import json
import tempfile
from pathlib import Path

import docker as docker
from behave import *
from nose.tools import *

from gssutils import CSVWSchema


@given("table2qb configuration at '{url}'")
def step_impl(context, url):
    context.schema = CSVWSchema(url)


@step("a CSV file '{filename}'")
def step_impl(context, filename):
    context.work_dir = tempfile.TemporaryDirectory()
    context.cwd = Path(context.work_dir.name)
    context.csv_filename = context.cwd / filename
    with open(context.csv_filename, 'w') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(context.table.headings)
        for row in context.table:
            writer.writerow(row)


@when("I create a CSVW schema '{filename}'")
def step_impl(context, filename):
    context.schema_filename = context.cwd / filename
    context.schema.create(context.csv_filename, context.schema_filename)


@then("The schema is valid JSON")
def step_impl(context):
    with open(context.schema_filename) as schema_file:
        json.load(schema_file)


@step("cloudfluff/csvlint validates ok")
def step_impl(context):
    abs_schema_dir = context.schema_filename.resolve().parent
    client = docker.from_env()
    csvlint = client.containers.run('cloudfluff/csvlint', ['csvlint', '-s', 'schema.json'],
                                    volumes={
                                        str(abs_schema_dir): {'bind': '/workspace', 'mode': 'ro'}
                                    },
                                    working_dir='/workspace', detach=True)
    response = csvlint.wait()
    sys.stdout.write(csvlint.logs().decode(sys.stdout.encoding))
    assert_equal(response['StatusCode'], 0)
