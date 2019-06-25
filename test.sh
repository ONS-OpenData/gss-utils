#!/bin/bash

pip install -r test-requirements.txt
pip install .
patch -d /usr/local/lib/python3.7/site-packages/behave/formatter -p1 < cucumber-format.patch
PYTHONDONTWRITEBYTECODE=1 behave -f json.cucumber -o test-results.json
