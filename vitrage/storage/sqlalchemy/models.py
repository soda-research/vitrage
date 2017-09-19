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

import six
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
        for k, v in six.iteritems(values):
            setattr(self, k, v)


Base = declarative_base(cls=VitrageBase)
