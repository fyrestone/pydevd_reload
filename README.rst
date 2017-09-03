pydevd_reload
==============

This is a reload library based on pydevd_reload.py from https://github.com/fabioz/PyDev.Debugger. The original library is used in PyDev & PyCharm.


Installation
--------------

If you don't have much time, just perform

 `$ pip install pydevd_reload`

which will install just the module on your system.

Also, you can just copy & paste the pydevd_reload.py which require no third-party dependency.


Usage
--------------

Just import pydevd_reload and use pydevd_reload.xreload as the reload built-in function.

.. code-block:: python

    import pydevd_reload
    pydevd_reload.xreload(module_instance)
	
pydevd_reload reload code objects in a module by default, and provide __xreload_old_new__ and __xreload_after_reload_update__ custom hook allow user update data in a module:


Original module:

.. code-block:: python

	class B(object):
		CONSTANT = 1

		def foo(self):
			return self.CONSTANT
			
			
Updated module:

.. code-block:: python

	class B(object):

		CONSTANT = 2

		# Custom hooks can be added in a reload.
		def __xreload_old_new__(cls, name, old, new):
			if name == 'CONSTANT':
				cls.CONSTANT = new
		__xreload_old_new__ = classmethod(__xreload_old_new__)

		def foo(self):
			return self.CONSTANT	


Improvements
--------------

This standalone pydevd_reload library has following improvements than original pydevd_reload.py:

- Removed pydevd dependency.

- Removed limitation that functions with decorators cannot be handled. *

- Added support to update function closure. *

- Added code object name check to avoid update monkey patched code. *

- Refined reload callbacks. (eg, __xreload_old_new__ and __xreload_after_reload_update__)

- Fixed __file__ attribute in namespace so they will be updated.

- Fixed compiled python file support.

- Fixed reload failed when python code compiled from different paths.


Testing
--------------
If you have the source code you can run the tests with

 `$ python pydevd_reload/tests/test_pydevd_reload.py`


Repository
--------------

The project is hosted on GitHub. You can look at the source here:

 https://github.com/fyrestone/pydevd_reload
 