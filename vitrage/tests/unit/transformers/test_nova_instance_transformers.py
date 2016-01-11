# Copyright 2016 - Alcatel-Lucent
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

import datetime

from oslo_log import log as logging

import vitrage.common.constants as cons
from vitrage.entity_graph.transformer import base as transformer_base
from vitrage.entity_graph.transformer import nova_transformers
from vitrage.tests.mocks import mock_syncronizer as mock_sync
from vitrage.tests.unit import base


LOG = logging.getLogger(__name__)


class NovaInstanceTransformerTest(base.BaseTest):

    def test_create_placeholder_vertex(self):
        LOG.debug('Test create placeholder vertex')

        instance_id = 'Instance123'
        timestamp = datetime.datetime.utcnow()

        it = nova_transformers.InstanceTransformer()
        placeholder = it.create_placeholder_vertex(
            instance_id,
            timestamp
        )

        observed_id_values = placeholder.vertex_id.split(
            transformer_base.Transformer.KEY_SEPARATOR)
        expected_id_values = it.key_values(
            [instance_id]
        )
        self.assertEqual(observed_id_values, expected_id_values)

        observed_time = placeholder.get(
            cons.VertexProperties.UPDATE_TIMESTAMP
        )
        self.assertEqual(observed_time, timestamp)

        observed_subtype = placeholder.get(
            cons.VertexProperties.SUBTYPE
        )
        self.assertEqual(observed_subtype, nova_transformers.INSTANCE_SUBTYPE)

        observed_entity_id = placeholder.get(
            cons.VertexProperties.ID
        )
        self.assertEqual(observed_entity_id, instance_id)

        observed_type = placeholder.get(
            cons.VertexProperties.TYPE
        )
        self.assertEqual(observed_type, cons.EntityTypes.RESOURCE)

        is_placeholder = placeholder.get(
            cons.VertexProperties.IS_PLACEHOLDER
        )
        self.assertEqual(is_placeholder, True)

    def test_key_fields(self):
        LOG.debug('Test get key fields from nova instance transformer')

        expected_key_fields = [cons.VertexProperties.TYPE,
                               cons.VertexProperties.SUBTYPE,
                               cons.VertexProperties.ID]

        it = nova_transformers.InstanceTransformer()
        observed_key_fields = it.key_fields()
        self.assert_list_equal(expected_key_fields, observed_key_fields)

    def test_transform(self):
        LOG.debug('Test actual transform action')

        spec_list = mock_sync.simple_instance_generators(
            host_num=1,
            vm_num=1,
            snapshot_events=10,
            update_events=5
        )
        instance_events = mock_sync.generate_random_events_list(spec_list)

        for event in instance_events:
            wrapper = nova_transformers.InstanceTransformer().transform(event)
            self._validate_vertex_props(wrapper.vertex, event)

            # Validate the neighbor list:
            # 1. Exactly one host neighbor and and
            # 3. Make sure the host neighbor is correct
            # 2. TODO(lhartal): validate volume neighbors
            host_neighbor_exists = False
            for neighbor in wrapper.neighbors:

                neighbor_subtype = neighbor.vertex[
                    cons.VertexProperties.SUBTYPE
                ]

                if neighbor_subtype == nova_transformers.HOST_SUBTYPE:
                    self.assertEqual(False,
                                     host_neighbor_exists,
                                     'Instance has only one host neighbor')
                    self._validate_host_neighbor(neighbor, event)

        values = {
            'sync_mode': cons.SyncMode.INIT_SNAPSHOT,
        }
        self._check_event_action(cons.EventAction.CREATE,
                                 True,
                                 snap_vals=values)

        values['sync_mode'] = cons.SyncMode.SNAPSHOT
        self._check_event_action(cons.EventAction.UPDATE,
                                 True,
                                 snap_vals=values)

        values['sync_mode'] = cons.SyncMode.UPDATE
        self._check_event_action(cons.EventAction.UPDATE,
                                 False,
                                 update_vals=values)

        values['event_type'] = 'compute.instance.delete.end'
        self._check_event_action(cons.EventAction.DELETE,
                                 False,
                                 update_vals=values)

        values['event_type'] = 'compute.instance.create.start'
        self._check_event_action(cons.EventAction.CREATE,
                                 False,
                                 update_vals=values)

    def _validate_vertex_props(self, vertex, event):

        self.assertEqual(9, vertex.properties.__len__())

        sync_mode = event['sync_mode']

        extract_value = transformer_base.extract_field_value
        expected_id = extract_value(
            event,
            nova_transformers.InstanceTransformer.INSTANCE_ID[sync_mode]
        )
        observed_id = vertex[cons.VertexProperties.ID]
        self.assertEqual(expected_id, observed_id)

        self.assertEqual(
            cons.EntityTypes.RESOURCE,
            vertex[cons.VertexProperties.TYPE]
        )

        self.assertEqual(
            nova_transformers.INSTANCE_SUBTYPE,
            vertex[cons.VertexProperties.SUBTYPE]
        )

        expected_project = extract_value(
            event,
            nova_transformers.InstanceTransformer.PROJECT_ID[sync_mode]
        )
        observed_project = vertex[cons.VertexProperties.PROJECT]
        self.assertEqual(expected_project, observed_project)

        expected_state = extract_value(
            event,
            nova_transformers.InstanceTransformer.INSTANCE_STATE[sync_mode]
        )
        observed_state = vertex[cons.VertexProperties.STATE]
        self.assertEqual(expected_state, observed_state)

        expected_timestamp = extract_value(
            event,
            nova_transformers.InstanceTransformer.TIMESTAMP[sync_mode]
        )
        observed_timestamp = vertex[cons.VertexProperties.UPDATE_TIMESTAMP]
        self.assertEqual(expected_timestamp, observed_timestamp)

        expected_name = extract_value(
            event,
            nova_transformers.InstanceTransformer.INSTANCE_NAME[sync_mode]
        )
        observed_name = vertex[cons.VertexProperties.NAME]
        self.assertEqual(expected_name, observed_name)

        is_placeholder = vertex[cons.VertexProperties.IS_PLACEHOLDER]
        self.assertFalse(is_placeholder)

        is_deleted = vertex[cons.VertexProperties.IS_DELETED]
        self.assertFalse(is_deleted)

    def _validate_host_neighbor(self, h_neighbor, event):

        it = nova_transformers.InstanceTransformer()
        sync_mode = event['sync_mode']
        host_name = transformer_base.extract_field_value(
            event,
            it.HOST_NAME[sync_mode]
        )
        time = transformer_base.extract_field_value(
            event,
            it.TIMESTAMP[sync_mode]
        )

        ht = nova_transformers.HostTransformer()
        expected_neighbor = ht.create_placeholder_vertex(host_name, time)
        self.assertEqual(expected_neighbor, h_neighbor.vertex)

        # Validate neighbor edge
        edge = h_neighbor.edge
        self.assertEqual(edge.source_id, h_neighbor.vertex.vertex_id)
        self.assertEqual(edge.target_id, it.extract_key(event))
        self.assertEqual(edge.label, cons.EdgeLabels.CONTAINS)

    def _check_event_action(
            self,
            expected_action,
            is_snap,
            snap_vals=None,
            update_vals=None
    ):

        spec_list = mock_sync.simple_instance_generators(
            host_num=1,
            vm_num=1,
            snapshot_events=1 if is_snap else 0,
            update_events=0 if is_snap else 1,
            update_vals=update_vals,
            snap_vals=snap_vals
        )
        event = mock_sync.generate_random_events_list(spec_list)[0]

        wrapper = nova_transformers.InstanceTransformer().transform(event)

        self.assertEqual(expected_action, wrapper.action)

    def test_extract_key(self):
        LOG.debug('Test get key from nova instance transformer')

        spec_list = mock_sync.simple_instance_generators(
            host_num=1,
            vm_num=1,
            snapshot_events=1,
            update_events=0
        )
        instance_events = mock_sync.generate_random_events_list(spec_list)

        it = nova_transformers.InstanceTransformer()
        for event in instance_events:
            observed_key = it.extract_key(event)
            observed_key_fields = observed_key.split(
                transformer_base.Transformer.KEY_SEPARATOR)

            self.assertEqual(cons.EntityTypes.RESOURCE, observed_key_fields[0])
            self.assertEqual(
                nova_transformers.INSTANCE_SUBTYPE,
                observed_key_fields[1]
            )

            instance_id = transformer_base.extract_field_value(
                event,
                it.INSTANCE_ID[event['sync_mode']]
            )

            self.assertEqual(instance_id, observed_key_fields[2])

            key_values = it.key_values([instance_id])
            expected_key = transformer_base.build_key(key_values)

            self.assertEqual(expected_key, observed_key)

    def test_build_instance_key(self):
        LOG.debug('Test build instance key')

        instance_id = '456'
        expected_key = 'RESOURCE:nova.instance:%s' % instance_id

        it = nova_transformers.InstanceTransformer()
        key_fields = it.key_values([instance_id])
        observed_key = transformer_base.build_key(key_fields)

        self.assertEqual(expected_key, observed_key)

    def test_create_host_neighbor(self):
        LOG.debug('Test create host neighbor')

        vertex_id = 'RESOURCE:nova.instance:456'
        host_name = 'host123'
        time = datetime.datetime.utcnow()
        it = nova_transformers.InstanceTransformer()
        neighbor = it.create_host_neighbor(vertex_id, host_name, time)

        host_vertex_id = 'RESOURCE:nova.host:host123'
        self.assertEqual(host_vertex_id, neighbor.vertex.vertex_id)
        self.assertEqual(
            time,
            neighbor.vertex.get(cons.VertexProperties.UPDATE_TIMESTAMP)
        )

        # test relation edge
        self.assertEqual(host_vertex_id, neighbor.edge.source_id)
        self.assertEqual(vertex_id, neighbor.edge.target_id)
        self.assertEqual(cons.EdgeLabels.CONTAINS, neighbor.edge.label)
