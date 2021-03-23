from collections import defaultdict
from urllib.parse import urlparse

from pathlib import Path
from yaml import load, dump
try:
    from yaml import CLoader as Loader, CDumper as Dumper
except ImportError:
    from yaml import Loader, Dumper

fixtures = load(open('features/fixtures/scrape.yml'), Loader=Loader)

domain_dir = Path('features') / 'fixtures' / 'cassettes' / 'domains'

domain_fixtures = {}
for site in domain_dir.iterdir():
    if site.name.endswith('.yml'):
        domain_fixtures[site.stem] = load(open(site), Loader=Loader)

for interaction in fixtures['interactions']:
    uri = urlparse(interaction['request']['uri'])
    domain = uri.hostname.lower()
    domain = {
        'open.statswales.gov.wales': 'statswales.gov.wales',
        'files.digital.nhs.uk': 'digital.nhs.uk'
    }.get(domain, domain)
    if domain in domain_fixtures:
        domain_fixtures[domain]['interactions'].append(interaction)
    else:
        domain_fixtures[domain] = {'interactions': [interaction], 'version': 1}

for domain, interactions in domain_fixtures.items():
    with open(domain_dir / (domain + '.yml'), 'w') as out:
        dump(interactions, out)
