# Copyright 2018 - Nokia
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
import os

from oslo_log import log
from oslo_utils import uuidutils

from vitrage.common.constants import TemplateStatus
from vitrage.common.constants import TemplateTypes as TType
from vitrage.common.exception import VitrageError
from vitrage.evaluator.base import Template
from vitrage.evaluator.template_fields import TemplateFields
from vitrage.evaluator import template_validation
from vitrage.evaluator.template_validation import base
from vitrage.evaluator.template_validation.template_syntax_validator import \
    EXCEPTION
from vitrage.storage.sqlalchemy import models
from vitrage.utils import file

LOG = log.getLogger(__name__)

METADATA = 'metadata'
NAME = 'name'


def add_template_to_db(db, path, template_type):
    """Add templates to db

    Loads template files, for every template, check it is valid and does
     not exist, if so adds it to the database.

    :param db:
    :param path: path to a file or directory
    :param template_type: standard/definition/equivalence
    :return: all the templates that were added
    :rtype: list of models.Template
    """

    added_rows = list()
    files = _list_files(path)
    for f in files:
        template = load_template_file(f)
        template_name = template[METADATA][NAME]

        templates = db.templates.query(name=template_name)
        if [t for t in templates if t.status != TemplateStatus.DELETED]:
            LOG.warning("Duplicate templates found %s."
                        " new template will not be added", template_name)
        else:
            validation_result = _validate_template(db, template, template_type)
            db_row = _to_db_row(validation_result, template, template_type)
            db.templates.create(db_row)
            added_rows.append(db_row)
    return added_rows


def _list_files(path):
    if os.path.isdir(path):
        LOG.info("Adding all templates from %s", path)
        return file.list_files(path, '.yaml', with_pathname=True)
    elif os.path.isfile(path):
        LOG.info("Adding template %s", path)
        return [path]  # only one file
    else:
        raise VitrageError("No such file or directory %s" % path)


def _validate_template(db, template, template_type):
    if template_type == TType.DEFINITION:
        result = template_validation.validate_definition_template(template)
    elif template_type == TType.STANDARD:
        result = template_validation.validate_template(template,
                                                       _load_def_templates(db))
    elif template_type == TType.EQUIVALENCE:
        result = base.Result("", True, "", "No Validation")
    else:
        raise VitrageError("Unknown template type %s", template_type)
    return result


def load_template_file(file_name):
    try:
        return file.load_yaml_file(file_name, with_exception=True)
    except Exception as e:
        return {TemplateFields.METADATA: {TemplateFields.NAME: file_name},
                EXCEPTION: str(e)}


def _to_db_row(result, template, template_type):
    uuid = uuidutils.generate_uuid()
    status = TemplateStatus.LOADING if result.is_valid_config else \
        TemplateStatus.ERROR
    status_details = result.comment
    db_row = models.Template(
        name=template[METADATA][NAME],
        uuid=uuid,
        status=status,
        status_details=status_details,
        file_content=template,
        template_type=template_type,
    )
    return db_row


def _load_def_templates(db):
    def_templates = {}
    items = db.templates.query(template_type=TType.DEFINITION)
    def_templates_db = [x for x in items if x.status in [
                        TemplateStatus.ACTIVE,
                        TemplateStatus.LOADING]]
    for df in def_templates_db:
        def_templates[df.uuid] = Template(df.uuid,
                                          df.file_content,
                                          df.created_at)
    return def_templates
