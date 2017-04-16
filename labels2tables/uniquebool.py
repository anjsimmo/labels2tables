import copy
import collections
from enum import Enum

# Python's built in bools, True and False, are equal to 1 and 0.
# This can lead to many subtle bugs in table columns that mix bools with numbers.
# For example, if one row starts with a True cell, and the row below starts with a 1 cell,
# these might be accidentally merged together in a partition because True == 1.
# To solve this, we introduce our own bool variables that behave like ordinary objects.

class UniqueBool(object):
    def __init__(self, name):
        self._name = name
    def __repr__(self):
        return self._name
    def __deepcopy__(self, _):
        # For equity to work as expected, we want to keep the same instance
        # http://stackoverflow.com/questions/9887501/deepcopy-does-not-respect-metaclass
        return self
    def __copy__(self, _):
        # For equity to work as expected, we want to keep the same instance
        # http://stackoverflow.com/questions/9887501/deepcopy-does-not-respect-metaclass
        return self

TRUE = UniqueBool("TRUE") # unique object
FALSE = UniqueBool("FALSE") # unique object

def deep_replace_bool(obj):
    """
    obj -- list, tuple or item that contains ordinary Python bools.
           Assumed to be acyclic.
    return -- santitized copy of object with Python bools replaced by TRUE and FALSE objects.
              Only values will be replaced, keys will be unchanged.
              Immutable collections (other than tuple) are not supported
    """
    def rep(item):
        if item is True:
            return TRUE
        elif item is False:
            return FALSE
        else:
            return item
    
    cpy = copy.deepcopy(obj)
    deep_replace(cpy, rep)
    return cpy

def deep_replace(obj, replace_func):
    """
    obj -- list, tuple or item. Assumed to be acyclic.
    replace_func -- function(item) to return replacement items
    """
    if isinstance(obj, collections.Mapping):
        for k,v in obj.items():
            obj[k] = deep_replace(v, replace_func)
        return obj
    elif isinstance(obj, collections.MutableSequence):
        for k,v in enumerate(obj):
            obj[k] = deep_replace(v, replace_func)
        return obj
    elif type(obj) is tuple:
        return tuple(deep_replace(v, replace_func) for v in obj)
    else:
        return replace_func(obj)
