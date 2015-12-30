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

import vitrage.common.constants as cons
import vitrage.entity_graph.transformer.base as trans_base
from vitrage.entity_graph.transformer import nova_transformer as nt
from vitrage.tests.mocks import mock_syncronizer as mock_sync
from vitrage.tests.unit import base

LOG = logging.getLogger(__name__)


def get_nova_instance_transformer():
    return nt.InstanceTransformer()


def get_instance_entity_spec_list(config_file_path, number_of_instances):

    """Returns a list of nova instance specifications by

    given specific configuration file.
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

        expected_key_fields = [cons.VertexProperties.TYPE,
                               cons.VertexProperties.SUB_TYPE,
                               cons.VertexProperties.ID]
        observed_key_fields = transformer.key_fields()
        self.assert_list_equal(expected_key_fields, observed_key_fields)

    def test_transform(self):
        LOG.debug('Test actual transform action')

        transformer = get_nova_instance_transformer()

        spec_list = mock_sync.simple_instance_generators(
            host_num=1,
            vm_num=1,
            snapshot_events=10,
            update_events=5
        )
        instance_events = mock_sync.generate_random_events_list(spec_list)

        for event in instance_events:
            wrapper = transformer.transform(event)
            self._validate_vertex_props(wrapper.vertex, event)

            # Validate the neighbor list:
            # 1. Exactly one host neighbor and and
            # 3. Make sure the host neighbor is correct
            # 2. TODO(lhartal): validate volume neighbors
            host_neighbor_exist = False
            for neighbor in wrapper.neighbors:

                neighbor_subtype = neighbor.vertex[
                    cons.VertexProperties.SUB_TYPE
                ]

                if neighbor_subtype == nt.HOST_SUBTYPE:
                    self.assertEqual(False,
                                     host_neighbor_exist,
                                     'Instance has only one host neighbor')
                    self._validate_host_neighbor(neighbor, event)

    def _validate_vertex_props(self, vertex, event):

        self.assertEqual(9, vertex.properties.__len__())

        sync_mode = event['sync_mode']

        it = nt.InstanceTransformer
        expected_id = trans_base.extract_field_value(
            event,
            it.INSTANCE_ID[sync_mode]
        )
        observed_id = vertex[cons.VertexProperties.ID]
        self.assertEqual(expected_id, observed_id)

        self.assertEqual(cons.EntityTypes.RESOURCE,
                         vertex[cons.VertexProperties.TYPE])

        self.assertEqual(nt.INSTANCE_SUBTYPE,
                         vertex[cons.VertexProperties.SUB_TYPE])

        expected_project = trans_base.extract_field_value(
            event,
            it.PROJECT_ID[sync_mode]
        )
        observed_project = vertex[cons.VertexProperties.PROJECT]
        self.assertEqual(expected_project, observed_project)

        expected_state = trans_base.extract_field_value(
            event,
            it.INSTANCE_STATE[sync_mode]
        )
        observed_state = vertex[cons.VertexProperties.STATE]
        self.assertEqual(expected_state, observed_state)

        expected_timestamp = trans_base.extract_field_value(
            event,
            it.TIMESTAMP[sync_mode]
        )
        observed_timestamp = vertex[cons.VertexProperties.UPDATE_TIMESTAMP]
        self.assertEqual(expected_timestamp, observed_timestamp)

        expected_name = trans_base.extract_field_value(
            event,
            it.INSTANCE_NAME[sync_mode]
        )
        observed_name = vertex[cons.VertexProperties.NAME]
        self.assertEqual(expected_name, observed_name)

        is_placeholder = vertex[cons.VertexProperties.IS_PLACEHOLDER]
        self.assertEqual(False, is_placeholder)

        is_deleted = vertex[cons.VertexProperties.IS_DELETED]
        self.assertEqual(False, is_deleted)

    def _validate_host_neighbor(self, h_neighbor, event):

        it = nt.InstanceTransformer()
        sync_mode = event['sync_mode']
        host_name = trans_base.extract_field_value(
            event,
            it.HOST_NAME[sync_mode]
        )
        expected_neighbor = nt.HostTransformer.create_placeholder_vertex(
            host_name
        )
        self.assertEqual(expected_neighbor, h_neighbor.vertex)

        # Validate neighbor edge
        edge = h_neighbor.edge
        self.assertEqual(edge.source_id, h_neighbor.vertex.vertex_id)
        self.assertEqual(edge.target_id, it.extract_key(event))
        self.assertEqual(edge.label, cons.EdgeLabels.CONTAINS)

    def test_extract_key(self):
        LOG.debug('Test get key from nova instance transformer')

        transformer = get_nova_instance_transformer()

        spec_list = mock_sync.simple_instance_generators(
            host_num=1,
            vm_num=1,
            snapshot_events=1,
            update_events=0
        )
        instance_events = mock_sync.generate_random_events_list(spec_list)

        for event in instance_events:
            observed_key = transformer.extract_key(event)
            observed_key_fields = observed_key.split(
                trans_base.Transformer.KEY_SEPARATOR)

            self.assertEqual(cons.EntityTypes.RESOURCE, observed_key_fields[0])
            self.assertEqual(nt.INSTANCE_SUBTYPE, observed_key_fields[1])

            event_id = trans_base.extract_field_value(
                event,
                transformer.INSTANCE_ID[event['sync_mode']]
            )

            self.assertEqual(event_id, observed_key_fields[2])

            expected_key = trans_base.Transformer.KEY_SEPARATOR.join(
                [cons.EntityTypes.RESOURCE,
                 nt.INSTANCE_SUBTYPE,
                 event_id])
            self.assertEqual(expected_key, observed_key)

    def test_build_instance_key(self):
        LOG.debug('Test build instance key')

        expected_key = 'RESOURCE:nova.instance:456'
        observed_key = nt.InstanceTransformer.build_instance_key('456')

        self.assertEqual(expected_key, observed_key)

    def test_create_host_neighbor(self):
        LOG.debug('Test create host neighbor')

        vertex_id = 'RESOURCE:nova.instance:456'
        host_name = 'host123'
        neighbor = nt.InstanceTransformer.create_host_neighbor(vertex_id,
                                                               host_name)

        host_vertex_id = 'RESOURCE:nova.host:host123'
        self.assertEqual(host_vertex_id, neighbor.vertex.vertex_id)

        # test relation edge
        self.assertEqual(host_vertex_id, neighbor.edge.source_id)
        self.assertEqual(vertex_id, neighbor.edge.target_id)
        self.assertEqual(cons.EdgeLabels.CONTAINS, neighbor.edge.label)

    def test_create_placeholder_vertex(self):
        LOG.debug('Test create placeholder vertex')

        instance_id = '123456'
        vertex_id = nt.InstanceTransformer.build_instance_key(instance_id)
        p_vertex = nt.InstanceTransformer.create_placeholder_vertex(
            instance_id)

        self.assertEqual(vertex_id, p_vertex.vertex_id)
        self.assertEqual(5, p_vertex.properties.keys().__len__())
        self.assertEqual(instance_id,
                         p_vertex.get(cons.VertexProperties.ID))
        self.assertEqual(cons.EntityTypes.RESOURCE,
                         p_vertex.get(cons.VertexProperties.TYPE))
        self.assertEqual(nt.INSTANCE_SUBTYPE,
                         p_vertex.get(cons.VertexProperties.SUB_TYPE))
        self.assertEqual(True,
                         p_vertex.get(
                             cons.VertexProperties.IS_PLACEHOLDER))
