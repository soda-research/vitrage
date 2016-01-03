# Copyright 2015 - Alcatel-Lucent
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

from oslo_service import service as os_service

from vitrage.common.constants import SyncMode
from vitrage import entity_graph as entity_graph_svc
from vitrage import service
from vitrage import synchronizer as synchronizer_svc
from vitrage.synchronizer.synchronizer import Synchronizer


def main():
    """Runs the Entity graph service

    1. Starts the Processor and the Synchronizer services
    2. Calls the initial get_all to the Synchronizer to get all the resources
       in the system.
    """

    event_queue = multiprocessing.Queue()
    conf = service.prepare_service()
    # TODO(Alexey): Need to implement "signal_handle" of ProcessLauncher in
    #               order that the stop method of the services will be called
    launcher = os_service.ProcessLauncher(conf)

    launcher.launch_service(entity_graph_svc.VitrageEntityGraphService(
        event_queue), workers=1)

    synchronizer = Synchronizer(event_queue)
    launcher.launch_service(synchronizer_svc.VitrageSynchronizerService(
        synchronizer), workers=1)

    synchronizer.get_all(sync_mode=SyncMode.INIT_SNAPSHOT)

    launcher.wait()
