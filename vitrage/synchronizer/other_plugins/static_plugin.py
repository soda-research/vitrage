# Copyright 2016 - Nokia
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

from oslo_config import cfg

from vitrage.common import file_utils
from vitrage.synchronizer.base_plugin import BasePlugin


class StaticPlugin(BasePlugin):
    def __init__(self):
        super(StaticPlugin, self).__init__()
        self.cfg_opts = cfg.ConfigOpts()

    def get_all(self):
        return self.make_pickleable(self.get_instances(), None, ['manager'])

    def get_instances(self):
        static_entities = []
        static_plugin_configs = file_utils.load_yaml_files(
            self.cfg_opts.synchronizer.other_plugins.static_plugins_dir)

        for config in static_plugin_configs:
            for entity in config:
                static_entities.append(entity)

        return static_entities
