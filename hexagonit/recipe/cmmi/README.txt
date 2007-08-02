Supported options
=================

url
    URL to the package that will be downloaded and extracted. The
    supported package formats are .tar.gz, .tar.bz2, and .zip. The
    value must be a full URL,
    e.g. http://python.org/ftp/python/2.4.4/Python-2.4.4.tgz.

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
    package: Extracting package to /tmp/...package
    configure --prefix=/sample_buildout/parts/package
    building package
    installing package

As we can see the configure script was called with the ``--prefix``
option by default followed by calls to ``make`` and ``make install``.

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
    package: Extracting package to /tmp/...
    package: Applying patches
    patching file configure
    patching file Makefile.dist
    patched-configure --prefix=/sample_buildout/parts/package --with-threads --without-foobar CFLAGS=-I/sw/include LDFLAGS=-L/sw/lib
    building patched package
    installing patched package
    installing patched package-lib


For more specific needs you can write your own recipe that uses
``hexagonit.recipe.cmmi`` and set the ``keep-compile-dir`` option to
``true``. You can then continue from where this recipe finished by
reading the location of the compile directory from
``options['compile-directory']``.
