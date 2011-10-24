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
import urlparse
import json
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

        #TODO: need to move this stuff out to util files
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
            http = httplib2.Http()
            path = "http://%s:%s/%s/tokens" % (self.config['keystone']['host'],
                                             self.config['keystone']['port'],
                                             self.config['keystone']['apiver'])
            if self.config['keystone']['apiver'] == "v2.0":
                body = {"passwordCredentials": {
                                      "username": self.keystone['user'],
                                      "password": self.keystone['pass']},
                       "tenantid": self.keystone['tenantid']}
                post_path = urlparse.urljoin(path, "tokens")
                post_data = json.dumps(body)
                response, content = http.request(post_path, 'POST',
                                 post_data,
                                 headers={'Content-Type': 'application/json'})
                if response.status == 200:
                    decode = json.loads(content)
                    self.keystone['catalog'] = decode['auth']['serviceCatalog']
                    return decode['auth']['token']['id'].encode('utf-8')
            if self.config['keystone']['apiver'] == "v1.0":
                headers = {'X-Auth-User': self.keystone['user'],
                           'X-Auth-Key': self.keystone['key']}
                response, content = http.request(path, 'HEAD', headers=headers)
                if response.status == 204:
                    return response['X-Auth-Token']
            else:
                raise Exception("Unable to get a valid token, please fix")

        def _gen_nova_path(self):
            for k, v in enumerate(self.keystone['catalog']['nova']):
                if v['region'] == self.keystone['region']:
                    self.nova['path'] = str(v['publicURL'])
                    self.nova['adminPath'] = str(v['adminURL'])
                    return True
            raise Exception(
                "Cannot find region defined in configuration file.")

        def _gen_glance_path(self):
            for k, v in enumerate(self.keystone['catalog']['glance']):
                if v['region'] == self.keystone['region']:
                    self.glance['path'] = str(v['publicURL'])
                    self.glance['adminPath'] = str(v['adminURL'])
                    return True
            raise Exception(
                "Cannot find region defined in configuration file.")

        def _gen_keystone_admin_path(self):
            path = "http://%s:%s/%s" % (self.keystone['host'],
                                        self.keystone['admin_port'],
                                        self.keystone['apiver'])
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

        def setupKeystone(self):
            ret_hash = {}
            ret_hash['host'] = self.config['keystone']['host']
            ret_hash['port'] = self.config['keystone']['port']
            ret_hash['admin_port'] = self.config['keystone']['admin_port']
            ret_hash['apiver'] = self.config['keystone']['apiver']
            ret_hash['user'] = self.config['keystone']['user']
            ret_hash['pass'] = self.config['keystone']['password']
            ret_hash['tenantid'] = self.config['keystone']['tenantid']
            ret_hash['region'] = self.config['keystone']['region']
            return ret_hash

        # Parse the config file
        self.config = parse_config_file(self)
        # pprint(self.config)

        if 'keystone' in self.config:
            self.keystone = setupKeystone(self)
            self.keystone['admin_path'] = _gen_keystone_admin_path(self)
            self.nova = {}
            self.nova['X-Auth-Token'] = _generate_auth_token(self)
            gen_path = _gen_nova_path(self)
            self.glance = {}
            gen_path = _gen_glance_path(self)
            self.limits = {}
        else:
            raise Exception(
                "A valid keystone block must be provided in the configuration."
            )
        # TODO: add support for swift from keystone service catalog
        if 'swift' in self.config:
            self.swift = setupSwift(self)
        else:
            raise Exception(
                "A valid swift block must be provided in the configuration."
            )


    @classmethod
    def tearDownClass(self):
        self.config = ""
        self.nova = ""
        self.keystone = ""
        self.glance = ""
        self.swift = ""
        self.rabbitmq = ""

    def setUp(self):
        x = 1

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

    def _keystone_json(self, user, passwd, tenantid):
        build = {"passwordCredentials": {
                            "username": user,
                            "password": passwd}}
        if tenantid:
            build['passwordCredentials']['tenantId'] = tenantid
        else:
            raise Exception("tenantId is required for Keystone "
                            "auth service v2.0")
        return json.dumps(build)
