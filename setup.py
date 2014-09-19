import os, os.path, stat, sys, setuptools, subprocess, urllib2

def os_system(cmd):
	retcode = subprocess.call(cmd, shell = True)
	if retcode < 0:
		raise ValueError('child was terminated by signal: %i' % (retcode,))
	elif retcode > 0:
		raise ValueError('child returned: %i' % (retcode,))

# NORMAL 1: get cwd so we can revert to it later
d = os.getcwd()
s = os.path.abspath(os.path.dirname(__file__))
p = sys.argv[:]

# HACK 0: from the V8 Makefile, add these to cache GYP and ICU locally
v8_path = os.path.join(s, 'v8')
pyv8_path = os.path.join(s, 'pyv8')
gyp_path = os.path.join(v8_path, 'build', 'gyp')
icu_path = os.path.join(v8_path, 'third_party', 'icu')
boost_fname = os.path.join(s, 'boost_1_55_0.tar.bz2')
boost_url = 'http://heanet.dl.sourceforge.net/project/boost/boost/1.55.0/boost_1_55_0.tar.bz2'

if not os.path.exists(os.path.join(v8_path, 'build/gyp/gyp')):
	os_system('(mkdir -p %(p)s && cd %(p)s && (svn upgrade || true)) && svn checkout --force http://pyv8.googlecode.com/svn/trunk                           %(p)s --revision 531   ' % {'p': pyv8_path})
	os_system('(mkdir -p %(p)s && cd %(p)s && (svn upgrade || true)) && svn checkout --force http://v8.googlecode.com/svn/trunk                             %(p)s --revision 16470 ' % {'p': v8_path})
	os_system('(mkdir -p %(p)s && cd %(p)s && (svn upgrade || true)) && svn checkout --force http://gyp.googlecode.com/svn/trunk                            %(p)s --revision 1685  ' % {'p': gyp_path})
	os_system('(mkdir -p %(p)s && cd %(p)s && (svn upgrade || true)) && svn checkout --force https://src.chromium.org/chrome/trunk/deps/third_party/icu46   %(p)s --revision 214189' % {'p': icu_path})

try:
	os_system('chmod +x %s' % (os.path.join(v8_path, 'build/gyp/gyp'),))
except:
	pass

# HACK 1: we need to add '-lrt' to extra_link_arguments, and this is one way
old_extension = setuptools.Extension

def MyExtension(*args, **kwargs):
	extra_link_args = kwargs['extra_link_args']
	extra_link_args.append('-lrt')
	return old_extension(*args, **kwargs)

setuptools.Extension = MyExtension

# HACK 2: since we chdir() before calling PyV8 setup.py, we need to adjust egg-info path
if sys.argv == ['-c', 'egg_info', '--egg-base', 'pip-egg-info']:
	sys.argv[:] = ['-c', 'egg_info', '--egg-base', '../pip-egg-info']

# HACK 3: compile Boost libraries
n = os.path.split(sys.prefix)[1]
BOOST_BASE_PATH = os.path.expanduser(os.path.join('~/src/', n))

def get_boost():
	print 'downloading boost 1.55'
	response = urllib2.urlopen(boost_url)
	size = int(response.info().getheader('Content-Length').strip())
	n_read = 0

	if os.path.exists(boost_fname):
		if os.stat(boost_fname)[stat.ST_SIZE] == size:
			print '...but it already exists and is big enough'
			return

	with open(boost_fname, 'wb+') as f:
		while True:
			chunk = response.read(1024 ** 2)

			if len(chunk) == 0:
				break

			n_read += len(chunk)
			f.write(chunk)
			print '%.2f MB read out of %.2f MB' % (float(n_read) / 1024**2, float(size) / 1024**2)

	print 'done'

get_boost()

if sys.argv != ['setup.py', 'egg_info']:
	os_system('(cd %s; tar jxf boost_1_55_0.tar.bz2; cd boost_1_55_0; ./bootstrap.sh --with-python-root=%s; ./b2 -a cxxflags=-fPIC -j8 -q --build-type=minimal --with-system --with-python --with-thread variant=release link=static runtime-link=static)' % (s, sys.prefix,))

try:
	# HACK 4: execfile() PyV8 setup.py with local() namespace

	# path of buildconf.py
	sys.path.insert(0, s)

	# path of PyV8
	sys.path.insert(0, pyv8_path)

	# jump into PyV8 build script
	os.chdir(pyv8_path)
	execfile(os.path.join(pyv8_path, 'setup.py'))

finally:
	os.chdir(d)
	sys.argv = p
