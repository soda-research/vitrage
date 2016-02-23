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
from vitrage.common import file_utils


class NagiosConfig(object):

    NAGIOS = 'nagios'
    NAGIOS_HOST = 'nagios_host'
    HOST = 'host'
    TYPE = 'type'
    NAME = 'name'

    def __init__(self, conf):
        self.rules = []

        nagios_config = file_utils.load_yaml_file(
            conf.synchronizer_plugins.nagios_config_file)

        for config in nagios_config[self.NAGIOS]:
            self.rules.append(NagiosHostMapping(config[self.NAGIOS_HOST],
                                                config[self.TYPE],
                                                config[self.NAME]))


class NagiosHostMapping(object):
    def __init__(self, nagios_host, type, name):
        self.nagios_host = nagios_host
        self.type = type
        self.name = name

    def applies(self, service):
        """Check if the rule applies to this service

        :param service:
        :return: true/false
        """

        # TODO(iafek) implement it
        pass
