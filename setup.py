from setuptools import setup
from setuptools.extension import Extension

dic = {}
exec(open('pydevd_reload/pydevd_reload.py').read(), dic)
VERSION = dic['__version__']


if __name__ == '__main__':
    setup(name='pydevd_reload',
          version=VERSION,
          description='An enhanced reload module from PyDev',
          long_description=open('README.rst').read(),
          author='fyrestone',
          author_email='fyrestone@outlook.com',
          url='https://github.com/fyrestone/pydevd_reload',
          license="Eclipse Public License",
          packages=['pydevd_reload'],
          ext_modules=[Extension("pydevd_reload._pydevd_reload", ["pydevd_reload/_pydevd_reload.c"])],
          keywords="reload generic utility",
          platforms=["All"],
          classifiers=['Development Status :: 5 - Production/Stable',
                       'Intended Audience :: Developers',
                       'License :: OSI Approved :: Eclipse Public License 1.0 (EPL-1.0)',
                       'Natural Language :: English',
                       'Operating System :: OS Independent',
                       'Programming Language :: Python :: 2',
                       'Programming Language :: Python :: 3',
                       'Topic :: Software Development :: Libraries',
                       'Topic :: Utilities'],
          test_suite='tests',
          zip_safe=False)
