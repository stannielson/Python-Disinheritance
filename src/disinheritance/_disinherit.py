"""module for managing inherited methods/attributes in subclassed object
types
"""


from functools import wraps
from inspect import getabsfile
from inspect import getmodule
from types import MethodType


__all__ = 'disinherit',


class disinherit:

    """decorator to remove access to inherited methods/attributes in an
    object type, except where specified by the exempt keyword argument
    
    - exemptions are applied in order of argument declaration
    
    - exemptions not available through inheritance or overridden in the
      target type are ignored
      
    - functionally required "origin" object methods will be retained
    
    - disinherited methods/attributes are replaced with NotImplemented in
      the target type
      
      -> NotImplemented methods/attributes are ignored in dir() calls for
         and produce an AttributeError when retrieved from target type
         instances
        
      -> provides explicit status in help() call on target type
      
      -> use ensures reversion back to disinheritance if used for
         assignment but deleted in instances
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
        mro_map = cls._map_mro(target)
        exempt = cls._coerce_exempt(mro_map, exempt)
        invalid = cls._get_invalid_names(target, mro_map, exempt)
        for name in invalid: setattr(target, name, NotImplemented)
        target_map = dict((k, v) for k, v in cls._map_type(target).items()
                          if k not in invalid)
        for exempt_map in exempt.values():
            for name, value in exempt_map.items():
                if name not in target_map:
                    setattr(target, name, value)
        cls._wrap_dir(target)
        cls._wrap_getter(target)
        return target

    @classmethod
    def _coerce_exempt(cls, mro_map: dict, exempt: type | MethodType |
                       list | tuple | set = None) -> dict[str, dict]:
        """internal class method to coerce exemptions for disinheritance
        to a mapping of methods/attributes
        """
        if exempt is None: return dict()
        elif not isinstance(exempt, (list, tuple, set)):
            exempt = [exempt]
        elif not isinstance(exempt, list):
            try: exempt = list(exempt)
            except: return dict()
        exempt = list(i for i in exempt if hasattr(i, '__objclass__')
                      or isinstance(i, type))
        coerced = dict()
        for i in exempt:
            if isinstance(i, type):
                coerced[cls._make_type_key(i)] = cls._map_type(i)
            else: 
                key = cls._make_type_key(i.__objclass__)
                submap = {i.__name__: i}
                try: coerced[key].update(submap)
                except: coerced[key] = submap
        coerced = dict((k, v) for k, v in coerced.items()
                       if k in mro_map)
        return coerced

    @classmethod
    def _get_invalid_names(cls, target: type, mro_map: dict,
                           exempt: dict) -> set[str]:
        """internal class method to identify names of methods/attributes
        considered invalid in the target subclass (unless part of exempted
        methods/attributes)
        """
        *ancestor_keys, _ = list(mro_map)[1:]
        required = set(
            i for i in cls._map_type(object) if len(i.strip('_')) > 2)
        valid, invalid = set(vars(target)), set()
        for key in ancestor_keys:
            type_invalid = dict(
                (name, value) for name, value in mro_map[key].items()
                if all((name not in required, name not in valid,
                        name not in exempt.get(key, set()),
                        name != '__dict__')))
            invalid |= set(type_invalid)
        return invalid

    @classmethod
    def _make_type_key(cls, target: type) -> str:
        """internal class method to create a nominally unique key for a
        target type based on its module file location (or module name)
        and its own name; intended to account for conflicting type names
        in a target MRO
        """
        if not isinstance(target, type):
            error = TypeError(f'{repr(target)} not a valid type')
            raise error
        try:
            name = target.__name__
            try: source = getabsfile(target)
            except: source = getmodule(target).__name__
            return f'{source}->{repr(name)}'
        except Exception as e:
            error = TypeError(
                f'cannot determine origin of {repr(target)} as a type')
            raise error
        return

    @classmethod
    def _map_mro(cls, target: type) -> dict:
        """internal class method to map the MRO of a target type with
        nominally unique key references for types and associated method/
        attribute mappings by name and value
        """
        return dict((cls._make_type_key(i), cls._map_type(i))
                    for i in target.mro())

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
