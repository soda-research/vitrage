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

from vitrage.entity_graph import utils
from vitrage import messaging


LOG = log.getLogger(__name__)


class ListenerService(os_service.Service):

    def __init__(self, conf, drivers, callback):
        super(ListenerService, self).__init__()

        self.enrich_callbacks_by_events = \
            self._create_callbacks_by_events_dict(drivers, conf)

        topics = conf.datasources.notification_topics
        exchange = conf.datasources.notification_exchange
        self.listener = self._get_topics_listener(
            conf, topics, callback, exchange)

    def start(self):
        LOG.info("Vitrage data source Listener Service - Starting...")

        super(ListenerService, self).start()
        self.listener.start()

        LOG.info("Vitrage data source Listener Service - Started!")

    def stop(self, graceful=False):
        LOG.info("Vitrage data source Listener Service - Stopping...")

        # Should it be here?
        # self.listener.stop()
        # self.listener.wait()
        super(ListenerService, self).stop(graceful)

        LOG.info("Vitrage data source Listener Service - Stopped!")

    @classmethod
    def _create_callbacks_by_events_dict(cls, drivers, conf):
        ret = defaultdict(list)
        push_drivers = utils.get_push_datasources(drivers, conf)

        for driver in push_drivers:
            for event in driver.get_event_types():
                ret[event].append(driver.enrich_event)

        return ret

    def _get_topics_listener(self, conf, topics, callback, exchange=None):
        # Create a listener for each topic
        transport = messaging.get_transport(conf)
        targets = [oslo_messaging.Target(exchange=exchange, topic=topic)
                   for topic in topics]

        return messaging.get_notification_listener(
            transport,
            targets,
            [NotificationsEndpoint(self.enrich_callbacks_by_events, callback)])


class NotificationsEndpoint(object):

    def __init__(self, enrich_callback_by_events, enqueue_callback):
        self.enrich_callbacks_by_events = enrich_callback_by_events
        self.enqueue_callback = enqueue_callback

    def info(self, ctxt, publisher_id, event_type, payload, metadata):
        for event_string in self.enrich_callbacks_by_events:
            if str(event_type) == event_string:

                callbacks = self.enrich_callbacks_by_events[event_string]
                enriched_events = []
                for callback in callbacks:
                    result = callback(payload, event_type)
                    if isinstance(result, list):
                        enriched_events += result
                    else:
                        enriched_events.append(result)
                self._enqueue_events(enriched_events)

    def _enqueue_events(self, enriched_events):
        for event in enriched_events:
            if event is not None:
                self.enqueue_callback(event)
                LOG.debug('EVENT ENQUEUED: \n' + str(event))
