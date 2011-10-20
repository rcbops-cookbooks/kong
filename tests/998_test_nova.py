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

import hashlib
import httplib2
import json
import os
import tempfile
import unittest
import urllib
import time

from pprint import pprint

import tests


class TestNovaSpinup(tests.FunctionalTest):
    def build_check(self, id):
        self.result = {}
        """
        This is intended to check that a server completes the build process
        and enters an active state upon creation. Due to reporting errors in
        the API we are also testing ping and ssh
        """
        count = 0
        path = "http://%s:%s/%s/%s/servers/%s" % (self.nova['host'],
                                       self.nova['port'],
                                       self.nova['ver'],
                                       self.keystone['tenantid'],
                                       id)
        http = httplib2.Http()
        headers = {'X-Auth-User': '%s' % (self.nova['user']),
                   'X-Auth-Token': '%s' % (self.nova['X-Auth-Token'])}
        response, content = http.request(path, 'GET', headers=headers)
        self.assertEqual(response.status, 200)
        data = json.loads(content)

        # Get Server status exit when active
        while (data['server']['status'] != 'ACTIVE'):
            response, content = http.request(path, 'GET', headers=headers)
            data = json.loads(content)
            time.sleep(5)
            count = count + 5
        self.result['serverid'] = id
        self.result['status'] = data['server']['status']

        # Get IP Address of newly created server
        network = data['server']['addresses'][self.config['nova']['network_label']]
        if network:
            for i in network:
                try:
                    r = "" . join(os.popen('ping -c5 %s' %
                        (i['addr'])).readlines())
                    if r.find('64 bytes') > 1:
                        self.result['ping'] = True
                except:
                    self.result['ping'] = False
                    return self.result

        return self.result

    def test_002_upload_kernel_to_glance(self):
        """
        Uploads a test kernal to glance api
        """
        kernel = self.config['environment']['kernel']
        if 'apiver' in self.glance:
            path = "http://%s:%s/%s/images" % (self.glance['host'],
                          self.glance['port'], self.glance['apiver'])
        else:
            path = "http://%s:%s/images" % (self.glance['host'],
                                        self.glance['port'])
        headers = {'x-image-meta-is-public': 'true',
                   'x-image-meta-name': 'test-kernel',
                   'x-image-meta-disk-format': 'aki',
                   'x-image-meta-container-format': 'aki',
                   'Content-Length': '%d' % os.path.getsize(kernel),
                   'Content-Type': 'application/octet-stream'}

        if self.config['keystone']:
            headers['X-Auth-Token'] = self.nova['X-Auth-Token']

        image_file = open(kernel, "rb")
        http = httplib2.Http()
        response, content = http.request(path, 'POST',
                                         headers=headers,
                                         body=image_file)
        image_file.close()
        self.assertEqual(201, response.status)
        data = json.loads(content)
        self.glance['kernel_id'] = data['image']['id']
        self.assertEqual(data['image']['name'], "test-kernel")
        self.assertEqual(data['image']['checksum'], self._md5sum_file(kernel))
    test_002_upload_kernel_to_glance.tags = ['glance', 'nova']

    def test_003_upload_initrd_to_glance(self):
        """
        Uploads a test initrd to glance api
        """
        initrd = self.config['environment']['initrd']
        if 'apiver' in self.glance:
            path = "http://%s:%s/%s/images" % (self.glance['host'],
                          self.glance['port'], self.glance['apiver'])
        else:
            path = "http://%s:%s/images" % (self.glance['host'],
                                        self.glance['port'])
        headers = {'x-image-meta-is-public': 'true',
                   'x-image-meta-name': 'test-ramdisk',
                   'x-image-meta-disk-format': 'ari',
                   'x-image-meta-container-format': 'ari',
                   'Content-Length': '%d' % os.path.getsize(initrd),
                   'Content-Type': 'application/octet-stream'}

        if self.config['keystone']:
            headers['X-Auth-Token'] = self.nova['X-Auth-Token']

        image_file = open(initrd, "rb")
        http = httplib2.Http()
        response, content = http.request(path,
                                         'POST',
                                         headers=headers,
                                         body=image_file)
        image_file.close()
        self.assertEqual(201, response.status)
        data = json.loads(content)
        self.glance['ramdisk_id'] = data['image']['id']
        self.assertEqual(data['image']['name'], "test-ramdisk")
        self.assertEqual(data['image']['checksum'], self._md5sum_file(initrd))
    test_003_upload_initrd_to_glance.tags = ['glance', 'nova']

    def test_004_upload_image_to_glance(self):
        """
        Uploads a test image to glance api, and
        links it to the initrd and kernel uploaded
        earlier
        """
        image = self.config['environment']['image']
        upload_data = ""
        for chunk in self._read_in_chunks(image):
            upload_data += chunk
        if 'apiver' in self.glance:
            path = "http://%s:%s/%s/images" % (self.glance['host'],
                          self.glance['port'], self.glance['apiver'])
        else:
            path = "http://%s:%s/images" % (self.glance['host'],
                                        self.glance['port'])
        headers = {'x-image-meta-is-public': 'true',
                   'x-image-meta-name': 'test-image',
                   'x-image-meta-disk-format': 'ami',
                   'x-image-meta-container-format': 'ami',
                   'x-image-meta-property-Kernel_id': '%s' % \
                       self.glance['kernel_id'],
                   'x-image-meta-property-Ramdisk_id': '%s' % \
                       self.glance['ramdisk_id'],
                   'Content-Length': '%d' % os.path.getsize(image),
                   'Content-Type': 'application/octet-stream'}

        if self.config['keystone']:
            headers['X-Auth-Token'] = self.nova['X-Auth-Token']

        http = httplib2.Http()
        response, content = http.request(path, 'POST',
                                         headers=headers,
                                         body=upload_data)
        self.assertEqual(201, response.status)
        data = json.loads(content)
        self.glance['image_id'] = data['image']['id']
        self.assertEqual(data['image']['name'], "test-image")
        self.assertEqual(data['image']['checksum'], self._md5sum_file(image))
    test_004_upload_image_to_glance.tags = ['glance', 'nova']

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
    #    # Set up Auth Token for all future API interactions
    #    self.nova['X-Auth-Token'] = response['x-auth-token']
    #test_002_verify_nova_auth.tags = ['nova']

    def test_111_verify_kernel_active_v1_1(self):
        # for testing purposes change self.glance['kernel_id'] to an active
        # kernel image allow for skipping glance tests
        if not 'kernel_id' in self.glance:
            self.glance['kernel_id'] = "61"

        path = "http://%s:%s/%s/%s/images/%s" % (self.nova['host'],
                                              self.nova['port'],
                                              self.nova['ver'],
                                              self.keystone['tenantid'],
                                              self.glance['kernel_id'])
        http = httplib2.Http()
        headers = {'X-Auth-User': '%s' % (self.nova['user']),
                   'X-Auth-Token': '%s' % (self.nova['X-Auth-Token'])}
        response, content = http.request(path, 'GET', headers=headers)
        self.assertEqual(response.status, 200)
        data = json.loads(content)
        self.assertEqual(data['image']['status'], 'ACTIVE')
    test_111_verify_kernel_active_v1_1.tags = ['nova']

    def test_112_verify_ramdisk_active_v1_1(self):
        # for testing purposes change self.glance['ramdisk_id'] to an active
        # ramdisk image, allows you to skip glance tests
        if not 'ramdisk_id' in self.glance:
            self.glance['ramdisk_id'] = "62"

        path = "http://%s:%s/%s/%s/images/%s" % (self.nova['host'],
                                              self.nova['port'],
                                              self.nova['ver'],
                                              self.keystone['tenantid'],
                                              self.glance['ramdisk_id'])
        http = httplib2.Http()
        headers = {'X-Auth-User': '%s' % (self.nova['user']),
                   'X-Auth-Token': '%s' % (self.nova['X-Auth-Token'])}
        response, content = http.request(path, 'GET', headers=headers)
        self.assertEqual(response.status, 200)
        data = json.loads(content)
        self.assertEqual(data['image']['status'], 'ACTIVE')
    test_112_verify_ramdisk_active_v1_1.tags = ['nova']

    def test_113_verify_image_active_v1_1(self):
        # for testing purposes change self.glance['image_id'] to an active
        # image id allows for skipping glance tests
        if not 'image_id' in self.glance:
            self.glance['image_id'] = "63"

        path = "http://%s:%s/%s/%s/images/%s" % (self.nova['host'],
                                              self.nova['port'],
                                              self.nova['ver'],
                                              self.keystone['tenantid'],
                                              self.glance['image_id'])
        http = httplib2.Http()
        headers = {'X-Auth-User': '%s' % (self.nova['user']),
                   'X-Auth-Token': '%s' % (self.nova['X-Auth-Token'])}
        response, content = http.request(path, 'GET', headers=headers)
        self.assertEqual(response.status, 200)
        data = json.loads(content)
        self.assertEqual(data['image']['status'], 'ACTIVE')
    test_113_verify_image_active_v1_1.tags = ['nova']

    def test_200_create_server(self):
        path = self.nova['path'] + '/servers'
        #path = "http://%s:%s/%s/servers" % (self.nova['host'],
        #                                    self.nova['port'],
        #                                    self.nova['ver'])
        http = httplib2.Http()
        headers = {'X-Auth-User': '%s' % (self.nova['user']),
                   'X-Auth-Token': '%s' % (self.nova['X-Auth-Token']),
                   'Content-Type': 'application/json'}

        # Change imageRef to self.glance['image_id']
        json_str = {"server":
            {
                "name": "testing server creation",
                "flavorRef": "http://%s:%s/%s/flavors/2" % (self.nova['host'],
                                                      self.nova['port'],
                                                      self.nova['ver']),
                "imageRef": self.glance['image_id']}}
#                "imageRef": "http://%s:%s/%s/images/%s" % (self.nova['host'],
#                                                      self.nova['port'],
#                                                      self.nova['ver'],
#                                                      self.glance['image_id'])
#           }
#       }
        data = json.dumps(json_str)
        response, content = http.request(path, 'POST', headers=headers,
                                         body=data)
        json_return = json.loads(content)
        self.assertEqual(response.status, 202)
        self.assertEqual(json_return['server']['status'], "BUILD")
        self.nova['single_server_id'] = json_return['server']['id']
        time.sleep(5)
        build_result = self.build_check(self.nova['single_server_id'])
        self.assertEqual(build_result['status'], "ACTIVE")
        self.assertEqual(build_result['ping'], True)
    test_200_create_server.tags = ['nova']

    def test_201_get_server_details(self):
        path = self.nova['path'] + '/servers/' + str(self.nova['single_server_id'])
        #path = "http://%s:%s/%s/servers/%s" % (self.nova['host'],
        #                                       self.nova['port'],
        #                                       self.nova['ver'],
        #                                       self.nova['single_server_id'])
        http = httplib2.Http()
        headers = {'X-Auth-User': '%s' % (self.nova['user']),
                   'X-Auth-Token': '%s' % (self.nova['X-Auth-Token'])}

        response, content = http.request(path, 'GET', headers=headers)
        self.assertEqual(response.status, 200)
    test_201_get_server_details.tags = ['nova']

    def test_202_delete_server(self):
        path = self.nova['path'] + '/servers/' + str(self.nova['single_server_id'])
        #path = "http://%s:%s/%s/servers/%s" % (self.nova['host'],
        #                                       self.nova['port'],
        #                                       self.nova['ver'],
        #                                       self.nova['single_server_id'])
        http = httplib2.Http()
        headers = {'X-Auth-User': '%s' % (self.nova['user']),
                   'X-Auth-Token': '%s' % (self.nova['X-Auth-Token'])}
        response, content = http.request(path, 'DELETE', headers=headers)
        self.assertEqual(response.status, 204)
    test_202_delete_server.tags = ['nova']

    # MOVING TO 900 because it can kill the API
    # Uncomment next line for testing
    # def create_multi(self):
    def test_900_create_multiple(self):
        self.nova['multi_server'] = {}
        path = self.nova['path'] + '/servers'
        #path = "http://%s:%s/%s/servers" % (self.nova['host'],
        #                                    self.nova['port'],
        #                                    self.nova['ver'])
        http = httplib2.Http()
        headers = {'X-Auth-User': '%s' % (self.nova['user']),
                   'X-Auth-Token': '%s' % (self.nova['X-Auth-Token']),
                   'Content-Type': 'application/json'}

        for i in range(1, 2):
            # Change imageRef to self.glance['image_id']
            json_str = {"server":
                {
                    "name": "test %s" % (i),
                    "flavorRef": "http://%s:%s/%s/flavors/2" % (
                                                   self.nova['host'],
                                                   self.nova['port'],
                                                   self.nova['ver']),
                    "imageRef": self.glance['image_id']}}
#                    "imageRef": "http://%s:%s/%s/images/%s" % (
#                                                   self.nova['host'],
#                                                   self.nova['port'],
#                                                   self.nova['ver'],
#                                                   self.glance['image_id'])
#                }
            #}
            data = json.dumps(json_str)
            response, content = http.request(path, 'POST', headers=headers,
                                             body=data)
            json_return = json.loads(content)
            self.assertEqual(response.status, 202)
            self.assertEqual(json_return['server']['status'], "BUILD")
            self.nova['multi_server']["test %s" % (i)] = \
                        json_return['server']['id']
            time.sleep(30)

        for k, v in self.nova['multi_server'].iteritems():
            build_result = self.build_check(v)
            self.assertEqual(build_result['ping'], True)
    test_900_create_multiple.tags = ['nova']

    def test_901_delete_multi_server(self):
        print "Deleting %s instances." % (len(self.nova['multi_server']))
        for k, v in self.nova['multi_server'].iteritems():
            path = self.nova['path'] + '/servers/' + str(v)
            #path = "http://%s:%s/%s/servers/%s" % (self.nova['host'],
            #                                       self.nova['port'],
            #                                       self.nova['ver'],
            #                                       v)
            http = httplib2.Http()
            headers = {'X-Auth-User': '%s' % (self.nova['user']),
                       'X-Auth-Token': '%s' % (self.nova['X-Auth-Token'])}
            response, content = http.request(path, 'DELETE', headers=headers)
            self.assertEqual(204, response.status)
    test_901_delete_multi_server.tags = ['nova']

    def test_997_delete_kernel_from_glance(self):
        if 'apiver' in self.glance:
            path = "http://%s:%s/%s/images/%s" % (self.glance['host'],
                          self.glance['port'], self.glance['apiver'],
                          self.glance['kernel_id'])
        else:
            path = "http://%s:%s/images/%s" % (self.glance['host'],
                          self.glance['port'], self.glance['kernel_id'])
        http = httplib2.Http()

        if self.config['keystone']:
            headers = {'X-Auth-Token': self.nova['X-Auth-Token']}
            response, content = http.request(path, 'DELETE', headers=headers)
        else:
            response, content = http.request(path, 'DELETE')

        self.assertEqual(200, response.status)
    test_997_delete_kernel_from_glance.tags = ['glance', 'nova']

    def test_998_delete_initrd_from_glance(self):
        if 'apiver' in self.glance:
            path = "http://%s:%s/%s/images/%s" % (self.glance['host'],
                          self.glance['port'], self.glance['apiver'],
                          self.glance['ramdisk_id'])
        else:
            path = "http://%s:%s/images/%s" % (self.glance['host'],
                          self.glance['port'], self.glance['ramdisk_id'])
        http = httplib2.Http()

        if self.config['keystone']:
            headers = {'X-Auth-Token': self.nova['X-Auth-Token']}
            response, content = http.request(path, 'DELETE', headers=headers)
        else:
            response, content = http.request(path, 'DELETE')

        self.assertEqual(200, response.status)
    test_998_delete_initrd_from_glance.tags = ['glance', 'nova']

    def test_999_delete_image_from_glance(self):
        if 'apiver' in self.glance:
            path = "http://%s:%s/%s/images/%s" % (self.glance['host'],
                          self.glance['port'], self.glance['apiver'],
                          self.glance['image_id'])
        else:
            path = "http://%s:%s/images/%s" % (self.glance['host'],
                          self.glance['port'], self.glance['image_id'])
        http = httplib2.Http()

        if self.config['keystone']:
            headers = {'X-Auth-Token': self.nova['X-Auth-Token']}
            response, content = http.request(path, 'DELETE', headers=headers)
        else:
            response, content = http.request(path, 'DELETE')

        self.assertEqual(200, response.status)
    test_999_delete_image_from_glance.tags = ['glance', 'nova']
