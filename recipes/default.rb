#
# Cookbook Name:: kong
# Recipe:: default
#
# Copyright 2012, Rackspace US, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# this recipe installs the openstack api test suite 'kong'


%w{git curl python-virtualenv}.each do |pkg|
  package pkg do
    action :install
  end
end

execute "git clone https://github.com/rcbops/kong" do
  command "git clone https://github.com/rcbops/kong"
  cwd "/opt"
  user "root"
  not_if do File.exists?("/opt/kong") end
end

execute "checkout kong branch" do
  command "git checkout #{node['kong']['branch']}"
  cwd "/opt/kong"
  user "root"
end

directory "/tmp/images/tty" do
  action :create
  group "root"
  owner "root"
  mode "0700"
  recursive true
end

%w{ttylinux.img ttylinux-vmlinuz ttylinux-initrd}.each do |image|
  execute "grab the sample_vm #{image}" do
    cwd "/tmp/images"
    user "root"
    command "curl http://build.monkeypuppetlabs.com/ttylinux.tgz | tar -zx -C tty/"
    not_if do File.exists?("/tmp/images/tty/#{image}") end
  end

  execute "copy sample_vm #{image} " do
    cwd "/opt/kong/include/sample_vm"
    user "root"
    command "cp /tmp/images/tty/#{image} /opt/kong/include/sample_vm/#{image}"
    not_if do File.exists?("/opt/kong/include/sample_vm/#{image}") end
  end 
end

execute "install virtualenv" do
  command "python tools/install_venv.py"
  cwd "/opt/kong"
  user "root"
end

ks_service_endpoint = get_access_endpoint("keystone", "keystone","service-api")
keystone = get_settings_by_role("keystone", "keystone")
keystone_admin_user = keystone["admin_user"]
keystone_admin_password = keystone["users"][keystone_admin_user]["password"]
keystone_admin_tenant = keystone["users"][keystone_admin_user]["default_tenant"]
swift_proxy_endpoint = get_access_endpoint("swift-proxy-server", "swift", "proxy")
swift = get_settings_by_role("swift-proxy-server", "swift")

swift_authmode = "swauth"
if not swift.nil?
  swift_authmode = swift["authmode"]
end

ssl_auth = "no"
swift_proxy_host = ""
swift_proxy_port = ""
if not swift_proxy_endpoint.nil?
    if swift_proxy_endpoint["scheme"] == "https"
        ssl_auth = "yes"
    end
    swift_proxy_host = swift_proxy_endpoint["host"]
    swift_proxy_port = swift_proxy_endpoint["port"]
end

template "/opt/kong/etc/config.ini" do
  source "config.ini.erb"
  owner "root"
  group "root"
  mode "0644"
  variables(
    "ks_service_endpoint" => ks_service_endpoint,
    "keystone_region" => 'RegionOne',
    "keystone_user" => keystone_admin_user,
    "keystone_pass" => keystone_admin_password,
    "keystone_tenant" => keystone_admin_tenant,
    "nova_network_label" => node["nova"]["network_label"],
    "swift_proxy_host" => swift_proxy_host,
    "swift_proxy_port" => swift_proxy_port,
    "swift_auth_prefix" => "/auth/",
    "swift_ssl_auth" => ssl_auth,
    "swift_auth_type" => swift_authmode,
    "swift_account" => node["swift"]["account"],
    "swift_user" => node["swift"]["username"],
    "swift_pass" => node["swift"]["password"]
  )
end

execute "Kong: Nova test suite" do
  command "./run_tests.sh -V --nova"
  cwd "/opt/kong"
  user "root"
  action :nothing
end
