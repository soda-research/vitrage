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

from oslo_config import cfg

from vitrage.common.constants import EntityCategory
from vitrage.common.constants import EntityType
from vitrage.common.constants import VertexProperties as VProps
from vitrage.common.datetime_utils import utcnow
from vitrage.entity_graph.consistency.consistency_enforcer \
    import ConsistencyEnforcer
from vitrage.entity_graph.processor.processor import Processor
from vitrage.tests.unit.entity_graph import TestEntityGraph


class TestConsistency(TestEntityGraph):

    OPTS = [
        cfg.IntOpt('consistency_interval',
                   default=1,
                   min=1),
        cfg.IntOpt('min_time_to_delete',
                   default=1,
                   min=1),
    ]

    def setUp(self):
        super(TestConsistency, self).setUp()
        self.processor = Processor()
        self.conf = cfg.ConfigOpts()
        self.conf.register_opts(self.OPTS, group='consistency')
        self.consistency_enforcer = ConsistencyEnforcer(
            self.conf, self.processor.entity_graph)

    def test_periodic_process(self):
        self._create_processor_with_graph(processor=self.processor)
        current_time = utcnow()
        consistency_inteval = self.conf.consistency.consistency_interval

        # set all vertices to be have timestamp that consistency won't get
        self._update_timestamp(self.processor.entity_graph.get_vertices(),
                               current_time +
                               timedelta(seconds=1.5 * consistency_inteval))

        # check number of instances in graph
        instance_vertices = self.processor.entity_graph.get_vertices(
            {VProps.CATEGORY: EntityCategory.RESOURCE,
             VProps.TYPE: EntityType.NOVA_INSTANCE}
        )
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

        # sleep
        time.sleep(2 * consistency_inteval + 1)

        # run periodic check
        self.consistency_enforcer.periodic_process()

        # check number of instances
        instance_vertices = self.processor.entity_graph.get_vertices(
            {VProps.CATEGORY: EntityCategory.RESOURCE,
             VProps.TYPE: EntityType.NOVA_INSTANCE}
        )
        self.assertEqual(self.NUM_INSTANCES - 6, len(instance_vertices))
        self.assertEqual(self._num_total_expected_vertices() - 6,
                         len(self.processor.entity_graph.get_vertices()))

    def test_starting_process(self):
        pass

    def _update_timestamp(self, list, timestamp):
        for vertex in list:
            vertex[VProps.UPDATE_TIMESTAMP] = str(timestamp)
            self.processor.entity_graph.update_vertex(vertex)
