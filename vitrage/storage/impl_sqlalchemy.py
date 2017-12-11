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


from __future__ import absolute_import

from oslo_db.sqlalchemy import session as db_session
from oslo_log import log
from sqlalchemy.engine import url as sqlalchemy_url

from vitrage import storage
from vitrage.storage import base
from vitrage.storage.sqlalchemy import models

LOG = log.getLogger(__name__)


class Connection(base.Connection):
    def __init__(self, conf, url):
        options = dict(conf.database.items())
        # set retries to 0 , since reconnection is already implemented
        # in storage.__init__.get_connection_from_config function
        options['max_retries'] = 0
        # add vitrage opts to database group
        for opt in storage.OPTS:
            options.pop(opt.name, None)
        self._engine_facade = db_session.EngineFacade(self._dress_url(url),
                                                      **options)
        self.conf = conf
        self._active_actions = ActiveActionsConnection(self._engine_facade)
        self._events = EventsConnection(self._engine_facade)

    @property
    def active_actions(self):
        return self._active_actions

    @property
    def events(self):
        return self._events

    @staticmethod
    def _dress_url(url):
        # If no explicit driver has been set, we default to pymysql
        if url.startswith("mysql://"):
            url = sqlalchemy_url.make_url(url)
            url.drivername = "mysql+pymysql"
            return str(url)
        return url

    def upgrade(self, nocreate=False):
        engine = self._engine_facade.get_engine()
        engine.connect()
        models.Base.metadata.drop_all(engine, tables=[models.Event.__table__])
        models.Base.metadata.create_all(engine)
        # TODO(idan_hefetz) upgrade logic is missing

    def disconnect(self):
        self._engine_facade.get_engine().dispose()

    def clear(self):
        engine = self._engine_facade.get_engine()
        for table in reversed(models.Base.metadata.sorted_tables):
            engine.execute(table.delete())
        engine.dispose()


class BaseTableConn(object):
    def __init__(self, engine_facade):
        super(BaseTableConn, self).__init__()
        self._engine_facade = engine_facade

    def query_filter(self, model, **kwargs):
        session = self._engine_facade.get_session()
        query = session.query(model)
        for keyword, arg in kwargs.items():
            if arg is not None:
                query = query.filter(getattr(model, keyword) == arg)
        return query


class ActiveActionsConnection(base.ActiveActionsConnection, BaseTableConn):
    def __init__(self, engine_facade):
        super(ActiveActionsConnection, self).__init__(engine_facade)

    def create(self, active_action):
        session = self._engine_facade.get_session()
        with session.begin():
            session.add(active_action)

    def update(self, active_action):
        session = self._engine_facade.get_session()
        with session.begin():
            session.merge(active_action)

    def query(self,
              action_type=None,
              extra_info=None,
              source_vertex_id=None,
              target_vertex_id=None,
              action_id=None,
              score=None,
              trigger=None):
        query = self.query_filter(
            models.ActiveAction,
            action_type=action_type,
            extra_info=extra_info,
            source_vertex_id=source_vertex_id,
            target_vertex_id=target_vertex_id,
            action_id=action_id,
            score=score,
            trigger=trigger)
        return query.all()

    def delete(self,
               action_type=None,
               extra_info=None,
               source_vertex_id=None,
               target_vertex_id=None,
               action_id=None,
               score=None,
               trigger=None):
        query = self.query_filter(
            models.ActiveAction,
            action_type=action_type,
            extra_info=extra_info,
            source_vertex_id=source_vertex_id,
            target_vertex_id=target_vertex_id,
            action_id=action_id,
            score=score,
            trigger=trigger)
        return query.delete()


class EventsConnection(base.EventsConnection, BaseTableConn):
    def __init__(self, engine_facade):
        super(EventsConnection, self).__init__(engine_facade)

    def create(self, event):
        session = self._engine_facade.get_session()
        with session.begin():
            session.add(event)

    def update(self, event):
        session = self._engine_facade.get_session()
        with session.begin():
            session.merge(event)

    def query(self,
              event_id=None,
              collector_timestamp=None,
              payload=None,
              gt_collector_timestamp=None,
              lt_collector_timestamp=None):
        query = self.query_filter(
            models.Event,
            event_id=event_id,
            collector_timestamp=collector_timestamp,
            payload=payload)

        query = self._update_query_gt_lt(gt_collector_timestamp,
                                         lt_collector_timestamp,
                                         query)

        return query.all()

    @staticmethod
    def _update_query_gt_lt(gt_collector_timestamp,
                            lt_collector_timestamp,
                            query):
        if gt_collector_timestamp is not None:
            query = query.filter(models.Event.collector_timestamp >=
                                 gt_collector_timestamp)
        if lt_collector_timestamp is not None:
            query = query.filter(models.Event.collector_timestamp <=
                                 lt_collector_timestamp)
        return query

    def delete(self,
               event_id=None,
               collector_timestamp=None,
               payload=None,
               gt_collector_timestamp=None,
               lt_collector_timestamp=None):
        query = self.query_filter(
            models.Event,
            event_id=event_id,
            collector_timestamp=collector_timestamp,
            payload=payload)

        query = self._update_query_gt_lt(gt_collector_timestamp,
                                         lt_collector_timestamp,
                                         query)

        query.delete()
