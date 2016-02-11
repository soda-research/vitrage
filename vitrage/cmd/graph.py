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

from vitrage import entity_graph as entity_graph_svc
from vitrage.entity_graph import api_handler as api_handler_svc
from vitrage.entity_graph.consistency import service as consistency_svc
from vitrage.entity_graph.processor import entity_graph
from vitrage import service
from vitrage.synchronizer import launcher as synchronizer_launcher


def main():
    """Starts all the Entity graph services

    1. Starts the Entity graph service
    2. Starts the api_handler service
    3. Starts the Synchronizer service
    4. Starts the Consistency service
    """

    e_graph = entity_graph.EntityGraph("Entity Graph")
    event_queue = multiprocessing.Queue()
    conf = service.prepare_service()
    launcher = os_service.ServiceLauncher(conf)
    synchronizer = synchronizer_launcher.Launcher(
        conf, synchronizer_launcher.create_send_to_queue_callback(event_queue))

    launcher.launch_service(entity_graph_svc.VitrageGraphService(
        event_queue, e_graph))

    launcher.launch_service(api_handler_svc.VitrageApiHandlerService(
        e_graph))

    synchronizer.launch()

    launcher.launch_service(consistency_svc.VitrageGraphConsistencyService(
        conf, e_graph))

    launcher.wait()

if __name__ == "__main__":
    sys.exit(main())
