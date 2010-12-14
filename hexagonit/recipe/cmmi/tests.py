from zope.testing import doctest
from zope.testing import renormalizing

import errno
import os
import re
import shutil
import stat
import tarfile
import tempfile
import unittest
import zc.buildout
import zc.buildout.testing
import zc.buildout.tests

optionflags =  (doctest.ELLIPSIS |
                doctest.NORMALIZE_WHITESPACE |
                doctest.REPORT_ONLY_FIRST_FAILURE)

def setUp(test):
    zc.buildout.testing.buildoutSetUp(test)
    zc.buildout.testing.install('hexagonit.recipe.download', test)
    zc.buildout.testing.install_develop('hexagonit.recipe.cmmi', test)

class NonInformativeTests(unittest.TestCase):

    def setUp(self):
        self.dir = os.path.realpath(tempfile.mkdtemp())

    def tearDown(self):
        shutil.rmtree(self.dir)
        for var in os.environ.keys():
            if var.startswith('HRC_'):
                del os.environ[var]

    def write_file(self, filename, contents, mode=stat.S_IREAD|stat.S_IWUSR):
        path = os.path.join(self.dir, filename)
        fh = open(path, 'w')
        fh.write(contents)
        fh.close()
        os.chmod(path, mode)
        return path

    def make_recipe(self, buildout, name, options):
        from hexagonit.recipe.cmmi import Recipe
        parts_directory_path = os.path.join(self.dir, 'test_parts')
        try:
            os.mkdir(parts_directory_path)
        except OSError, e:
            if e.errno != errno.EEXIST:
                raise
        bo = {
            'buildout' : {
                'parts-directory' : parts_directory_path,
                'directory' : self.dir,
            }
        }
        bo.update(buildout)
        return Recipe(bo, name, options)

    def test_working_directory_restored_after_failure(self):
        compile_directory = os.path.join(self.dir, 'compile_directory')
        os.makedirs(compile_directory)
        recipe = self.make_recipe({}, 'test', {'path' : compile_directory})
        os.chdir(self.dir)

        self.assertRaises(zc.buildout.UserError, recipe.install)
        self.assertEquals(self.dir, os.getcwd())

    def test_working_directory_restored_after_success(self):
        compile_directory = os.path.join(self.dir, 'compile_directory')
        os.makedirs(compile_directory)
        self.write_file(os.path.join(compile_directory, 'configure'), 'Dummy configure')

        recipe = self.make_recipe({}, 'test', {'path' : compile_directory})
        os.chdir(self.dir)
        self.assertEquals(self.dir, os.getcwd())

    def test_compile_directory_exists(self):
        """
        Do not fail if the compile-directory already exists
        """
        compile_directory = os.path.join(self.dir, 'test_parts/test__compile__')
        os.makedirs(compile_directory)

        recipe = self.make_recipe({}, 'test', dict(url="some invalid url"))
        os.chdir(self.dir)

        # if compile directory exists, recipe should raise an IOError because
        # of the bad URL, and _not_ some OSError because test__compile__
        # already exists
        self.assertRaises(IOError, recipe.install)

    def test_restart_after_failure(self):
        temp_directory = tempfile.mkdtemp(dir=self.dir, prefix="fake_package")

        configure_path = os.path.join(temp_directory, 'configure')
        self.write_file(configure_path, 'exit 0', mode=stat.S_IRWXU)
        makefile_path = os.path.join(temp_directory, 'Makefile')
        self.write_file(makefile_path, 'all:\n\texit -1')

        os.chdir(temp_directory)

        ignore, tarfile_path = tempfile.mkstemp(suffix=".tar")
        tar = tarfile.open(tarfile_path, 'w')
        tar.add('configure')
        tar.add('Makefile')
        tar.close()

        recipe = self.make_recipe({}, 'test', {'url' : tarfile_path})
        os.chdir(self.dir)

        try:
            # expected failure
            self.assertRaises(zc.buildout.UserError, recipe.install)

            # User deletes the __compile__ path
            build_directory = os.path.join(self.dir, 'test_parts/test__compile__')
            shutil.rmtree(build_directory)

            # the install should still fail, and _not_ raise an OSError
            self.assertRaises(zc.buildout.UserError, recipe.install)
        finally:
            try:
                shutil.rmtree(temp_directory)
                os.remove(tarfile_path)
            except:
                pass

    def test_environment_restored_after_building_a_part(self):
        # Make sure the test variables do not exist beforehand
        self.failIf('HRC_FOO' in os.environ)
        self.failIf('HRC_BAR' in os.environ)
        # Place a sentinel value to make sure the original environment is
        # maintained
        os.environ['HRC_SENTINEL'] = 'sentinel'
        self.assertEquals(os.environ.get('HRC_SENTINEL'), 'sentinel')

        recipe = self.make_recipe({}, 'test', {
            'url' : 'file://%s/testdata/package-0.0.0.tar.gz' % os.path.dirname(__file__),
            'environment' : 'HRC_FOO=bar\nHRC_BAR=foo'})
        os.chdir(self.dir)
        recipe.install()

        # Make sure the test variables are not kept in the environment after
        # the part has been built.
        self.failIf('HRC_FOO' in os.environ)
        self.failIf('HRC_BAR' in os.environ)
        # Make sure the sentinel value is still in the environment
        self.assertEquals(os.environ.get('HRC_SENTINEL'), 'sentinel')

    def test_run__unknown_command(self):
        recipe = self.make_recipe({}, 'test', {
            'url' : 'file://%s/testdata/package-0.0.0.tar.gz' % os.path.dirname(__file__)})
        self.assertRaises(zc.buildout.UserError, lambda:recipe.run('this-command-does-not-exist'))


    def test_call_script__bbb_for_callable_with_two_parameters(self):
        recipe = self.make_recipe({}, 'test', {
            'url' : 'file://%s/testdata/package-0.0.0.tar.gz' % os.path.dirname(__file__),
            })

        # The hook script does not return anything so we (ab)use exceptions
        # as a mechanism for asserting the function behaviour.
        filename = os.path.join(self.dir, 'hooks.py')
        script = open(filename, 'w')
        script.write('def my_hook(options, buildout): raise ValueError("I got called")\n')
        script.close()

        try:
            recipe.call_script('%s:my_hook' % filename)
            self.fail("The hook script was not called.")
        except ValueError, e:
            self.assertEquals(str(e), 'I got called')

    def test_call_script__augmented_environment_as_third_parameter(self):
        os.environ['HRC_SENTINEL'] = 'sentinel'
        os.environ['HRC_TESTVAR'] = 'foo'

        recipe = self.make_recipe({}, 'test', {
            'url' : 'file://%s/testdata/package-0.0.0.tar.gz' % os.path.dirname(__file__),
            'environment' : 'HRC_TESTVAR=bar'
            })

        # The hook script does not return anything so we (ab)use exceptions
        # as a mechanism for asserting the function behaviour.
        filename = os.path.join(self.dir, 'hooks.py')
        script = open(filename, 'w')
        script.write('def my_hook(options, buildout, env): raise ValueError("%(HRC_SENTINEL)s %(HRC_TESTVAR)s" % env)\n')
        script.close()

        try:
            recipe.call_script('%s:my_hook' % filename)
            self.fail("The hook script was not called.")
        except ValueError, e:
            self.assertEquals(str(e), 'sentinel bar')


def test_suite():
    suite = unittest.TestSuite((
            doctest.DocFileSuite(
                'README.txt',
                setUp=setUp,
                tearDown=zc.buildout.testing.buildoutTearDown,
                optionflags=optionflags,
                checker=renormalizing.RENormalizing([
                        (re.compile('--prefix=\S+sample-buildout'),
                         '--prefix=/sample_buildout'),
                        (re.compile('\s/\S+sample-buildout'),
                         ' /sample_buildout'),
                        zc.buildout.testing.normalize_path,
                        ]),
                ),
            unittest.makeSuite(NonInformativeTests),
            ))
    return suite

if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')
