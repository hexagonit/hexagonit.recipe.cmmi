import hexagonit.recipe.download
import errno
import imp
import logging
import os
import shutil
import subprocess
import zc.buildout

class Recipe(object):
    """zc.buildout recipe for compiling and installing software"""

    def __init__(self, buildout, name, options):
        self.options = options
        self.buildout = buildout
        self.name = name

        options['location'] = os.path.join(
            buildout['buildout']['parts-directory'],
            self.name)
        options['prefix'] = options.get('prefix', options['location'])
        options['url'] = options.get('url', '').strip()
        options['path'] = options.get('path', '').strip()

        if options['url'] and options['path']:
            raise zc.buildout.UserError('You must use either "url" or "path", not both!')
        if not (options['url'] or options['path']):
            raise zc.buildout.UserError('You must provide either "url" or "path".')

        if options['url']:
            options['compile-directory'] = '%s__compile__' % options['location']
        else:
            options['compile-directory'] = options['path']

        self.environ = {}
        self.original_environment = os.environ.copy()

        environment_section = self.options.get('environment-section', '').strip()
        if environment_section and environment_section in buildout:
            # Use environment variables from the designated config section.
            self.environ.update(buildout[environment_section])
        for variable in self.options.get('environment', '').splitlines():
            if variable.strip():
                try:
                    key, value = variable.split('=', 1)
                    self.environ[key.strip()] = value
                except ValueError:
                    raise zc.buildout.UserError('Invalid environment variable definition: %s', variable)
        # Extrapolate the environment variables using values from the current
        # environment.
        for key in self.environ:
            self.environ[key] = self.environ[key] % os.environ

    def augmented_environment(self):
        """Returns a dictionary containing the current environment variables
        augmented with the part specific overrides.

        The dictionary is an independent copy of ``os.environ`` and
        modifications will not be reflected in back in ``os.environ``.
        """
        env = os.environ.copy()
        env.update(self.environ)
        return env

    def update(self):
        pass

    def call_script(self, script):
        """This method is copied from z3c.recipe.runscript.

        See http://pypi.python.org/pypi/z3c.recipe.runscript for details.
        """
        filename, callable = script.split(':')
        filename = os.path.abspath(filename)
        module = imp.load_source('script', filename)
        script = getattr(module, callable.strip())

        try:
            script(self.options, self.buildout, self.augmented_environment())
        except TypeError:
            # BBB: Support hook scripts that do not take the environment as
            # the third parameter
            script(self.options, self.buildout)


    def run(self, cmd):
        """Run the given ``cmd`` in a child process."""
        log = logging.getLogger(self.name)
        try:
            retcode = subprocess.call(cmd, shell=True, env=self.augmented_environment())

            if retcode < 0:
                log.error('Command received signal %s: %s' % (-retcode, cmd))
                raise zc.buildout.UserError('System error')
            elif retcode > 0:
                log.error('Command failed with exit code %s: %s' % (retcode, cmd))
                raise zc.buildout.UserError('System error')
        except OSError, e:
            log.error('Command failed: %s: %s' % (e, cmd))
            raise zc.buildout.UserError('System error')


    def install(self):
        log = logging.getLogger(self.name)
        parts = []

        make_cmd = self.options.get('make-binary', 'make').strip()
        make_options = ' '.join(self.options.get('make-options', '').split())
        make_targets = ' '.join(self.options.get('make-targets', 'install').split())

        configure_options = self.options.get('configure-options','').split()
        configure_cmd = self.options.get('configure-command', '').strip()

        if not configure_cmd:
            # Default to using basic configure script.
            configure_cmd = './configure'
            # Inject the --prefix parameter if not already present
            if '--prefix' not in ' '.join(configure_options):
                configure_options.insert(0, '--prefix=%s' % self.options['prefix'])

        patch_cmd = self.options.get('patch-binary', 'patch').strip()
        patch_options = ' '.join(self.options.get('patch-options', '-p0').split())
        patches = self.options.get('patches', '').split()

        if self.environ:
            for key in sorted(self.environ.keys()):
                log.info('[ENV] %s = %s', key, self.environ[key])

        # Download the source using hexagonit.recipe.download
        if self.options['url']:
            compile_dir = self.options['compile-directory']
            try:
                os.mkdir(compile_dir)
            except OSError, e:
                # leftovers from a previous failed attempt,
                # download recipe will raise a clean error message
                if e.errno != errno.EEXIST:
                    raise

            try:
                opt = self.options.copy()
                opt['destination'] = compile_dir
                hexagonit.recipe.download.Recipe(
                    self.buildout, self.name, opt).install()
            except:
                shutil.rmtree(compile_dir)
                raise
        else:
            log.info('Using local source directory: %s' % self.options['path'])
            compile_dir = self.options['path']

        current_dir = os.getcwd()
        try:
            os.mkdir(self.options['location'])
        except OSError, e:
            if e.errno == errno.EEXIST:
                pass
        os.chdir(compile_dir)

        try:
            try:
                # We support packages that either extract contents to the $PWD
                # or alternatively have a single directory.
                contents = os.listdir(compile_dir)
                if len(contents) == 1 and os.path.isdir(contents[0]):
                    # Single container
                    os.chdir(contents[0])

                if patches:
                    log.info('Applying patches')
                    for patch in patches:
                        self.run('%s %s < %s' % (patch_cmd, patch_options, patch))

                if 'pre-configure-hook' in self.options and len(self.options['pre-configure-hook'].strip()) > 0:
                    log.info('Executing pre-configure-hook')
                    self.call_script(self.options['pre-configure-hook'])

                self.run('%s %s' % (configure_cmd, ' '.join(configure_options)))

                if 'pre-make-hook' in self.options and len(self.options['pre-make-hook'].strip()) > 0:
                    log.info('Executing pre-make-hook')
                    self.call_script(self.options['pre-make-hook'])

                self.run('%s %s' % (make_cmd, make_options))
                self.run('%s %s %s' % (make_cmd, make_options, make_targets))

                if 'post-make-hook' in self.options and len(self.options['post-make-hook'].strip()) > 0:
                    log.info('Executing post-make-hook')
                    self.call_script(self.options['post-make-hook'])

            except:
                log.error('Compilation error. The package is left as is at %s where '
                          'you can inspect what went wrong' % os.getcwd())
                raise
        finally:
            os.chdir(current_dir)

        if self.options['url']:
            if self.options.get('keep-compile-dir', '').lower() in ('true', 'yes', '1', 'on'):
                # If we're keeping the compile directory around, add it to
                # the parts so that it's also removed when this recipe is
                # uninstalled.
                parts.append(self.options['compile-directory'])
            else:
                shutil.rmtree(compile_dir)
                del self.options['compile-directory']

        parts.append(self.options['location'])
        return parts
