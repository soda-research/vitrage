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

from oslo_config import cfg
from oslo_log import log as logging

from six.moves import queue
from vitrage.common.constants import VertexProperties as VProps
from vitrage.datasources.nova.host import NOVA_HOST_DATASOURCE
from vitrage.evaluator.scenario_evaluator import ScenarioEvaluator
from vitrage.evaluator.scenario_repository import ScenarioRepository
from vitrage.tests.functional.base import \
    TestFunctionalBase
from vitrage.tests.mocks import utils

LOG = logging.getLogger(__name__)


class TestScenarioEvaluator(TestFunctionalBase):

    EVALUATOR_OPTS = [
        cfg.StrOpt('templates_dir',
                   default=utils.get_resources_dir() +
                   '/templates/evaluator',
                   ),
        cfg.StrOpt('notifier_topic',
                   default='vitrage.evaluator',
                   ),
    ]

    # noinspection PyPep8Naming
    @classmethod
    def setUpClass(cls):
        cls.conf = cfg.ConfigOpts()
        cls.conf.register_opts(cls.PROCESSOR_OPTS, group='entity_graph')
        cls.conf.register_opts(cls.EVALUATOR_OPTS, group='evaluator')
        cls.conf.register_opts(cls.DATASOURCES_OPTS, group='datasources')
        TestScenarioEvaluator.load_datasources(cls.conf)
        cls.scenario_repository = ScenarioRepository(cls.conf)

    def test_deduced_state(self):

        # Test Setup
        processor = self._create_processor_with_graph(self.conf)
        event_queue = queue.Queue()
        ScenarioEvaluator(self.conf,
                          processor.entity_graph,
                          self.scenario_repository,
                          event_queue,
                          enabled=True)

        target_host = 'host-2'
        host_v = self._get_host_from_graph(target_host, processor.entity_graph)
        self.assertEqual('RUNNING', host_v[VProps.AGGREGATED_STATE],
                         'host should be RUNNING when starting')

        nagios_event = {'last_check': '2016-02-07 15:26:04',
                        'resource_name': target_host,
                        'resource_type': NOVA_HOST_DATASOURCE,
                        'service': 'Check_MK',
                        'status': 'CRITICAL',
                        'status_info': 'ok',
                        'sync_mode': 'snapshot',
                        'sync_type': 'nagios',
                        'sample_date': '2016-02-07 15:26:04'}
        processor.process_event(nagios_event)
        # The set_state action should have added an event to the queue, so
        processor.process_event(event_queue.get())

        host_v = self._get_host_from_graph(target_host, processor.entity_graph)
        self.assertEqual('SUBOPTIMAL', host_v[VProps.AGGREGATED_STATE],
                         'host should be SUBOPTIMAL after nagios alarm event')

        # next disable the alarm
        nagios_event['status'] = 'OK'
        processor.process_event(nagios_event)
        # The set_state action should have added an event to the queue, so
        processor.process_event(event_queue.get())

        host_v = self._get_host_from_graph(target_host, processor.entity_graph)
        self.assertEqual('RUNNING', host_v[VProps.AGGREGATED_STATE],
                         'host should be RUNNING when starting')

    @staticmethod
    def _get_host_from_graph(host_name, entity_graph):
        vertex_attrs = {VProps.TYPE: NOVA_HOST_DATASOURCE,
                        VProps.NAME: host_name}
        host_vertices = entity_graph.get_vertices(
            vertex_attr_filter=vertex_attrs)
        assert len(host_vertices) == 1, "incorrect number of vertices"
        return host_vertices[0]
