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

from six.moves import queue

from oslo_config import cfg

from vitrage.common.constants import DatasourceAction
from vitrage.common.constants import DatasourceProperties as DSProps
from vitrage.common.constants import EdgeProperties as EProps
from vitrage.common.constants import EntityCategory
from vitrage.common.constants import VertexProperties as VProps
from vitrage.datasources.cinder.volume.transformer import \
    CINDER_VOLUME_DATASOURCE
from vitrage.datasources.nagios.properties import NagiosProperties
from vitrage.datasources.nagios.properties import NagiosTestStatus
from vitrage.datasources.neutron.network import NEUTRON_NETWORK_DATASOURCE
from vitrage.datasources.neutron.port import NEUTRON_PORT_DATASOURCE
from vitrage.datasources.nova.host import NOVA_HOST_DATASOURCE
from vitrage.datasources.nova.instance import NOVA_INSTANCE_DATASOURCE
from vitrage.datasources.nova.zone import NOVA_ZONE_DATASOURCE
from vitrage.evaluator.scenario_evaluator import ScenarioEvaluator
from vitrage.evaluator.scenario_repository import ScenarioRepository
from vitrage.graph import create_edge
from vitrage.tests.functional.base import \
    TestFunctionalBase
import vitrage.tests.mocks.mock_driver as mock_driver
from vitrage.tests.mocks import utils
from vitrage.utils.datetime import utcnow

_TARGET_HOST = 'host-2'
_TARGET_ZONE = 'zone-1'
_NAGIOS_TEST_INFO = {'resource_name': _TARGET_HOST,
                     'resource_id': _TARGET_HOST,
                     DSProps.DATASOURCE_ACTION: DatasourceAction.SNAPSHOT}


class TestScenarioEvaluator(TestFunctionalBase):

    EVALUATOR_OPTS = [
        cfg.StrOpt('templates_dir',
                   default=utils.get_resources_dir() +
                   '/templates/evaluator',
                   ),
        cfg.StrOpt('equivalences_dir',
                   default=utils.get_resources_dir() +
                   '/equivalences',
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

        event_queue, processor, evaluator = self._init_system()

        host_v = self._get_entity_from_graph(NOVA_HOST_DATASOURCE,
                                             _TARGET_HOST,
                                             _TARGET_HOST,
                                             processor.entity_graph)
        self.assertEqual('AVAILABLE', host_v[VProps.AGGREGATED_STATE],
                         'host should be AVAILABLE when starting')

        # generate nagios alarm to trigger template scenario
        test_vals = {'status': 'WARNING', 'service': 'cause_suboptimal_state'}
        test_vals.update(_NAGIOS_TEST_INFO)
        generator = mock_driver.simple_nagios_alarm_generators(1, 1, test_vals)
        warning_test = mock_driver.generate_random_events_list(generator)[0]

        host_v = self.get_host_after_event(event_queue, warning_test,
                                           processor, _TARGET_HOST)
        self.assertEqual('SUBOPTIMAL', host_v[VProps.AGGREGATED_STATE],
                         'host should be SUBOPTIMAL with warning alarm')

        # next disable the alarm
        warning_test['status'] = 'OK'
        host_v = self.get_host_after_event(event_queue, warning_test,
                                           processor, _TARGET_HOST)
        self.assertEqual('AVAILABLE', host_v[VProps.AGGREGATED_STATE],
                         'host should be AVAILABLE when alarm disabled')

    def test_overlapping_deduced_state_1(self):

        event_queue, processor, evaluator = self._init_system()

        host_v = self._get_entity_from_graph(NOVA_HOST_DATASOURCE,
                                             _TARGET_HOST,
                                             _TARGET_HOST,
                                             processor.entity_graph)
        self.assertEqual('AVAILABLE', host_v[VProps.AGGREGATED_STATE],
                         'host should be AVAILABLE when starting')

        # generate nagios alarm to trigger
        test_vals = {'status': 'WARNING', 'service': 'cause_suboptimal_state'}
        test_vals.update(_NAGIOS_TEST_INFO)
        generator = mock_driver.simple_nagios_alarm_generators(1, 1, test_vals)
        warning_test = mock_driver.generate_random_events_list(generator)[0]

        host_v = self.get_host_after_event(event_queue, warning_test,
                                           processor, _TARGET_HOST)
        self.assertEqual('SUBOPTIMAL', host_v[VProps.AGGREGATED_STATE],
                         'host should be SUBOPTIMAL with warning alarm')

        # generate CRITICAL nagios alarm to trigger
        test_vals = {'status': 'CRITICAL', 'service': 'cause_error_state'}
        test_vals.update(_NAGIOS_TEST_INFO)
        generator = mock_driver.simple_nagios_alarm_generators(1, 1, test_vals)
        critical_test = mock_driver.generate_random_events_list(generator)[0]

        host_v = self.get_host_after_event(event_queue, critical_test,
                                           processor, _TARGET_HOST)
        self.assertEqual('ERROR', host_v[VProps.AGGREGATED_STATE],
                         'host should be ERROR with critical alarm')

        # next disable the critical alarm
        critical_test['status'] = 'OK'
        host_v = self.get_host_after_event(event_queue, critical_test,
                                           processor, _TARGET_HOST)
        self.assertEqual('SUBOPTIMAL', host_v[VProps.AGGREGATED_STATE],
                         'host should be SUBOPTIMAL with only warning alarm')

        # next disable the alarm
        warning_test['status'] = 'OK'
        host_v = self.get_host_after_event(event_queue, warning_test,
                                           processor, _TARGET_HOST)
        self.assertEqual('AVAILABLE', host_v[VProps.AGGREGATED_STATE],
                         'host should be AVAILABLE after alarm disabled')

    def test_overlapping_deduced_state_2(self):

        event_queue, processor, evaluator = self._init_system()

        host_v = self._get_entity_from_graph(NOVA_HOST_DATASOURCE,
                                             _TARGET_HOST,
                                             _TARGET_HOST,
                                             processor.entity_graph)
        self.assertEqual('AVAILABLE', host_v[VProps.AGGREGATED_STATE],
                         'host should be AVAILABLE when starting')

        # generate CRITICAL nagios alarm to trigger
        test_vals = {'status': 'CRITICAL', 'service': 'cause_error_state'}
        test_vals.update(_NAGIOS_TEST_INFO)
        generator = mock_driver.simple_nagios_alarm_generators(1, 1, test_vals)
        critical_test = mock_driver.generate_random_events_list(generator)[0]

        host_v = self.get_host_after_event(event_queue, critical_test,
                                           processor, _TARGET_HOST)
        self.assertEqual('ERROR', host_v[VProps.AGGREGATED_STATE],
                         'host should be ERROR with critical alarm')

        # generate WARNING nagios alarm to trigger
        test_vals = {'status': 'WARNING', 'service': 'cause_suboptimal_state'}
        test_vals.update(_NAGIOS_TEST_INFO)
        generator = mock_driver.simple_nagios_alarm_generators(1, 1, test_vals)
        warning_test = mock_driver.generate_random_events_list(generator)[0]

        host_v = self.get_host_after_event(event_queue, warning_test,
                                           processor, _TARGET_HOST)
        self.assertEqual('ERROR', host_v[VProps.AGGREGATED_STATE],
                         'host should be ERROR with critical alarm')

        # next disable the critical alarm
        critical_test['status'] = 'OK'
        host_v = self.get_host_after_event(event_queue, critical_test,
                                           processor, _TARGET_HOST)
        self.assertEqual('SUBOPTIMAL', host_v[VProps.AGGREGATED_STATE],
                         'host should be SUBOPTIMAL with only warning alarm')

    def test_deduced_alarm(self):

        event_queue, processor, evaluator = self._init_system()

        host_v = self._get_entity_from_graph(NOVA_HOST_DATASOURCE,
                                             _TARGET_HOST,
                                             _TARGET_HOST,
                                             processor.entity_graph)
        self.assertEqual('AVAILABLE', host_v[VProps.AGGREGATED_STATE],
                         'host should be AVAILABLE when starting')

        # generate CRITICAL nagios alarm to trigger
        test_vals = {'status': 'WARNING',
                     'service': 'cause_warning_deduced_alarm'}
        test_vals.update(_NAGIOS_TEST_INFO)
        generator = mock_driver.simple_nagios_alarm_generators(1, 1, test_vals)
        warning_test = mock_driver.generate_random_events_list(generator)[0]

        host_v = self.get_host_after_event(event_queue, warning_test,
                                           processor, _TARGET_HOST)
        alarms = \
            self._get_deduced_alarms_on_host(host_v, processor.entity_graph)
        self.assertEqual(1, len(alarms))
        self.assertEqual('WARNING', alarms[0]['severity'])
        causes = self._get_alarm_causes(alarms[0], processor.entity_graph)
        self.assertEqual(1, len(causes))

        # next disable the alarm
        warning_test['status'] = 'OK'
        host_v = self.get_host_after_event(event_queue, warning_test,
                                           processor, _TARGET_HOST)
        alarms = \
            self._get_deduced_alarms_on_host(host_v, processor.entity_graph)
        self.assertEqual(0, len(alarms))

        # recreate the nagios alarm
        warning_test['status'] = 'WARNING'
        warning_test[DSProps.SAMPLE_DATE] = str(utcnow())
        host_v = self.get_host_after_event(event_queue, warning_test,
                                           processor, _TARGET_HOST)
        alarms = \
            self._get_deduced_alarms_on_host(host_v, processor.entity_graph)
        self.assertEqual(1, len(alarms))
        self.assertEqual('WARNING', alarms[0]['severity'])
        causes = self._get_alarm_causes(alarms[0], processor.entity_graph)
        self.assertEqual(1, len(causes))

        # next disable the alarm
        warning_test['status'] = 'OK'
        host_v = self.get_host_after_event(event_queue, warning_test,
                                           processor, _TARGET_HOST)
        alarms = \
            self._get_deduced_alarms_on_host(host_v, processor.entity_graph)
        self.assertEqual(0, len(alarms))

    def test_overlapping_deduced_alarm_1(self):

        event_queue, processor, evaluator = self._init_system()

        # generate WARNING nagios alarm
        vals = {'status': 'WARNING', 'service': 'cause_warning_deduced_alarm'}
        vals.update(_NAGIOS_TEST_INFO)
        generator = mock_driver.simple_nagios_alarm_generators(1, 1, vals)
        warning_test = mock_driver.generate_random_events_list(generator)[0]

        host_v = self.get_host_after_event(event_queue, warning_test,
                                           processor, _TARGET_HOST)
        alarms = \
            self._get_deduced_alarms_on_host(host_v, processor.entity_graph)
        self.assertEqual(1, len(alarms))
        self.assertEqual('WARNING', alarms[0]['severity'])
        causes = self._get_alarm_causes(alarms[0], processor.entity_graph)
        self.assertEqual(1, len(causes))

        # generate CRITICAL nagios alarm to trigger
        vals = {'status': 'CRITICAL',
                'service': 'cause_critical_deduced_alarm'}
        vals.update(_NAGIOS_TEST_INFO)
        generator = mock_driver.simple_nagios_alarm_generators(1, 1, vals)
        critical_test = mock_driver.generate_random_events_list(generator)[0]

        host_v = self.get_host_after_event(event_queue, critical_test,
                                           processor, _TARGET_HOST)
        alarms = \
            self._get_deduced_alarms_on_host(host_v, processor.entity_graph)
        self.assertEqual(1, len(alarms))
        self.assertEqual('CRITICAL', alarms[0]['severity'])
        causes = self._get_alarm_causes(alarms[0], processor.entity_graph)
        self.assertEqual(2, len(causes))

        # remove WARNING nagios alarm, leaving only CRITICAL one
        warning_test['status'] = 'OK'
        host_v = self.get_host_after_event(event_queue, warning_test,
                                           processor, _TARGET_HOST)
        alarms = \
            self._get_deduced_alarms_on_host(host_v, processor.entity_graph)
        self.assertEqual(1, len(alarms))
        self.assertEqual('CRITICAL', alarms[0]['severity'])
        causes = self._get_alarm_causes(alarms[0], processor.entity_graph)
        self.assertEqual(1, len(causes))

        # next disable the alarm
        critical_test['status'] = 'OK'
        host_v = self.get_host_after_event(event_queue, critical_test,
                                           processor, _TARGET_HOST)
        alarms = \
            self._get_deduced_alarms_on_host(host_v, processor.entity_graph)
        self.assertEqual(0, len(alarms))

    def test_overlapping_deduced_alarm_2(self):

        event_queue, processor, evaluator = self._init_system()

        # generate CRITICAL nagios alarm to trigger
        test_vals = {'status': 'CRITICAL',
                     'service': 'cause_critical_deduced_alarm'}
        test_vals.update(_NAGIOS_TEST_INFO)
        generator = mock_driver.simple_nagios_alarm_generators(1, 1, test_vals)
        critical_test = mock_driver.generate_random_events_list(generator)[0]

        host_v = self.get_host_after_event(event_queue, critical_test,
                                           processor, _TARGET_HOST)
        alarms = \
            self._get_deduced_alarms_on_host(host_v, processor.entity_graph)
        self.assertEqual(1, len(alarms))
        self.assertEqual('CRITICAL', alarms[0]['severity'])

        # generate WARNING nagios alarm to trigger
        test_vals = {'status': 'WARNING',
                     'service': 'cause_warning_deduced_alarm'}
        test_vals.update(_NAGIOS_TEST_INFO)
        generator = mock_driver.simple_nagios_alarm_generators(1, 1, test_vals)
        warning_test = mock_driver.generate_random_events_list(generator)[0]

        host_v = self.get_host_after_event(event_queue, warning_test,
                                           processor, _TARGET_HOST)
        alarms = \
            self._get_deduced_alarms_on_host(host_v, processor.entity_graph)
        self.assertEqual(1, len(alarms))
        self.assertEqual('CRITICAL', alarms[0]['severity'])

        # remove CRITICAL nagios alarm, leaving only WARNING one
        critical_test['status'] = 'OK'
        host_v = self.get_host_after_event(event_queue, critical_test,
                                           processor, _TARGET_HOST)
        alarms = \
            self._get_deduced_alarms_on_host(host_v, processor.entity_graph)
        self.assertEqual(1, len(alarms))
        self.assertEqual('WARNING', alarms[0]['severity'])

    def test_simple_not_operator_deduced_alarm(self):
        """Handles a simple not operator use case

        We have created the following template: if there is a neutron.port that
        doesn't have a nagios alarm of type PORT_PROBLEM on it, then raise a
        deduced alarm on the port called simple_port_deduced_alarm.
        The test has 5 steps in it:
        1. create neutron.network and neutron.port and check that the
           simple_port_deduced_alarm is raised on the neutron.port because it
           doesn't have a nagios alarm on it.
        2. create a nagios alarm called PORT_PROBLEM on the port and check
           that the alarm simple_port_deduced_alarm doesn't appear on the
           neutron.port.
        3. delete the edge between nagios alarm called PORT_PROBLEM and the
           neutron.port. check that the alarm simple_port_deduced_alarm appear
           on the neutron.port.
        4. create the edge between nagios alarm called PORT_PROBLEM and the
           neutron.port.check that the alarm simple_port_deduced_alarm doesn't
           appear on the neutron.port.
        5. delete the nagios alarm called PORT_PROBLEM from the port, and
           check that the alarm alarm simple_port_deduced_alarm appear on the
           neutron.port.
        """

        event_queue, processor, evaluator = self._init_system()
        entity_graph = processor.entity_graph

        # constants
        num_orig_vertices = entity_graph.num_vertices()
        num_orig_edges = entity_graph.num_edges()
        num_added_vertices = 2
        num_added_edges = 2
        num_deduced_vertices = 1
        num_deduced_edges = 1
        num_nagios_alarm_vertices = 1
        num_nagios_alarm_edges = 1

        # find instances
        query = {
            VProps.CATEGORY: 'RESOURCE',
            VProps.TYPE: NOVA_INSTANCE_DATASOURCE
        }
        instance_ver = entity_graph.get_vertices(vertex_attr_filter=query)[0]

        # update network
        network_event = {
            'tenant_id': 'admin',
            'name': 'net-0',
            'updated_at': '2015-12-01T12:46:41Z',
            'status': 'active',
            'id': '12345',
            'vitrage_entity_type': 'neutron.network',
            'vitrage_datasource_action': 'snapshot',
            'vitrage_sample_date': '2015-12-01T12:46:41Z',
        }

        # update port
        port_event = {
            'tenant_id': 'admin',
            'name': 'port-0',
            'updated_at': '2015-12-01T12:46:41Z',
            'status': 'active',
            'id': '54321',
            'vitrage_entity_type': 'neutron.port',
            'vitrage_datasource_action': 'snapshot',
            'vitrage_sample_date': '2015-12-01T12:46:41Z',
            'network_id': '12345',
            'device_id': instance_ver.get(VProps.ID),
            'device_owner': 'compute:nova',
            'fixed_ips': {}
        }

        processor.process_event(network_event)
        processor.process_event(port_event)
        port_vertex = entity_graph.get_vertices(
            vertex_attr_filter={VProps.TYPE: NEUTRON_PORT_DATASOURCE})[0]
        while not event_queue.empty():
            processor.process_event(event_queue.get())

        # test asserts
        query = {VProps.CATEGORY: EntityCategory.ALARM}
        port_neighbors = entity_graph.neighbors(port_vertex.vertex_id,
                                                vertex_attr_filter=query)
        self.assertEqual(num_orig_vertices + num_added_vertices +
                         num_deduced_vertices, entity_graph.num_vertices())
        self.assertEqual(num_orig_edges + num_added_edges + num_deduced_edges,
                         entity_graph.num_edges())
        self.assertEqual(1, len(port_neighbors))
        self.assertEqual(port_neighbors[0][VProps.CATEGORY],
                         EntityCategory.ALARM)
        self.assertEqual(port_neighbors[0][VProps.TYPE], 'vitrage')
        self.assertEqual(port_neighbors[0][VProps.NAME],
                         'simple_port_deduced_alarm')

        # Add PORT_PROBLEM alarm
        test_vals = {'status': 'WARNING',
                     'service': 'PORT_PROBLEM',
                     'name': 'PORT_PROBLEM',
                     DSProps.DATASOURCE_ACTION: DatasourceAction.SNAPSHOT,
                     VProps.RESOURCE_ID: port_vertex.get(VProps.ID),
                     'resource_name': port_vertex.get(VProps.ID),
                     'resource_type': NEUTRON_PORT_DATASOURCE}
        generator = mock_driver.simple_nagios_alarm_generators(1, 1, test_vals)
        nagios_event = mock_driver.generate_random_events_list(generator)[0]

        processor.process_event(nagios_event)
        while not event_queue.empty():
            processor.process_event(event_queue.get())

        # test asserts
        self.assertEqual(num_orig_vertices + num_added_vertices +
                         num_deduced_vertices + num_nagios_alarm_vertices,
                         entity_graph.num_vertices())
        self.assertEqual(num_orig_edges + num_added_edges + num_deduced_edges +
                         num_nagios_alarm_edges, entity_graph.num_edges())

        query = {VProps.CATEGORY: EntityCategory.ALARM, VProps.TYPE: 'vitrage'}
        port_neighbors = entity_graph.neighbors(port_vertex.vertex_id,
                                                vertex_attr_filter=query)
        self.assertEqual(1, len(port_neighbors))
        self.assertEqual(port_neighbors[0][VProps.CATEGORY],
                         EntityCategory.ALARM)
        self.assertEqual(port_neighbors[0][VProps.TYPE], 'vitrage')
        self.assertEqual(port_neighbors[0][VProps.NAME],
                         'simple_port_deduced_alarm')
        self.assertEqual(port_neighbors[0][VProps.IS_DELETED], True)

        query = {VProps.CATEGORY: EntityCategory.ALARM, VProps.TYPE: 'nagios'}
        port_neighbors = entity_graph.neighbors(port_vertex.vertex_id,
                                                vertex_attr_filter=query)
        self.assertEqual(port_neighbors[0][VProps.CATEGORY],
                         EntityCategory.ALARM)
        self.assertEqual(port_neighbors[0][VProps.TYPE], 'nagios')
        self.assertEqual(port_neighbors[0][VProps.NAME], 'PORT_PROBLEM')
        self.assertEqual(port_neighbors[0][VProps.IS_DELETED], False)
        self.assertEqual(port_neighbors[0][VProps.IS_PLACEHOLDER], False)

        # ###################   STEP 3   ###################
        # disable connection between port and alarm
        query = {VProps.CATEGORY: 'ALARM', VProps.TYPE: 'nagios'}
        nagios_vertex = \
            processor.entity_graph.get_vertices(vertex_attr_filter=query)[0]
        nagios_edge = [e for e in processor.entity_graph.get_edges(
            nagios_vertex.vertex_id)][0]
        nagios_edge[EProps.IS_DELETED] = True
        processor.entity_graph.update_edge(nagios_edge)
        while not event_queue.empty():
            processor.process_event(event_queue.get())

        # test asserts
        self.assertEqual(num_orig_vertices + num_added_vertices +
                         num_deduced_vertices + num_nagios_alarm_vertices +
                         # This is due to keeping alarm history :
                         # new alarm doesn't update same deleted alarm.
                         # Instead, it keeps the old one and creates a new one
                         1,
                         entity_graph.num_vertices())
        self.assertEqual(num_orig_edges + num_added_edges + num_deduced_edges +
                         num_nagios_alarm_edges + 1, entity_graph.num_edges())

        query = {VProps.CATEGORY: EntityCategory.ALARM, VProps.TYPE: 'vitrage',
                 VProps.IS_DELETED: True}
        is_deleted = True
        for counter in range(0, 1):
            port_neighbors = entity_graph.neighbors(port_vertex.vertex_id,
                                                    vertex_attr_filter=query)
            self.assertEqual(1, len(port_neighbors))
            self.assertEqual(port_neighbors[0][VProps.CATEGORY],
                             EntityCategory.ALARM)
            self.assertEqual(port_neighbors[0][VProps.TYPE], 'vitrage')
            self.assertEqual(port_neighbors[0][VProps.NAME],
                             'simple_port_deduced_alarm')
            self.assertEqual(port_neighbors[0][VProps.IS_DELETED], is_deleted)
            query = {VProps.CATEGORY: EntityCategory.ALARM,
                     VProps.TYPE: 'vitrage', VProps.IS_DELETED: False}
            is_deleted = False

        query = {VProps.CATEGORY: EntityCategory.ALARM, VProps.TYPE: 'nagios'}
        port_neighbors = entity_graph.neighbors(port_vertex.vertex_id,
                                                vertex_attr_filter=query)
        self.assertEqual(port_neighbors[0][VProps.CATEGORY],
                         EntityCategory.ALARM)
        self.assertEqual(port_neighbors[0][VProps.TYPE], 'nagios')
        self.assertEqual(port_neighbors[0][VProps.NAME], 'PORT_PROBLEM')
        self.assertEqual(port_neighbors[0][VProps.IS_DELETED], False)

        # ###################   STEP 4   ###################
        # enable connection between port and alarm
        query = {VProps.CATEGORY: 'ALARM', VProps.TYPE: 'nagios'}
        nagios_vertex = \
            processor.entity_graph.get_vertices(vertex_attr_filter=query)[0]
        nagios_edge = [e for e in processor.entity_graph.get_edges(
            nagios_vertex.vertex_id)][0]
        nagios_edge[EProps.IS_DELETED] = False
        processor.entity_graph.update_edge(nagios_edge)
        while not event_queue.empty():
            processor.process_event(event_queue.get())

        # test asserts
        self.assertEqual(num_orig_vertices + num_added_vertices +
                         num_deduced_vertices + num_nagios_alarm_vertices +
                         # This is due to keeping alarm history :
                         # new alarm doesn't update same deleted alarm.
                         # Instead, it keeps the old one and creates a new one
                         1,
                         entity_graph.num_vertices())
        self.assertEqual(num_orig_edges + num_added_edges + num_deduced_edges +
                         num_nagios_alarm_edges + 1, entity_graph.num_edges())

        query = {VProps.CATEGORY: EntityCategory.ALARM, VProps.TYPE: 'vitrage',
                 VProps.IS_DELETED: True}
        is_deleted = True
        for counter in range(0, 1):
            port_neighbors = entity_graph.neighbors(port_vertex.vertex_id,
                                                    vertex_attr_filter=query)
            self.assertEqual(2, len(port_neighbors))
            for in_counter in range(0, 1):
                self.assertEqual(port_neighbors[in_counter][VProps.CATEGORY],
                                 EntityCategory.ALARM)
                self.assertEqual(port_neighbors[in_counter][VProps.TYPE],
                                 'vitrage')
                self.assertEqual(port_neighbors[in_counter][VProps.NAME],
                                 'simple_port_deduced_alarm')
                self.assertEqual(
                    port_neighbors[in_counter][VProps.IS_DELETED], is_deleted)

            query = {VProps.CATEGORY: EntityCategory.ALARM,
                     VProps.TYPE: 'vitrage', VProps.IS_DELETED: False}
            is_deleted = False

        query = {VProps.CATEGORY: EntityCategory.ALARM, VProps.TYPE: 'nagios'}
        port_neighbors = entity_graph.neighbors(port_vertex.vertex_id,
                                                vertex_attr_filter=query)
        self.assertEqual(port_neighbors[0][VProps.CATEGORY],
                         EntityCategory.ALARM)
        self.assertEqual(port_neighbors[0][VProps.TYPE], 'nagios')
        self.assertEqual(port_neighbors[0][VProps.NAME], 'PORT_PROBLEM')
        self.assertEqual(port_neighbors[0][VProps.IS_DELETED], False)

        # ###################   STEP 5   ###################
        # disable PORT_PROBLEM alarm
        nagios_event[NagiosProperties.STATUS] = NagiosTestStatus.OK
        processor.process_event(nagios_event)
        while not event_queue.empty():
            processor.process_event(event_queue.get())

        # test asserts
        self.assertEqual(num_orig_vertices + num_added_vertices +
                         num_deduced_vertices + num_nagios_alarm_vertices +
                         # This is due to keeping alarm history :
                         # new alarm doesn't update same deleted alarm.
                         # Instead, it keeps the old one and creates a new one
                         # Since this is the second test, there are already two
                         # alarms of this type
                         2,
                         entity_graph.num_vertices())
        self.assertEqual(num_orig_edges + num_added_edges + num_deduced_edges +
                         num_nagios_alarm_edges + 2, entity_graph.num_edges())

        query = {VProps.CATEGORY: EntityCategory.ALARM,
                 VProps.TYPE: 'vitrage', VProps.IS_DELETED: True}
        is_deleted = True
        for counter in range(0, 1):
            port_neighbors = entity_graph.neighbors(port_vertex.vertex_id,
                                                    vertex_attr_filter=query)
            self.assertEqual(2, len(port_neighbors))
            for in_counter in range(0, 1):
                self.assertEqual(port_neighbors[in_counter][VProps.CATEGORY],
                                 EntityCategory.ALARM)
                self.assertEqual(port_neighbors[in_counter][VProps.TYPE],
                                 'vitrage')
                self.assertEqual(port_neighbors[in_counter][VProps.NAME],
                                 'simple_port_deduced_alarm')
                self.assertEqual(
                    port_neighbors[in_counter][VProps.IS_DELETED], is_deleted)

            query = {VProps.CATEGORY: EntityCategory.ALARM,
                     VProps.TYPE: 'vitrage', VProps.IS_DELETED: False}
            is_deleted = False

        query = {VProps.CATEGORY: EntityCategory.ALARM, VProps.TYPE: 'nagios'}
        port_neighbors = entity_graph.neighbors(port_vertex.vertex_id,
                                                vertex_attr_filter=query)
        self.assertEqual(port_neighbors[0][VProps.CATEGORY],
                         EntityCategory.ALARM)
        self.assertEqual(port_neighbors[0][VProps.TYPE], 'nagios')
        self.assertEqual(port_neighbors[0][VProps.NAME], 'PORT_PROBLEM')
        self.assertEqual(port_neighbors[0][VProps.IS_DELETED], True)

    def test_complex_not_operator_deduced_alarm(self):
        """Handles a complex not operator use case

        We have created the following template: if there is a openstack.cluster
        that has a nova.zone which is connected to a neutron.network and also
        there is no nagios alarm of type CLUSTER_PROBLEM on the cluster and no
        nagios alarm of type NETWORK_PROBLEM on the neutron.network, then raise
        a deduced alarm on the nova.zone called complex_zone_deduced_alarm.
        The test has 3 steps in it:
        1. create a neutron.network and connect it to a zone, and check that
           the complex_zone_deduced_alarm is raised on the nova.zone because it
           doesn't have nagios alarms the openstack.cluster and on the
           neutron.network.
        2. create a nagios alarm called NETWORK_PROBLEM on the network and
           check that the alarm complex_zone_deduced_alarm doesn't appear on
           the nova.zone.
        3. delete the nagios alarm called NETWORK_PROBLEM from the port, and
           check that the alarm alarm complex_zone_deduced_alarm appear on the
           nova.zone.
        """

        event_queue, processor, evaluator = self._init_system()
        entity_graph = processor.entity_graph

        # constants
        num_orig_vertices = entity_graph.num_vertices()
        num_orig_edges = entity_graph.num_edges()
        num_added_vertices = 2
        num_added_edges = 3
        num_deduced_vertices = 1
        num_deduced_edges = 1
        num_network_alarm_vertices = 1
        num_network_alarm_edges = 1

        # ###################   STEP 1   ###################
        # update zone
        generator = mock_driver.simple_zone_generators(1, 1, snapshot_events=1)
        zone_event = mock_driver.generate_random_events_list(generator)[0]
        zone_event['zoneName'] = 'zone-7'

        # update network
        network_event = {
            'tenant_id': 'admin',
            'name': 'net-0',
            'updated_at': '2015-12-01T12:46:41Z',
            'status': 'active',
            'id': '12345',
            'vitrage_entity_type': 'neutron.network',
            'vitrage_datasource_action': 'snapshot',
            'vitrage_sample_date': '2015-12-01T12:46:41Z',
        }

        # process events
        processor.process_event(zone_event)
        query = {VProps.TYPE: NOVA_ZONE_DATASOURCE, VProps.ID: 'zone-7'}
        zone_vertex = entity_graph.get_vertices(vertex_attr_filter=query)[0]
        processor.process_event(network_event)
        query = {VProps.TYPE: NEUTRON_NETWORK_DATASOURCE}
        network_vertex = entity_graph.get_vertices(vertex_attr_filter=query)[0]

        # add edge between network and zone
        edge = create_edge(network_vertex.vertex_id, zone_vertex.vertex_id,
                           'attached')
        entity_graph.add_edge(edge)

        while not event_queue.empty():
            processor.process_event(event_queue.get())

        # test asserts
        query = {VProps.CATEGORY: EntityCategory.ALARM}
        zone_neighbors = entity_graph.neighbors(zone_vertex.vertex_id,
                                                vertex_attr_filter=query)
        self.assertEqual(num_orig_vertices + num_added_vertices +
                         num_deduced_vertices, entity_graph.num_vertices())
        self.assertEqual(num_orig_edges + num_added_edges + num_deduced_edges,
                         entity_graph.num_edges())
        self.assertEqual(1, len(zone_neighbors))
        self.assertEqual(zone_neighbors[0][VProps.CATEGORY],
                         EntityCategory.ALARM)
        self.assertEqual(zone_neighbors[0][VProps.TYPE], 'vitrage')
        self.assertEqual(zone_neighbors[0][VProps.NAME],
                         'complex_zone_deduced_alarm')

        # ###################   STEP 2   ###################
        # Add NETWORK_PROBLEM alarm
        test_vals = {'status': 'WARNING',
                     'service': 'NETWORK_PROBLEM',
                     'name': 'NETWORK_PROBLEM',
                     DSProps.DATASOURCE_ACTION: DatasourceAction.SNAPSHOT,
                     VProps.RESOURCE_ID: network_vertex[VProps.ID],
                     'resource_name': network_vertex[VProps.ID],
                     'resource_type': NEUTRON_NETWORK_DATASOURCE}
        generator = mock_driver.simple_nagios_alarm_generators(1, 1, test_vals)
        nagios_event = mock_driver.generate_random_events_list(generator)[0]

        processor.process_event(nagios_event)
        while not event_queue.empty():
            processor.process_event(event_queue.get())

        self.assertEqual(num_orig_vertices + num_added_vertices +
                         num_deduced_vertices + num_network_alarm_vertices,
                         entity_graph.num_vertices())
        self.assertEqual(num_orig_edges + num_added_edges + num_deduced_edges +
                         num_network_alarm_edges, entity_graph.num_edges())

        query = {VProps.CATEGORY: EntityCategory.ALARM}
        network_neighbors = entity_graph.neighbors(network_vertex.vertex_id,
                                                   vertex_attr_filter=query)
        self.assertEqual(1, len(network_neighbors))
        self.assertEqual(network_neighbors[0][VProps.CATEGORY],
                         EntityCategory.ALARM)
        self.assertEqual(network_neighbors[0][VProps.TYPE], 'nagios')
        self.assertEqual(network_neighbors[0][VProps.NAME], 'NETWORK_PROBLEM')
        self.assertEqual(network_neighbors[0][VProps.IS_DELETED], False)
        self.assertEqual(network_neighbors[0][VProps.IS_PLACEHOLDER], False)

        zone_neighbors = entity_graph.neighbors(zone_vertex.vertex_id,
                                                vertex_attr_filter=query)
        self.assertEqual(1, len(zone_neighbors))
        self.assertEqual(zone_neighbors[0][VProps.CATEGORY],
                         EntityCategory.ALARM)
        self.assertEqual(zone_neighbors[0][VProps.TYPE], 'vitrage')
        self.assertEqual(zone_neighbors[0][VProps.NAME],
                         'complex_zone_deduced_alarm')
        self.assertEqual(zone_neighbors[0][VProps.IS_DELETED], True)

        # ###################   STEP 3   ###################
        # delete NETWORK_PROBLEM alarm
        nagios_event[NagiosProperties.STATUS] = NagiosTestStatus.OK
        processor.process_event(nagios_event)
        while not event_queue.empty():
            processor.process_event(event_queue.get())

        self.assertEqual(num_orig_vertices + num_added_vertices +
                         num_deduced_vertices + num_network_alarm_vertices +
                         # This is due to keeping alarm history :
                         # new alarm doesn't update same deleted alarm.
                         # Instead, it keeps the old one and creates a new one
                         1,
                         entity_graph.num_vertices())
        self.assertEqual(num_orig_edges + num_added_edges + num_deduced_edges +
                         num_network_alarm_edges + 1, entity_graph.num_edges())

        query = {VProps.CATEGORY: EntityCategory.ALARM}
        network_neighbors = entity_graph.neighbors(network_vertex.vertex_id,
                                                   vertex_attr_filter=query)
        self.assertEqual(1, len(network_neighbors))
        self.assertEqual(network_neighbors[0][VProps.CATEGORY],
                         EntityCategory.ALARM)
        self.assertEqual(network_neighbors[0][VProps.TYPE], 'nagios')
        self.assertEqual(network_neighbors[0][VProps.NAME], 'NETWORK_PROBLEM')
        self.assertEqual(network_neighbors[0][VProps.IS_DELETED], True)

        query = {VProps.CATEGORY: EntityCategory.ALARM,
                 VProps.IS_DELETED: True}
        is_deleted = True
        # Alarm History is saved. We are testing the deleted alarm and
        # then we are testing the live alarm
        for counter in range(0, 1):
            zone_neighbors = entity_graph.neighbors(zone_vertex.vertex_id,
                                                    vertex_attr_filter=query)
            self.assertEqual(1, len(zone_neighbors))
            self.assertEqual(zone_neighbors[0][VProps.CATEGORY],
                             EntityCategory.ALARM)
            self.assertEqual(zone_neighbors[0][VProps.TYPE], 'vitrage')
            self.assertEqual(zone_neighbors[0][VProps.NAME],
                             'complex_zone_deduced_alarm')
            self.assertEqual(zone_neighbors[0][VProps.IS_DELETED], is_deleted)

            query = {VProps.CATEGORY: EntityCategory.ALARM,
                     VProps.IS_DELETED: False}
            is_deleted = False

    def test_ha(self):
        event_queue, processor, evaluator = self._init_system()
        entity_graph = processor.entity_graph

        # find host
        query = {
            VProps.CATEGORY: 'RESOURCE',
            VProps.TYPE: NOVA_HOST_DATASOURCE
        }
        hosts = entity_graph.get_vertices(vertex_attr_filter=query)

        # find instances on host
        query = {
            VProps.CATEGORY: 'RESOURCE',
            VProps.TYPE: NOVA_INSTANCE_DATASOURCE
        }
        instances = entity_graph.neighbors(hosts[0].vertex_id,
                                           vertex_attr_filter=query)
        entity_graph.remove_vertex(instances[2])
        entity_graph.remove_vertex(instances[3])

        # constants
        num_orig_vertices = entity_graph.num_vertices()
        num_orig_edges = entity_graph.num_edges()

        # ###################   STEP 1   ###################
        # Add cinder volume 1
        generator = mock_driver.simple_volume_generators(volume_num=1,
                                                         instance_num=1,
                                                         snapshot_events=1)
        volume_event1 = mock_driver.generate_random_events_list(generator)[0]
        volume_event1['display_name'] = 'volume-1'
        volume_event1[VProps.ID] = 'volume-1'
        volume_event1['attachments'][0]['server_id'] = instances[0][VProps.ID]

        processor.process_event(volume_event1)
        while not event_queue.empty():
            processor.process_event(event_queue.get())

        # test asserts
        num_volumes = 1
        num_deduced_alarms = 1
        self.assertEqual(num_orig_vertices + num_volumes + num_deduced_alarms,
                         entity_graph.num_vertices())
        self.assertEqual(num_orig_edges + num_volumes + num_deduced_alarms,
                         entity_graph.num_edges())

        query = {VProps.CATEGORY: EntityCategory.RESOURCE,
                 VProps.TYPE: CINDER_VOLUME_DATASOURCE}
        instance_neighbors = entity_graph.neighbors(instances[0].vertex_id,
                                                    vertex_attr_filter=query)
        self.assertEqual(1, len(instance_neighbors))
        self.assertEqual(instance_neighbors[0][VProps.CATEGORY],
                         EntityCategory.RESOURCE)
        self.assertEqual(instance_neighbors[0][VProps.TYPE],
                         CINDER_VOLUME_DATASOURCE)
        self.assertEqual(instance_neighbors[0][VProps.NAME], 'volume-1')
        self.assertEqual(instance_neighbors[0][VProps.IS_DELETED], False)
        self.assertEqual(instance_neighbors[0][VProps.IS_PLACEHOLDER], False)

        query = {VProps.CATEGORY: EntityCategory.ALARM, VProps.TYPE: 'vitrage'}
        host_neighbors = entity_graph.neighbors(hosts[0].vertex_id,
                                                vertex_attr_filter=query)
        self.assertEqual(host_neighbors[0][VProps.CATEGORY],
                         EntityCategory.ALARM)
        self.assertEqual(host_neighbors[0][VProps.TYPE], 'vitrage')
        self.assertEqual(host_neighbors[0][VProps.NAME],
                         'ha_warning_deduced_alarm')
        self.assertEqual(host_neighbors[0][VProps.IS_DELETED], False)
        self.assertEqual(host_neighbors[0][VProps.IS_PLACEHOLDER], False)

        # ###################   STEP 2   ###################
        # Add cinder volume 2
        generator = mock_driver.simple_volume_generators(volume_num=1,
                                                         instance_num=1,
                                                         snapshot_events=1)
        volume_event2 = mock_driver.generate_random_events_list(generator)[0]
        volume_event2['display_name'] = 'volume-2'
        volume_event2[VProps.ID] = 'volume-2'
        volume_event2['attachments'][0]['server_id'] = instances[1][VProps.ID]

        processor.process_event(volume_event2)
        while not event_queue.empty():
            processor.process_event(event_queue.get())

        # test asserts
        num_volumes = 2
        num_deduced_alarms = 2
        self.assertEqual(num_orig_vertices + num_volumes + num_deduced_alarms,
                         entity_graph.num_vertices())
        self.assertEqual(num_orig_edges + num_volumes + num_deduced_alarms,
                         entity_graph.num_edges())

        # check instance neighbors
        query = {VProps.CATEGORY: EntityCategory.RESOURCE,
                 VProps.TYPE: CINDER_VOLUME_DATASOURCE}
        instance_neighbors = entity_graph.neighbors(instances[1].vertex_id,
                                                    vertex_attr_filter=query)
        self.assertEqual(1, len(instance_neighbors))
        self.assertEqual(instance_neighbors[0][VProps.CATEGORY],
                         EntityCategory.RESOURCE)
        self.assertEqual(instance_neighbors[0][VProps.TYPE],
                         CINDER_VOLUME_DATASOURCE)
        self.assertEqual(instance_neighbors[0][VProps.NAME], 'volume-2')
        self.assertEqual(instance_neighbors[0][VProps.IS_DELETED], False)
        self.assertEqual(instance_neighbors[0][VProps.IS_PLACEHOLDER], False)

        # check ha_error_deduced_alarm
        query = {VProps.CATEGORY: EntityCategory.ALARM,
                 VProps.TYPE: 'vitrage',
                 VProps.NAME: 'ha_error_deduced_alarm'}
        host_neighbors = entity_graph.neighbors(hosts[0].vertex_id,
                                                vertex_attr_filter=query)
        self.assertEqual(1, len(host_neighbors))
        self.assertEqual(host_neighbors[0][VProps.CATEGORY],
                         EntityCategory.ALARM)
        self.assertEqual(host_neighbors[0][VProps.TYPE], 'vitrage')
        self.assertEqual(host_neighbors[0][VProps.NAME],
                         'ha_error_deduced_alarm')
        self.assertEqual(host_neighbors[0][VProps.IS_DELETED], False)
        self.assertEqual(host_neighbors[0][VProps.IS_PLACEHOLDER], False)

        # check ha_warning_deduced_alarm
        query = {VProps.CATEGORY: EntityCategory.ALARM,
                 VProps.TYPE: 'vitrage',
                 VProps.NAME: 'ha_warning_deduced_alarm'}
        host_neighbors = entity_graph.neighbors(hosts[0].vertex_id,
                                                vertex_attr_filter=query)
        self.assertEqual(1, len(host_neighbors))
        self.assertEqual(host_neighbors[0][VProps.CATEGORY],
                         EntityCategory.ALARM)
        self.assertEqual(host_neighbors[0][VProps.TYPE], 'vitrage')
        self.assertEqual(host_neighbors[0][VProps.NAME],
                         'ha_warning_deduced_alarm')
        self.assertEqual(host_neighbors[0][VProps.IS_DELETED], True)
        self.assertEqual(host_neighbors[0][VProps.IS_PLACEHOLDER], False)

        # ###################   STEP 3   ###################
        #  Remove Cinder Volume 2
        volume_event2[DSProps.DATASOURCE_ACTION] = DatasourceAction.UPDATE
        volume_event2[DSProps.EVENT_TYPE] = 'volume.detach.start'
        volume_event2['volume_id'] = volume_event2['id']
        volume_event2['volume_attachment'] = volume_event2['attachments']
        volume_event2['volume_attachment'][0]['instance_uuid'] = \
            volume_event2['attachments'][0]['server_id']
        processor.process_event(volume_event2)
        while not event_queue.empty():
            processor.process_event(event_queue.get())

        # test asserts
        self.assertEqual(num_orig_vertices + num_volumes + num_deduced_alarms +
                         # This is due to keeping alarm history :
                         # new alarm doesn't update same deleted alarm.
                         # Instead, it keeps the old one and creates a new one
                         1,
                         entity_graph.num_vertices())
        self.assertEqual(num_orig_edges + num_volumes + num_deduced_alarms + 1,
                         entity_graph.num_edges())

        query = {VProps.CATEGORY: EntityCategory.RESOURCE,
                 VProps.TYPE: CINDER_VOLUME_DATASOURCE}
        instance_neighbors = entity_graph.neighbors(instances[1].vertex_id,
                                                    vertex_attr_filter=query)
        self.assertEqual(1, len(instance_neighbors))
        self.assertEqual(instance_neighbors[0][VProps.CATEGORY],
                         EntityCategory.RESOURCE)
        self.assertEqual(instance_neighbors[0][VProps.TYPE],
                         CINDER_VOLUME_DATASOURCE)
        self.assertEqual(instance_neighbors[0][VProps.NAME], 'volume-2')
        self.assertEqual(instance_neighbors[0][VProps.IS_DELETED], False)
        self.assertEqual(instance_neighbors[0][VProps.IS_PLACEHOLDER], False)

        # check ha_error_deduced_alarm
        query = {VProps.CATEGORY: EntityCategory.ALARM,
                 VProps.TYPE: 'vitrage',
                 VProps.NAME: 'ha_error_deduced_alarm'}
        host_neighbors = entity_graph.neighbors(hosts[0].vertex_id,
                                                vertex_attr_filter=query)
        self.assertEqual(1, len(host_neighbors))
        self.assertEqual(host_neighbors[0][VProps.CATEGORY],
                         EntityCategory.ALARM)
        self.assertEqual(host_neighbors[0][VProps.TYPE], 'vitrage')
        self.assertEqual(host_neighbors[0][VProps.NAME],
                         'ha_error_deduced_alarm')
        self.assertEqual(host_neighbors[0][VProps.IS_DELETED], True)
        self.assertEqual(host_neighbors[0][VProps.IS_PLACEHOLDER], False)

        # check new ha_warning_deduced_alarm
        query = {VProps.CATEGORY: EntityCategory.ALARM,
                 VProps.TYPE: 'vitrage',
                 VProps.NAME: 'ha_warning_deduced_alarm',
                 VProps.IS_DELETED: False}
        host_neighbors = entity_graph.neighbors(hosts[0].vertex_id,
                                                vertex_attr_filter=query)
        self.assertEqual(1, len(host_neighbors))
        self.assertEqual(host_neighbors[0][VProps.CATEGORY],
                         EntityCategory.ALARM)
        self.assertEqual(host_neighbors[0][VProps.TYPE], 'vitrage')
        self.assertEqual(host_neighbors[0][VProps.NAME],
                         'ha_warning_deduced_alarm')
        self.assertEqual(host_neighbors[0][VProps.IS_DELETED], False)
        self.assertEqual(host_neighbors[0][VProps.IS_PLACEHOLDER], False)

        # check old deleted ha_warning_deduced_alarm
        query = {VProps.CATEGORY: EntityCategory.ALARM,
                 VProps.TYPE: 'vitrage',
                 VProps.NAME: 'ha_warning_deduced_alarm',
                 VProps.IS_DELETED: True}
        host_neighbors = entity_graph.neighbors(hosts[0].vertex_id,
                                                vertex_attr_filter=query)
        self.assertEqual(1, len(host_neighbors))
        self.assertEqual(host_neighbors[0][VProps.CATEGORY],
                         EntityCategory.ALARM)
        self.assertEqual(host_neighbors[0][VProps.TYPE], 'vitrage')
        self.assertEqual(host_neighbors[0][VProps.NAME],
                         'ha_warning_deduced_alarm')
        self.assertEqual(host_neighbors[0][VProps.IS_DELETED], True)
        self.assertEqual(host_neighbors[0][VProps.IS_PLACEHOLDER], False)

        # ###################   STEP 4   ###################
        #  Remove Cinder Volume 1
        volume_event1[DSProps.DATASOURCE_ACTION] = DatasourceAction.UPDATE
        volume_event1[DSProps.EVENT_TYPE] = 'volume.detach.start'
        volume_event1['volume_id'] = volume_event1['id']
        volume_event1['volume_attachment'] = volume_event1['attachments']
        volume_event1['volume_attachment'][0]['instance_uuid'] = \
            volume_event1['attachments'][0]['server_id']
        processor.process_event(volume_event1)
        while not event_queue.empty():
            processor.process_event(event_queue.get())

        # test asserts
        self.assertEqual(num_orig_vertices + num_volumes + num_deduced_alarms +
                         # This is due to keeping alarm history :
                         # new alarm doesn't update same deleted alarm.
                         # Instead, it keeps the old one and creates a new one
                         1,
                         entity_graph.num_vertices())
        self.assertEqual(num_orig_edges + num_volumes + num_deduced_alarms + 1,
                         entity_graph.num_edges())

        query = {VProps.CATEGORY: EntityCategory.RESOURCE,
                 VProps.TYPE: CINDER_VOLUME_DATASOURCE}
        instance_neighbors = entity_graph.neighbors(instances[0].vertex_id,
                                                    vertex_attr_filter=query)
        self.assertEqual(1, len(instance_neighbors))
        self.assertEqual(instance_neighbors[0][VProps.CATEGORY],
                         EntityCategory.RESOURCE)
        self.assertEqual(instance_neighbors[0][VProps.TYPE],
                         CINDER_VOLUME_DATASOURCE)
        self.assertEqual(instance_neighbors[0][VProps.NAME], 'volume-1')
        self.assertEqual(instance_neighbors[0][VProps.IS_DELETED], False)
        self.assertEqual(instance_neighbors[0][VProps.IS_PLACEHOLDER], False)

        # check ha_error_deduced_alarm
        query = {VProps.CATEGORY: EntityCategory.ALARM,
                 VProps.TYPE: 'vitrage',
                 VProps.NAME: 'ha_error_deduced_alarm'}
        host_neighbors = entity_graph.neighbors(hosts[0].vertex_id,
                                                vertex_attr_filter=query)
        self.assertEqual(1, len(host_neighbors))
        self.assertEqual(host_neighbors[0][VProps.CATEGORY],
                         EntityCategory.ALARM)
        self.assertEqual(host_neighbors[0][VProps.TYPE], 'vitrage')
        self.assertEqual(host_neighbors[0][VProps.NAME],
                         'ha_error_deduced_alarm')
        self.assertEqual(host_neighbors[0][VProps.IS_DELETED], True)
        self.assertEqual(host_neighbors[0][VProps.IS_PLACEHOLDER], False)

        # check old ha_warning_deduced_alarm
        query = {VProps.CATEGORY: EntityCategory.ALARM,
                 VProps.TYPE: 'vitrage',
                 VProps.NAME: 'ha_warning_deduced_alarm'}
        host_neighbors = entity_graph.neighbors(hosts[0].vertex_id,
                                                vertex_attr_filter=query)
        self.assertEqual(2, len(host_neighbors))

        self.assertEqual(host_neighbors[0][VProps.CATEGORY],
                         EntityCategory.ALARM)
        self.assertEqual(host_neighbors[0][VProps.TYPE], 'vitrage')
        self.assertEqual(host_neighbors[0][VProps.NAME],
                         'ha_warning_deduced_alarm')
        self.assertEqual(host_neighbors[0][VProps.IS_DELETED], True)
        self.assertEqual(host_neighbors[0][VProps.IS_PLACEHOLDER], False)

        self.assertEqual(host_neighbors[1][VProps.CATEGORY],
                         EntityCategory.ALARM)
        self.assertEqual(host_neighbors[1][VProps.TYPE], 'vitrage')
        self.assertEqual(host_neighbors[1][VProps.NAME],
                         'ha_warning_deduced_alarm')
        self.assertEqual(host_neighbors[1][VProps.IS_DELETED], True)
        self.assertEqual(host_neighbors[1][VProps.IS_PLACEHOLDER], False)

    def test_simple_or_operator_deduced_alarm(self):
        """Handles a simple not operator use case

        We have created the following template:
        alarm1 or alarm2 cause alarm3

        """

        event_queue, processor, evaluator = self._init_system()

        host_v = self._get_entity_from_graph(NOVA_HOST_DATASOURCE,
                                             _TARGET_HOST,
                                             _TARGET_HOST,
                                             processor.entity_graph)
        self.assertEqual('AVAILABLE', host_v[VProps.AGGREGATED_STATE],
                         'host should be AVAILABLE when starting')

        # generate nagios alarm1 to trigger, raise alarm3
        test_vals = {'status': 'WARNING',
                     'service': 'alarm1'}
        test_vals.update(_NAGIOS_TEST_INFO)
        generator = mock_driver.simple_nagios_alarm_generators(1, 1, test_vals)
        alarm1_test = mock_driver.generate_random_events_list(generator)[0]

        host_v = self.get_host_after_event(event_queue, alarm1_test,
                                           processor, _TARGET_HOST)
        alarms = self._get_alarms_on_host(host_v, processor.entity_graph)
        self.assertEqual(2, len(alarms))

        # generate nagios alarm2 to trigger
        test_vals = {'status': 'WARNING',
                     'service': 'alarm2'}
        test_vals.update(_NAGIOS_TEST_INFO)
        generator = mock_driver.simple_nagios_alarm_generators(1, 1, test_vals)
        alarm2_test = mock_driver.generate_random_events_list(generator)[0]

        host_v = self.get_host_after_event(event_queue, alarm2_test,
                                           processor, _TARGET_HOST)
        alarms = self._get_alarms_on_host(host_v, processor.entity_graph)
        self.assertEqual(3, len(alarms))

        # disable alarm1, alarm3 is not deleted
        alarm1_test['status'] = 'OK'
        host_v = self.get_host_after_event(event_queue, alarm1_test,
                                           processor, _TARGET_HOST)
        alarms = self._get_alarms_on_host(host_v, processor.entity_graph)
        self.assertEqual(2, len(alarms))

        # disable alarm2, alarm3 is deleted
        alarm2_test['status'] = 'OK'
        alarm2_test[DSProps.SAMPLE_DATE] = str(utcnow())
        host_v = self.get_host_after_event(event_queue, alarm2_test,
                                           processor, _TARGET_HOST)
        alarms = self._get_alarms_on_host(host_v, processor.entity_graph)
        self.assertEqual(0, len(alarms))

    def test_both_and_or_operator_for_tracker(self):
        """(alarm_a or alarm_b) and alarm_c use case

        We have created the following template:
        (alarm_a or alarm_b) and alarm_c cause alarm_d

        1. alarm_a is reported
        2. alarm_b is reported
        3. alarm_c is reported  --> alarm_d is raised
        4. alarm_b is removed   --> alarm_d should not be removed
        5. alarm_a is removed   --> alarm_d should be removed

        """

        event_queue, processor, evaluator = self._init_system()
        entity_graph = processor.entity_graph

        # constants
        num_orig_vertices = entity_graph.num_vertices()
        num_orig_edges = entity_graph.num_edges()

        host_v = self._get_entity_from_graph(NOVA_HOST_DATASOURCE,
                                             _TARGET_HOST,
                                             _TARGET_HOST,
                                             entity_graph)
        self.assertEqual('AVAILABLE', host_v[VProps.AGGREGATED_STATE],
                         'host should be AVAILABLE when starting')

        # generate nagios alarm_a to trigger
        test_vals = {'status': 'WARNING',
                     'service': 'alarm_a'}
        test_vals.update(_NAGIOS_TEST_INFO)
        generator = mock_driver.simple_nagios_alarm_generators(1, 1, test_vals)
        alarm_a_test = mock_driver.generate_random_events_list(generator)[0]

        host_v = self.get_host_after_event(event_queue, alarm_a_test,
                                           processor, _TARGET_HOST)
        alarms = self._get_alarms_on_host(host_v, entity_graph)
        self.assertEqual(1, len(alarms))
        self.assertEqual(num_orig_vertices + 1, entity_graph.num_vertices())
        self.assertEqual(num_orig_edges + 1, entity_graph.num_edges())

        # generate nagios alarm_b to trigger
        test_vals = {'status': 'WARNING',
                     'service': 'alarm_b'}
        test_vals.update(_NAGIOS_TEST_INFO)
        generator = mock_driver.simple_nagios_alarm_generators(1, 1, test_vals)
        alarm_b_test = mock_driver.generate_random_events_list(generator)[0]

        host_v = self.get_host_after_event(event_queue, alarm_b_test,
                                           processor, _TARGET_HOST)
        alarms = self._get_alarms_on_host(host_v, entity_graph)
        self.assertEqual(2, len(alarms))
        self.assertEqual(num_orig_vertices + 2, entity_graph.num_vertices())
        self.assertEqual(num_orig_edges + 2, entity_graph.num_edges())

        # generate nagios alarm_c to trigger, alarm_d is raised
        test_vals = {'status': 'WARNING',
                     'service': 'alarm_c'}
        test_vals.update(_NAGIOS_TEST_INFO)
        generator = mock_driver.simple_nagios_alarm_generators(1, 1, test_vals)
        alarm_c_test = mock_driver.generate_random_events_list(generator)[0]

        host_v = self.get_host_after_event(event_queue, alarm_c_test,
                                           processor, _TARGET_HOST)
        alarms = self._get_alarms_on_host(host_v, entity_graph)
        self.assertEqual(4, len(alarms))
        self.assertEqual(num_orig_vertices + 4, entity_graph.num_vertices())
        self.assertEqual(num_orig_edges + 4, entity_graph.num_edges())

        # remove nagios alarm_b, alarm_d should not be removed
        test_vals = {'status': 'OK',
                     'service': 'alarm_b'}
        test_vals.update(_NAGIOS_TEST_INFO)
        generator = mock_driver.simple_nagios_alarm_generators(1, 1, test_vals)
        alarm_b_ok = mock_driver.generate_random_events_list(generator)[0]

        host_v = self.get_host_after_event(event_queue, alarm_b_ok,
                                           processor, _TARGET_HOST)
        alarms = self._get_alarms_on_host(host_v, entity_graph)
        self.assertEqual(3, len(alarms))

        query = {VProps.CATEGORY: EntityCategory.ALARM,
                 VProps.IS_DELETED: True}
        deleted_alarms = entity_graph.neighbors(host_v.vertex_id,
                                                vertex_attr_filter=query)
        self.assertEqual(num_orig_vertices + len(deleted_alarms) + 3,
                         entity_graph.num_vertices())

        query = {VProps.IS_DELETED: True}
        deleted_edges = entity_graph.neighbors(host_v.vertex_id,
                                               edge_attr_filter=query)
        self.assertEqual(num_orig_edges + len(deleted_edges) + 3,
                         entity_graph.num_edges())

        # remove nagios alarm_a, alarm_d should be removed
        test_vals = {'status': 'OK',
                     'service': 'alarm_a'}
        test_vals.update(_NAGIOS_TEST_INFO)
        generator = mock_driver.simple_nagios_alarm_generators(1, 1, test_vals)
        alarm_a_ok = mock_driver.generate_random_events_list(generator)[0]

        host_v = self.get_host_after_event(event_queue, alarm_a_ok,
                                           processor, _TARGET_HOST)
        alarms = self._get_alarms_on_host(host_v, entity_graph)
        self.assertEqual(1, len(alarms))

        query = {VProps.CATEGORY: EntityCategory.ALARM,
                 VProps.IS_DELETED: True}
        deleted_alarms = entity_graph.neighbors(host_v.vertex_id,
                                                vertex_attr_filter=query)
        self.assertEqual(num_orig_vertices + len(deleted_alarms) + 1,
                         entity_graph.num_vertices())

        query = {VProps.IS_DELETED: True}
        deleted_edges = entity_graph.neighbors(host_v.vertex_id,
                                               edge_attr_filter=query)
        self.assertEqual(num_orig_edges + len(deleted_edges) + 1,
                         entity_graph.num_edges())

    def get_host_after_event(self, event_queue, nagios_event,
                             processor, target_host):
        processor.process_event(nagios_event)
        while not event_queue.empty():
            processor.process_event(event_queue.get())
        host_v = self._get_entity_from_graph(NOVA_HOST_DATASOURCE,
                                             target_host,
                                             target_host,
                                             processor.entity_graph)
        return host_v

    def _init_system(self):
        processor = self._create_processor_with_graph(self.conf, uuid=True)
        event_queue = queue.Queue()
        evaluator = ScenarioEvaluator(self.conf, processor.entity_graph,
                                      self.scenario_repository, event_queue,
                                      enabled=True)
        return event_queue, processor, evaluator

    @staticmethod
    def _get_entity_from_graph(entity_type, entity_name,
                               entity_id,
                               entity_graph):
        vertex_attrs = {VProps.TYPE: entity_type,
                        VProps.ID: entity_id,
                        VProps.NAME: entity_name}
        vertices = entity_graph.get_vertices(vertex_attr_filter=vertex_attrs)
        # assert len(vertices) == 1, "incorrect number of vertices"
        return vertices[0]

    @staticmethod
    def _get_deduced_alarms_on_host(host_v, entity_graph):
        v_id = host_v.vertex_id
        vertex_attrs = {VProps.NAME: 'deduced_alarm',
                        VProps.TYPE: 'vitrage',
                        VProps.IS_DELETED: False, }
        return entity_graph.neighbors(v_id=v_id,
                                      vertex_attr_filter=vertex_attrs)

    @staticmethod
    def _get_alarms_on_host(host_v, entity_graph):
        v_id = host_v.vertex_id
        vertex_attrs = {VProps.CATEGORY: EntityCategory.ALARM,
                        VProps.IS_DELETED: False, }
        return entity_graph.neighbors(v_id=v_id,
                                      vertex_attr_filter=vertex_attrs)

    @staticmethod
    def _get_alarm_causes(alarm_v, entity_graph):
        v_id = alarm_v.vertex_id
        edge_attrs = {EProps.RELATIONSHIP_TYPE: "causes",
                      EProps.IS_DELETED: False, }
        return entity_graph.neighbors(v_id=v_id, edge_attr_filter=edge_attrs)
