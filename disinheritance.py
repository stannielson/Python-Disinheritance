"""module for managing inherited methods/attributes in subclassed object
types
"""


from dataclasses import dataclass
from functools import wraps
from types import MethodType


__author__  = 'Stanton K. Nielson'
__license__ = 'Unlicense'
__version__ = '1.0.0'
__status__  = 'Production'
__date__    = '2025-07-09'


__all__ = 'disinherit',


class disinherit:

    """decorator to remove access to inherited methods/attributes in an
    object type, except where specified by the exempt keyword argument
    - functionally required "progenitor" object methods will be retained
    - exemptions not part of MRO are ignored
    """

    def __init__(self, *, exempt: type | MethodType |
                 list[type | MethodType] | tuple[type | MethodType] |
                 set[type | MethodType] = None):
        self.exempt = exempt
        return

    def __call__(self, target: type):
        return self.in_type(target, self.exempt)

    @classmethod
    def in_type(cls, target: type, exempt: type | MethodType |
                list[type | MethodType] | tuple[type | MethodType] |
                set[type | MethodType] = None) -> type:
        """disinherits methods/attributes from a target type, except for
        required methods and specified exemptions
        """
        for i in cls._get_invalid_names(target, exempt):
            setattr(target, i, NotImplemented)
        cls._wrap_dir(target)
        cls._wrap_getter(target)
        return target

    @classmethod
    def _coerce_exempt(cls, exempt: list | tuple | set | type) -> list:
        """internal class method to coerce exemptions for disinheritance
        to a set of methods/attributes
        """
        if exempt is None: return set()
        elif not isinstance(exempt, (list, tuple, set)):
            exempt = [exempt]
        exempt, coerced = list(exempt), set()
        for i in exempt:
            if isinstance(i, type):
                coerced |= set(cls._map_type(i).values())
            else:
                try: coerced.add(i)
                except: pass
        return list(coerced)

    @classmethod
    def _get_invalid_names(
        cls, target: type,
        exempt: list | tuple | set | type = None) -> set[str]:
        """internal class method to identify names of methods/attributes
        considered invalid in the target subclass (unless part of exempted
        methods/attributes)
        """
        exempt = cls._coerce_exempt(exempt)
        current, *ancestors, progenitor = target.mro()
        required = dict(
            (k, v) for k, v in cls._map_type(progenitor).items()
            if len(k.strip('_')) > 2)
        valid, invalid = dict(vars(target)), set()
        for ancestor in ancestors:
            type_invalid = cls._map_type(ancestor)
            type_invalid.pop('__dict__', None)
            for k, v in required.items():
                type_invalid.pop(k, None)
            for k, v in valid.items():
                if k in type_invalid and v != type_invalid[k]:
                    type_invalid.pop(k)
            type_invalid = dict((k, v) for k, v in type_invalid.items()
                              if v is NotImplemented or v not in exempt)
            invalid |= set(type_invalid)
        return invalid

    @classmethod
    def _map_type(cls, target: type) -> dict:
        """internal class method to return mapping of names and associated
        methods/attributes for a target type
        """
        return dict((name, getattr(target, name)) for name in dir(target))

    @classmethod
    def _wrap_dir(cls, target: type) -> object.__dir__:
        """internal class method to wrap __dir__ in the target type to
        prevent return of disinherited methods/attributes
        """
        dir_base = target.__dir__
        @wraps(dir_base)
        def __dir__(self) -> list[str]:
            return list(i for i in dir_base(self) if
                        getattr(self, i, NotImplemented) is not
                        NotImplemented)
        if __dir__ != dir_base: target.__dir__ = __dir__
        return

    @classmethod
    def _wrap_getter(cls, target: type):
        """internal class method to wrap __getattribute__ in the target
        type to prevent return of disinherited methods/attributes
        """
        getter_base = target.__getattribute__
        @wraps(getter_base)
        def __getattribute__(self, name: str):
            result = getter_base(self, name)
            if result is NotImplemented:
                error = AttributeError(
                    f'{repr(type(self).__name__)} object has no '\
                    f'attribute {repr(name)}')
                raise error
            return result
        if __getattribute__ != getter_base:
            target.__getattribute__ = __getattribute__    
        return   
