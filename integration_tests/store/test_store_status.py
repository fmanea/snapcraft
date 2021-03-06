# -*- Mode:Python; indent-tabs-mode:nil; tab-width:4 -*-
#
# Copyright (C) 2016-2017 Canonical Ltd
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
import subprocess
import unittest

from testtools.matchers import Equals, Contains, FileExists

import integration_tests


class StatusTestCase(integration_tests.StoreTestCase):

    def test_status_without_login(self):
        error = self.assertRaises(
            subprocess.CalledProcessError,
            self.run_snapcraft, ['status', 'test-snap'])
        self.assertIn('No valid credentials found. Have you run "snapcraft '
                      'login"?', str(error.output))

    def test_status_with_login_wrong_snap(self):
        self.addCleanup(self.logout)
        self.login()

        error = self.assertRaises(
            subprocess.CalledProcessError,
            self.run_snapcraft, ['status', 'mysnap'])
        self.assertIn(
            "Snap 'mysnap' was not found in '16' series.", str(error.output))

    def test_status_with_login_bad_snap_with_series(self):
        self.addCleanup(self.logout)
        self.login()

        error = self.assertRaises(
            subprocess.CalledProcessError,
            self.run_snapcraft, ['status', 'mysnap', '--series=16'])
        self.assertIn(
            "Snap 'mysnap' was not found in '16' series.", str(error.output))

    def test_status_with_login_bad_snap_with_arch(self):
        self.addCleanup(self.logout)
        self.login()

        error = self.assertRaises(
            subprocess.CalledProcessError,
            self.run_snapcraft, ['status', 'mysnap', '--arch=i386'])
        self.assertIn(
            "Snap 'mysnap' for 'i386' was not found in '16' series.",
            str(error.output))

    @unittest.skipUnless(
        os.getenv('TEST_STORE', 'fake') == 'fake', 'Skip fake store.')
    def test_status_fake_store(self):
        self.addCleanup(self.logout)
        self.login()

        output = self.run_snapcraft(['status', 'basic'])
        expected = '\n'.join((
            'Track    Arch    Channel    Version    Revision',
            'latest   amd64   stable     1.0-amd64  2',
            '                 beta       1.1-amd64  4',
            '                 edge       ^          ^',
            '         i386    stable     -          -',
            '                 beta       -          -',
            '                 edge       1.0-i386   3'))
        self.assertThat(output, Contains(expected))

    @unittest.skipUnless(
        os.getenv('TEST_STORE', 'fake') == 'staging', 'Skip staging store.')
    def test_status_staging_store(self):
        self.addCleanup(self.logout)
        self.login()

        # Build a random snap, register, push and release it.
        name = self.get_unique_name()
        version = self.get_unique_version()
        self.copy_project_to_cwd('basic')
        self.update_name_and_version(name, version)
        self.run_snapcraft('snap')
        snap_path = '{}_{}_{}.snap'.format(name, version, 'all')
        self.assertThat(snap_path, FileExists())
        self.register(name)
        self.assertThat(
            self.push(snap_path, release='candidate,beta'),
            Equals(0))

        output = self.run_snapcraft(['status', name])
        expected = '\n'.join((
            'Track    Arch    Channel    Version                           Revision',  # noqa
            'latest   all     stable     -                                 -',
            '                 candidate  {version}  1',
            '                 beta       {version}  1',
            '                 edge       ^                                 ^'
        )).format(version=version)
        self.assertThat(output, Contains(expected))
