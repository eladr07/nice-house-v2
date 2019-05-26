def cache_method(func):
    def wrapper(self, *args):
        cache_key = (func.__name__, args)
        if not hasattr(self, '_method_cache'):
            self._method_cache = {}
        if cache_key in self._method_cache:
            return self._method_cache[cache_key]
        ret_val = func(self, *args)
        self._method_cache[cache_key] = ret_val
        return ret_val
    return wrapper 