# Copyright 2017 - Nokia
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
from vitrage.cli import VITRAGE_TITLE
from vitrage.datasources.listener_service import ListenerService

from vitrage.datasources.collector_notifier import CollectorNotifier
from vitrage.datasources import launcher as datasource_launcher
from vitrage.entity_graph import utils
from vitrage import service


def main():

    """Starts all the datasources drivers services"""

    print(VITRAGE_TITLE)
    conf = service.prepare_service()
    launcher = os_service.ServiceLauncher(conf)
    rabbitmq = CollectorNotifier(conf)
    callback = datasource_launcher.create_send_to_queue_callback(rabbitmq)
    launcher.launch_service(ListenerService(conf,
                                            utils.get_drivers(conf),
                                            callback))

    datasources = datasource_launcher.Launcher(conf, callback)
    datasources.launch()

    launcher.wait()


if __name__ == "__main__":
    sys.exit(main())
