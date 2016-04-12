# Copyright 2015 - Nokia
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
import six

from oslo_log import log
from voluptuous import Any
from voluptuous import Error
from voluptuous import Required
from voluptuous import Schema

from vitrage.evaluator.template_fields import TemplateFields


LOG = log.getLogger(__name__)


MANDATORY_SECTIONS_ERROR = '"definitions", "metadata" and "scenarios are ' \
                           'mandatory sections in template file.'
TEMPLATE_VALIDATION_ERROR = 'Template validation failure.'
ELEMENTS_MIN_NUM_ERROR = 'At least one %s must be defined.'
DICT_STRUCTURE_SCHEMA_ERROR = '%s must refer to dictionary.'
SCHEMA_CONTENT_ERROR = '%s must contain %s Fields.'


def syntax_valid(template_conf):

    is_valid = validate_template_sections(template_conf)

    if is_valid:
        is_metadata_valid = validate_metadata_section(
            template_conf[TemplateFields.METADATA])
        is_defs_valid = validate_definitions_section(
            template_conf[TemplateFields.DEFINITIONS])
        is_scenarios_valid = validate_scenarios_section(
            template_conf[TemplateFields.SCENARIOS])

        return is_metadata_valid and is_defs_valid and is_scenarios_valid

    return False


def validate_template_sections(template_conf):

    schema = Schema({
        Required(TemplateFields.DEFINITIONS): dict,
        Required(TemplateFields.METADATA): dict,
        Required(TemplateFields.SCENARIOS): list
    })
    return _validate_dict_schema(
        schema, template_conf, MANDATORY_SECTIONS_ERROR)


def validate_metadata_section(metadata):

    schema = Schema({
        Required(TemplateFields.ID): Any(str, six.text_type),
        TemplateFields.DESCRIPTION: Any(str, six.text_type)
    })

    error_msg = SCHEMA_CONTENT_ERROR % (
        TemplateFields.METADATA, TemplateFields.ID)
    return _validate_dict_schema(schema, metadata, error_msg)


def validate_definitions_section(definitions):

    schema = Schema({
        Required(TemplateFields.ENTITIES): list,
        TemplateFields.RELATIONSHIPS: list
    })

    error_msg = SCHEMA_CONTENT_ERROR % (
        TemplateFields.DEFINITIONS,
        '"%s"' % TemplateFields.ENTITIES
    )
    is_defs_valid = _validate_dict_schema(schema, definitions, error_msg)

    if is_defs_valid:
        is_entities_valid = validate_entities(
            definitions[TemplateFields.ENTITIES]
        )

        relationships = definitions.get(TemplateFields.RELATIONSHIPS, None)
        is_relationships_valid = True
        if relationships:
            is_relationships_valid = validate_relationships(relationships)

        return is_relationships_valid and is_entities_valid

    return False


def validate_entities(entities):

    if len(entities) <= 0:
        error_msg = ELEMENTS_MIN_NUM_ERROR % TemplateFields.ENTITY
        LOG.error(_build_error_message(error_msg))
        return False

    for entity in entities:

        try:
            Schema({
                Required(TemplateFields.ENTITY): dict,
            })(entity)
        except Error as e:
            error_msg = DICT_STRUCTURE_SCHEMA_ERROR % TemplateFields.ENTITY
            LOG.error(_build_error_message(error_msg, e))
            return False

        return validate_entity(entity[TemplateFields.ENTITY])


def validate_entity(entity):

    schema = Schema({
        Required(TemplateFields.CATEGORY): Any(str, six.text_type),
        TemplateFields.TYPE: Any(str, six.text_type),
        Required(TemplateFields.TEMPLATE_ID): Any(str, six.text_type, int)
    }, extra=True)
    error_msg = SCHEMA_CONTENT_ERROR % (
        TemplateFields.ENTITY,
        '"%s" and "%s"' % (TemplateFields.CATEGORY, TemplateFields.TEMPLATE_ID)
    )
    return _validate_dict_schema(schema, entity, error_msg)


def validate_relationships(relationships):

    for relationship in relationships:

        try:
            Schema({
                Required(TemplateFields.RELATIONSHIP): dict,
            })(relationship)
        except Error as e:
            error_msg = DICT_STRUCTURE_SCHEMA_ERROR % (
                TemplateFields.RELATIONSHIP
            )
            LOG.error(_build_error_message(error_msg, e))
            return False

        return validate_relationship(relationship[TemplateFields.RELATIONSHIP])


def validate_relationship(relationship):

    schema = Schema({
        Required(TemplateFields.SOURCE): Any(str, six.text_type, int),
        Required(TemplateFields.TARGET): Any(str, six.text_type, int),
        TemplateFields.RELATIONSHIP_TYPE: Any(str, six.text_type),
        Required(TemplateFields.TEMPLATE_ID): Any(str, six.text_type, int)
    })

    error_msg = SCHEMA_CONTENT_ERROR % (
        TemplateFields.RELATIONSHIP, '"%s", "%s" and "%s"' % (
            TemplateFields.SOURCE,
            TemplateFields.TARGET,
            TemplateFields.RELATIONSHIP_TYPE
        )
    )
    return _validate_dict_schema(schema, relationship, error_msg)


def validate_scenarios_section(scenarios):

    if len(scenarios) <= 0:
        error_msg = ELEMENTS_MIN_NUM_ERROR % TemplateFields.SCENARIOS
        LOG.error(_build_error_message(error_msg))
        return False

    for scenario in scenarios:

        try:
            Schema({
                Required(TemplateFields.SCENARIO): dict,
            })(scenario)
        except Error as e:
            error_msg = DICT_STRUCTURE_SCHEMA_ERROR % TemplateFields.SCENARIO
            LOG.error(_build_error_message(error_msg, e))
            return False

        is_valid = validate_scenario(scenario[TemplateFields.SCENARIO])
        if not is_valid:
            return False

    return True


def validate_scenario(scenario):

    schema = Schema({
        Required(TemplateFields.CONDITION): Any(str, six.text_type),
        Required(TemplateFields.ACTIONS): list
    })

    error_msg = SCHEMA_CONTENT_ERROR % (
        TemplateFields.SCENARIOS,
        '"%s" and "%s"' % (TemplateFields.CONDITION, TemplateFields.ACTIONS)
    )
    is_scenario_valid = _validate_dict_schema(
        schema, scenario, error_msg)

    if is_scenario_valid:
        return validate_actions_schema(scenario[TemplateFields.ACTIONS])

    return False


def validate_actions_schema(actions):

    if len(actions) <= 0:
        error_message = ELEMENTS_MIN_NUM_ERROR % TemplateFields.ACTION
        LOG.error(_build_error_message(error_message))
        return False

    for action in actions:

        try:
            Schema({
                Required(TemplateFields.ACTION): dict,
            })(action)
        except Error as e:
            msg = DICT_STRUCTURE_SCHEMA_ERROR % TemplateFields.ACTION
            LOG.error(_build_error_message(msg, e))
            return False

        is_action_valid = validate_action_schema(action[TemplateFields.ACTION])
        if not is_action_valid:
            return False

    return True


def validate_action_schema(action):

    schema = Schema({
        Required(TemplateFields.ACTION_TYPE): Any(str, six.text_type),
        TemplateFields.PROPERTIES: dict,
        Required(TemplateFields.ACTION_TARGET): dict
    })

    error_msg = SCHEMA_CONTENT_ERROR % (
        TemplateFields.ACTION,
        '"%s" and "%s"' % (
            TemplateFields.ACTION_TYPE,
            TemplateFields.ACTION_TARGET
        )
    )
    return _validate_dict_schema(schema, action, error_msg)


def _build_error_message(message, e=None):

    if e:
        return '%s %s %s' % (TEMPLATE_VALIDATION_ERROR, message, e)
    else:
        return '%s %s' % (TEMPLATE_VALIDATION_ERROR, message)


def _validate_dict_schema(schema, value, error_message):

    try:
        schema(value)
    except Error as e:
        LOG.error(_build_error_message(error_message, e))
        return False

    return True
