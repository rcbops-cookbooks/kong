#
# Cookbook Name:: kong
# Recipe:: default
#
# Copyright 2012-2013, Rackspace US, Inc.
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

git "/opt/kong" do
  repository "https://github.com/rcbops/kong"
  reference "master"
  action "checkout"
end

directory "/#{Chef::Config[:file_cache_path]}/images/cirros" do
  action :create
  group "root"
  owner "root"
  mode "0700"
  recursive true
end

# Download tar
remote_file "/#{Chef::Config[:file_cache_path]}/images/cirros-0.3.1-x86_64-uec.tar.gz" do
  source "http://build.monkeypuppetlabs.com/cirros-0.3.1-x86_64-uec.tar.gz"
end

# Extract tar
execute "extract downloaded image" do
  cwd "/#{Chef::Config[:file_cache_path]}/images"
  user "root"
  command "tar -zxf cirros-0.3.1-x86_64-uec.tar.gz -C cirros/"
end

%w{cirros-0.3.1-x86_64-blank.img
  cirros-0.3.1-x86_64-vmlinuz cirros-0.3.1-x86_64-initrd}.each do |image|
  execute "copy sample_vm #{image} " do
    cwd "/opt/kong/include/sample_vm"
    user "root"
    command "cp /#{Chef::Config[:file_cache_path]}/images/cirros/#{image} \
      /opt/kong/include/sample_vm/#{image}"
    not_if do File.exists?("/opt/kong/include/sample_vm/#{image}") end
  end
end

execute "install virtualenv" do
  command "python tools/install_venv.py"
  cwd "/opt/kong"
  user "root"
end


if Chef::Config[:solo]
  ks_service_endpoint = node["solo"]["ks_service_endpoint"]
  keystone = node["solo"]["keystone_settings"]
  swift_proxy_endpoint = node["solo"]["swift_proxy_endpoint"]
  swift = node["solo"]["swift_settings"]
  glance = node["solo"]["glance_settings"]

else
  ks_service_endpoint = get_access_endpoint(
    "keystone-api", "keystone", "service-api")
  keystone = get_settings_by_role("keystone-setup", "keystone")
  swift_proxy_endpoint = get_access_endpoint(
    "swift-proxy-server", "swift", "proxy")
  swift = get_settings_by_role("swift-proxy-server", "swift")
  glance = get_settings_by_role("glance-setup", "glance")
end

keystone_admin_user = keystone["admin_user"]
keystone_admin_password = keystone["users"][keystone_admin_user]["password"]
keystone_admin_tenant = keystone["users"]\
  [keystone_admin_user]["default_tenant"]
swift_store_auth_address = "http://swiftendpoint"
swift_store_user = "swift_store_user"
swift_store_tenant = "swift_store_tenant"
swift_store_key = "swift_store_key"
swift_store_container = "container"

if glance && glance["api"]["swift_store_auth_address"].nil?
  swift_store_auth_address = "http://#{ks_service_endpoint["host"]}"\
    + ":#{ks_service_endpoint["port"]}"
  swift_store_tenant=glance["service_tenant_name"]
  swift_store_user=glance["service_user"]
  swift_store_key=glance["service_pass"]
  swift_store_container = glance["api"]["swift"]["store_container"]
  swift_store_region=node["osops"]["region"]
elsif glance
  swift_store_auth_address=glance["api"]["swift_store_auth_address"]
  swift_store_user=glance["api"]["swift_store_user"]
  swift_store_tenant=glance["api"]["swift_store_tenant"]
  swift_store_key=glance["api"]["swift_store_key"]
  swift_store_container = glance["api"]["swift"]["store_container"]
  if node["kong"]["swift_store_region"].nil?
    swift_store_region=node["osops"]["region"]
  else
    swift_store_region=node["kong"]["swift_store_region"]
  end
end

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
    "swift_store_region" => swift_store_region,
    "swift_proxy_host" => swift_proxy_host,
    "swift_proxy_port" => swift_proxy_port,
    "swift_auth_prefix" => "/auth/",
    "swift_ssl_auth" => ssl_auth,
    "swift_auth_type" => swift_authmode,
    "swift_account" => node["swift"]["account"],
    "swift_user" => node["swift"]["username"],
    "swift_pass" => node["swift"]["password"],
    "swift_store_auth_address" => swift_store_auth_address,
    "swift_store_user" => swift_store_user,
    "swift_store_key" => swift_store_key,
    "swift_store_tenant" => swift_store_tenant,
    "swift_store_container" => swift_store_container
  )
end

#execute "Kong: Nova test suite" do
#  command "./run_tests.sh -V --nova"
#  cwd "/opt/kong"
#  user "root"
#  action :nothing
#end
