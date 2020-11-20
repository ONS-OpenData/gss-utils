import os
import yaml
import json
import sys

# TODO - use an arg parser
clean_the_yaml = False
index_to_keep = None
try:
    uri_arg = sys.argv[1]
    print("\nWith uri {}\n".format(uri_arg))
except:
    raise Exception("Please provide a uri as the first argument")

try:
    do_clean = sys.argv[2].strip()
    if do_clean != "-clean-all" and do_clean != "-clean-but-keep":
        raise Exception('The second argument must be "-clean-all", "-clean-but-keep" or not passed at all (to just view occurances of the uri without altering scrape.yaml).')
    clean_the_yaml = True

    if do_clean == "-clean-but-keep":
        try:
            index_to_keep = int(sys.argv[3].strip())
        except Exception as err:
            raise Exception('If you\'re using the "-clean-but-keep" flag your last argument must be an integer denoting which request to keep')

except IndexError as err:
    # No cleaning arg provided - we're just looking
    pass

# Load the scrape yaml
here = os.path.dirname(os.path.realpath(__file__))
with open("{}/features/fixtures/scrape.yml".format(here), 'r') as f:
    try:
        data = yaml.safe_load(f)
    except Exception as err:
        raise Exception("Problem encountered when trying to load scrape yaml") from err

# List occurances of the uri
requests_with_uri_in = [x for x in data["interactions"] if x["request"]["uri"] == str(uri_arg)]
for i, request in enumerate(requests_with_uri_in):
    print("Uri recorded:", request["request"]["uri"])
    print("Index No >>>> ", i)
    try:
        print("Age:", request["response"]["headers"]["Date"][0])
    except:
        print("Couldnt get age!")
        print(request["response"]["headers"].keys())
    
    print()

# Remove the uri
found_count = 0
if clean_the_yaml:
    all_interactions = data["interactions"]
    data["interactions"] = []

    for interaction in all_interactions:
        if interaction["request"]["uri"] != str(uri_arg):
            data["interactions"].append(interaction)
        elif index_to_keep is not None:
            if index_to_keep == found_count:
                data["interactions"].append(interaction)
            found_count += 1

    #requests_with_uri_removed = [x for x in data["interactions"] if x["request"]["uri"] != uri_arg]
    #data["interactions"] = requests_with_uri_removed

    # Write back the updated yaml
    with open("{}/features/fixtures/scrape.yml".format(here), 'w') as f:
        yaml.dump(data, f)