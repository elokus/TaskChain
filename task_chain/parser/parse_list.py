

def parse_list_in_json(o: dict, key: str):
    import json

    if o is None:
        raise ValueError("object is None for")
    if o[key] is None:
        o[key] = []
    if isinstance(o[key], str):
        if "[" in o[key]:
            try:
                o[key] = json.loads(o[key])
                return o
            except:
                o[key] = o[key].replace("[", "").replace("]", "")
    if "," in o[key]:
        o[key] = o[key].split(",")
    if isinstance(o[key], str):
        o[key] = [o[key]]
    if not isinstance(o[key], list):
        o[key] = [o[key]]
    return o
