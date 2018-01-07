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

import sys

from oslo_service import service as os_service

from vitrage.api_handler.service import VitrageApiHandlerService
from vitrage.cli import VITRAGE_TITLE
from vitrage import entity_graph
from vitrage.entity_graph.consistency.service import VitrageConsistencyService
from vitrage import service
from vitrage import storage

from vitrage.entity_graph.service import VitrageGraphService
from vitrage.evaluator.evaluator_service import EvaluatorManager


def main():
    """Starts all the Entity graph services

    1. Starts the Entity graph service
    2. Starts the api_handler service
    3. Starts the Consistency service
    """

    print(VITRAGE_TITLE)
    conf = service.prepare_service()
    e_graph = entity_graph.get_graph_driver(conf)('Entity Graph')
    evaluator = EvaluatorManager(conf, e_graph)
    launcher = os_service.ServiceLauncher(conf)
    db_connection = storage.get_connection_from_config(conf)
    clear_active_actions_table(db_connection)

    launcher.launch_service(VitrageGraphService(
        conf, e_graph, evaluator, db_connection))

    launcher.launch_service(VitrageApiHandlerService(conf, e_graph))

    launcher.launch_service(VitrageConsistencyService(conf, e_graph))

    launcher.wait()


def clear_active_actions_table(db_connection):
    """Delete all data from active_actions table

    The following deletes the entire vitrage database
    It should be removed once graph is persistent
    """
    db_connection.active_actions.delete()

if __name__ == "__main__":
    sys.exit(main())
