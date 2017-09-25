# Copyright 2017 - Nokia
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

from unittest import TestCase

from vitrage.datasources.collectd.mapper import CollectdMapper


class TestCollectdMapper(TestCase):
    def setUp(self):
        super(TestCollectdMapper, self).setUp()
        self.mapping = {
            'host1': {'type': 'value_host1', 'name': 'value_host1'},
            'host_(.*)': {'type': 'value_host_2', 'name': 'value_host_2'},
            'host-(.*)': {'type': 'value_hostX', 'name': '${collectd_host}'},
            'hostabc': {'type': 'type_host_abc', 'name': 'name_host_abc'}
        }

        self.mapper = CollectdMapper(self.mapping)

    def test_match_resource_no_regex(self):
        self.should_match('host1', 'host1')

    def test_match_resource_with_regex_concrete_value(self):
        self.should_match('host_1', 'host_(.*)')

    def test_match_resource_with_regex_parameter_value(self):
        self.should_match_on_collectd_host_param('host-5', 'host-(.*)')

    def test_match_ambiguous_value(self):
        # the host name is "hosta.c",
        # dot is part of the host name NOT a wildcard
        # should not match "hostabc"
        self.should_not_match('hosta.c')

    def should_match(self, host, expected):
        value = self.mapper.find(host)
        resource_name = value['resource_name']
        resource_type = value['resource_type']
        expected_name = self.mapping[expected]['name']
        expected_type = self.mapping[expected]['type']

        self.assertEqual(resource_name, expected_name)
        self.assertEqual(resource_type, expected_type)

    def should_match_on_collectd_host_param(self, host, expected):
        value = self.mapper.find(host)
        resource_name = value['resource_name']
        resource_type = value['resource_type']
        expected_name = self.mapping[expected]['name']
        expected_type = self.mapping[expected]['type']

        self.assertEqual('${collectd_host}', expected_name)
        self.assertEqual(resource_name, host)
        self.assertEqual(resource_type, expected_type)

    def should_not_match(self, host):
        self.assertRaises(KeyError, self.mapper.find, host)
