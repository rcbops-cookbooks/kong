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
import subprocess
from pprint import pprint


class TestNovaAPI(tests.FunctionalTest):
    def ping_host(self, address, interval, max_wait):
        """
        Ping a host ever <interval> seconds, up to a maximum of <max_wait>
        seconds for until the address is succesfully pingable, or the
        maximum wait interval has expired
        """
        start = time.time()
        while(time.time() - start < max_wait):
            try:
                retcode = subprocess.call('ping -c1 -q %s > /dev/null 2>&1'
                                          % (address),
                                          shell=True)
                if retcode == 0:
                    return True
            except OSError, e:
                print "Error running external ping command: ", e
                print retcode
                return False

            time.sleep(2)
        return False

    def build_check(self, id):
        self.result = {}
        """
        This is intended to check that a server completes the build process
        and enters an active state upon creation. Due to reporting errors in
        the API we are also testing ping and ssh
        """
        count = 0
        path = "%s/servers/%s" % (self.nova['path'], id)
        http = httplib2.Http()
        headers = {'X-Auth-User': '%s' % (self.keystone['user']),
                   'X-Auth-Token': '%s' % (self.nova['X-Auth-Token'])}
        response, content = http.request(path, 'GET', headers=headers)
        self.assertEqual(response.status, 200)
        data = json.loads(content)

        # Get Server status exit when active
        # (rp) if it isn't active in two minutes, it won't be
        while ((data['server']['status'] != 'ACTIVE') and (count < 120)):
            response, content = http.request(path, 'GET', headers=headers)
            data = json.loads(content)
            time.sleep(5)
            count = count + 5
        self.result['serverid'] = id
        self.result['status'] = data['server']['status']

        # Get IP Address of newly created server
        net = data['server']['addresses'][self.config['nova']['network_label']]
        self.nova['address'] = net
        self.result['ping'] = False

        if net:
            for i in net:
                if self.ping_host(i['addr'], 5, 60):
                    self.result['ping'] = True
                    return self.result
        else:
            raise Exception("network_label is a required configuration value.")

        return self.result

    def test_001_verify_version_selection_default(self):
        remove = "/v1.1/" + self.keystone['tenantid']
        path = self.nova['path'].replace(remove, '')
        http = httplib2.Http()
        headers = {'X-Auth-User': self.keystone['user'],
                   'X-Auth-Token': self.nova['X-Auth-Token']}
        response, content = http.request(path, 'GET', headers=headers)
        self.assertEqual(response.status, 200)
        data = json.loads(content)
        self.assertEqual(len(data['versions']), 2)
    test_001_verify_version_selection_default.tags = ['nova', 'nova-api']

    # @tests.skip_test("Currently Not Working")
    def test_002_verify_version_selection_json(self):
        remove = "/v1.1/" + self.keystone['tenantid']
        path = self.nova['path'].replace(remove, '') + "/.json"
        http = httplib2.Http()
        headers = {'X-Auth-Token': self.nova['X-Auth-Token']}
        response, content = http.request(path, 'GET', headers=headers)
        self.assertEqual(response.status, 300)
        data = json.loads(content)
        self.assertEqual(len(data['choices']), 2)
    test_002_verify_version_selection_json.tags = ['nova', 'nova-api']

    # @tests.skip_test("Currently Not Working")
    def test_003_verify_version_selection_xml(self):
        remove = "/v1.1/" + self.keystone['tenantid']
        path = self.nova['path'].replace(remove, '') + "/.xml"
        http = httplib2.Http()
        headers = {'X-Auth-Token': self.nova['X-Auth-Token']}
        response, content = http.request(path, 'GET', headers=headers)
        self.assertEqual(response.status, 300)
        self.assertTrue('<version ' in content)
    test_003_verify_version_selection_xml.tags = ['nova', 'nova-api']

    def test_010_bad_user_bad_key(self):
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
    test_010_bad_user_bad_key.tags = ['nova', 'nova-api', 'keystone']

    def test_011_bad_user_good_key(self):
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
    test_011_bad_user_good_key.tags = ['nova', 'nova-api', 'keystone']

    def test_012_good_user_bad_key(self):
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
    test_012_good_user_bad_key.tags = ['nova', 'nova-api', 'keystone']

    def test_013_no_key(self):
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
    test_013_no_key.tags = ['nova', 'nova-api', 'keystone']

    def test_014_bad_token(self):
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
    test_014_bad_token.tags = ['nova', 'nova-api', 'keystone']

    def test_015_no_tenant(self):
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
    test_015_no_tenant.tags = ['nova', 'nova-api', 'keystone']

    # @tests.skip_test("Currently Not Working")
    def test_016_get_tenant_list(self):
        path = "http://%s:%s/%s/tenants" % (self.keystone['host'],
                                           self.keystone['port'],
                                           self.keystone['apiver'])
        http = httplib2.Http()
        response, content = http.request(path,
                            'GET',
                            headers={'Content-Type': 'application/json',
                                 'X-Auth-Token': self.nova['X-Auth-Token']})
        self.assertEqual(response.status, 200)
    test_016_get_tenant_list.tags = ['nova', 'nova-api', 'keystone']

    def test_020_list_flavors_v1_1(self):
        path = self.nova['path'] + '/flavors'
        http = httplib2.Http()
        headers = {'X-Auth-User': '%s' % (self.keystone['user']),
                   'X-Auth-Token': '%s' % (self.nova['X-Auth-Token'])}
        response, content = http.request(path, 'GET', headers=headers)
        data = json.loads(content)
        for i in data['flavors']:
            if i['name'] == "m1.tiny":
                self.flavor['id'] = i['id']
        self.assertEqual(response.status, 200)
        self.assertNotEqual(content, '{"flavors": []}')
    test_020_list_flavors_v1_1.tags = ['nova', 'nova-api']

    # @tests.skip_test("Skipping verify extensions")
    def test_021_verify_extensions_v1_1(self):
        path = self.nova['path'] + "/extensions"
        http = httplib2.Http()
        headers = {'X-Auth-Token': '%s' % (self.nova['X-Auth-Token'])}
        response, content = http.request(path, 'GET', headers=headers)
        self.assertEqual(response.status, 200)
        data = json.loads(content)
        required_extensions = {'os-simple-tenant-usage': 1,
                               'os-hosts': 1,
                               'ADMIN': 1,
                               'os-quota-sets': 1,
                               'os-flavor-extra-specs': 1,
                               'os-create-server-ext': 1,
                               'os-keypairs': 1,
                               'os-floating-ips': 1}

        for i in required_extensions:
            for j in data['extensions']:
                if j['alias'] == i:
                    required = True
                else:
                    required = i

        self.assertEqual(required, True)
    test_021_verify_extensions_v1_1.tags = ['nova', 'nova-api']

    def test_022_verify_not_blank_limits(self):
        path = self.nova['path'] + '/limits'
        http = httplib2.Http()
        headers = {'X-Auth-Token': '%s' % (self.nova['X-Auth-Token'])}
        response, content = http.request(path, 'GET', headers=headers)
        data = json.loads(content)
        rate_limits = data['limits']['rate']

        #### PUT, POST, DELETE Rate Limits (Defaults)
        for i, l in enumerate(rate_limits):
            for k, v in enumerate(rate_limits[i]['limit']):
                if v['verb'] == "POST" and v['unit'] == "MINUTE":
                    self.limits['POST'] = v['value']
                if v['verb'] == "PUT":
                    self.limits['PUT'] = v['value']
                if v['verb'] == "DELETE":
                    self.limits['DELETE'] = v['value']

        self.assertEqual(response.status, 200)
        self.assertNotEqual(content, '{"limits": []}')
    test_022_verify_not_blank_limits.tags = ['nova', 'nova-api']

    def test_101_upload_kernel_to_glance(self):
        """
        Uploads a test kernal to glance api
        """
        kernel = self.config['environment']['kernel']
        path = self.glance['path'] + "/images"
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
    test_101_upload_kernel_to_glance.tags = ['glance', 'nova']

    def test_102_upload_initrd_to_glance(self):
        """
        Uploads a test initrd to glance api
        """
        initrd = self.config['environment']['initrd']
        path = self.glance['path'] + "/images"
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
    test_102_upload_initrd_to_glance.tags = ['glance', 'nova']

    def test_103_upload_image_to_glance(self):
        """
        Uploads a test image to glance api, and
        links it to the initrd and kernel uploaded
        earlier
        """
        image = self.config['environment']['image']
        upload_data = ""
        for chunk in self._read_in_chunks(image):
            upload_data += chunk
        path = self.glance['path'] + "/images"
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
    test_103_upload_image_to_glance.tags = ['glance', 'nova']

    def test_104_verify_kernel_active_v1_1(self):
        # for testing purposes change self.glance['kernel_id'] to an active
        # kernel image allow for skipping glance tests
        if not 'kernel_id' in self.glance:
            self.glance['kernel_id'] = "61"

        path = self.nova['path'] + "/images/%s" % (self.glance['kernel_id'])
        http = httplib2.Http()
        headers = {'X-Auth-User': '%s' % (self.keystone['user']),
                   'X-Auth-Token': '%s' % (self.nova['X-Auth-Token'])}
        response, content = http.request(path, 'GET', headers=headers)
        self.assertEqual(response.status, 200)
        data = json.loads(content)
        self.assertEqual(data['image']['status'], 'ACTIVE')
    test_104_verify_kernel_active_v1_1.tags = ['nova']

    def test_105_verify_ramdisk_active_v1_1(self):
        # for testing purposes change self.glance['ramdisk_id'] to an active
        # ramdisk image, allows you to skip glance tests
        if not 'ramdisk_id' in self.glance:
            self.glance['ramdisk_id'] = "62"

        path = self.nova['path'] + "/images/%s" % (self.glance['ramdisk_id'])
        http = httplib2.Http()
        headers = {'X-Auth-User': '%s' % (self.keystone['user']),
                   'X-Auth-Token': '%s' % (self.nova['X-Auth-Token'])}
        response, content = http.request(path, 'GET', headers=headers)
        self.assertEqual(response.status, 200)
        data = json.loads(content)
        self.assertEqual(data['image']['status'], 'ACTIVE')
    test_105_verify_ramdisk_active_v1_1.tags = ['nova']

    def test_106_verify_image_active_v1_1(self):
        # for testing purposes change self.glance['image_id'] to an active
        # image id allows for skipping glance tests
        if not 'image_id' in self.glance:
            self.glance['image_id'] = "63"

        path = self.nova['path'] + "/images/%s" % (self.glance['image_id'])
        http = httplib2.Http()
        headers = {'X-Auth-User': '%s' % (self.keystone['user']),
                   'X-Auth-Token': '%s' % (self.nova['X-Auth-Token'])}
        response, content = http.request(path, 'GET', headers=headers)
        self.assertEqual(response.status, 200)
        data = json.loads(content)
        self.assertEqual(data['image']['status'], 'ACTIVE')
    test_106_verify_image_active_v1_1.tags = ['nova']

    def test_200_create_server(self):
        path = self.nova['path'] + '/servers'
        http = httplib2.Http()
        headers = {'X-Auth-User': '%s' % (self.keystone['user']),
                   'X-Auth-Token': '%s' % (self.nova['X-Auth-Token']),
                   'Content-Type': 'application/json'}

        # Change imageRef to self.glance['image_id']
        json_str = {"server":
            {
                "name": "testing server creation",
                "flavorRef": "%s/flavors/%s" % (self.nova['path'],
                                                self.flavor['id']),
                "imageRef": self.glance['image_id']}}
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

    def test_201_list_servers(self):
        match = False
        path = self.nova['path'] + '/servers/detail'
        http = httplib2.Http()
        headers = {'X-Auth-Token': '%s' % (self.nova['X-Auth-Token'])}
        response, content = http.request(path, 'GET', headers=headers)
        json_return = json.loads(content)
        self.assertEqual(response.status, 200)

        for i in json_return['servers']:
            if i['id'] == self.nova['single_server_id']:
                match = True

        self.assertEqual(match, True)
    test_201_list_servers.tags = ['nova']

    def test_202_get_server_details(self):
        path = self.nova['path'] + '/servers/'
        path = path + str(self.nova['single_server_id'])
        http = httplib2.Http()
        headers = {'X-Auth-User': '%s' % (self.keystone['user']),
                   'X-Auth-Token': '%s' % (self.nova['X-Auth-Token'])}

        response, content = http.request(path, 'GET', headers=headers)
        self.assertEqual(response.status, 200)
    test_202_get_server_details.tags = ['nova']

    def test_203_update_server(self):
        path = self.nova['path'] + '/servers/'\
                + str(self.nova['single_server_id'])
        name = "updated"
        match = False
        json_put = json.dumps({"server":
                                    {"name": name}})
        headers = {'X-Auth-Token': '%s' % (self.nova['X-Auth-Token']),
                   'Content-Type': 'application/json'}
        http = httplib2.Http()
        response, content = http.request(path,
                                         'PUT',
                                         headers=headers,
                                         body=json_put)
        self.assertEqual(response.status, 200)
        json_return = json.loads(content)
        for i in json_return['server']:
            if i[0]['name'] == name:
                match = True
        self.assertEqual(match, True)
    test_203_update_server.tags = ['nova']

    def test_210_list_addresses(self):
        path = self.nova['path'] + '/servers/'\
                    + str(self.nova['single_server_id']) + 'ips'
        headers = {'X-Auth-Token': '%s' % (self.nova['X-Auth-Token'])}
        http = httplib2.Http()
        response, content = http.request(path, 'GET', headers=headers)
        json_return = json.loads(content)
    test_210_list_addresses.tags = ['nova']

    @tests.skip_test("Skipping multi-instance tests")
    def test_300_create_to_postpm_limit(self):
        self.nova['multi_server'] = {}
        self.nova['multi_fails'] = {}
        path = self.nova['path'] + '/servers'
        http = httplib2.Http()
        headers = {'X-Auth-Token': '%s' % (self.nova['X-Auth-Token']),
                   'Content-Type': 'application/json'}

        # It appears that nova allows you to overrun the limit by 1.
        # We are trying to get a failure so adding 2 to limit
        # provided by API.
        for i in range(0, self.limits['POST']):
            json_str = {"server":
                           {
                            "name": "test post limit %s" % (i),
                            "flavorRef": "%s/flavors/%s" % (self.nova['path'],
                                                            self.flavor['id']),
                            "imageRef": self.glance['image_id']}}
            data = json.dumps(json_str)
            response, content = http.request(path,
                                             'POST',
                                             headers=headers,
                                             body=data)
            json_return = json.loads(content)
            if response.status == 202:
                self.nova['multi_server']["test post limit %s" % (i)] = \
                    json_return['server']['id']
            else:
                self.nova['multi_fails'] = [i]

        # API allows us to overrun by one so accounting for that
        # in the result.
        self.assertEqual(self.limits['POST'],
                        len(self.nova['multi_server']))
        self.assertEqual(1, len(self.nova['multi_fails']))

        for i, name in enumerate(self.nova['multi_server']):
            build_result = self.build_check(
                               self.nova['multi_server'][str(name)])
            self.assertEqual(build_result['ping'], True)
    test_300_create_to_postpm_limit.tags = ['nova', 'nova-api']

    def test_900_delete_server(self):
        path = self.nova['path'] + '/servers/'
        path = path + str(self.nova['single_server_id'])
        http = httplib2.Http()
        headers = {'X-Auth-User': '%s' % (self.keystone['user']),
                   'X-Auth-Token': '%s' % (self.nova['X-Auth-Token'])}
        response, content = http.request(path, 'DELETE', headers=headers)
        self.assertEqual(response.status, 204)
    test_900_delete_server.tags = ['nova']

    @tests.skip_test("Skipping multi-instance tests")
    def test_996_delete_multi_server(self):
        http = httplib2.Http()
        headers = {'X-Auth-Token': '%s' % (self.nova['X-Auth-Token'])}
        for i, name in enumerate(self.nova['multi_server']):
            path = self.nova['path'] + '/servers/' + str(
                        self.nova['multi_server'][name])
            response, content = http.request(path, 'DELETE', headers=headers)
            self.assertEqual(response.status, 204)
    test_996_delete_multi_server.tags = ['nova']

    def test_997_delete_kernel_from_glance(self):
        path = self.glance['path'] + "/images/%s" % (self.glance['kernel_id'])
        http = httplib2.Http()

        headers = {'X-Auth-Token': self.nova['X-Auth-Token']}
        response, content = http.request(path, 'DELETE', headers=headers)

        self.assertEqual(200, response.status)
    test_997_delete_kernel_from_glance.tags = ['glance', 'nova']

    def test_998_delete_initrd_from_glance(self):
        path = self.glance['path'] + "/images/%s" % (self.glance['ramdisk_id'])
        http = httplib2.Http()

        headers = {'X-Auth-Token': self.nova['X-Auth-Token']}
        response, content = http.request(path, 'DELETE', headers=headers)

        self.assertEqual(200, response.status)
    test_998_delete_initrd_from_glance.tags = ['glance', 'nova']

    def test_999_delete_image_from_glance(self):
        path = self.glance['path'] + "/images/%s" % (self.glance['image_id'])
        http = httplib2.Http()

        headers = {'X-Auth-Token': self.nova['X-Auth-Token']}
        response, content = http.request(path, 'DELETE', headers=headers)

        self.assertEqual(200, response.status)
    test_999_delete_image_from_glance.tags = ['glance', 'nova']
