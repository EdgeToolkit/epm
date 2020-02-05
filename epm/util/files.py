import yaml


def load_yaml(filename):
    with open(filename) as f:
        return yaml.safe_load(f)


def save_yaml(filename, data):
    with open(filename, 'w') as f:
        yaml.dump(data, f, default_flow_style=False)


def decode_text(text):
    import codecs
    encodings = {codecs.BOM_UTF8: "utf_8_sig",
                 codecs.BOM_UTF16_BE: "utf_16_be",
                 codecs.BOM_UTF16_LE: "utf_16_le",
                 codecs.BOM_UTF32_BE: "utf_32_be",
                 codecs.BOM_UTF32_LE: "utf_32_le",
                 b'\x2b\x2f\x76\x38': "utf_7",
                 b'\x2b\x2f\x76\x39': "utf_7",
                 b'\x2b\x2f\x76\x2b': "utf_7",
                 b'\x2b\x2f\x76\x2f': "utf_7",
                 b'\x2b\x2f\x76\x38\x2d': "utf_7"}
    for bom in sorted(encodings, key=len, reverse=True):
        if text.startswith(bom):
            try:
                return text[len(bom):].decode(encodings[bom])
            except UnicodeDecodeError:
                continue
    decoders = ["utf-8", "Windows-1252"]
    for decoder in decoders:
        try:
            return text.decode(decoder)
        except UnicodeDecodeError:
            continue
    #print("can't decode %s" % str(text))
    return text.decode("utf-8", "ignore")  # Ignore not compatible characters


import conans.util.files
mkdir = conans.util.files.mkdir
rmdir = conans.util.files.rmdir
remove = conans.util.files.remove
path_exists = conans.util.files.path_exists
list_folder_subdirs = conans.util.files.list_folder_subdirs
save = conans.util.files.save