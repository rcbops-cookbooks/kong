kong Cookbook
==================
Cookbook for testing the kong cookbook, which deploys the kong
tests for openstack. 

Requirements
------------
Requirements are listed in the kong Berksfile, metadata file and 
gemfile.

Attributes
----------
This cookbook requires no attributes, but it supplies some attributes to the
kong cookbook, see .kitchen.yml in the root of the kong cookbook
for details.

Usage
-----
#### kong::default
From the kong cookbook, run bundle install; kitchen test all
Also read TESTING.md in the kong cookbook.
