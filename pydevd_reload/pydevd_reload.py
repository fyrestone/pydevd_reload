"""
Based on the python xreload.

GitHub: https://github.com/fyrestone/pydevd_reload
Original: https://github.com/fabioz/PyDev.Debugger/blob/master/_pydevd_bundle/pydevd_reload.py


Changes
======================

1. we don't recreate the old namespace from new classes. Rather, we keep the existing namespace,
load a new version of it and update only some of the things we can inplace. That way, we don't break
things such as singletons or end up with a second representation of the same class in memory.

2. If we find it to be a __metaclass__, we try to update it as a regular class.

3. We don't remove old attributes (and leave them lying around even if they're no longer used).

4. Reload hooks were changed

These changes make it more stable, especially in the common case (where in a debug session only the
contents of a function are changed), besides providing flexibility for users that want to extend
on it.



Hooks
======================

Classes/modules can be specially crafted to work with the reload (so that it can, for instance,
update some constant which was changed).

1. To participate in the change of some attribute:

    In a module:

    __xreload_old_new__(namespace, name, old, new)

    in a class:

    @classmethod
    __xreload_old_new__(cls, name, old, new)

    A class or module may include a method called '__xreload_old_new__' which is called when we're
    unable to reload a given attribute.



2. To do something after the whole reload is finished:

    In a module:

    __xreload_after_reload_update__(old_namespace, new_namespace):

    In a class:

    @classmethod
    __xreload_after_reload_update__(cls, old_namespace, new_namespace):


    A class or module may include a method called '__xreload_after_reload_update__' which is called
    after the reload finishes.


Important: when providing a hook, always use the namespace or cls provided and not anything in the global
namespace, as the global namespace are only temporarily created during the reload and may not reflect the
actual application state (while the cls and namespace passed are).


Current limitations
======================


- Attributes/constants are added, but not changed (so singletons and the application state is not
  broken -- use provided hooks to workaround it).

- Code using metaclasses may not always work.

- Renamings are not handled correctly.

- Dependent modules are not reloaded.

- New __slots__ can't be added to existing classes.


Info
======================

Original: http://svn.python.org/projects/sandbox/trunk/xreload/xreload.py
Note: it seems https://github.com/plone/plone.reload/blob/master/plone/reload/xreload.py enhances it (to check later)

Interesting alternative: https://code.google.com/p/reimport/

Alternative to reload().

This works by executing the module in a scratch namespace, and then patching classes, methods and
functions in place.  This avoids the need to patch instances.  New objects are copied into the
target namespace.

"""

import imp
# from pydev_imports import Exec
# import pydevd_dont_trace
import os
import sys
import traceback
import types
try:
    from itertools import izip
except ImportError:
    izip = zip

__version__ = '1.2'

NO_DEBUG = 0
LEVEL1 = 1
LEVEL2 = 2

DEBUG = NO_DEBUG


def _exec(exp, global_vars, local_vars=None):
    if local_vars is not None:
        exec(exp, global_vars, local_vars)
    else:
        exec(exp, global_vars)

def write(*args):
    new_lst = []
    for a in args:
        new_lst.append(str(a))

    msg = ' '.join(new_lst)
    sys.stdout.write('%s\n' % (msg,))

def write_err(*args):
    new_lst = []
    for a in args:
        new_lst.append(str(a))

    msg = ' '.join(new_lst)
    sys.stderr.write('pydev debugger: %s\n' % (msg,))

def notify_info0(*args):
    write_err(*args)

def notify_info(*args):
    if DEBUG >= LEVEL1:
        write(*args)

def notify_info2(*args):
    if DEBUG >= LEVEL2:
        write(*args)

def notify_error(*args):
    write_err(*args)



#=======================================================================================================================
# code_objects_equal
#=======================================================================================================================
def code_objects_monkeypatched(code0, code1):
    """
    If the code name changed, the old code probably be monkey patched,
    but monkey patched code object may not change the code name.
    """
    return getattr(code0, 'co_name') != getattr(code1, 'co_name')

def code_objects_equal(code0, code1):
    for d in dir(code0):
        # old code and new code may compile from different paths, so it is not necessary to compare the filename.
        if d.startswith('_') or 'lineno' in d or 'filename' in d:
            continue
        if getattr(code0, d) != getattr(code1, d):
            return False
    return True


#=======================================================================================================================
# xreload
#=======================================================================================================================
def xreload(mod):
    """Reload a module in place, updating classes, methods and functions.

    mod: a module object

    Returns a boolean indicating whether a change was done.
    """
    r = Reload(mod)
    r.apply()
    found_change = r.found_change
    # r = None
    # pydevd_dont_trace.clear_trace_filter_cache()
    return found_change


# This isn't actually used... Initially I planned to reload variables which are immutable on the
# namespace, but this can destroy places where we're saving state, which may not be what we want,
# so, we're being conservative and giving the user hooks if he wants to do a reload.
#
# immutable_types = [int, str, float, tuple] #That should be common to all Python versions
#
# for name in 'long basestr unicode frozenset'.split():
#     try:
#         immutable_types.append(__builtins__[name])
#     except:
#         pass #Just ignore: not all python versions are created equal.
# immutable_types = tuple(immutable_types)


#=======================================================================================================================
# Reload
#=======================================================================================================================
class Reload(object):

    def __init__(self, mod):
        self.mod = mod
        self.found_change = False
        self._on_finish_callbacks = []

    def apply(self):
        mod = self.mod
        self._on_finish_callbacks = []
        try:
            # Get the module name, e.g. 'foo.bar.whatever'
            modname = mod.__name__
            # Compatible with main module
            mainmod = False
            if modname == '__main__':
                modname = os.path.splitext(os.path.basename(mod.__file__))[0]
                mainmod = True
            # Get the module namespace (dict) early; this is part of the type check
            modns = mod.__dict__
            # Parse it into package name and module name, e.g. 'foo.bar' and 'whatever'
            i = modname.rfind(".")
            if i >= 0:
                pkgname, modname = modname[:i], modname[i + 1:]
            else:
                pkgname = None
            # Compute the search path
            if pkgname:
                # We're not reloading the package, only the module in it
                pkg = sys.modules[pkgname]
                path = pkg.__path__  # Search inside the package
            else:
                # Search the top-level module path
                pkg = None
                path = None  # Make find_module() uses the default search path
            # Find the module; may raise ImportError
            (stream, filename, (suffix, mode, kind)) = imp.find_module(modname, path)
            # Turn it into a code object
            try:
                # Is it Python source code or byte code read from a file?
                if kind not in (imp.PY_COMPILED, imp.PY_SOURCE):
                    # Fall back to built-in reload()
                    notify_error('Could not find source to reload (mod: %s)' % (modname,))
                    return
                if kind == imp.PY_SOURCE:
                    source = stream.read()
                    code = compile(source, filename, "exec")
                else:
                    import marshal
                    # Compiled Python file consist of
                    # 1, magic number (4 bytes) to determine type and version of Python,
                    # 2, timestamp (4 bytes) to check whether we have newer source,
                    # 3, size of source file (4 bytes) since Python 3.3+,
                    # 4, marshaled code object.
                    # see also, pkgutil.read_code and runpy._get_code_from_file
                    stream.read(8)
                    if sys.version_info.major == 3 and sys.version_info.minor >= 3:
                        stream.read(4)
                    code = marshal.load(stream)
            finally:
                if stream:
                    stream.close()
            # Execute the code.  We copy the module dict to a temporary; then
            # clear the module dict; then execute the new code in the module
            # dict; then swap things back and around.  This trick (due to
            # Glyph Lefkowitz) ensures that the (readonly) __globals__
            # attribute of methods and functions is set to the correct dict
            # object.
            new_namespace = modns.copy()
            new_namespace.clear()
            if mainmod:
                new_namespace["__name__"] = modname
            else:
                new_namespace["__name__"] = modns["__name__"]
            new_namespace["__file__"] = modns["__file__"]
            _exec(code, new_namespace)
            # Now we get to the hard part
            oldnames = set(modns)
            newnames = set(new_namespace)

            # Create new tokens (note: not deleting existing)
            for name in newnames - oldnames:
                notify_info0('Added:', name, 'to namespace')
                self.found_change = True
                modns[name] = new_namespace[name]

            # Update in-place what we can
            for name in oldnames & newnames:
                self._update(modns, name, modns[name], new_namespace[name])

            self._handle_namespace(modns, new_namespace)

            for c in self._on_finish_callbacks:
                ret = c()
                if ret not in [True, False]:
                    notify_error('Unexpected return value %s of function %s' % (ret, c.__name__))
                elif ret is True:
                    self.found_change = True
            del self._on_finish_callbacks[:]
        except:
            traceback.print_exc()


    def _handle_namespace(self, old_namespace, new_namespace, is_class_namespace=False):
        on_finish = None
        if is_class_namespace:
            xreload_after_update = getattr(old_namespace, '__xreload_after_reload_update__', None)
            if callable(xreload_after_update):
                on_finish = lambda: xreload_after_update(old_namespace, new_namespace)
                on_finish.__name__ = '.'.join([old_namespace.__name__, xreload_after_update.__name__])

        elif '__xreload_after_reload_update__' in old_namespace:
            xreload_after_update = old_namespace['__xreload_after_reload_update__']
            if callable(xreload_after_update):
                on_finish = lambda: xreload_after_update(old_namespace, new_namespace)
                on_finish.__name__ = '.'.join([old_namespace['__name__'], xreload_after_update.__name__])


        if on_finish is not None:
            # If a client wants to know about it, give him a chance.
            self._on_finish_callbacks.append(on_finish)



    def _update(self, namespace, name, oldobj, newobj, is_class_namespace=False):
        """Update oldobj, if possible in place, with newobj.

        If oldobj is immutable, this simply returns newobj.

        Args:
          oldobj: the object to be updated
          newobj: the object used as the source for the update
        """
        try:
            notify_info2('Updating: ', oldobj)
            if oldobj is newobj:
                # Probably something imported
                notify_info2('Identical objects: ', oldobj, newobj)
                return

            if type(oldobj) is not type(newobj) and type(oldobj).__name__ != type(newobj).__name__:
                # Cop-out: if the type changed, give up
                notify_error('Type of: %s changed... Skipping.' % (oldobj,))
                return

            if isinstance(newobj, types.FunctionType):
                notify_info2('Update function: ', oldobj, newobj)
                self._update_function(oldobj, newobj)
                return

            if isinstance(newobj, types.MethodType):
                notify_info2('Update method: ', oldobj, newobj)
                self._update_method(oldobj, newobj)
                return

            if isinstance(newobj, classmethod):
                notify_info2('Update classmethod: ', oldobj, newobj)
                self._update_classmethod(oldobj, newobj)
                return

            if isinstance(newobj, staticmethod):
                notify_info2('Update staticmethod: ', oldobj, newobj)
                self._update_staticmethod(oldobj, newobj)
                return

            if hasattr(types, 'ClassType'):
                classtype = (types.ClassType, type) #object is not instance of types.ClassType.
            else:
                classtype = type

            if isinstance(newobj, classtype):
                notify_info2('Update class: ', oldobj, newobj)
                self._update_class(oldobj, newobj)
                return

            # New: dealing with metaclasses.
            if hasattr(newobj, '__metaclass__') and hasattr(newobj, '__class__') and newobj.__metaclass__ == newobj.__class__:
                notify_info2('Update metaclass: ', oldobj, newobj)
                self._update_class(oldobj, newobj)
                return

            if hasattr(newobj, '__call__'):
                notify_info2('Update callable: ', oldobj, newobj)
                self._update_callable(oldobj, newobj)
                return

            if namespace is not None:
                notify_info2('Update data: ', newobj)

                if oldobj != newobj and str(oldobj) != str(newobj) and repr(oldobj) != repr(newobj):
                    if is_class_namespace:
                        xreload_old_new = getattr(namespace, '__xreload_old_new__', None)
                        if callable(xreload_old_new):
                            ret = xreload_old_new(name, oldobj, newobj)
                            if ret not in [True, False]:
                                func_name = '.'.join([namespace.__name__, xreload_old_new.__name__])
                                notify_error('Unexpected return value %s of function %s.' % (ret, func_name))
                            elif ret is True:
                                self.found_change = True

                    elif '__xreload_old_new__' in namespace:
                        xreload_old_new = namespace['__xreload_old_new__']
                        if callable(xreload_old_new):
                            ret = xreload_old_new(namespace, name, oldobj, newobj)
                            if ret not in [True, False]:
                                func_name = '.'.join([namespace['__name__'], xreload_old_new.__name__])
                                notify_error('Unexpected return value %s of function %s.' % (ret, func_name))
                            elif ret is True:
                                self.found_change = True

                    # Too much information to the user...
                    # else:
                    #     notify_info0('%s NOT updated. Create __xreload_old_new__(name, old, new) for custom reload' % (name,))

        except:
            notify_error('Exception found when updating %s. Proceeding for other items.' % (name,))
            traceback.print_exc()


    # All of the following functions have the same signature as _update()


    def _update_function(self, oldfunc, newfunc):
        """Update a function object."""
        oldfunc.__doc__ = newfunc.__doc__
        oldfunc.__dict__.update(newfunc.__dict__)

        try:
            oldfunc.__annotations__ = newfunc.__annotations__
        except AttributeError:
            pass  # No function annotation in Python 2.x

        try:
            newfunc.__code__
            attr_name = '__code__'
        except AttributeError:
            newfunc.func_code
            attr_name = 'func_code'

        old_code = getattr(oldfunc, attr_name)
        new_code = getattr(newfunc, attr_name)

        if code_objects_monkeypatched(old_code, new_code):
            notify_error('Code of: %s monkey patched... Skipping.' % (oldfunc,))
            return oldfunc

        if not code_objects_equal(old_code, new_code):
            notify_info0('Updated function code:', oldfunc)
            setattr(oldfunc, attr_name, new_code)
            self.found_change = True

        try:
            oldfunc.__defaults__ = newfunc.__defaults__
        except AttributeError:
            oldfunc.func_defaults = newfunc.func_defaults

        # Update func_closure:
        # 1, skip if function closure count mismatch,
        # 2, only do update by the same function closure sequence.

        try:
            newfunc.__closure__
            attr_name = '__closure__'
        except AttributeError:
            newfunc.func_closure
            attr_name = 'func_closure'

        old_closure = getattr(oldfunc, attr_name) or []
        new_closure = getattr(newfunc, attr_name) or []

        if len(old_closure) != len(new_closure):
            notify_error('Closure count of: %s changed... Skipping.' % (oldfunc,))
            return oldfunc

        for old_cell, new_cell in izip(old_closure, new_closure):
            self._update(None, None, old_cell.cell_contents, new_cell.cell_contents)

        return oldfunc


    def _update_method(self, oldmeth, newmeth):
        """Update a method object."""
        # XXX What if im_func is not a function?
        if hasattr(oldmeth, 'im_func') and hasattr(newmeth, 'im_func'):
            self._update(None, None, oldmeth.im_func, newmeth.im_func)
        elif hasattr(oldmeth, '__func__') and hasattr(newmeth, '__func__'):
            self._update(None, None, oldmeth.__func__, newmeth.__func__)
        return oldmeth


    def _update_class(self, oldclass, newclass):
        """Update a class object."""
        olddict = oldclass.__dict__
        newdict = newclass.__dict__

        oldnames = set(olddict)
        newnames = set(newdict)

        for name in newnames - oldnames:
            setattr(oldclass, name, newdict[name])
            notify_info0('Added:', name, 'to', oldclass)
            self.found_change = True

        # Note: not removing old things...
        # for name in oldnames - newnames:
        #    notify_info('Removed:', name, 'from', oldclass)
        #    delattr(oldclass, name)

        for name in (oldnames & newnames) - {'__dict__', '__doc__'}:
            self._update(oldclass, name, olddict[name], newdict[name], is_class_namespace=True)

        old_bases = getattr(oldclass, '__bases__', None)
        new_bases = getattr(newclass, '__bases__', None)
        if str(old_bases) != str(new_bases):
            notify_error('Changing the hierarchy of a class is not supported. %s may be inconsistent.' % (oldclass,))

        self._handle_namespace(oldclass, newclass, is_class_namespace=True)


    def _update_classmethod(self, oldcm, newcm):
        """Update a classmethod update."""
        # While we can't modify the classmethod object itself (it has no
        # mutable attributes), we *can* extract the underlying function
        # (by calling __get__(), which returns a method object) and update
        # it in-place.  We don't have the class available to pass to
        # __get__() but any object except None will do.
        self._update(None, None, oldcm.__get__(0), newcm.__get__(0))


    def _update_staticmethod(self, oldsm, newsm):
        """Update a staticmethod update."""
        # While we can't modify the staticmethod object itself (it has no
        # mutable attributes), we *can* extract the underlying function
        # (by calling __get__(), which returns it) and update it in-place.
        # We don't have the class available to pass to __get__() but any
        # object except None will do.
        self._update(None, None, oldsm.__get__(0), newsm.__get__(0))


    def _update_callable(self, oldcb, newcb):
        """
        Update a callable object, this object may contains one or many
        functions. But for performance issue, we only update first level
        of object's dict.
        """
        olddict = oldcb.__dict__
        newdict = newcb.__dict__

        oldnames = set(olddict)
        newnames = set(newdict)

        for name in newnames - oldnames:
            setattr(oldcb, name, newdict[name])
            notify_info0('Added:', name, 'to', oldcb)
            self.found_change = True

        # Note: not removing old things...
        # for name in oldnames - newnames:
        #    notify_info('Removed:', name, 'from', oldclass)
        #    delattr(oldclass, name)

        for name in (oldnames & newnames) - {'__dict__', '__doc__'}:
            self._update(oldcb, name, olddict[name], newdict[name])

        # self._update_class(type(oldcb), type(newcb))
