# Python Disinheritance
**_Disinheritance_** is the removal of inherited methods and attributes to prevent (i.e., "disinherit") unwanted capabilities in subclass types. Nominally, the approach to disinheritance in Python is by individually overriding the unwanted methods and attributes of a subclass. However, depending on the behavior of a parent class, this can be a laborious process, especially if a large amount of parent methods and attributes are unwanted. Another approach is by structuring types and subclassed types to ensure limited inheritance (e.g., with "mixin" use), which could require more complexity in creating appropriate subclass types.

When other approaches are impractical, the `disinheritance` module may be a viable alternative. The `disinherit` decorator object automatically overrides unwanted inherited methods and attributes and prevents their use in subclass instances, except where specified as exemptions. Features of `disinherit` include:

* Exemptions can be one or more type methods/attributes or even entire types in the subclass MRO (though exemptions are managed internally by type/containing type and declaration order)
* Exemptions can be from anywhere in the MRO and will be applied to the subclass as overrides (unless already overriden in the subclass)
* `dir()` call on a subclass instance will not include disinherited methods/attributes
* Attempts at attribute retrieval of disinherited methods/attributes from an instance produce attribute errors
* `help()` call on a subclass type will show disinherited methods/attributes as not implemented (i.e., as the `NotImplemented` singleton)
* Invalid exemptions (i.e., types and type methods/attributes not in the MRO) are silently ignored
* Subclass `__dir__` and `__getattribute__` methods are wrapped to both maintain original functionality and account for disinherited methods/attributes
* Exemptions are explicitly specified using an `exempt` keyword argument for the sake of clarity and deliberate use in style

## Example:
```
from disinheritance import disinherit

@disinherit()
class StrStandin(str):
    """object does not function like a regular str"""

@disinherit(exempt=str.upper)
class StrUpper(str):
    """object allows upper method"""
```

```
>>> standin = StrStandin('hello, world!')
>>> upperonly = StrUpper('spam and eggs')
```

```
>>> dir(standin)
['__class__', '__delattr__', '__dict__', '__dir__', '__doc__', '__format__',
'__getattribute__', '__getstate__', '__hash__', '__init__', '__init_subclass__',
'__module__', '__new__', '__reduce__', '__reduce_ex__', '__repr__',
'__setattr__', '__sizeof__', '__str__', '__subclasshook__', '__weakref__']
```

```
>>> standin.upper()
Traceback (most recent call last):
  File "<pyshell#87>", line 1, in <module>
    value.upper()
  File ".../disinheritance.py", line 188, in __getattribute__
    raise error
AttributeError: 'StrStandin' object has no attribute 'upper'
```

```
>>> upperonly.upper()
'SPAM AND EGGS'
```
