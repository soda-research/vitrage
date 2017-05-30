# Copyright 2017 - ZTE Corporation
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

from vitrage.evaluator.equivalence_data import EquivalenceData
from vitrage.tests import base
from vitrage.tests.mocks import utils
from vitrage.utils import file as file_utils


class EquivalenceTemplateTest(base.BaseTest):

    BASIC_TEMPLATE = 'basic.yaml'

    def test_equivalence_template(self):

        equivalence_path = '%s/templates/general/equivalences/%s' % (
            utils.get_resources_dir(),
            self.BASIC_TEMPLATE)
        equivalence_definition = file_utils.load_yaml_file(equivalence_path,
                                                           True)
        equivalence_data = EquivalenceData(equivalence_definition)
        equivalences = equivalence_data.equivalences

        expected = [
            frozenset([
                frozenset([('category', 'ALARM'),
                           ('type', 'nagios'),
                           ('name', 'host_problem')]),
                frozenset([('category', 'ALARM'),
                           ('type', 'zabbix'),
                           ('name', 'host_fail')]),
                frozenset([('category', 'ALARM'),
                           ('type', 'vitrage'),
                           ('name', 'host_down')])
            ]),
        ]

        self.assertEqual(expected, equivalences)
