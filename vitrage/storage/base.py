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
import abc

import six


@six.add_metaclass(abc.ABCMeta)
class Connection(object):
    """Base class for storage system connections."""

    def __init__(self, conf, url):
        pass

    @property
    def active_actions(self):
        return None

    @property
    def events(self):
        return None

    @abc.abstractmethod
    def upgrade(self, nocreate=False):
        raise NotImplementedError('upgrade not implemented')

    @abc.abstractmethod
    def disconnect(self):
        raise NotImplementedError('disconnect not implemented')

    @abc.abstractmethod
    def clear(self):
        raise NotImplementedError('clear not implemented')


@six.add_metaclass(abc.ABCMeta)
class ActiveActionsConnection(object):
    @abc.abstractmethod
    def create(self, active_action):
        """Create a new action.

        :type active_action: vitrage.storage.sqlalchemy.models.ActiveAction
        """
        raise NotImplementedError('create active action not implemented')

    @abc.abstractmethod
    def update(self, active_action):
        """Update an existing action.

        :type active_action: vitrage.storage.sqlalchemy.models.ActiveAction
        """
        raise NotImplementedError('update active action not implemented')

    @abc.abstractmethod
    def query(self,
              action_type=None,
              extra_info=None,
              source_vertex_id=None,
              target_vertex_id=None,
              action_id=None,
              score=None,
              trigger=None,
              ):
        """Yields a lists of active actions that match filters.

        :rtype: list of vitrage.storage.sqlalchemy.models.ActiveAction
        """
        raise NotImplementedError('query active actions not implemented')

    @abc.abstractmethod
    def delete(self,
               action_type=None,
               extra_info=None,
               source_vertex_id=None,
               target_vertex_id=None,
               action_id=None,
               score=None,
               trigger=None,
               ):
        """Delete all active actions that match the filters."""
        raise NotImplementedError('delete active actions not implemented')


@six.add_metaclass(abc.ABCMeta)
class EventsConnection(object):
    def create(self, event):
        """Create a new event.

        :type event: vitrage.storage.sqlalchemy.models.Event
        """
        raise NotImplementedError('create event not implemented')

    def update(self, event):
        """Update an existing event.

        :type event: vitrage.storage.sqlalchemy.models.Event
        """
        raise NotImplementedError('update event not implemented')

    def query(self,
              event_id=None,
              collector_timestamp=None,
              payload=None,
              gt_collector_timestamp=None,
              lt_collector_timestamp=None):
        """Yields a lists of events that match filters.

        :rtype: list of vitrage.storage.sqlalchemy.models.Event
        """
        raise NotImplementedError('query events not implemented')

    def delete(self,
               event_id=None,
               collector_timestamp=None,
               payload=None,
               gt_collector_timestamp=None,
               lt_collector_timestamp=None):
        """Delete all events that match the filters."""
        raise NotImplementedError('delete events not implemented')
