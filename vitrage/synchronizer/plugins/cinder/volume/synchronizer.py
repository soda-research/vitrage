# Copyright 2016 - Alcatel-Lucent
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing,  software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND,  either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

from oslo_log import log as logging

from vitrage import clients
from vitrage.common.constants import SynchronizerProperties as SyncProps
from vitrage.common.constants import SyncMode
from vitrage.synchronizer.plugins.cinder.volume import CINDER_VOLUME_PLUGIN
from vitrage.synchronizer.plugins.synchronizer_base import SynchronizerBase

LOG = logging.getLogger(__name__)


class CinderVolumeSynchronizer(SynchronizerBase):

    def __init__(self, conf):
        super(CinderVolumeSynchronizer, self).__init__()
        self.client = clients.cinder_client(conf)
        self.conf = conf

    @staticmethod
    def extract_events(volumes):
        return [volume.__dict__ for volume in volumes]

    def get_all(self, sync_mode):
        return self.make_pickleable(
            self.extract_events(self.client.volumes.list()),
            CINDER_VOLUME_PLUGIN,
            sync_mode)

    @staticmethod
    def enrich_event(event, event_type):
        event[SyncProps.EVENT_TYPE] = event_type

        return CinderVolumeSynchronizer.make_pickleable([event],
                                                        CINDER_VOLUME_PLUGIN,
                                                        SyncMode.UPDATE)[0]

    @staticmethod
    def get_event_types(conf):
        return ['volume.']

    @staticmethod
    def get_topic(conf):
        return conf[CINDER_VOLUME_PLUGIN].notification_topic
