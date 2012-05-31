
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

execute "grab the sample_vm" do
  cwd "/opt/kong/include/sample_vm"
  user "root"
  command "curl http://c250663.r63.cf1.rackcdn.com/ttylinux.tgz | tar -zx"
  not_if do File.exists?("/opt/kong/include/sample_vm/ttylinux.img") end
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

ssl_auth = "no"
if swift_proxy_endpoint["scheme"] == "https"
    ssl_auth = "yes"
end

template "/opt/kong/etc/config.ini" do
  source "config.ini.erb"
  owner "root"
  group "root"
  mode "0644"
  variables(
    "keystone_auth_uri" => ks_service_endpoint["uri"],
    "keystone_region" => 'RegionOne',
    "keystone_user" => keystone_admin_user,
    "keystone_pass" => keystone_admin_password,
    "keystone_tenant" => keystone_admin_tenant,
    "nova_network_label" => node["nova"]["network_label"],
    "swift_proxy_host" => swift_proxy_endpoint["host"],
    "swift_proxy_port" => swift_proxy_endpoint["port"],
    "swift_auth_prefix" => "/auth/",
    "swift_ssl_auth" => ssl_auth,
    "swift_auth_type" => swift["authmode"],
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
