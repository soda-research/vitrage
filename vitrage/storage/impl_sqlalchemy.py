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
        models.Base.metadata.create_all(engine, checkfirst=False)
        # TODO(ihefetz) upgrade logic is missing

    def disconnect(self):
        self._engine_facade.get_engine().dispose()

    def clear(self):
        engine = self._engine_facade.get_engine()
        for table in reversed(models.Base.metadata.sorted_tables):
            engine.execute(table.delete())
        engine.dispose()
