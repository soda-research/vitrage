# Copyright 2015 - Alcatel-Lucent
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

from oslo_log import log as logging

from vitrage.common.constants import VertexConstants as vertexCons
from vitrage.entity_graph.transformer import nova_transformer as nt
from vitrage.tests.mocks import mock_syncronizer as mock_sync
from vitrage.tests.unit import base

LOG = logging.getLogger(__name__)


def get_nova_instance_transformer():
    return nt.InstanceTransformer()


def get_instance_entity_spec_list(config_file_path, number_of_instances):

    """Returns a list of nova instance specifications by

    given specific configuration file.

    :rtype : list
    """
    return {
        'filename': config_file_path,
        '#instances': number_of_instances,
        'name': 'Instance generator'
    }


class NovaInstanceTransformerTest(base.BaseTest):

    def test_key_fields(self):
        LOG.debug('Test get key fields from nova instance transformer')
        transformer = get_nova_instance_transformer()

        expected_key_fields = [vertexCons.TYPE,
                               vertexCons.SUB_TYPE,
                               vertexCons.ID]
        observed_key_fields = transformer.key_fields()
        self.assert_list_equal(expected_key_fields, observed_key_fields)

    def test_extract_key(self):
        LOG.debug('Test get key from nova instance transformer')

        transformer = get_nova_instance_transformer()

        instance_specifications = [
            get_instance_entity_spec_list('mock_nova_inst_snapshot.txt', 1),
            get_instance_entity_spec_list('mock_nova_inst_update.txt', 1)
        ]

        spec_list = mock_sync.get_mock_generators(instance_specifications)
        instance_events = mock_sync.generate_random_events_list(spec_list)

        for event in instance_events:
            observed_key = transformer.extract_key(event)
            observed_key_fields = observed_key.split(nt.KEY_SEPARATOR)

            self.assertEqual(nt.ENTITY_TYPE, observed_key_fields[0])
            self.assertEqual(nt.INSTANCE_SUB_TYPE, observed_key_fields[1])

            event_id = event[transformer.ENTITY_ID_DICT[event['sync_mode']]]
            self.assertEqual(event_id, observed_key_fields[2])

            expected_key = nt.KEY_SEPARATOR.join(
                [nt.ENTITY_TYPE,
                 nt.INSTANCE_SUB_TYPE,
                 event_id])
            self.assertEqual(expected_key, observed_key)
