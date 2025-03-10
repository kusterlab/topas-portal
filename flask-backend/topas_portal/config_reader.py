import json
def config_reader(config_path):
    with open(config_path, "r") as f:
        config = json.load(f)
    return config