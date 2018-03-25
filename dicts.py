class BiDict(dict):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for key, value in self.items():
            self[value] = key

    def __setitem__(self, key, value):
        if key in self:
            super().__delitem__(self[key])
        super().__setitem__(key, value)
        super().__setitem__(value, key)

    def __delitem__(self, key):
        super().__delitem__(self[key])
        super().__delitem__(key)


class AttrDict(dict):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.__dict__ = self

    def update(self, *d, **kwargs):
        for key, val in (d[0] if d else kwargs).items():
            setattr(self, key, val)

    def __getattr__(self, item):
        # expected behaviour:
        raise AttributeError(f"{self.__class__.__name__} object has no attribute {item}")

        # what we actually do:
        # return self.setdefault(item, AttrDict())

__all__ = ['AttrDict', 'BiDict']
