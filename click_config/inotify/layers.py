__author__ = 'bergundy'


class LayerDict(object):
    def __init__(self):
        self._layers = {}
        """
        :type self._layers: dict(dict)
        """

    def set_layer(self, key, dct):
        prev = self._layers.get(key, {})
        self._layers[key] = dct
        return self._calc_changes(key, prev, dct)

    def del_layer(self, key):
        prev = self._layers.pop(key, {})
        return self._calc_changes(key, prev, {})

    def _calc_changes(self, key, prev, curr):
        added, removed, modified = calc_diff(prev, curr)
        updated = added | removed | modified
        sorted_layers = (self._layers[k] for k in sorted(self._layers) if k > key)
        for l in sorted_layers:
            updated -= l.viewkeys()
            if not updated:
                break

        return {k: curr.get(k) for k in updated}


def calc_diff(a, b):
    a_keys = a.viewkeys()
    b_keys = b.viewkeys()

    added = b_keys - a_keys
    removed = a_keys - b_keys
    common = a_keys & b_keys

    values = lambda d: (d[k] for k in common)
    modified = {k for k, ak, bk in zip(common, values(a), values(b)) if ak != bk}

    return added, removed, modified
