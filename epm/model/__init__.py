
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

