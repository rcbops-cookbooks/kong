maintainer        "Rackspace Hosting, Inc."
license           "Apache 2.0"
description       "kong module"
long_description  IO.read(File.join(File.dirname(__FILE__), 'README.md'))
version           "1.0.1"

%w{ ubuntu fedora }.each do |os|
  supports os
end

%w{osops-utils}.each do |dep|
  depends dep
end
