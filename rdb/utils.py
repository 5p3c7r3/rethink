# borrowed heavily from google/appengine/ext/ndb/utils.py


def wrapping(wrapped):
    # A decorator to decorate a decorator's wrapper.  Following the lead
    # of Twisted and Monocle, this is supposed to make debugging heavily
    # decorated code easier.  We'll see...
    # TODO(pcostello): This copies the functionality of functools.wraps
    # following the patch in http://bugs.python.org/issue3445. We can replace
    # this once upgrading to python 3.3.
    def wrapping_wrapper(wrapper):
        try:
            wrapper.__wrapped__ = wrapped
            wrapper.__name__ = wrapped.__name__
            wrapper.__doc__ = wrapped.__doc__
            wrapper.__dict__.update(wrapped.__dict__)
            # Local functions won't have __module__ attribute.
            if hasattr(wrapped, '__module__'):
                wrapper.__module__ = wrapped.__module__
        except Exception:
            pass
        return wrapper

    return wrapping_wrapper


def positional(max_pos_args):
    """A decorator to declare that only the first N arguments may be positional.

    Note that for methods, n includes 'self'.
    """

    def positional_decorator(wrapped):

        @wrapping(wrapped)
        def positional_wrapper(*args, **kwds):
            if len(args) > max_pos_args:
                plural_s = ''
                if max_pos_args != 1:
                    plural_s = 's'
                raise TypeError(
                    '%s() takes at most %d positional argument%s (%d given)' %
                    (wrapped.__name__, max_pos_args, plural_s, len(args)))
            return wrapped(*args, **kwds)

        return positional_wrapper

    return positional_decorator