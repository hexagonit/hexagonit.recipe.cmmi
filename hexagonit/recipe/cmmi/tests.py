import unittest
import zc.buildout.tests
import zc.buildout.testing
import re

from zope.testing import doctest, renormalizing

optionflags =  (doctest.ELLIPSIS |
                doctest.NORMALIZE_WHITESPACE |
                doctest.REPORT_ONLY_FIRST_FAILURE)

def setUp(test):
    zc.buildout.testing.buildoutSetUp(test)
    zc.buildout.testing.install('hexagonit.recipe.download', test)
    zc.buildout.testing.install_develop('hexagonit.recipe.cmmi', test)

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
            ))
    return suite

if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')
