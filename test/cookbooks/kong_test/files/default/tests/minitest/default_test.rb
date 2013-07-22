#
# Cookbook Name:: kong_test
# Recipe:: server
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
#

require_relative "./support/helpers"

describe_recipe "kong_test::default" do
  include KongTestHelpers

  describe "downloads the required code and images" do
    it "creates the image directory" do
      file("/#{Chef::Config[:file_cache_path]}/images").must_exist
    end # it
    %w{cirros-0.3.1-x86_64-blank.img cirros-0.3.1-x86_64-vmlinuz cirros-0.3.1-x86_64-initrd}.each do |image|
      it "downloads #{image}" do
        file("/#{Chef::Config[:file_cache_path]}/images").must_exist
      end #it
    end #each
    it "clones the kong git repo" do
      file("/opt/kong/.gitignore").must_exist
    end #it
  end #describe

  describe "installs the required packages" do
    it "installs the required packcages" do
      %w(git curl python-virtualenv).each do |package_name|
        package(package_name).must_be_installed
      end #each
    end #it
  end #describe

  describe "creates the necessary configuration files" do
    it "creates config.ini" do
      file("/opt/kong/etc/config.ini").must_exist
    end #it
  end #describe
end #describe_recipe
