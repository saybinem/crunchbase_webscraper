import json

# Non modifiable globals
_browser = None
n_requests=0

def saveDictToJsonFile(dict_data, json_file):
    with open(json_file, 'w', encoding="utf-8") as fileh:
        fileh.write(jsonPretty(dict_data))


def myTextStrip(str):
    return str.replace('\n', '').strip()


def jsonPretty(dict_data):
    return json.dumps(dict_data, sort_keys=True, indent=4, separators=(',', ': '))
