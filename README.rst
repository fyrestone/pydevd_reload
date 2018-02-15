pydevd_reload
==============

This is a reload library based on pydevd_reload.py from https://github.com/fabioz/PyDev.Debugger. The original library is used in PyDev & PyCharm.


Installation
--------------

If you don't have much time, just perform

 `$ pip install pydevd_reload`

which will install the module(without tests) on your system.

Also, you can just copy & paste the pydevd_reload.py which require no third-party dependency.


Usage
--------------

Just import pydevd_reload and use pydevd_reload.xreload as the reload built-in function.

.. code-block:: python

    import pydevd_reload
    pydevd_reload.xreload(module_instance)

Update code by default
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

A running python program consists of code logic and corresponding data. Code logic is the logic of what the program perform. Corresponding data is the environment of logic running.

- A program may contain modules, classes and functions.
- A module may contain classes and functions.
- A class may contain functions.

So, function is the basic logic structure of a program. The code logic hides in the high-level function object, reloading is based on replacing the code object of function object. The running environment may change, which means it's probably dangerous to manipulate logic relevant data, so pydevd_reload provide custom hooks which allow data updates in demands.

1. pydevd_reload don't recreate the old namespace from new classes. Rather, it keeps the existing namespace, load a new version of it and update only some of the things pydevd_reload can inplace. That way, pydevd_reload don't break things such as singletons or end up with a second representation of the same class in memory.

2. If pydevd_reload find it to be a __metaclass__, then try to update it as a regular class.

3. pydevd_reload don't remove old attributes (and leave them lying around even if they're no longer used).

4. Reload hooks were changed

These changes make it more stable, especially in the common case (where in a debug session only the
contents of a function are changed), besides providing flexibility for users that want to extend
on it.

Update data by custom hooks
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

pydevd_reload reloads code objects in a module by default, and provides ``__xreload_old_new__`` and ``__xreload_after_reload_update__`` custom hooks which allow user to update data in a module. The hook functions can also be hot updated in a reload.

1. To participate in the change of some attribute:

    In a module:

    .. code-block:: python

        __xreload_old_new__(namespace, name, old, new):
            pass

    in a class:

    .. code-block:: python

        @classmethod
        def __xreload_old_new__(cls, name, old, new):
            pass

    A class or module may include a method called '__xreload_old_new__' which is called when pydevd_reload is
    unable to reload a given attribute.

2. To do something after the whole reload is finished:

    In a module:

    .. code-block:: python

        def __xreload_after_reload_update__(old_namespace, new_namespace):
            pass

    In a class:

    .. code-block:: python

        @classmethod
        def __xreload_after_reload_update__(cls, old_namespace, new_namespace):
            pass

    A class or module may include a method called '__xreload_after_reload_update__' which is called
    after the reload finishes.

Important: when providing a hook, always use the namespace or cls provided and not anything in the global
namespace, as the global namespace are only temporarily created during the reload and may not reflect the
actual application state (while the cls and namespace passed are).

Improvements
--------------

This standalone pydevd_reload library has following improvements than original pydevd_reload.py:

- Removed pydevd dependency.

- Removed limitation that functions with decorators cannot be handled. *

- Added support to update function closure. *

- Added support to update callable object. *

- Added support to update function annotation.

- Added code object name check to avoid update monkey patched code. *

- Refined reload hooks. (eg, __xreload_old_new__ and __xreload_after_reload_update__)

- Fixed __file__ attribute in namespace so they will be updated.

- Fixed compiled python file support.

- Fixed reload failed when python code compiled from different paths.

Limitations
--------------

- Attributes/constants are added, but not changed (so singletons and the application state is not
  broken -- use provided hooks to workaround it).

- Code using metaclasses may not always work.

- Renamings are not handled correctly.

- Dependent modules are not reloaded.

- New __slots__ can't be added to existing classes.

Testing
--------------
If you have the source code you can run the tests with

 `$ python pydevd_reload/tests/test_pydevd_reload.py`


Repository
--------------

The project is hosted on GitHub. You can look at the source here:

 https://github.com/fyrestone/pydevd_reload
 