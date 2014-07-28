import sys, os.path

V8_SVN_REVISION = 16470
V8_HOME = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'v8')
BOOST_HOME = os.path.expanduser(os.path.join('~/src/', os.path.split(sys.prefix)[1], 'boost_1_55_0'))
PYTHON_HOME = sys.prefix
