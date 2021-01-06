import sys
import os
import yaml


def abspath(x):
    return os.path.abspath(os.path.expanduser(x))

def exec_extension(name, argv):
    extension_path = abspath(f"~/.epm/extension/{name}")
    if not os.path.exists(f"{extension_path}/extension.yml"):
        raise
    with open(f"{extension_path}/extension.yml") as f:
        conf = yaml.safe_load(f)

    prototype = conf.get('prototype', None)
    Prototype = None
    if prototype:
        Prototype = load_prototype(prototype)
        assert Prototype
    if Prototype:


# epm extension hx zzz
def main(argv):
    exec_extension('mkprj', argv)

if __name__ == '__main__':
    main(sys.argv[1:])