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
        remove = "/v1.1/" + self.keystone['tenantid']
        path = self.nova['path'].replace(remove, '')
        http = httplib2.Http()
        headers = {'X-Auth-User': self.keystone['user'],
                   'X-Auth-Token': self.nova['X-Auth-Token']}
        response, content = http.request(path, 'GET', headers=headers)
        pprint(content)
        self.assertEqual(response.status, 200)
        data = json.loads(content)
        self.assertEqual(len(data['versions']), 2)
    test_101_verify_version_selection_default.tags = ['nova', 'nova-api']

    # @tests.skip_test("Currently Not Working")
    def test_102_verify_version_selection_json(self):
        remove = "/v1.1/" + self.keystone['tenantid']
        path = self.nova['path'].replace(remove, '') + "/.json"
        http = httplib2.Http()
        headers = {'X-Auth-Token': self.nova['X-Auth-Token']}
        response, content = http.request(path, 'GET', headers=headers)
        self.assertEqual(response.status, 300)
        data = json.loads(content)
        self.assertEqual(len(data['choices']), 2)
    test_102_verify_version_selection_json.tags = ['nova', 'nova-api']

    # @tests.skip_test("Currently Not Working")
    def test_103_verify_version_selection_xml(self):
        remove = "/v1.1/" + self.keystone['tenantid']
        path = self.nova['path'].replace(remove, '') + "/.xml"
        http = httplib2.Http()
        headers = {'X-Auth-Token': self.nova['X-Auth-Token']}
        response, content = http.request(path, 'GET', headers=headers)
        self.assertEqual(response.status, 300)
        self.assertTrue('<version ' in content)
    test_103_verify_version_selection_xml.tags = ['nova', 'nova-api']

    def test_104_bad_user_bad_key(self):
        path = self.nova['path']
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
        path = self.nova['path']
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
        path = self.nova['path']
        http = httplib2.Http()
        if not self.keystone:
            headers = {'X-Auth-User': self.keystone['user'],
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
        path = self.nova['path']
        http = httplib2.Http()
        if not self.keystone:
            headers = {'X-Auth-User': self.keystone['user']}
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
        path = self.nova['path']
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
        path = self.nova['path'] + "/tokens"
        http = httplib2.Http()
        body = {"passwordCredentials": {
            "username": self.keystone['user'],
            "password": self.keystone['pass']}}
        body = json.dumps(body)
        response, content = http.request(path,
                            'POST',
                            body,
                            headers={'Content-Type': 'application/json'})
        self.assertEqual(response.status, 401)
    test_109_no_tenant.tags = ['nova', 'nova-api']

    # @tests.skip_test("Currently Not Working")
    def test_110_get_tenant_list(self):
        path = "http://%s:%s/%s/tenants" % (self.keystone['host'],
                                           self.keystone['port'],
                                           self.keystone['apiver'])
        http = httplib2.Http()
        response, content = http.request(path,
                            'GET',
                            headers={'Content-Type': 'application/json',
                                     'X-Auth-Token': self.nova['X-Auth-Token']})
        self.assertEqual(response.status, 200)
        pprint(content)
    test_110_get_tenant_list.tags = ['nova', 'nova-api']

    def test_201_verify_blank_limits(self):
        path = self.nova['path'] + '/limits'
        http = httplib2.Http()
        headers = {'X-Auth-User': '%s' % (self.keystone['user']),
                   'X-Auth-Token': '%s' % (self.nova['X-Auth-Token'])}
        response, content = http.request(path, 'GET', headers=headers)
        self.assertEqual(response.status, 200)
        self.assertNotEqual(content, '{"limits": []}')
    test_201_verify_blank_limits.tags = ['nova', 'nova-api']

    def test_202_list_flavors_v1_1(self):
        path = self.nova['path'] + '/flavors'
        http = httplib2.Http()
        headers = {'X-Auth-User': '%s' % (self.keystone['user']),
                   'X-Auth-Token': '%s' % (self.nova['X-Auth-Token'])}
        response, content = http.request(path, 'GET', headers=headers)
        self.assertEqual(response.status, 200)
        self.assertNotEqual(content, '{"flavors": []}')
    test_202_list_flavors_v1_1.tags = ['nova', 'nova-api']

    @tests.skip_test("Skipping verify extensions")
    def test_203_verify_extensions_v1_1(self):
        remove = "/v1.1/" + self.keystone['tenantid']
        path = self.nova['path'].replace(remove, '') + "/extensions"
        http = httplib2.Http()
        headers = {'X-Auth-Token': '%s' % (self.nova['X-Auth-Token'])}
        response, content = http.request(path, 'GET', headers=headers)
        self.assertEqual(response.status, 200)
        data = json.loads(content)
        pprint(data['extensions'])
        required_extensions = {'os-simple-tenant-usage': 1,
                               'os-hosts': 1,
                               'ADMIN': 1,
                               'os-quota-sets': 1,
                               'os-flavor-extra-specs': 1,
                               'os-create-server-ext': 1,
                               'os-keypairs': 1,
                               'os-floating-ips': 1}
        self.assertNotEqual(content, '{"flavors": []}')
    test_203_verify_extensions_v1_1.tags = ['nova', 'nova-api']
