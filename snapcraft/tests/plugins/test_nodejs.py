# -*- Mode:Python; indent-tabs-mode:nil; tab-width:4 -*-
#
# Copyright (C) 2015, 2017 Canonical Ltd
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License version 3 as
# published by the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import os

from unittest import mock
from testtools.matchers import DirExists, Equals, HasLength

import snapcraft
from snapcraft.plugins import nodejs
from snapcraft.internal import errors
from snapcraft import tests


class NodePluginBaseTestCase(tests.TestCase):

    def setUp(self):
        super().setUp()

        self.project_options = snapcraft.ProjectOptions()

        patcher = mock.patch('snapcraft.internal.common.run')
        self.run_mock = patcher.start()
        self.addCleanup(patcher.stop)

        patcher = mock.patch('snapcraft.sources.Tar')
        self.tar_mock = patcher.start()
        self.addCleanup(patcher.stop)

        patcher = mock.patch('sys.stdout')
        patcher.start()
        self.addCleanup(patcher.stop)

        self.nodejs_url = nodejs.get_nodejs_release(
            nodejs._NODEJS_VERSION, self.project_options.deb_arch)


class NodePluginTestCase(NodePluginBaseTestCase):

    scenarios = [
        ('npm', dict(package_manager='npm')),
        ('yarn', dict(package_manager='yarn')),
    ]

    def test_pull_local_sources(self):
        class Options:
            source = '.'
            node_packages = []
            node_engine = nodejs._NODEJS_VERSION
            npm_run = []
            node_package_manager = self.package_manager
            source = '.'

        plugin = nodejs.NodePlugin('test-part', Options(),
                                   self.project_options)

        os.makedirs(plugin.sourcedir)

        plugin.pull()

        if self.package_manager == 'npm':
            expected_tar_calls = [
                mock.call(self.nodejs_url, plugin._npm_dir),
                mock.call().download(),
                mock.call().provision(
                    plugin.installdir, clean_target=False, keep_tarball=True),
            ]
        else:
            expected_tar_calls = [
                mock.call(self.nodejs_url, plugin._npm_dir),
                mock.call('https://yarnpkg.com/latest.tar.gz',
                          plugin._npm_dir),
                mock.call().download(),
                mock.call().download(),
                mock.call().provision(plugin.installdir, clean_target=False,
                                      keep_tarball=True),
                mock.call().provision(plugin._npm_dir,
                                      clean_target=False, keep_tarball=True),
            ]

        self.run_mock.assert_has_calls([])
        self.tar_mock.assert_has_calls(expected_tar_calls)

    def test_build_local_sources(self):
        class Options:
            source = '.'
            node_packages = []
            node_engine = nodejs._NODEJS_VERSION
            npm_run = []
            node_package_manager = self.package_manager
            source = '.'

        open('package.json', 'w').close()

        plugin = nodejs.NodePlugin('test-part', Options(),
                                   self.project_options)

        os.makedirs(plugin.builddir)
        open(os.path.join(plugin.builddir, 'package.json'), 'w').close()

        plugin.build()

        if self.package_manager == 'npm':
            cmd = ['npm', '--cache-min=Infinity', 'install']
            expected_run_calls = [
                mock.call(cmd, cwd=plugin.builddir),
                mock.call(cmd + ['--global'], cwd=plugin.builddir),
            ]
            expected_tar_calls = [
                mock.call(self.nodejs_url, plugin._npm_dir),
                mock.call().provision(
                    plugin.installdir, clean_target=False, keep_tarball=True),
            ]
        else:
            cmd = os.path.join(plugin.partdir, 'npm', 'bin', 'yarn')
            expected_run_calls = [
                mock.call([cmd, 'global', 'add', 'file:{}'.format(self.path),
                           '--offline', '--prod', '--global-folder',
                           plugin.installdir], cwd=plugin.builddir)
            ]
            expected_tar_calls = [
                mock.call(self.nodejs_url, plugin._npm_dir),
                mock.call('https://yarnpkg.com/latest.tar.gz',
                          plugin._npm_dir),
                mock.call().provision(plugin.installdir, clean_target=False,
                                      keep_tarball=True),
                mock.call().provision(plugin._npm_dir,
                                      clean_target=False, keep_tarball=True),
            ]

        self.run_mock.assert_has_calls(expected_run_calls)
        self.tar_mock.assert_has_calls(expected_tar_calls)

    def test_pull_and_build_node_packages_sources(self):
        class Options:
            source = None
            node_packages = ['my-pkg']
            node_engine = nodejs._NODEJS_VERSION
            npm_run = []
            node_package_manager = self.package_manager
            source = '.'

        plugin = nodejs.NodePlugin('test-part', Options(),
                                   self.project_options)

        os.makedirs(plugin.sourcedir)

        plugin.pull()
        plugin.build()

        if self.package_manager == 'npm':
            cmd = ['npm', '--cache-min=Infinity', 'install',
                   '--global', 'my-pkg']
            expected_run_calls = [
                mock.call(cmd, cwd=plugin.sourcedir),
                mock.call(cmd, cwd=plugin.builddir),
            ]
            expected_tar_calls = [
                mock.call(self.nodejs_url, plugin._npm_dir),
                mock.call().download(),
                mock.call().provision(
                    plugin.installdir, clean_target=False, keep_tarball=True),
            ]
        else:
            cmd = os.path.join(plugin.partdir, 'npm', 'bin', 'yarn')
            expected_run_calls = [
                mock.call([cmd, 'add', 'my-pkg'],
                          cwd=plugin.sourcedir),
                mock.call([cmd, 'global', 'add', 'my-pkg',
                           '--offline', '--prod', '--global-folder',
                           plugin.installdir], cwd=plugin.builddir)
            ]
            expected_tar_calls = [
                mock.call(self.nodejs_url, plugin._npm_dir),
                mock.call('https://yarnpkg.com/latest.tar.gz',
                          plugin._npm_dir),
                mock.call().download(),
                mock.call().download(),
                mock.call().provision(plugin.installdir, clean_target=False,
                                      keep_tarball=True),
                mock.call().provision(plugin._npm_dir,
                                      clean_target=False, keep_tarball=True),
                mock.call().provision(plugin.installdir, clean_target=False,
                                      keep_tarball=True),
                mock.call().provision(plugin._npm_dir,
                                      clean_target=False, keep_tarball=True),
            ]

        self.run_mock.assert_has_calls(expected_run_calls)
        self.tar_mock.assert_has_calls(expected_tar_calls)

    def test_build_executes_npm_run_commands(self):
        class Options:
            source = '.'
            node_packages = []
            node_engine = '4'
            npm_run = ['command_one', 'avocado']
            node_package_manager = self.package_manager
            source = '.'

        plugin = nodejs.NodePlugin('test-part', Options(),
                                   self.project_options)

        os.makedirs(plugin.sourcedir)
        open(os.path.join(plugin.sourcedir, 'package.json'), 'w').close()

        plugin.build()

        if self.package_manager == 'npm':
            cmd = ['npm', 'run']
        else:
            cmd = [os.path.join(plugin.partdir, 'npm', 'bin', 'yarn'), 'run']

        expected_run_calls = [
            mock.call(cmd + ['command_one'], cwd=plugin.builddir),
            mock.call(cmd + ['avocado'], cwd=plugin.builddir),
        ]
        self.run_mock.assert_has_calls(expected_run_calls)

    @mock.patch('snapcraft.ProjectOptions.deb_arch', 'fantasy-arch')
    def test_unsupported_arch_raises_exception(self):
        class Options:
            source = None
            node_packages = []
            node_engine = '4'
            npm_run = []
            node_package_manager = self.package_manager
            source = '.'

        raised = self.assertRaises(
            errors.SnapcraftEnvironmentError,
            nodejs.NodePlugin,
            'test-part', Options(),
            self.project_options)

        self.assertThat(raised.__str__(),
                        Equals('architecture not supported (fantasy-arch)'))

    def test_get_build_properties(self):
        expected_build_properties = ['node-packages', 'npm-run']
        resulting_build_properties = nodejs.NodePlugin.get_build_properties()

        self.assertThat(resulting_build_properties,
                        HasLength(len(expected_build_properties)))

        for property in expected_build_properties:
            self.assertIn(property, resulting_build_properties)

    def test_get_pull_properties(self):
        expected_pull_properties = ['node-engine', 'node-package-manager']
        resulting_pull_properties = nodejs.NodePlugin.get_pull_properties()

        self.assertThat(resulting_pull_properties,
                        HasLength(len(expected_pull_properties)))

        for property in expected_pull_properties:
            self.assertIn(property, resulting_pull_properties)

    def test_clean_pull_step(self):
        class Options:
            source = '.'
            node_packages = []
            node_engine = '4'
            npm_run = []
            node_package_manager = self.package_manager

        plugin = nodejs.NodePlugin('test-part', Options(),
                                   self.project_options)

        os.makedirs(plugin.sourcedir)

        plugin.pull()

        self.assertTrue(os.path.exists(plugin._npm_dir))

        plugin.clean_pull()

        self.assertFalse(os.path.exists(plugin._npm_dir))


class NodePluginNpmWorkaroundsTestCase(NodePluginBaseTestCase):

    def test_build_from_local_fixes_symlinks(self):
        class Options:
            source = '.'
            node_packages = []
            node_engine = '4'
            npm_run = []
            node_package_manager = 'npm'
            source = '.'

        plugin = nodejs.NodePlugin('test-part', Options(),
                                   self.project_options)

        os.makedirs(plugin.sourcedir)
        open(os.path.join(plugin.sourcedir, 'package.json'), 'w').close()

        # Setup stub project symlinks
        modules_path = os.path.join('lib', 'node_modules')
        project_path = os.path.join(plugin.installdir, modules_path, 'project')
        dep_path = os.path.join(modules_path, 'dep')
        os.makedirs(os.path.join(plugin.builddir, dep_path))
        os.makedirs(os.path.join(plugin.installdir, modules_path))
        os.symlink(os.path.join('..', '..', '..', 'build'), project_path)

        plugin.build()

        self.assertThat(project_path, DirExists())
        self.assertThat(os.path.join(project_path, dep_path), DirExists())
        self.assertFalse(os.path.islink(project_path))


class NodeReleaseTestCase(tests.TestCase):

    scenarios = [
        ('i686', dict(
            architecture=('32bit', 'ELF'),
            machine='i686',
            engine='4.4.4',
            expected_url=(
                'https://nodejs.org/dist/v4.4.4/'
                'node-v4.4.4-linux-x86.tar.gz'))),
        ('x86_64', dict(
            architecture=('64bit', 'ELF'),
            machine='x86_64',
            engine='4.4.4',
            expected_url=(
                'https://nodejs.org/dist/v4.4.4/'
                'node-v4.4.4-linux-x64.tar.gz'))),
        ('i686-on-x86_64', dict(
            architecture=('32bit', 'ELF'),
            machine='x86_64',
            engine='4.4.4',
            expected_url=(
                'https://nodejs.org/dist/v4.4.4/'
                'node-v4.4.4-linux-x86.tar.gz'))),
        ('armv7l', dict(
            architecture=('32bit', 'ELF'),
            machine='armv7l',
            engine='4.4.4',
            expected_url=(
                'https://nodejs.org/dist/v4.4.4/'
                'node-v4.4.4-linux-armv7l.tar.gz'))),
        ('aarch64', dict(
            architecture=('64bit', 'ELF'),
            machine='aarch64',
            engine='4.4.4',
            expected_url=(
                'https://nodejs.org/dist/v4.4.4/'
                'node-v4.4.4-linux-arm64.tar.gz'))),
        ('armv7l-on-aarch64', dict(
            architecture=('32bit', 'ELF'),
            machine='aarch64',
            engine='4.4.4',
            expected_url=(
                'https://nodejs.org/dist/v4.4.4/'
                'node-v4.4.4-linux-armv7l.tar.gz'))),
    ]

    @mock.patch('platform.architecture')
    @mock.patch('platform.machine')
    def test_get_nodejs_release(self, machine_mock, architecture_mock):
        machine_mock.return_value = self.machine
        architecture_mock.return_value = self.architecture
        project = snapcraft.ProjectOptions()
        node_url = nodejs.get_nodejs_release(self.engine, project.deb_arch)
        self.assertThat(node_url, Equals(self.expected_url))


class NodePluginSchemaTestCase(tests.TestCase):

    def test_schema(self):
        schema = nodejs.NodePlugin.schema()
        properties = schema['properties']
        self.assertTrue('node-packages' in properties,
                        'Expected "node-packages" to be included in '
                        'properties')
        node_packages = properties['node-packages']

        self.assertTrue(
            'type' in node_packages,
            'Expected "type" to be included in "node-packages"')
        self.assertThat(node_packages['type'], Equals('array'),
                        'Expected "node-packages" "type" to be "array", but '
                        'it was "{}"'.format(node_packages['type']))

        self.assertTrue(
            'minitems' in node_packages,
            'Expected "minitems" to be included in "node-packages"')
        self.assertThat(node_packages['minitems'], Equals(1),
                        'Expected "node-packages" "minitems" to be 1, but '
                        'it was "{}"'.format(node_packages['minitems']))

        self.assertTrue('node-package-manager' in properties,
                        'Expected "node-package-manager" to be included in '
                        'properties')
        node_package_manager = properties['node-package-manager']

        self.assertTrue(
            'type' in node_package_manager,
            'Expected "type" to be included in "node-package-manager"')
        self.assertThat(node_package_manager['type'], Equals('string'),
                        'Expected "node-package-manager" "type" to be '
                        '"string", but it was '
                        '"{}"'.format(node_package_manager['type']))
        self.assertTrue(
            'default' in node_package_manager,
            'Expected "default" to be included in "node-package-manager"')
        self.assertThat(node_package_manager['default'], Equals('npm'),
                        'Expected "node-package-manager" "default" to be '
                        '"npm", but it was '
                        '"{}"'.format(node_package_manager['type']))

        self.assertTrue(
            'uniqueItems' in node_packages,
            'Expected "uniqueItems" to be included in "node-packages"')
        self.assertTrue(
            node_packages['uniqueItems'],
            'Expected "node-packages" "uniqueItems" to be "True"')

        self.assertTrue('node-packages' in properties,
                        'Expected "node-packages" to be included in '
                        'properties')

        npm_run = properties['npm-run']

        self.assertTrue(
            'type' in npm_run,
            'Expected "type" to be included in "npm-run"')
        self.assertThat(npm_run['type'], Equals('array'),
                        'Expected "npm-run" "type" to be "array", but '
                        'it was "{}"'.format(npm_run['type']))

        self.assertTrue(
            'minitems' in npm_run,
            'Expected "minitems" to be included in "npm-run"')
        self.assertThat(npm_run['minitems'], Equals(1),
                        'Expected "npm-run" "minitems" to be 1, but '
                        'it was "{}"'.format(npm_run['minitems']))

        self.assertTrue(
            'uniqueItems' in npm_run,
            'Expected "uniqueItems" to be included in "npm-run"')
        self.assertFalse(
            npm_run['uniqueItems'],
            'Expected "npm-run" "uniqueItems" to be "False"')

        self.assertTrue('node-engine' in properties,
                        'Expected "node-engine" to be included in '
                        'properties')
        node_engine_type = properties['node-engine']['type']
        self.assertThat(node_engine_type, Equals('string'),
                        'Expected "node_engine" "type" to be '
                        '"string", but it was "{}"'
                        .format(node_engine_type))
