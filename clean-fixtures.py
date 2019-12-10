from yaml import load, dump
try:
    from yaml import CLoader as Loader, CDumper as Dumper
except ImportError:
    from yaml import Loader, Dumper

fixtures = load(open('features/fixtures/scrape.yml'), Loader=Loader)

visited = set()
def already_visited(uri):
    if uri in visited:
        return True
    else:
        visited.add(uri)
        return False

cleaned_interactions = list(reversed([interaction for interaction in reversed(fixtures['interactions']) if not already_visited(interaction['request']['uri'])]))
fixtures['interactions'] = cleaned_interactions

with open('features/fixtures/clean_scrape.yml', 'w') as clean_scrape:
    dump(fixtures, clean_scrape)
