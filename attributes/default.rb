default["swift"]["auth_port"] = "443"                 # node_attribute
default["swift"]["auth_prefix"] = "/auth/"            # node_attribute
default["swift"]["auth_ssl"] = "yes"                  # node_attribute
default["swift"]["account"] = "system"                # node_attribute
default["swift"]["username"] = "root"                 # node_attribute
default["swift"]["password"] = "password"             # node_attribute

default["nova"]["network_label"] = "public"           # node_attribute

default["kong"]["branch"] = "master"                  # node_attribute

default["kong"]["swift_store_region"] = nil           # node_attribute
