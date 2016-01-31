# Copyright 2016 - Alcatel-Lucent
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

from oslo_log import log
from oslo_service import service as os_service

from vitrage.common.constants import SynchronizerProperties as SyncProps
from vitrage.common.constants import SyncMode

LOG = log.getLogger(__name__)


class SynchronizerService(os_service.Service):

    def __init__(self, conf, registered_plugins):
        super(SynchronizerService, self).__init__()
        self.conf = conf
        self.registered_plugins = registered_plugins

    def set_callback(self, callback_function):
        self.callback_function = callback_function


class SnapshotsService(SynchronizerService):

    def __init__(self, conf, registered_plugins):
        super(SnapshotsService, self).__init__(conf, registered_plugins)
        self.first_time = True

    def start(self):
        LOG.info("Start VitrageSnapshotsService")
        super(SnapshotsService, self).start()
        interval = self.conf.synchronizer.snapshots_interval
        self.tg.add_timer(interval, self._get_all)
        LOG.info("Finish start VitrageSnapshotsService")

    def stop(self):
        LOG.info("Stop VitrageSynchronizerService")

        super(SnapshotsService, self).stop()

        LOG.info("Finish stop VitrageSynchronizerService")

    def _get_all(self):
        sync_mode = SyncMode.INIT_SNAPSHOT \
            if self.first_time else SyncMode.SNAPSHOT
        LOG.debug("start get all with sync mode %s" % sync_mode)

        for plugin in self.registered_plugins:
            entities_dictionaries = \
                self._mark_snapshot_entities(plugin.get_all(), sync_mode)
            for entity in entities_dictionaries:
                self.callback_function(entity)

        LOG.debug("end get all with sync mode %s" % sync_mode)
        self.first_time = False

    @staticmethod
    def _mark_snapshot_entities(dicts, sync_mode):
        [x.setdefault(SyncProps.SYNC_MODE, sync_mode) for x in dicts]
        return dicts
