# Copyright 2016 - Nokia
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
from collections import defaultdict

from oslo_log import log
import oslo_messaging
from oslo_service import service as os_service

from vitrage import messaging


LOG = log.getLogger(__name__)


class ListenerService(os_service.Service):

    def __init__(self, conf, synchronizers, callback):

        super(ListenerService, self).__init__()

        # Get the topics of the synchronizers and callbacks
        topics = self._get_topics_set(synchronizers, conf)
        self.enrich_callbacks_by_events = \
            self.create_callbacks_by_events_dict(synchronizers, conf)

        self.listener = self.get_topics_listener(conf, topics, callback)

    def start(self):
        LOG.info("Vitrage Synchronizer Listener Service - Starting...")
        super(ListenerService, self).start()
        self.listener.start()
        LOG.info("Vitrage Synchronizer Listener Service - Started!")

    def stop(self, graceful=False):
        LOG.info("Vitrage Synchronizer Listener Service - Stopping...")
        super(ListenerService, self).stop(graceful)
        LOG.info("Vitrage Synchronizer Listener Service - Stopped!")

    @staticmethod
    def _get_topics_set(synchronizers, conf):
        topics = set([sync.get_topic(conf) for sync in synchronizers.values()])
        topics.remove(None)
        return topics

    @staticmethod
    def create_callbacks_by_events_dict(synchronizers, conf):
        ret = defaultdict(list)
        for sync in synchronizers.values():
            for event in sync.get_event_types(conf):
                ret[event].append(sync.enrich_event)
        return ret

    def get_topics_listener(self, conf, topics, callback):
        # Create a listener for each topic
        transport = messaging.get_transport(conf)
        targets = []
        for topic in topics:
            targets.append(oslo_messaging.Target(topic=topic, exchange='nova'))

        return messaging.get_notification_listener(
            transport, targets,
            [NotificationsEndpoint(self.enrich_callbacks_by_events, callback)])


class NotificationsEndpoint(object):

    def __init__(self, enrich_callback_by_events, enqueue_callback):
        self.enrich_callbacks_by_events = enrich_callback_by_events
        self.enqueue_callback = enqueue_callback

    def info(self, ctxt, publisher_id, event_type, payload, metadata):
        LOG.info('EVENT RECEIVED: ' + str(event_type))
        for event_pattern in self.enrich_callbacks_by_events.keys():
            if event_type.startswith(event_pattern):
                callbacks = self.enrich_callbacks_by_events[event_pattern]
                enriched_events = [callback(payload, event_type)
                                   for callback in callbacks]
                self._enqueue_events(enriched_events)

    def _enqueue_events(self, enriched_events):
        for event in enriched_events:
            self.enqueue_callback(event)
            LOG.debug('EVENT ENQUEUED: \n' + "enrichment: " + str(event))
