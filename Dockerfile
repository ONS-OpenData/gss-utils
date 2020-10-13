FROM python:3.8

WORKDIR /workspace
COPY Pipfile Pipfile.lock cucumber-format.patch setup.py /workspace/
RUN \
  pip install pipenv && \
  pipenv install --dev
RUN \
  patch -d `pipenv --venv`/lib/python3.8/site-packages/behave/formatter -p1 < cucumber-format.patch

ENV PYTHONDONTWRITEBYTECODE=1
