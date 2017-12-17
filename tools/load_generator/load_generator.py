# Copyright 2017 - Nokia
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.
import copy

import sys

from oslo_log import log
import oslo_messaging
from oslo_service import service as os_service
from tools.load_generator.notification_info import *  # noqa
from vitrage.messaging import get_transport
from vitrage import service


LOG = log.getLogger(__name__)

EXISTING_COMPUTES_NUM = 64
VMS_PER_COMPUTE = 2
NET_ID = '59fec1a4-7ab2-4bc6-8792-0ddf54b15dfe'
RUN_EVERY_X_SECONDS = 600

"""
Stress Notifications Tool:

Following service runs a timed action every X seconds.
Action will send mock bus notifications, as configured in the constants above.
Sends mock notifications for:
    VM create
    Port create
    volume create
    volume attach

1. To use this, place computes.yaml at /etc/vitrage/static_datasources/
   and restart vitrage-graph.
2. EXISTING_COMPUTES_NUM should match the computes defined in computes.yaml
3. Configure NET_ID to an existing network (this tool doesnt create networks)
4. Run 'python load_generator.py'

Number of vms = VMS_PER_COMPUTE * EXISTING_COMPUTES_NUM
Number of ports = VMS_PER_COMPUTE * EXISTING_COMPUTES_NUM
Number of volumes = VMS_PER_COMPUTE * EXISTING_COMPUTES_NUM

Notifications are sent repeatedly every RUN_EVERY_X_SECONDS, this is
to avoid Vitrage consistency deleting the created resources.

* Folder /templates also includes templates to create load on the evaluator

"""


class StressNotificationsService(os_service.Service):
    def __init__(self, conf):
        super(StressNotificationsService, self).__init__()
        self.oslo_notifier = None
        topics = conf.datasources.notification_topics
        self.oslo_notifier = oslo_messaging.Notifier(
            get_transport(conf),
            driver='messagingv2',
            publisher_id='vitrage.stress',
            topics=topics)

    def start(self):
        super(StressNotificationsService, self).start()
        self.tg.add_timer(RUN_EVERY_X_SECONDS, self.stress_notifications, )
        LOG.info("StressNotificationsService - Started!")

    def stop(self, graceful=False):
        super(StressNotificationsService, self).stop(graceful)
        LOG.info("StressNotificationsService - Stopped!")

    def stress_notifications(self):
        notifications = []
        for i in range(EXISTING_COMPUTES_NUM * VMS_PER_COMPUTE):
            vm = create_vm(i, i % EXISTING_COMPUTES_NUM)
            port = create_port(i, vm[0][1]['instance_id'], vm[0][1]['host'],
                               NET_ID)
            storage = create_storage(i, vm[0][1]['instance_id'])
            notifications.extend(vm)
            notifications.extend(port)
            notifications.extend(storage)

        LOG.info("Notifications Created - " + str(len(notifications)))
        LOG.info("Sending...")
        for n in notifications:
            self._send(*n)
        LOG.info("Sent!")

    def _send(self, notification_type, payload):
        try:
            self.oslo_notifier.info(
                {},
                notification_type,
                payload)
        except Exception as e:
            LOG.exception('Cannot notify - %s - %s', notification_type, e)


def create_port(port_num, instance_id, host_id, net_id):
    payload = copy.deepcopy(PORT_CREATE_END)
    payload['port']['id'] = 'StressPort-' + str(port_num)
    payload['port']['device_id'] = instance_id
    payload['port']['binding:host_id'] = host_id
    payload['port']['network_id'] = net_id
    return [('port.create.end', payload)]


def create_storage(volume_num, instance_id):
    payload_1 = copy.deepcopy(VOLUME_CREATE_END)
    payload_1['volume_id'] = 'StressVolume-' + str(volume_num)

    payload_2 = copy.deepcopy(VOLUME_ATTACH_END)
    payload_2['volume_id'] = payload_1['volume_id']
    payload_2['volume_attachment'][0]['volume']['id'] = payload_1['volume_id']
    payload_2['volume_attachment'][0]['instance_uuid'] = instance_id

    return [('volume.create.end', payload_1),
            ('volume.attach.end', payload_2)]


def create_vm(instance_num, compute_num):
    payload = copy.deepcopy(COMPUTE_INSTANCE_CREATE_END)
    payload['instance_id'] = 'StressVM-' + str(instance_num)
    payload['node'] = payload['host'] = "compute-0-" + str(compute_num)
    return [('compute.instance.create.end', payload)]


def main():
    conf = service.prepare_service()
    launcher = os_service.ServiceLauncher(conf)
    launcher.launch_service(StressNotificationsService(conf))
    launcher.wait()


if __name__ == "__main__":
    sys.exit(main())
