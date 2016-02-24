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
import os
import re

from vitrage.common import file_utils

NAGIOS_HOST = 'nagios_host'


class NagiosConfig(object):

    NAGIOS = 'nagios'
    HOST = 'host'
    TYPE = 'type'
    NAME = 'name'

    def __init__(self, conf):
        self.mappings = []

        nagios_config_file = conf.synchronizer_plugins.nagios_config_file

        if nagios_config_file and os.path.isfile(nagios_config_file):
            nagios_config = file_utils.load_yaml_file(nagios_config_file)

            for config in nagios_config[self.NAGIOS]:
                self.mappings.append(NagiosHostMapping(config[NAGIOS_HOST],
                                                       config[self.TYPE],
                                                       config[self.NAME]))

    def get_vitrage_resource(self, nagios_host):
        """Get Vitrage resource type and name for the given nagios host name

        Go over the configuration mappings one by one, and return the resource
        by the first mapping that applies to nagios host name.

        :param nagios_host: nagios host name
        :return: Vitrage (resource type, resource name)
        """
        for mapping in self.mappings:
            mapped_resource = mapping.map(nagios_host)
            if mapped_resource:
                return mapped_resource

        return None


class NagiosHostMapping(object):
    NAGIOS_HOST_NAME = '${' + NAGIOS_HOST + '}'

    def __init__(self, nagios_host_regexp, resource_type, resource_name):
        self.nagios_host_regexp = re.compile(nagios_host_regexp)
        self.resource_type = resource_type
        self.resource_name = resource_name

    def map(self, nagios_host):
        """Check if the mapping applies to this service

        :param nagios_host: nagios host name
        :return: a tuple of (resource type, resource name)
        In case nagios_host_regexp is ${nagios_host}, return nagios host name
        as the resource name
        """

        if nagios_host and self.nagios_host_regexp.match(nagios_host):
            resource_name = \
                nagios_host if self.resource_name == self.NAGIOS_HOST_NAME \
                else self.resource_name
            return self.resource_type, resource_name
        else:
            return None
