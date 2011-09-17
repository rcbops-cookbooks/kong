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

from pprint import pprint

import tests


class TestNovaAPI(tests.FunctionalTest):
    #def test_002_verify_nova_auth(self):
    #    if 'keystone' in self.config:
    #        path = "http://%s:%s/%s" % (self.keystone['host'],
    #                                   self.keystone['port'],
    #                                   self.keystone['apiver'])
    #        headers = {'X-Auth-User': self.keystone['user'],
    #                   'X-Auth-Key': self.keystone['pass']}
    #    else:
    #        path = "http://%s:%s/%s" % (self.nova['host'],
    #                                    self.nova['port'],
    #                                    self.nova['ver'])
    #        headers = {'X-Auth-User': self.nova['user'],
    #                   'X-Auth-Key': self.nova['key']}

    #    http = httplib2.Http()
    #    response, content = http.request(path, 'HEAD', headers=headers)
    #    self.assertEqual(response.status, 204)
    #    self.assertNotEqual(response['x-auth-token'], '')
    #    self.assertNotEqual(response['x-server-management-url'], '')
#
    #    # Set up Auth Token for all future API interactions
    #    self.nova['X-Auth-Token'] = response['x-auth-token']
    #test_002_verify_nova_auth.tags = ['nova', 'nova-api']

    def test_101_verify_version_selection_default(self):
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
        if 'keystone' in self.config:
            path = "http://%s:%s/%s" % (self.keystone['host'],
                                       self.keystone['port'],
                                       self.keystone['apiver'])
        else:
            path = "http://%s:%s/%s" % (self.nova['host'],
                                        self.nova['port'],
                                        self.nova['ver'])
        http = httplib2.Http()
        headers = {'X-Auth-User': 'unknown_auth_user',
                  'X-Auth-Key': 'unknown_auth_key'}
        response, content = http.request(path, 'GET', headers=headers)
        self.assertEqual(response.status, 401)
    test_104_bad_user_bad_key.tags = ['nova', 'nova-api']

    def test_105_bad_user_good_key(self):
        if 'keystone' in self.config:
            path = "http://%s:%s/%s" % (self.keystone['host'],
                                       self.keystone['port'],
                                       self.keystone['apiver'])
        else:
            path = "http://%s:%s/%s" % (self.nova['host'],
                                        self.nova['port'],
                                        self.nova['ver'])
        http = httplib2.Http()
        headers = {'X-Auth-User': 'unknown_auth_user',
                  'X-Auth-Key': self.nova['key']}
        response, content = http.request(path, 'GET', headers=headers)
        self.assertEqual(response.status, 401)
    test_105_bad_user_good_key.tags = ['nova', 'nova-api']

    def test_106_good_user_bad_key(self):
        if 'keystone' in self.config:
            path = "http://%s:%s/%s" % (self.keystone['host'],
                                       self.keystone['port'],
                                       self.keystone['apiver'])
        else:
            path = "http://%s:%s/%s" % (self.nova['host'],
                                        self.nova['port'],
                                        self.nova['ver'])
        http = httplib2.Http()
        headers = {'X-Auth-User': self.nova['user'],
                  'X-Auth-Key': 'unknown_auth_key'}
        response, content = http.request(path, 'GET', headers=headers)
        self.assertEqual(response.status, 401)
    test_106_good_user_bad_key.tags = ['nova', 'nova-api']

    def test_107_no_key(self):
        if 'keystone' in self.config:
            path = "http://%s:%s/%s" % (self.keystone['host'],
                                       self.keystone['port'],
                                       self.keystone['apiver'])
        else:
            path = "http://%s:%s/%s" % (self.nova['host'],
                                        self.nova['port'],
                                        self.nova['ver'])
        http = httplib2.Http()
        headers = {'X-Auth-User': self.nova['user']}
        response, content = http.request(path, 'GET', headers=headers)
        self.assertEqual(response.status, 401)
    test_107_no_key.tags = ['nova', 'nova-api']

    def test_108_bad_token(self):
        if 'keystone' in self.config:
            path = "http://%s:%s/%s" % (self.keystone['host'],
                                       self.keystone['port'],
                                       self.keystone['apiver'])
        else:
            path = "http://%s:%s/%s" % (self.nova['host'],
                                        self.nova['port'],
                                        self.nova['ver'])
        http = httplib2.Http()
        headers = {'X-Auth-Token': 'unknown_token'}
        response, content = http.request(path, 'GET', headers=headers)
        self.assertEqual(response.status, 401)
    test_108_bad_token.tags = ['nova', 'nova-api']

    def test_109_verify_blank_limits(self):
        path = "http://%s:%s/%s/limits" % (self.nova['host'],
                                           self.nova['port'],
                                           self.nova['ver'])

        http = httplib2.Http()
        headers = {'X-Auth-User': '%s' % (self.nova['user']),
                   'X-Auth-Token': '%s' % (self.nova['X-Auth-Token'])}
        response, content = http.request(path, 'GET', headers=headers)
        self.assertEqual(response.status, 200)
        self.assertNotEqual(content, '{"limits": []}')
    test_109_verify_blank_limits.tags = ['nova', 'nova-api']

    def test_110_list_flavors_v1_1(self):
        path = "http://%s:%s/%s/flavors" % (self.nova['host'],
                                            self.nova['port'],
                                            self.nova['ver'])
        http = httplib2.Http()
        headers = {'X-Auth-User': '%s' % (self.nova['user']),
                   'X-Auth-Token': '%s' % (self.nova['X-Auth-Token'])}
        response, content = http.request(path, 'GET', headers=headers)
        self.assertEqual(response.status, 200)
        self.assertNotEqual(content, '{"flavors": []}')
    test_110_list_flavors_v1_1.tags = ['nova', 'nova-api']
