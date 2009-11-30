from zope.testing import doctest
from zope.testing import renormalizing

import os
import re
import shutil
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

    def write_file(self, filename, contents):
        path = os.path.join(self.dir, filename)
        fh = open(path, 'w')
        fh.write(contents)
        fh.close()
        return path

    def make_recipe(self, buildout, name, options):
        from hexagonit.recipe.cmmi import Recipe
        parts_directory_path = os.path.join(self.dir, 'test_parts')
        os.mkdir(parts_directory_path)
        bo = {
            'buildout' : {
                'parts-directory' : parts_directory_path,
            }
        }
        bo.update(buildout)
        return Recipe(bo, name, options)

    def test_is_build_dir__with_configure(self):
        recipe = self.make_recipe({}, 'test', {'url' : 'http://no.where.com/'})
        os.chdir(self.dir)
        self.failIf(recipe.is_build_dir())
        configure = self.write_file('configure', 'Dummy configure script')

        self.failUnless(os.path.exists(configure))
        self.failUnless(recipe.is_build_dir())

    def test_is_build_dir__with_makefile_pl(self):
        recipe = self.make_recipe({}, 'test', {'url' : 'http://no.where.com/'})
        os.chdir(self.dir)
        self.failIf(recipe.is_build_dir())
        makefile = self.write_file('Makefile.PL', 'Dummy Makefile.PL script')

        self.failUnless(os.path.exists(makefile))
        self.failUnless(recipe.is_build_dir())

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
