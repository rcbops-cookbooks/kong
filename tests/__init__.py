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
from xmlrpclib import Server

NOVA_DATA = {}
GLANCE_DATA = {}
SWIFT_DATA = {}
RABBITMQ_DATA = {}
CONFIG_DATA = {}
KEYSTONE_DATA = {}

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
        print "Running setUpClass"
        pprint(self)
        self.config = {}
        self.glance = {}
        self.nova = {}
        self.swift = {}
        self.rabbitmq = {}
        self.keystone = {}

    @classmethod
    def tearDownClass(self):
        x = 1

    def setUp(self):
        print "Running setUp"
        pprint(self)
        #global GLANCE_DATA, NOVA_DATA, SWIFT_DATA, RABBITMQ_DATA, KEYSTONE_DATA, CONFIG_DATA
        ## Define config dict
        #self.config = CONFIG_DATA
        ## Define service specific dicts
        #self.glance = GLANCE_DATA
        #self.nova = NOVA_DATA
        #self.swift = SWIFT_DATA
        #self.rabbitmq = RABBITMQ_DATA
        #self.keystone = KEYSTONE_DATA

        # Define nova auth cache
        self.authcache = ".cache/nova.authcache"

        self._parse_defaults_file()
        # pprint(self.config)

        # Swift Setup
        if 'swift' in self.config:
            self.swift['auth_host'] = self.config['swift']['auth_host']
            self.swift['auth_port'] = self.config['swift']['auth_port']
            self.swift['auth_prefix'] = self.config['swift']['auth_prefix']
            self.swift['auth_ssl'] = self.config['swift']['auth_ssl']
            self.swift['account'] = self.config['swift']['account']
            self.swift['username'] = self.config['swift']['username']
            self.swift['password'] = self.config['swift']['password']
            self.swift['ver'] = 'v1.0'  # need to find a better way to get this.

        # Glance Setup
        self.glance['host'] = self.config['glance']['host']
        self.glance['port'] = self.config['glance']['port']
        if 'apiver' in self.config['glance']:
            self.glance['apiver'] = self.config['glance']['apiver']

        if 'nova' in self.config:
            self.nova['host'] = self.config['nova']['host']
            self.nova['port'] = self.config['nova']['port']
            self.nova['ver'] = self.config['nova']['apiver']
            self.nova['user'] = self.config['nova']['user']
            self.nova['key'] = self.config['nova']['key']

        if 'keystone' in self.config:
            self.keystone['host'] = self.config['keystone']['host']
            self.keystone['port'] = self.config['keystone']['port']
            self.keystone['apiver'] = self.config['keystone']['apiver']
            self.keystone['user'] = self.config['keystone']['user']
            self.keystone['pass'] = self.config['keystone']['password']


        self.nova['auth_path'] = self._gen_nova_auth_path()
        self.nova['path'] = self._gen_nova_path()

        # setup nova auth token
        token = self.get_auth_token()
        self.nova['X-Auth-Token'] = token

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

    def get_auth_token(self):
        token = self._get_token_from_cachefile()
        if token == None or not self.valid_token(token):
            token = self._generate_new_token()
            self._cache_token(token)
        return token

    def _generate_new_token(self):
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
            raise Error("Unable to get a valid token, please fix")

    def valid_token(self, token):
        path = self.nova['path'] + "/extensions"
        headers = {'X-Auth-Token': token}
        http = httplib2.Http()
        response, content = http.request(path, 'GET', headers=headers)
        if response.status == 200:
            ret = True
        else:
            ret = False
        return ret

    def _cache_token(self, token):
        f = open(self.authcache, 'w')
        f.write(token)
        f.close()

    def _get_token_from_cachefile(self):
        if os.path.exists(self.authcache):
            f = open(self.authcache, 'r')
            ret = f.read()
            f.close()
        else:
          ret = None
        return ret

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

    def _parse_defaults_file(self):
        cfg = os.path.abspath(os.path.join(os.path.dirname(__file__),
                                   "..", "etc", "config.ini"))
        if os.path.exists(cfg):
            self._build_config(cfg)
        else:
            raise Exception("Cannot read %s" % cfg)

    def _build_config(self, config_file):
        parser = ConfigParser.ConfigParser()
        parser.read(config_file)

        for section in parser.sections():
            self.config[section] = {}
            for value in parser.options(section):
                self.config[section][value] = parser.get(section, value)
                # print "%s = %s" % (value, parser.get(section, value))
