from setuptools import setup

dic = {}
exec(open('pydevd_reload/pydevd_reload.py').read(), dic)
VERSION = dic['__version__']


if __name__ == '__main__':
    setup(name='pydevd_reload',
          version=VERSION,
          description='An enhanced reload module from pydev',
          long_description=open('README.rst').read(),
          author='fyrestone',
          author_email='fyrestone@outlook.com',
          url='https://github.com/fyrestone/pydevd_reload',
          license="Eclipse Public License",
          package_dir={'': 'pydevd_reload'},
          py_modules=['pydevd_reload'],
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
