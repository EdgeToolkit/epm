
from collections import OrderedDict


def to_ordered_dict(data):
    od = OrderedDict()
    data = data or []
    assert isinstance(data, (list, tuple))
    for i in data:
        assert isinstance(i, dict) and len(i) == 1
        for k, v in i.items():
            od[k] = v
    return od


def sandbox_builds_filter(name, sbs):
    builds = {}
    programs = name
    all = [sb.name for sb in sbs]

    if isinstance(name, str):
        programs = [name]

    if name is None:
        programs = all
    else:
        bads = set(programs).difference(set(all))
        if bads:
            raise Exception("{} not defined in sandbox".format(",".join(bads)))

    for sb in sbs:
        if sb.name in programs:
            if sb.directory not in builds:
                builds[sb.directory] = [sb]
            else:
                builds[sb.directory] += [sb]

    return builds