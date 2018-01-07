# Copyright 2017 - Nokia
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
from oslo_db.options import database_opts

from vitrage.common.constants import TemplateStatus
from vitrage.common.constants import TemplateTypes as TType
from vitrage.evaluator.template_db.template_repository import \
    add_template_to_db
from vitrage import storage
from vitrage.storage.sqlalchemy import models

TEMPLATE_DIR = '/etc/vitrage/templates'


class TestConfiguration(object):

    @classmethod
    def add_db(cls, conf):
        conf.register_opts(database_opts, group='database')
        db_name = "sqlite:///test_%s.db" % cls.__name__
        conf.set_override('connection', db_name, group='database')
        cls._db = storage.get_connection_from_config(conf)
        engine = cls._db._engine_facade.get_engine()
        models.Base.metadata.drop_all(engine)
        models.Base.metadata.create_all(engine)
        return cls._db

    @classmethod
    def add_templates(cls, templates_dir, templates_type=TType.STANDARD):
        templates = add_template_to_db(cls._db, templates_dir, templates_type)
        for t in templates:
            if t.status == TemplateStatus.LOADING:
                cls._db.templates.update(t.uuid, 'status',
                                         TemplateStatus.ACTIVE)
            if t.status == TemplateStatus.DELETING:
                cls._db.templates.update(t.uuid, 'status',
                                         TemplateStatus.DELETED)
        return templates
