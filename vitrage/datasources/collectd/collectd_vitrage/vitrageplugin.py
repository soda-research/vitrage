# -*- coding: utf-8 -*-
#
# © 2016 Nokia Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License.  You may obtain
# a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""
Collectd plugin for sending notifications to vitrage
"""

import collectd
import hashlib
import six

from vitrage.datasources.collectd.collectd_vitrage.plugin import CollectDPlugin
from vitrage.datasources.collectd.collectd_vitrage.plugin import PluginError

import uuid

from datetime import datetime
from oslo_config import cfg

import oslo_messaging as messaging


class VitrageNotifier(CollectDPlugin):
    """Collectd plugin for sending notifications to Vitrage. """

    def configure(self, config, **kwargs):

        super(VitrageNotifier, self).configure(config, **kwargs)

        # to be filled later
        for key in ('transport_url',):
            if key not in self.config.keys():
                message = 'Required configuration key %s missing!' % key
                self.error(message)
                raise PluginError(message)

    def initialize(self):
        """Set up the Vitrage API client and add the notification callback. """

        url = self.config['transport_url']
        transport = messaging.get_transport(cfg.CONF, url)
        self.notifier = messaging.Notifier(transport,
                                           driver='messagingv2',
                                           publisher_id='collectd',
                                           topic='vitrage_notifications')
        self.add_notification_callback(self.notify)

    def notify(self, notification):
        """Send the notification to Vitrage. """

        # Use a friendly string instead of a number.
        severity = {
            collectd.NOTIF_FAILURE: 'FAILURE',
            collectd.NOTIF_WARNING: 'WARNING',
            collectd.NOTIF_OKAY: 'OK',
        }.get(notification.severity)

        alarm = notification.host + notification.plugin_instance \
            + notification.type_instance

        alarm_uuid = hashlib.md5(six.b(alarm)).hexdigest()

        details = {
            'host': notification.host,
            'plugin': notification.plugin,
            'plugin_instance': notification.plugin_instance,
            'type': notification.type,
            'type_instance': notification.type_instance,
            'message': notification.message,
            'severity': severity,
            'time': notification.time,
            'id': alarm_uuid
        }

        notification_id = str(uuid.uuid4())

        self.notifier.info(ctxt={'message_id': notification_id,
                                 'publisher_id': 'collectd',
                                 'timestamp': datetime.utcnow()},
                           event_type='collectd.alarm.' + severity.lower(),
                           payload=details)
        self.info('notification id %r to vitrage: %r' % (notification_id,
                                                         details))


# We have to call the constructor in order to actually register our plugin
# with collectd.
VITRAGE = VitrageNotifier()
