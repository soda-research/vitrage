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
import oslo_messaging
import threading
import time

from oslo_log import log
from oslo_service import service as os_service

from vitrage.entity_graph import EVALUATOR_TOPIC
from vitrage.entity_graph.processor.processor import Processor
from vitrage.entity_graph.vitrage_init import VitrageInit
from vitrage.evaluator.template_loader_service import TemplateLoaderManager
from vitrage import messaging
from vitrage.persistency.graph_persistor import GraphPersistor

LOG = log.getLogger(__name__)


class VitrageGraphService(os_service.Service):

    def __init__(self,
                 conf,
                 graph,
                 evaluator,
                 db):
        super(VitrageGraphService, self).__init__()
        self.conf = conf
        self.graph = graph
        self.evaluator = evaluator
        self.templates_loader = TemplateLoaderManager(conf, graph, db)
        self.init = VitrageInit(conf, graph, self.evaluator,
                                self.templates_loader)
        self.graph_persistor = GraphPersistor(conf) if \
            self.conf.persistency.enable_persistency else None
        self.processor = Processor(self.conf, self.init, graph,
                                   self.graph_persistor)
        self.listener = self._init_listener()

    def _init_listener(self):
        collector_topic = self.conf.datasources.notification_topic_collector
        evaluator_topic = EVALUATOR_TOPIC
        return TwoPriorityListener(
            self.conf,
            self.process_event,
            collector_topic,
            evaluator_topic)

    def process_event(self, event):
        if event.get('template_action'):
            self.templates_loader.handle_template_event(event)
            self.evaluator.reload_evaluators_templates()
        else:
            self.processor.process_event(event)

    def start(self):
        LOG.info("Vitrage Graph Service - Starting...")
        super(VitrageGraphService, self).start()
        if self.graph_persistor:
            self.tg.add_timer(
                self.conf.persistency.graph_persistency_interval,
                self.graph_persistor.store_graph,
                self.conf.persistency.graph_persistency_interval,
                graph=self.graph)
        self.tg.add_thread(
            self.init.initializing_process,
            on_end_messages_func=self.processor.on_recieved_all_end_messages)
        self.listener.start()
        LOG.info("Vitrage Graph Service - Started!")

    def stop(self, graceful=False):
        LOG.info("Vitrage Graph Service - Stopping...")
        self.evaluator.stop_all_workers()
        self.templates_loader.stop_all_workers()
        self.listener.stop()
        self.listener.wait()
        super(VitrageGraphService, self).stop(graceful)

        LOG.info("Vitrage Graph Service - Stopped!")


PRIORITY_DELAY = 0.05


class TwoPriorityListener(object):
    def __init__(self, conf, do_work_func, topic_low, topic_high):
        self._conf = conf
        self._do_work_func = do_work_func
        self._lock = threading.Lock()
        self._high_event_finish_time = 0

        self._low_pri_listener = self._init_listener(
            topic_low, self._do_low_priority_work)
        self._high_pri_listener = self._init_listener(
            topic_high, self._do_high_priority_work)

    def start(self):
        self._high_pri_listener.start()
        self._low_pri_listener.start()

    def stop(self):
        self._low_pri_listener.stop()
        self._high_pri_listener.stop()

    def wait(self):
        self._low_pri_listener.wait()
        self._high_pri_listener.wait()

    def _do_high_priority_work(self, event):
        self._lock.acquire()
        self._do_work_func(event)
        self._high_event_finish_time = time.time()
        self._lock.release()

    def _do_low_priority_work(self, event):
        while True:
            self._lock.acquire()
            if (time.time() - self._high_event_finish_time) < PRIORITY_DELAY:
                self._lock.release()
                time.sleep(PRIORITY_DELAY)
            else:
                break
        self._do_work_func(event)
        self._lock.release()

    def _init_listener(self, topic, callback):
        if not topic:
            return
        return messaging.get_notification_listener(
            transport=messaging.get_transport(self._conf),
            targets=[oslo_messaging.Target(topic=topic)],
            endpoints=[PushNotificationsEndpoint(callback)])


class PushNotificationsEndpoint(object):
    def __init__(self, process_event_callback):
        self.process_event_callback = process_event_callback

    def info(self, ctxt, publisher_id, event_type, payload, metadata):
        try:
            self.process_event_callback(payload)
        except Exception as e:
            LOG.exception(e)
