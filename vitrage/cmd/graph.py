# Copyright 2015 - Alcatel-Lucent
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
import sys

from oslo_service import service as os_service

from vitrage.common.constants import EntityCategory
from vitrage.datasources import launcher as datasource_launcher
from vitrage.datasources import OPENSTACK_CLUSTER
from vitrage.entity_graph.api_handler import service as api_handler_svc
from vitrage.entity_graph.consistency import service as consistency_svc
from vitrage.entity_graph.initialization_status import InitializationStatus
from vitrage.entity_graph.processor import entity_graph
from vitrage.entity_graph import service as entity_graph_svc
from vitrage.evaluator.scenario_evaluator import ScenarioEvaluator
from vitrage.evaluator.scenario_repository import ScenarioRepository
from vitrage import service


def main():
    """Starts all the Entity graph services

    1. Starts the Entity graph service
    2. Starts the api_handler service
    3. Starts the datasource service
    4. Starts the Consistency service
    """

    conf, event_queue, evaluator, e_graph, initialization_status = init()
    launcher = os_service.ServiceLauncher(conf)
    datasources = datasource_launcher.Launcher(
        conf,
        datasource_launcher.create_send_to_queue_callback(event_queue))

    launcher.launch_service(entity_graph_svc.VitrageGraphService(
        conf, event_queue, evaluator, e_graph, initialization_status))

    launcher.launch_service(api_handler_svc.VitrageApiHandlerService(
        conf, e_graph))

    datasources.launch()

    launcher.launch_service(consistency_svc.VitrageGraphConsistencyService(
        conf, event_queue, evaluator, e_graph, initialization_status))

    launcher.wait()


def init():
    conf = service.prepare_service()
    event_queue = multiprocessing.Queue()
    e_graph = entity_graph.EntityGraph(
        'Entity Graph',
        '%s:%s' % (EntityCategory.RESOURCE, OPENSTACK_CLUSTER))
    scenario_repo = ScenarioRepository(conf)
    evaluator = ScenarioEvaluator(conf, e_graph, scenario_repo, event_queue)
    initialization_status = InitializationStatus()

    return conf, event_queue, evaluator, e_graph, initialization_status


if __name__ == "__main__":
    sys.exit(main())
