# Copyright 2016 - Nokia
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
import random
import string

from oslo_log import log as logging

from vitrage import clients
from vitrage.common.constants import NotifierEventTypes
from vitrage.notifier.plugins.base import NotifierBase


LOG = logging.getLogger(__name__)


def aodh_alarm_name_generator(name, unique=None, size=6,
                              chars=string.ascii_uppercase + string.digits):
    if unique:
        return name.join(['_', unique])
    else:
        unique = ''.join(random.choice(chars) for _ in range(size))
        return name.join(['_', unique])


class AodhNotifier(NotifierBase):

    def __init__(self, conf):
        super(AodhNotifier, self).__init__(conf)
        self.client = clients.ceilometer_client(conf)

    def process_event(self, data, event_type):
        if event_type == NotifierEventTypes.DEACTIVATE_DEDUCED_ALARM_EVENT:
            self._deactivate_aodh_alarm(data)
        elif event_type == NotifierEventTypes.ACTIVATE_DEDUCED_ALARM_EVENT:
            self._activate_aodh_alarm(data)

    # noinspection PyMethodMayBeStatic
    def _activate_aodh_alarm(self, data):
        LOG.info('### Activate aodh alarm')
        # alarm_name = aodh_alarm_name_generator(
        #     data.get(VProps.NAME),
        #     data.get('affected_resource_id'))
        # query = [dict(
        #     field='resource_id',
        #     type='string',
        #     op='eq',
        #     value=data.get('affected_resource_id'))]
        # severity = data.get(VProps.SEVERITY)
        # try:
        #     alarm = self.client.alarms.create(
        #         name=alarm_name,
        #         description='Vitrage deduced alarm',
        #         query=query,
        #         severity=severity,
        #         state='alarm',
        #         type='event',
        #         event_rule={"event_type": '*'})
        #     LOG.info('Aodh Alarm created: ' + str(alarm))
        # except Exception as e:
        #     LOG.exception('Failed to create Aodh Alarm, Got Exception: %s',e)
        # name
        # description
        # type' : event or threshold
        # threshold_rule
        # event_rule
        # state': ok, alarm, insufficient data
        # severity': moderate, critical, low
        # enabled
        # alarm_actions
        # ok_actions
        # insufficient_data_actions
        # repeat_actions
        # project_id
        # user_id
        # time_constraints

    # noinspection PyMethodMayBeStatic
    def _deactivate_aodh_alarm(self, data):
        LOG.info('### Deactivate aodh alarm')
        # try:
        #     alarm = self.client.alarms.update(
        #         alarm_id=data.get(VProps.ID),
        #         state='ok')
        #     LOG.info('Aodh Alarm deactivated ' + str(alarm))
        # except Exception as e:
        #     LOG.exception('Failed to update Aodh Alarm, Got Exception: %s',e)
