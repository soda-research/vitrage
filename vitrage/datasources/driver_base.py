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

import abc
import six

from oslo_log import log

from vitrage.common.constants import EventAction
from vitrage.common.constants import SynchronizerProperties as SyncProps
from vitrage.common.constants import SyncMode
from vitrage.common import datetime_utils

LOG = log.getLogger(__name__)


@six.add_metaclass(abc.ABCMeta)
class DriverBase(object):

    def __init__(self):
        pass

    @abc.abstractmethod
    def get_all(self, sync_mode):
        pass

    @staticmethod
    def _get_end_message(sync_type):
        end_message = {
            SyncProps.SYNC_TYPE: sync_type,
            SyncProps.SYNC_MODE: SyncMode.INIT_SNAPSHOT,
            SyncProps.EVENT_TYPE: EventAction.END_MESSAGE
        }
        return end_message

    def get_changes(self, sync_mode):
        pass

    @classmethod
    def make_pickleable(cls, entities, sync_type,
                        sync_mode, *args):
        pickleable_entities = []

        for entity in entities:
            for field in args:
                entity.pop(field)

            cls._add_sync_type(entity, sync_type)
            cls._add_sync_mode(entity, sync_mode)
            cls._add_sampling_time(entity)
            pickleable_entities.append(entity)

        if sync_mode == SyncMode.INIT_SNAPSHOT:
            pickleable_entities.append(cls._get_end_message(sync_type))

        return pickleable_entities

    @staticmethod
    def _add_sync_type(entity, sync_type):
        if SyncProps.SYNC_TYPE not in entity:
            entity[SyncProps.SYNC_TYPE] = sync_type

    @staticmethod
    def _add_sampling_time(entity):
        entity[SyncProps.SAMPLE_DATE] = str(datetime_utils.utcnow())

    @staticmethod
    def _add_sync_mode(entity, sync_mode):
        entity[SyncProps.SYNC_MODE] = sync_mode

    @staticmethod
    @abc.abstractmethod
    def enrich_event(event, event_type):
        """Return the given event with extra fields

        We add extra data, which the transformer uses later on.
        For example, we can add a timestamp and change the message's structure
        :param event: the event received by oslo
        :param event_type: the event type of the event
        :return: the enriched event
        """

        pass

    @staticmethod
    @abc.abstractmethod
    def get_event_types(conf):
        """Return a list of all event types relevant to this synchronizer

        Example:
        return ['compute.instance.update',
                'compute.instance.resume']

        It also supports prefixes- the event types which start
        with this prefix will be processed by this synchronizer:
        Example:
        return ['compute.instance']



        :return: a list of event types
        :rtype: list of str
        """

        return []

    @staticmethod
    @abc.abstractmethod
    def get_topic(conf):
        """Return the topic of events processed by this synchronizer

        Example:
        to listen to nova topic, add another topic to nova.conf so nova will
        notify the notifications to another queue.

        example of nova.conf:
         notification_topics = notifications,new_topic

        example of get_topic():
         return 'new_topic'

        :param conf: the synchronizer's configuration
        :return: the topic of the synchronizer
        :rtype: str
        """

        return None

    @staticmethod
    @abc.abstractmethod
    def get_skipped_event_types():
        return []
