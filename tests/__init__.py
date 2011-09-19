# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright 2010-2011 OpenStack LLC.
# All Rights Reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

import ConfigParser
from hashlib import md5
import httplib2
import nose.plugins.skip
import os
from pprint import pprint
import unittest2
# from xmlrpclib import Server


class skip_test(object):
    """Decorator that skips a test."""
    def __init__(self, msg):
        self.message = msg

    def __call__(self, func):
        def _skipper(*args, **kw):
            """Wrapped skipper function."""
            raise nose.SkipTest(self.message)
        _skipper.__name__ = func.__name__
        _skipper.__doc__ = func.__doc__
        return _skipper


class skip_if(object):
    """Decorator that skips a test."""
    def __init__(self, condition, msg):
        self.condition = condition
        self.message = msg

    def __call__(self, func):
        def _skipper(*args, **kw):
            """Wrapped skipper function."""
            if self.condition:
                raise nose.SkipTest(self.message)
            func(*args, **kw)
        _skipper.__name__ = func.__name__
        _skipper.__doc__ = func.__doc__
        return _skipper


class skip_unless(object):
    """Decorator that skips a test."""
    def __init__(self, condition, msg):
        self.condition = condition
        self.message = msg

    def __call__(self, func):
        def _skipper(*args, **kw):
            """Wrapped skipper function."""
            if not self.condition:
                raise nose.SkipTest(self.message)
            func(*args, **kw)
        _skipper.__name__ = func.__name__
        _skipper.__doc__ = func.__doc__
        return _skipper


class FunctionalTest(unittest2.TestCase):
    @classmethod
    def setUpClass(self):
        # Setup project hashes
        self.rabbitmq = {}

        def parse_config_file(self):
            cfg = os.path.abspath(os.path.join(os.path.dirname(__file__),
                                   "..", "etc", "config.ini"))
            if os.path.exists(cfg):
                ret_hash = _build_config(self, cfg)
            else:
                raise Exception("Cannot read %s" % cfg)
            return ret_hash

        def _build_config(self, config_file):
            parser = ConfigParser.ConfigParser()
            parser.read(config_file)
            ret_hash = {}
            for section in parser.sections():
                ret_hash[section] = {}
                for value in parser.options(section):
                    ret_hash[section][value] = parser.get(section, value)
            return ret_hash

        def _generate_auth_token(self):
            path = self.nova['auth_path']
            if 'keystone' in self.config:
                headers = {'X-Auth-User': self.keystone['user'],
                           'X-Auth-Key': self.keystone['pass']}
            else:
                headers = {'X-Auth-User': self.nova['user'],
                           'X-Auth-Key': self.nova['key']}
            http = httplib2.Http()
            response, content = http.request(path, 'HEAD', headers=headers)
            if response.status == 204:
                return response['x-auth-token']
            else:
                raise Exception("Unable to get a valid token, please fix")

        def _gen_nova_path(self):
            path = "http://%s:%s/%s" % (self.nova['host'],
                                         self.nova['port'],
                                         self.nova['ver'])
            return path

        def _gen_nova_auth_path(self):
            if 'keystone' in self.config:
                path = "http://%s:%s/%s" % (self.keystone['host'],
                                           self.keystone['port'],
                                           self.keystone['apiver'])
            else:
                path = "http://%s:%s/%s" % (self.nova['host'],
                                            self.nova['port'],
                                            self.nova['ver'])
            return path

        def setupSwift(self):
            ret_hash = {}
            ret_hash['auth_host'] = self.config['swift']['auth_host']
            ret_hash['auth_port'] = self.config['swift']['auth_port']
            ret_hash['auth_prefix'] = self.config['swift']['auth_prefix']
            ret_hash['auth_ssl'] = self.config['swift']['auth_ssl']
            ret_hash['account'] = self.config['swift']['account']
            ret_hash['username'] = self.config['swift']['username']
            ret_hash['password'] = self.config['swift']['password']
            # need to find a better way to get this.
            ret_hash['ver'] = 'v1.0'
            return ret_hash

        def setupNova(self):
            ret_hash = {}
            ret_hash['host'] = self.config['nova']['host']
            ret_hash['port'] = self.config['nova']['port']
            ret_hash['ver'] = self.config['nova']['apiver']
            ret_hash['user'] = self.config['nova']['user']
            ret_hash['key'] = self.config['nova']['key']
            return ret_hash

        def setupKeystone(self):
            ret_hash = {}
            ret_hash['host'] = self.config['keystone']['host']
            ret_hash['port'] = self.config['keystone']['port']
            ret_hash['apiver'] = self.config['keystone']['apiver']
            ret_hash['user'] = self.config['keystone']['user']
            ret_hash['pass'] = self.config['keystone']['password']
            return ret_hash

        def setupGlance(self):
            ret_hash = {}
            ret_hash['host'] = self.config['glance']['host']
            ret_hash['port'] = self.config['glance']['port']
            ret_hash['apiver'] = self.config['glance']['apiver']
            return ret_hash

        # Parse the config file
        self.config = parse_config_file(self)
        # pprint(self.config)

        if 'swift' in self.config:
            self.swift = setupSwift(self)
        if 'nova' in self.config:
            self.nova = setupNova(self)
        if 'keystone' in self.config:
            self.keystone = setupKeystone(self)
        if 'glance' in self.config:
            self.glance = setupGlance(self)

        # Setup nova path shortcuts
        self.nova['auth_path'] = _gen_nova_auth_path(self)
        self.nova['path'] = _gen_nova_path(self)
        # setup nova auth token
        self.nova['X-Auth-Token'] = _generate_auth_token(self)

    @classmethod
    def tearDownClass(self):
        self.config = ""
        self.nova = ""
        self.keystone = ""
        self.glance = ""
        self.swift = ""
        self.rabbitmq = ""

    def setUp(self):
        # Define nova auth cache
        self.authcache = ".cache/nova.authcache"

        # setup nova auth token
        # self.nova['X-Auth-Token'] = self.get_auth_token()

    def _md5sum_file(self, path):
        md5sum = md5()
        with open(path, 'rb') as file:
            for chunk in iter(lambda: file.read(8192), ''):
                md5sum.update(chunk)
        return md5sum.hexdigest()

    def _read_in_chunks(self, infile, chunk_size=1024 * 64):
        file_data = open(infile, "rb")
        while True:
            # chunk = file_data.read(chunk_size).encode('base64')
            chunk = file_data.read(chunk_size)
            if chunk:
                yield chunk
            else:
                return
        file_data.close()
