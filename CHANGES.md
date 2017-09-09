HISTORY
--------

## 1.1 (2017-09-09)

- Added support to update function annotation.
- Added and fixed test case.
- Fixed python 3 compatibility issue.
- Refined README.

## 1.0 (2017-09-03)

- Removed pydevd dependency.
- Removed limitation that functions with decorators cannot be handled. *
- Added support to update function closure. *
- Added code object name check to avoid update monkey patched code. *
- Refined reload hooks. (eg, __xreload_old_new__ and __xreload_after_reload_update__)
- Fixed __file__ attribute in namespace so they will be updated.
- Fixed compiled python file support.
- Fixed reload failed when python code compiled from different paths.
