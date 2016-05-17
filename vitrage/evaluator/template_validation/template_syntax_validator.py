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
import six

from oslo_log import log
from voluptuous import Any
from voluptuous import Error
from voluptuous import Required
from voluptuous import Schema

from vitrage.evaluator.template_fields import TemplateFields
from vitrage.evaluator.template_validation.utils import Result

LOG = log.getLogger(__name__)


MANDATORY_SECTIONS_ERROR = '"definitions", "metadata" and "scenarios are ' \
                           'mandatory sections in template file.'
ELEMENTS_MIN_NUM_ERROR = 'At least one %s must be defined.'
DICT_STRUCTURE_SCHEMA_ERROR = '%s must refer to dictionary.'
SCHEMA_CONTENT_ERROR = '%s must contain %s Fields.'


RESULT_DESCRIPTION = 'template syntax validation'


def syntax_validation(template_conf):

    result = validate_template_sections(template_conf)

    if result.is_valid:
        metadata = template_conf[TemplateFields.METADATA]
        result = validate_metadata_section(metadata)

    if result.is_valid:
        definitions = template_conf[TemplateFields.DEFINITIONS]
        result = validate_definitions_section(definitions)

    if result.is_valid:
        scenarios = template_conf[TemplateFields.SCENARIOS]
        result = validate_scenarios_section(scenarios)

    return result


def validate_template_sections(template_conf):

    schema = Schema({
        Required(TemplateFields.DEFINITIONS): dict,
        Required(TemplateFields.METADATA): dict,
        Required(TemplateFields.SCENARIOS): list
    })
    return _validate_dict_schema(schema,
                                 template_conf,
                                 MANDATORY_SECTIONS_ERROR)


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
    result = _validate_dict_schema(schema, definitions, error_msg)

    if result.is_valid:
        result = validate_entities(definitions[TemplateFields.ENTITIES])

        relationships = definitions.get(TemplateFields.RELATIONSHIPS, None)
        if result.is_valid and relationships:
            return validate_relationships(relationships)

    return result


def validate_entities(entities):

    if len(entities) <= 0:
        error_msg = ELEMENTS_MIN_NUM_ERROR % TemplateFields.ENTITY
        LOG.error(error_msg)
        return _get_fault_result(error_msg)

    for entity in entities:

        schema = Schema({
            Required(TemplateFields.ENTITY): dict,
        })

        error_msg = DICT_STRUCTURE_SCHEMA_ERROR % TemplateFields.ENTITY
        result = _validate_dict_schema(schema, entity, error_msg)

        if result.is_valid:
            result = validate_entity_dict(entity[TemplateFields.ENTITY])

        if not result.is_valid:
            return result

    return result


def validate_entity_dict(entity_dict):

    schema = Schema({
        Required(TemplateFields.CATEGORY): Any(str, six.text_type),
        TemplateFields.TYPE: Any(str, six.text_type),
        Required(TemplateFields.TEMPLATE_ID): Any(str, six.text_type, int)
    }, extra=True)

    error_msg = SCHEMA_CONTENT_ERROR % (
        TemplateFields.ENTITY,
        '"%s" and "%s"' % (TemplateFields.CATEGORY,
                           TemplateFields.TEMPLATE_ID)
    )
    return _validate_dict_schema(schema, entity_dict, error_msg)


def validate_relationships(relationships):

    for relationship in relationships:

        schema = Schema({
            Required(TemplateFields.RELATIONSHIP): dict,
        })
        error_msg = DICT_STRUCTURE_SCHEMA_ERROR % TemplateFields.RELATIONSHIP
        result = _validate_dict_schema(schema, relationship, error_msg)

        if result.is_valid:
            relationship_dict = relationship[TemplateFields.RELATIONSHIP]
            result = validate_relationship_dict(relationship_dict)

            if not result.is_valid:
                return result

    return result


def validate_relationship_dict(relationship_dict):

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
            TemplateFields.TEMPLATE_ID
        )
    )
    return _validate_dict_schema(schema, relationship_dict, error_msg)


def validate_scenarios_section(scenarios):

    if len(scenarios) <= 0:
        error_msg = ELEMENTS_MIN_NUM_ERROR % TemplateFields.SCENARIO
        LOG.error(error_msg)
        return _get_fault_result(error_msg)

    for scenario in scenarios:

        schema = Schema({
            Required(TemplateFields.SCENARIO): dict,
        })
        error_msg = DICT_STRUCTURE_SCHEMA_ERROR % TemplateFields.SCENARIO
        result = _validate_dict_schema(schema, scenario, error_msg)

        if result.is_valid:
            result = validate_scenario(scenario[TemplateFields.SCENARIO])

            if not result.is_valid:
                return result

    return result


def validate_scenario(scenario):

    schema = Schema({
        Required(TemplateFields.CONDITION): Any(str, six.text_type),
        Required(TemplateFields.ACTIONS): list
    })

    error_msg = SCHEMA_CONTENT_ERROR % (
        TemplateFields.SCENARIOS,
        '"%s" and "%s"' % (TemplateFields.CONDITION, TemplateFields.ACTIONS)
    )
    result = _validate_dict_schema(schema, scenario, error_msg)

    if result.is_valid:
        return validate_actions_schema(scenario[TemplateFields.ACTIONS])

    return result


def validate_actions_schema(actions):

    if len(actions) <= 0:
        error_msg = ELEMENTS_MIN_NUM_ERROR % TemplateFields.ACTION
        LOG.error(error_msg)
        return _get_fault_result(error_msg)

    for action in actions:

        schema = Schema({
            Required(TemplateFields.ACTION): dict,
        })
        error_msg = DICT_STRUCTURE_SCHEMA_ERROR % TemplateFields.ACTION
        result = _validate_dict_schema(schema, action, error_msg)

        if result.is_valid:
            result = validate_action_schema(action[TemplateFields.ACTION])

        if not result.is_valid:
            return result

    return result


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


def _validate_dict_schema(schema, value, error_msg):

    try:
        schema(value)
    except Error as e:
        LOG.error('%s %s' % (error_msg, e))
        return _get_fault_result(error_msg)

    return _get_correct_result()


def _get_fault_result(comment):
    return Result(RESULT_DESCRIPTION, False, comment)


def _get_correct_result():
    return Result(RESULT_DESCRIPTION, True, 'Template syntax is OK')
