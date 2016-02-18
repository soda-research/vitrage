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

from datetime import timedelta
import time
import unittest

from oslo_config import cfg

from vitrage.common.constants import EdgeLabels
from vitrage.common.constants import EntityCategory
from vitrage.common.constants import EntityType
from vitrage.common.constants import VertexProperties as VProps
from vitrage.common.datetime_utils import utcnow
from vitrage.entity_graph.consistency.consistency_enforcer \
    import ConsistencyEnforcer
from vitrage.entity_graph.initialization_status import InitializationStatus
from vitrage.entity_graph.processor.processor import Processor
import vitrage.graph.utils as graph_utils
from vitrage.tests.unit.entity_graph import TestEntityGraphBase


class TestConsistencyBase(TestEntityGraphBase):

    OPTS = [
        cfg.IntOpt('consistency_interval',
                   default=1,
                   min=1),
        cfg.IntOpt('min_time_to_delete',
                   default=1,
                   min=1),
    ]

    def setUp(self):
        super(TestConsistencyBase, self).setUp()
        self.initialization_status = InitializationStatus()
        self.processor = Processor(self.initialization_status)
        self.conf = cfg.ConfigOpts()
        self.conf.register_opts(self.OPTS, group='consistency')
        self.consistency_enforcer = ConsistencyEnforcer(
            self.conf, self.processor.entity_graph, self.initialization_status)

    # TODO(Alexey): unskip this test when evaluator is ready
    @unittest.skip("testing skipping")
    def test_initializing_process(self):
        # Setup
        num_external_alarms = self.NUM_HOSTS - 2
        num_instances_per_host = 4
        self._create_processor_with_graph(processor=self.processor)
        self._add_alarms()
        self._set_end_messages()
        self.assertEqual(self._num_total_expected_vertices() +
                         num_external_alarms + self.NUM_INSTANCES,
                         len(self.processor.entity_graph.get_vertices()))

        # Action
        self.consistency_enforcer.initializing_process()

        # Test Assertions
        num_correct_alarms = num_external_alarms + \
            num_external_alarms * num_instances_per_host
        self.assertEqual(self._num_total_expected_vertices() +
                         num_correct_alarms,
                         len(self.processor.entity_graph.get_vertices()))

        instance_vertices = self.processor.entity_graph.get_vertices({
            VProps.CATEGORY: EntityCategory.ALARM
        })
        self.assertEqual(num_correct_alarms, len(instance_vertices))

        instance_vertices = self.processor.entity_graph.get_vertices({
            VProps.CATEGORY: EntityCategory.ALARM,
            VProps.TYPE: EntityType.VITRAGE
        })
        self.assertEqual(num_external_alarms * num_instances_per_host,
                         len(instance_vertices))

    def test_periodic_process(self):
        # Setup
        consistency_inteval = self.conf.consistency.consistency_interval
        self._periodic_process_setup_stage(consistency_inteval)

        # Action
        time.sleep(2 * consistency_inteval + 1)
        self.consistency_enforcer.periodic_process()

        # Test Assertions
        instance_vertices = self.processor.entity_graph.get_vertices({
            VProps.CATEGORY: EntityCategory.RESOURCE,
            VProps.TYPE: EntityType.NOVA_INSTANCE
        })
        self.assertEqual(self.NUM_INSTANCES - 6, len(instance_vertices))
        self.assertEqual(self._num_total_expected_vertices() - 6,
                         len(self.processor.entity_graph.get_vertices()))

    def _periodic_process_setup_stage(self, consistency_inteval):
        self._create_processor_with_graph(processor=self.processor)
        current_time = utcnow()

        # set all vertices to be have timestamp that consistency won't get
        self._update_timestamp(self.processor.entity_graph.get_vertices(),
                               current_time +
                               timedelta(seconds=1.5 * consistency_inteval))

        # check number of instances in graph
        instance_vertices = self.processor.entity_graph.get_vertices({
            VProps.CATEGORY: EntityCategory.RESOURCE,
            VProps.TYPE: EntityType.NOVA_INSTANCE
        })
        self.assertEqual(self.NUM_INSTANCES, len(instance_vertices))

        # set current timestamp of part of the instances
        self._update_timestamp(instance_vertices[0:3], current_time)

        # set part of the instances as deleted + update to current timestamp
        for i in range(3, 6):
            instance_vertices[i][VProps.IS_DELETED] = True
            self.processor.entity_graph.update_vertex(instance_vertices[i])

        # set part of the instances as deleted
        for i in range(6, 9):
            instance_vertices[i][VProps.IS_DELETED] = True
            instance_vertices[i][VProps.UPDATE_TIMESTAMP] = str(
                current_time + timedelta(seconds=2 * consistency_inteval + 1))
            self.processor.entity_graph.update_vertex(instance_vertices[i])

    def _set_end_messages(self):
        self.initialization_status.end_messages[EntityType.NOVA_ZONE] = True
        self.initialization_status.end_messages[EntityType.NOVA_HOST] = True
        self.initialization_status.end_messages[EntityType.NOVA_INSTANCE] = \
            True
        self.initialization_status.end_messages[EntityType.NAGIOS] = True
        self.initialization_status.status = \
            self.initialization_status.RECEIVED_ALL_END_MESSAGES

    def _add_alarms(self):
        # find hosts and instances
        host_vertices = self.processor.entity_graph.get_vertices({
            VProps.CATEGORY: EntityCategory.RESOURCE,
            VProps.TYPE: EntityType.NOVA_HOST
        })

        # add external alarms + deduced alarms
        for host_vertex in host_vertices:
            alarm_vertex = self._create_alarm('external_alarm',
                                              EntityType.NAGIOS)
            self.processor.entity_graph.add_vertex(alarm_vertex)
            edge = graph_utils.create_edge(alarm_vertex.vertex_id,
                                           host_vertex.vertex_id,
                                           EdgeLabels.ON)
            self.processor.entity_graph.add_edge(edge)
            self.run_evaluator(alarm_vertex)

        # remove external alarms
        self.processor.entity_graph.remove_vertex(host_vertices[2])
        self.processor.entity_graph.remove_vertex(host_vertices[3])

    def _update_timestamp(self, lst, timestamp):
        for vertex in lst:
            vertex[VProps.UPDATE_TIMESTAMP] = str(timestamp)
            self.processor.entity_graph.update_vertex(vertex)
