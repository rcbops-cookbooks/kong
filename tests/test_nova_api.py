# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright 2011 OpenStack, LLC
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

"""Functional test case against the OpenStack Nova API server"""

import json
import os
import tempfile
import unittest
import httplib2
import urllib
import hashlib
import time
import os
import tests
from pprint import pprint


class TestNovaAPI(tests.FunctionalTest):
    def test_101_verify_version_selection_default(self):
        #path = self.nova['auth_path']
        path = "http://%s:%s/" % (self.nova['host'],
                                           self.nova['port'])
        http = httplib2.Http()
        headers = {'X-Auth-Token': self.nova['X-Auth-Token']}
        response, content = http.request(path, 'GET', headers=headers)
        self.assertEqual(response.status, 200)
        data = json.loads(content)
        self.assertEqual(len(data['versions']), 2)
    test_101_verify_version_selection_default.tags = ['nova', 'nova-api']

    @tests.skip_test("Currently Not Working")
    def test_102_verify_version_selection_json(self):
        path = "http://%s:%s/.json" % (self.nova['host'],
                                           self.nova['port'])
        http = httplib2.Http()
        headers = {'X-Auth-Token': self.nova['X-Auth-Token']}
        response, content = http.request(path, 'GET', headers=headers)
        self.assertEqual(response.status, 200)
        data = json.loads(content)
        self.assertEqual(len(data['versions']), 2)
    test_102_verify_version_selection_json.tags = ['nova', 'nova-api']

    @tests.skip_test("Currently Not Working")
    def test_103_verify_version_selection_xml(self):
        path = "http://%s:%s/.xml" % (self.nova['host'],
                                           self.nova['port'])
        http = httplib2.Http()
        headers = {'X-Auth-Token': self.nova['X-Auth-Token']}
        response, content = http.request(path, 'GET', headers=headers)
        self.assertEqual(response.status, 200)
        self.assertTrue('<versions>' in content)
    test_103_verify_version_selection_xml.tags = ['nova', 'nova-api']

    def test_104_bad_user_bad_key(self):
        path = self.nova['auth_path']
        http = httplib2.Http()
        if not self.keystone:
            headers = {'X-Auth-User': 'unknown_auth_user',
                      'X-Auth-Key': 'unknown_auth_key'}
            response, content = http.request(path, 'GET', headers=headers)
        else:
            path = path + "/tokens"
            body = self._keystone_json('unknown_auth_user',
                                       'unknown_auth_key',
                                       self.keystone['tenantid'])
            response, content = http.request(path,
                                             'POST',
                                             body,
                                             headers={'Content-Type': 'application/json'})
        self.assertEqual(response.status, 401)
    test_104_bad_user_bad_key.tags = ['nova', 'nova-api']

    def test_105_bad_user_good_key(self):
        path = self.nova['auth_path']
        http = httplib2.Http()
        if not self.keystone:
            headers = {'X-Auth-User': 'unknown_auth_user',
                      'X-Auth-Key': self.nova['key']}
            response, content = http.request(path, 'GET', headers=headers)
        else:
            path = path + "/tokens"
            body = self._keystone_json('unknown_auth_user',
                                       self.keystone['pass'],
                                       self.keystone['tenantid'])
            response, content = http.request(path,
                                             'POST',
                                             body,
                                             headers={'Content-Type': 'application/json'})
        self.assertEqual(response.status, 401)
    test_105_bad_user_good_key.tags = ['nova', 'nova-api']

    def test_106_good_user_bad_key(self):
        path = self.nova['auth_path']
        http = httplib2.Http()
        if not self.keystone:
            headers = {'X-Auth-User': self.nova['user'],
                      'X-Auth-Key': 'unknown_auth_key'}
            response, content = http.request(path, 'GET', headers=headers)
        else:
            path = path + "/tokens"
            body = self._keystone_json(self.keystone['user'],
                                       'unknown_auth_key',
                                       self.keystone['tenantid'])
            response, content = http.request(path,
                                             'POST',
                                             body,
                                             headers={'Content-Type': 'application/json'})
        self.assertEqual(response.status, 401)
    test_106_good_user_bad_key.tags = ['nova', 'nova-api']

    def test_107_no_key(self):
        path = self.nova['auth_path']
        http = httplib2.Http()
        if not self.keystone:
            headers = {'X-Auth-User': self.nova['user']}
            response, content = http.request(path, 'GET', headers=headers)
        else:
            path = path + "/tokens"
            body = self._keystone_json(self.keystone['user'],
                                       '',
                                       self.keystone['tenantid'])
            response, content = http.request(path,
                                             'POST',
                                             body,
                                             headers={'Content-Type': 'application/json'})
        self.assertEqual(response.status, 401)
    test_107_no_key.tags = ['nova', 'nova-api']

    def test_108_bad_token(self):
        path = self.nova['auth_path']
        http = httplib2.Http()
        if not self.keystone:
            headers = {'X-Auth-Token': 'unknown_token'}
            response, content = http.request(path, 'GET', headers=headers)
        else:
            path = path + "/tokens"
            body = self._keystone_json('',
                                       self.keystone['pass'],
                                       self.keystone['tenantid'])
            response, content = http.request(path,
                                             'POST',
                                             body,
                                             headers={'Content-Type': 'application/json'})
        self.assertEqual(response.status, 401)
    test_108_bad_token.tags = ['nova', 'nova-api']

    # Currently fails because keystone returns 200 on no tenant provided.
    def test_109_no_tenant(self):
        if self.keystone['apiver'] == "v2.0":
            path = self.nova['auth_path'] + "/tokens"
            http = httplib2.Http()
            body = {"passwordCredentials": {
                                  "username": self.keystone['user'],
                                  "password": self.keystone['pass']}}
            body = json.dumps(body)
            response, content = http.request(path,
                                             'POST',
                                             body,
                                             headers={'Content-Type': 'application/json'})
            self.assertEqual(response.status, 200)
    test_109_no_tenant.tags = ['nova', 'nova-api']

    @tests.skip_test("Currently Not Working")
    def test_110_get_tenant_list(self):
        if self.keystone['apiver'] == "v2.0":
            path = self.keystone['admin_path'] + "/tenants"
            pprint(path)
            http = httplib2.Http()
            body = self._keystone_json(self.keystone['user'],
                                       self.keystone['pass'],
                                       self.keystone['tenantid'])
            response, content = http.request(path,
                                             'GET',
                                             body,
                                             headers={'Content-Type': 'application/json'})
            self.assertEqual(response.status, 200)
    test_110_get_tenant_list.tags = ['nova', 'nova-api']

    def test_201_verify_blank_limits(self):
        path = self.nova['path'] + '/limits'
        http = httplib2.Http()
        headers = {'X-Auth-User': '%s' % (self.nova['user']),
                   'X-Auth-Token': '%s' % (self.nova['X-Auth-Token'])}
        response, content = http.request(path, 'GET', headers=headers)
        self.assertEqual(response.status, 200)
        self.assertNotEqual(content, '{"limits": []}')
    test_201_verify_blank_limits.tags = ['nova', 'nova-api']

    def test_202_list_flavors_v1_1(self):
        path = self.nova['path'] + '/flavors'
        http = httplib2.Http()
        headers = {'X-Auth-User': '%s' % (self.nova['user']),
                   'X-Auth-Token': '%s' % (self.nova['X-Auth-Token'])}
        response, content = http.request(path, 'GET', headers=headers)
        self.assertEqual(response.status, 200)
        self.assertNotEqual(content, '{"flavors": []}')
    test_202_list_flavors_v1_1.tags = ['nova', 'nova-api']
    
    def test_203_verify_extensions_v1_1(self):
        path = self.nova['path'] + '/extensions'
        http = httplib2.Http()
        headers = {'X-Auth-User': '%s' % (self.nova['user']),
                   'X-Auth-Token': '%s' % (self.nova['X-Auth-Token'])}
        response, content = http.request(path, 'GET', headers=headers)
        self.assertEqual(response.status, 200)
        pprint(content)
        self.assertNotEqual(content, '{"flavors": []}')
    test_203_verify_extensions_v1_1.tags = ['nova', 'nova-api']
