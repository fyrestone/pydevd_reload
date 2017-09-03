pydevd_reload
==============

This an reload Python library based on pydevd_reload.py from https://github.com/fabioz/PyDev.Debugger. The original library is used in PyDev & PyCharm which is based on the python xreload.

Improvements
======================

This standalone pydevd_reload library has following improvements from original pydevd_reload.py:

- Removed pydevd dependency.

- Removed limitation that functions with decorator can not be handled.

- Added support to update function closure. *

- Added detect and skip update co_name changed code objects which may be monkey patched.

- Refined reload callbacks. (eg, __xreload_old_new__ and __xreload_after_reload_update__)

- Fixed __file__ attribute in namespace not be updated.

- Fixed compiled python file support.

- Fixed reload failed when python code compiled from different paths.


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
 