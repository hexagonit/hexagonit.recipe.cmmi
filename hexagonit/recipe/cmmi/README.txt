Supported options
=================

url
    URL to the package that will be downloaded and extracted. The
    supported package formats are .tar.gz, .tar.bz2, and .zip. The
    value must be a full URL,
    e.g. http://python.org/ftp/python/2.4.4/Python-2.4.4.tgz. The
    ``path`` option can not be used at the same time with ``url``.

path
    Path to a local directory containing the source code to be built
    and installed. The directory must contain the ``configure``
    script. The ``url`` option can not be used at the same time with
    ``path``.

md5sum
    MD5 checksum for the package file. If available the MD5
    checksum of the downloaded package will be compared to this value
    and if the values do not match the execution of the recipe will
    fail.

make-binary
    Path to the ``make`` program. Defaults to 'make' which
    should work on any system that has the ``make`` program available
    in the system ``PATH``.

make-targets
    Targets for the ``make`` command. Defaults to 'install'
    which will be enough to install most software packages. You only
    need to use this if you want to build alternate targets. Each
    target must be given on a separate line.

configure-options
    Extra options to be given to the ``configure`` script. By default
    only the ``--prefix`` option is passed which is set to the part
    directory. Each option must be given on a separate line. Note that
    in addition to configure options you can also pass in environment
    variables such as ``CFLAGS`` and ``LDFLAGS`` to control the build
    process.

patch-binary
    Path to the ``patch`` program. Defaults to 'patch' which should
    work on any system that has the ``patch`` program available in the
    system ``PATH``.

patch-options
    Options passed to the ``patch`` program. Defaults to ``-p0``.

patches
    List of patch files to the applied to the extracted source. Each
    file should be given on a separate line.

pre-configure-hook
    Custom python script that will be executed before running the
    ``configure`` script. The format of the options is::

        /path/to/the/module.py:name_of_callable

    where the first part is a filesystem path to the python module and
    the second part is the name of the callable in the module that
    will be called. The callable will be passed two parameters: the
    ``options`` dictionary from the recipe and the global ``buildout``
    dictionary. The callable is not expected to return anything.

pre-make-hook
    Custom python script that will be executed before running
    ``make``. The format and semantics are the same as with the
    ``pre-configure-hook`` option.

post-make-hook
    Custom python script that will be executed after running
    ``make``. The format and semantics are the same as with the
    ``pre-configure-hook`` option.

keep-compile-dir
    Switch to optionally keep the temporary directory where the
    package was compiled. This is mostly useful for other recipes that
    use this recipe to compile a software but wish to do some
    additional steps not handled by this recipe. The location of the
    compile directory is stored in ``options['compile-directory']``.
    Accepted values are 'true' or 'false', defaults to 'false'.


Additionally, the recipe honors the ``download-directory`` option set
in the ``[buildout]`` section and stores the downloaded files under
it. If the value is not set a directory called ``downloads`` will be
created in the root of the buildout and the ``download-directory``
option set accordingly.

The recipe will first check if there is a local copy of the package
before downloading it from the net. Files can be shared among
different buildouts by setting the ``download-directory`` to the same
location.

Example usage
=============

We'll use a simple tarball to demonstrate the recipe.

    >>> import os.path
    >>> src = join(os.path.dirname(__file__), 'testdata')
    >>> ls(src)
    d .svn
    - package-0.0.0.tar.gz

The package contains a dummy ``configure`` script that will simply
echo the options it was called with and create a ``Makefile`` that
will do the same.

Let's create a buildout to build and install the package.

    >>> write('buildout.cfg',
    ... """
    ... [buildout]
    ... parts = package
    ...
    ... [package]
    ... recipe = hexagonit.recipe.cmmi
    ... url = file://%s/package-0.0.0.tar.gz
    ... """ % src)

This will download, extract and build our demo package with the
default build options.

    >>> print system(buildout)
    Installing package.
    package: Creating download directory: /sample_buildout/downloads
    package: Extracting package to /sample_buildout/parts/package__compile__
    configure --prefix=/sample_buildout/parts/package
    building package
    installing package

As we can see the configure script was called with the ``--prefix``
option by default followed by calls to ``make`` and ``make install``.


Installing checkouts
====================

Sometimes instead of downloading and building an existing tarball we
need to work with code that is already available on the filesystem,
for example an SVN checkout.

Instead of providing the ``url`` option we will provide a ``path``
option to the directory containing the source code.

Let's demonstrate this by first unpacking our test package to the
filesystem and building that.

    >>> checkout_dir = tmpdir('checkout')
    >>> import setuptools.archive_util
    >>> setuptools.archive_util.unpack_archive('%s/package-0.0.0.tar.gz' % src,
    ...                                        checkout_dir)
    >>> ls(checkout_dir)
    d package-0.0.0

    >>> write('buildout.cfg',
    ... """
    ... [buildout]
    ... parts = package
    ...
    ... [package]
    ... recipe = hexagonit.recipe.cmmi
    ... path = %s/package-0.0.0
    ... """ % checkout_dir)

    >>> print system(buildout)
    Uninstalling package.
    Installing package.
    package: Using local source directory: /checkout/package-0.0.0
    configure --prefix=/sample_buildout/parts/package
    building package
    installing package

Since using the ``path`` implies that the source code has been
acquired outside of the control of the recipe also the responsibility
of managing it is outside of the recipe.

Depending on the software you may need to manually run ``make clean``
etc. between buildout runs if you make changes to the code. Also, the
``keep-compile-dir`` has no effect when ``path`` is used.


Advanced configuration
======================

The above options are enough to build most packages. However, in some
cases it is not enough and we need to control the build process
more. Let's try again with a new buildout and provide more options.

    >>> write('buildout.cfg',
    ... """
    ... [buildout]
    ... parts = package
    ...
    ... [package]
    ... recipe = hexagonit.recipe.cmmi
    ... url = file://%(src)s/package-0.0.0.tar.gz
    ... md5sum = 6b94295c042a91ea3203857326bc9209
    ... configure-options =
    ...     --with-threads
    ...     --without-foobar
    ...     CFLAGS=-I/sw/include
    ...     LDFLAGS=-L/sw/lib
    ... make-targets =
    ...     install
    ...     install-lib
    ... patches =
    ...     patches/configure.patch
    ...     patches/Makefile.dist.patch
    ... """ % dict(src=src))

This configuration uses custom configure options, multiple make
targets and also patches the source code before the scripts are run.

    >>> print system(buildout)
    Uninstalling package.
    Installing package.
    package: Using a cached copy from /sample_buildout/downloads/package-0.0.0.tar.gz
    package: MD5 checksum OK
    package: Extracting package to /sample_buildout/parts/package__compile__
    package: Applying patches
    patching file configure
    patching file Makefile.dist
    patched-configure --prefix=/sample_buildout/parts/package --with-threads --without-foobar CFLAGS=-I/sw/include LDFLAGS=-L/sw/lib
    building patched package
    installing patched package
    installing patched package-lib


Customizing the build process
=============================

Sometimes even the above is not enough and you need to be able to
control the process in even more detail. One such use case would be to
perform dynamic substitutions on the source code (possible based on
information from the buildout) which cannot be done with static
patches or to simply run arbitrary commands.

The recipe allows you to write custom python scripts that hook into
the build process. You can define a script to be run:

 - before the configure script is executed (pre-configure-hook)
 - before the make process is executed (pre-make-hook)
 - after the make process is finished (post-make-hook)

Each option needs to contain the following information

  /full/path/to/the/python/module.py:name_of_callable

where the callable object (here name_of_callable) is expected to take
two parameters, the ``options`` dictionary from the recipe and the
global ``buildout`` dictionary.

Let's create a simple python script to demonstrate the
functionality. You can naturally have separate scripts for each hook
or simply use just one or two hooks. Here we use just a single module.

    >>> hooks = tmpdir('hooks')
    >>> write(hooks, 'customhandlers.py',
    ... """
    ... import logging
    ... log = logging.getLogger('hook')
    ...
    ... def preconfigure(options, buildout):
    ...     log.info('This is pre-configure-hook!')
    ...     
    ... def premake(options, buildout):
    ...     log.info('This is pre-make-hook!')
    ...     
    ... def postmake(options, buildout):
    ...     log.info('This is post-make-hook!')
    ...     
    ... """)

and a new buildout to try it out

    >>> write('buildout.cfg',
    ... """
    ... [buildout]
    ... parts = package
    ...
    ... [package]
    ... recipe = hexagonit.recipe.cmmi
    ... url = file://%(src)s/package-0.0.0.tar.gz
    ... pre-configure-hook = %(module)s:preconfigure
    ... pre-make-hook = %(module)s:premake
    ... post-make-hook = %(module)s:postmake
    ... """ % dict(src=src, module='%s/customhandlers.py' % hooks))

    >>> print system(buildout)
    Uninstalling package.
    Installing package.
    package: Using a cached copy from /sample_buildout/downloads/package-0.0.0.tar.gz
    package: Extracting package to /sample_buildout/parts/package__compile__
    package: Executing pre-configure-hook
    hook: This is pre-configure-hook!
    configure --prefix=/sample_buildout/parts/package
    package: Executing pre-make-hook
    hook: This is pre-make-hook!
    building package
    installing package
    package: Executing post-make-hook
    hook: This is post-make-hook!

For even more specific needs you can write your own recipe that uses
``hexagonit.recipe.cmmi`` and set the ``keep-compile-dir`` option to
``true``. You can then continue from where this recipe finished by
reading the location of the compile directory from
``options['compile-directory']`` from your own recipe.

