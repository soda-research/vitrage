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

from six.moves import queue
import sys

from oslo_service import service as os_service

from vitrage.api_handler.service import VitrageApiHandlerService
from vitrage.common.constants import EntityCategory
from vitrage.datasources import OPENSTACK_CLUSTER
from vitrage.datasources.transformer_base import CLUSTER_ID
from vitrage import entity_graph
from vitrage.entity_graph.consistency.service import VitrageConsistencyService
from vitrage.entity_graph.service import VitrageGraphService
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

    conf = service.prepare_service()
    evaluator_queue, evaluator, e_graph = init(conf)
    launcher = os_service.ServiceLauncher(conf)

    graph_svc = VitrageGraphService(conf, evaluator_queue, e_graph, evaluator)
    launcher.launch_service(graph_svc)

    launcher.launch_service(VitrageApiHandlerService(conf, e_graph,
                                                     evaluator.scenario_repo))

    launcher.launch_service(VitrageConsistencyService(conf, evaluator_queue,
                                                      e_graph))

    launcher.wait()


def init(conf):
    evaluator_q = queue.Queue()
    e_graph = entity_graph.get_graph_driver(conf)(
        'Entity Graph',
        '%s:%s:%s' % (EntityCategory.RESOURCE, OPENSTACK_CLUSTER, CLUSTER_ID),
        uuid=True)
    scenario_repo = ScenarioRepository(conf)

    evaluator = ScenarioEvaluator(conf, e_graph, scenario_repo, evaluator_q)

    return evaluator_q, evaluator, e_graph


if __name__ == "__main__":
    sys.exit(main())
