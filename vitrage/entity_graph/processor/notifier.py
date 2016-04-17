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
from oslo_log import log
import oslo_messaging

from vitrage.common.constants import EntityCategory
from vitrage.common.constants import NotifierEventTypes
from vitrage.common.constants import VertexProperties as VProps
from vitrage.evaluator.actions import evaluator_event_transformer as evaluator
from vitrage.messaging import get_transport


LOG = log.getLogger(__name__)


class DeducedAlarmNotifier(object):
    """Allows writing to message bus"""
    def __init__(self, conf):
        self.oslo_notifier = None
        try:
            topic = conf.entity_graph.notifier_topic
            notifier_plugins = conf.notifiers
            if not topic or not notifier_plugins:
                LOG.info('DeducedAlarmNotifier is disabled')
                return

            self.oslo_notifier = oslo_messaging.Notifier(
                get_transport(conf),
                driver='messagingv2',
                publisher_id='vitrage.deduced',
                topic=topic)
        except Exception as e:
            LOG.info('DeducedAlarmNotifier missing configuration %s' % str(e))

    @property
    def enabled(self):
        return self.oslo_notifier is not None

    def notify_when_applicable(self, before, current, is_vertex):
        """Callback subscribed to driver.graph updates

        :param is_vertex:
        :param before: The graph element (vertex or edge) prior to the
        change that happened. None if the element was just created.
        :param current: The graph element (vertex or edge) after the
        change that happened. Deleted elements should arrive with the
        is_deleted property set to True
        """
        notification_type = _get_notification_type(before, current, is_vertex)
        if not notification_type:
            return

        LOG.debug('DeducedAlarmNotifier : %s', notification_type)
        LOG.debug('DeducedAlarmNotifier : %s', current.properties)

        try:
            self.oslo_notifier.info({}, notification_type, current.properties)
        except Exception as e:
            LOG.exception('DeducedAlarmNotifier cannot notify - %s', e)


def _get_notification_type(before, current, is_vertex):
    if not is_vertex:
        return None
    if not _is_active_deduced_alarm(before) and \
        _is_active_deduced_alarm(current):
        return NotifierEventTypes.ACTIVATE_DEDUCED_ALARM_EVENT
    if _is_active_deduced_alarm(before) and \
        not _is_active_deduced_alarm(current):
        return NotifierEventTypes.DEACTIVATE_DEDUCED_ALARM_EVENT


def _is_active_deduced_alarm(vertex):
    if not vertex:
        return False

    if not (vertex.get(VProps.CATEGORY) == EntityCategory.ALARM and
            vertex.get(VProps.TYPE) == evaluator.VITRAGE_TYPE):
        return False

    if vertex.get(VProps.IS_DELETED, False) or \
            vertex.get(VProps.IS_PLACEHOLDER, False):
        return False
    return True
