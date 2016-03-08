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
import multiprocessing

from oslo_config import cfg
from oslo_log import log as logging

from vitrage.common.constants import EntityType
from vitrage.common.constants import VertexProperties as VProps
from vitrage.entity_graph.states.resource_state import NormalizedResourceState
from vitrage.evaluator.actions.action_executor import ActionExecutor
from vitrage.evaluator.actions.base import ActionMode
from vitrage.evaluator.actions.base import ActionType
from vitrage.evaluator.template import ActionSpecs
from vitrage.evaluator.template_fields import TemplateFields as TFields
from vitrage.service import load_plugin
from vitrage.tests.functional.entity_graph.base import \
    TestEntityGraphFunctionalBase

LOG = logging.getLogger(__name__)


class TestActionExecutor(TestEntityGraphFunctionalBase):

    @classmethod
    def setUpClass(cls):
        cls.conf = cfg.ConfigOpts()
        cls.conf.register_opts(cls.PROCESSOR_OPTS, group='entity_graph')
        cls.conf.register_opts(cls.PLUGINS_OPTS,
                               group='synchronizer_plugins')
        for plugin_name in cls.conf.synchronizer_plugins.plugin_type:
            load_plugin(cls.conf, plugin_name)

    def test_execute_update_vertex(self):

        # Test Setup
        processor = self._create_processor_with_graph(self.conf)

        vertex_attrs = {VProps.TYPE: EntityType.NOVA_HOST}
        host_vertices = processor.entity_graph.get_vertices(
            vertex_attr_filter=vertex_attrs)
        host_vertex_before = host_vertices[0]

        targets = {TFields.TARGET: host_vertex_before.vertex_id}
        props = {TFields.STATE: NormalizedResourceState.SUBOPTIMAL}
        action_spec = ActionSpecs(ActionType.SET_STATE, targets, props)

        event_queue = multiprocessing.Queue()
        action_executor = ActionExecutor(event_queue)

        # Test Action - do
        action_executor.execute(action_spec, ActionMode.DO)
        processor.process_event(event_queue.get())

        host_vertex_after = processor.entity_graph.get_vertex(
            host_vertex_before.vertex_id)

        # Test Assertions
        agg_state_before = host_vertex_before.get(VProps.AGGREGATED_STATE)
        self.assertTrue(agg_state_before != NormalizedResourceState.SUBOPTIMAL)
        self.assertFalse(VProps.VITRAGE_STATE in host_vertex_before.properties)

        agg_state_after = host_vertex_after.get(VProps.AGGREGATED_STATE)
        self.assertEqual(agg_state_after, NormalizedResourceState.SUBOPTIMAL)
        v_state_after = host_vertex_after.get(VProps.VITRAGE_STATE)
        self.assertEqual(v_state_after, NormalizedResourceState.SUBOPTIMAL)

        # Test Action - undo
        action_executor.execute(action_spec, ActionMode.UNDO)
        processor.process_event(event_queue.get())

        host_vertex_after_undo = processor.entity_graph.get_vertex(
            host_vertex_before.vertex_id)

        # Test Assertions
        agg_state_after_undo = host_vertex_before.get(VProps.AGGREGATED_STATE)
        self.assertEqual(agg_state_after_undo, agg_state_before)
        self.assertTrue(
            VProps.VITRAGE_STATE not in host_vertex_after_undo.properties)
