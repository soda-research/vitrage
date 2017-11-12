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

from oslo_db.sqlalchemy import models

from sqlalchemy import Column, String, SmallInteger, BigInteger, Index
from sqlalchemy.ext.declarative import declarative_base


class VitrageBase(models.TimestampMixin, models.ModelBase):
    """Base class for Vitrage Models."""
    __table_args__ = {'mysql_charset': "utf8",
                      'mysql_engine': "InnoDB"}
    __table_initialized__ = False

    def __setitem__(self, key, value):
        setattr(self, key, value)

    def __getitem__(self, key):
        return getattr(self, key)

    def update(self, values):
        """Make the model object behave like a dict."""
        for k, v in values.items():
            setattr(self, k, v)


Base = declarative_base(cls=VitrageBase)


class ActiveAction(Base):
    __tablename__ = 'active_actions'
    __table_args__ = (
        # Index 'ix_active_action' on fields:
        # action_type, extra_info, source_vertex_id, target_vertex_id
        Index('ix_active_action', 'action_type', 'extra_info',
              'source_vertex_id', 'target_vertex_id'),
    )

    action_type = Column(String(128))
    extra_info = Column(String(128))
    source_vertex_id = Column(String(128))
    target_vertex_id = Column(String(128))
    action_id = Column(String(128), primary_key=True)
    score = Column(SmallInteger())
    trigger = Column(BigInteger(), primary_key=True)

    def __repr__(self):
        return \
            "<ActiveAction(" \
            "created_at='%s', " \
            "action_type='%s', " \
            "extra_info='%s', " \
            "source_vertex_id='%s', " \
            "target_vertex_id='%s', " \
            "action_id='%s', " \
            "score='%s', " \
            "trigger='%s')>" %\
            (
                self.created_at,
                self.action_type,
                self.extra_info,
                self.source_vertex_id,
                self.target_vertex_id,
                self.action_id,
                self.score,
                self.trigger
            )
