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


LOG = log.getLogger(__name__)


MANDATORY_SECTIONS_ERROR = '"definitions", "metadata" and "scenarios are ' \
                           'mandatory sections in template file.'
ELEMENTS_MIN_NUM_ERROR = 'At least one %s must be defined.'
DICT_STRUCTURE_SCHEMA_ERROR = '%s must refer to dictionary.'
SCHEMA_CONTENT_ERROR = '%s must contain %s Fields.'


RESULT_DESCRIPTION = 'description'
RESULT_STATUS = 'status'
RESULT_COMMENT = 'comment'


def syntax_validation(template_conf):

    result = {
        RESULT_DESCRIPTION: 'template syntax validation',
        RESULT_STATUS: True,
        RESULT_COMMENT: 'Template syntax is OK'
    }

    validate_template_sections(template_conf, result)

    if result[RESULT_STATUS]:
        metadata = template_conf[TemplateFields.METADATA]
        validate_metadata_section(metadata, result)

    if result[RESULT_STATUS]:
        definitions = template_conf[TemplateFields.DEFINITIONS]
        validate_definitions_section(definitions, result)

    if result[RESULT_STATUS]:
        scenarios = template_conf[TemplateFields.SCENARIOS]
        validate_scenarios_section(scenarios, result)

    return result


def validate_template_sections(template_conf, result):

    schema = Schema({
        Required(TemplateFields.DEFINITIONS): dict,
        Required(TemplateFields.METADATA): dict,
        Required(TemplateFields.SCENARIOS): list
    })
    _validate_dict_schema(schema,
                          template_conf,
                          MANDATORY_SECTIONS_ERROR,
                          result)


def validate_metadata_section(metadata, result):

    schema = Schema({
        Required(TemplateFields.ID): Any(str, six.text_type),
        TemplateFields.DESCRIPTION: Any(str, six.text_type)
    })

    error_msg = SCHEMA_CONTENT_ERROR % (
        TemplateFields.METADATA, TemplateFields.ID)
    _validate_dict_schema(schema, metadata, error_msg, result)


def validate_definitions_section(definitions, result):

    schema = Schema({
        Required(TemplateFields.ENTITIES): list,
        TemplateFields.RELATIONSHIPS: list
    })

    error_msg = SCHEMA_CONTENT_ERROR % (
        TemplateFields.DEFINITIONS,
        '"%s"' % TemplateFields.ENTITIES
    )
    _validate_dict_schema(schema, definitions, error_msg, result)

    if result[RESULT_STATUS]:
        validate_entities(definitions[TemplateFields.ENTITIES], result)

        relationships = definitions.get(TemplateFields.RELATIONSHIPS, None)
        if result[RESULT_STATUS] and relationships:
            validate_relationships(relationships, result)


def validate_entities(entities, result):

    if len(entities) <= 0:
        error_msg = ELEMENTS_MIN_NUM_ERROR % TemplateFields.ENTITY
        LOG.error(error_msg)
        _update_result(result, error_msg)

    if result[RESULT_STATUS]:

        for entity in entities:

            schema = Schema({
                Required(TemplateFields.ENTITY): dict,
            })

            error_msg = DICT_STRUCTURE_SCHEMA_ERROR % TemplateFields.ENTITY
            _validate_dict_schema(schema, entity, error_msg, result)

            if result[RESULT_STATUS]:
                validate_entity_dict(entity[TemplateFields.ENTITY], result)


def validate_entity_dict(entity_dict, result):

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
    _validate_dict_schema(schema, entity_dict, error_msg, result)


def validate_relationships(relationships, result):

    for relationship in relationships:

        schema = Schema({
            Required(TemplateFields.RELATIONSHIP): dict,
        })
        error_msg = DICT_STRUCTURE_SCHEMA_ERROR % TemplateFields.RELATIONSHIP
        _validate_dict_schema(schema, relationship, error_msg, result)

        if result[RESULT_STATUS]:
            relationship_dict = relationship[TemplateFields.RELATIONSHIP]
            validate_relationship_dict(relationship_dict, result)


def validate_relationship_dict(relationship_dict, result):

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
    _validate_dict_schema(schema, relationship_dict, error_msg, result)


def validate_scenarios_section(scenarios, result):

    if len(scenarios) <= 0:
        error_msg = ELEMENTS_MIN_NUM_ERROR % TemplateFields.SCENARIO
        LOG.error(error_msg)
        _update_result(result, error_msg)

    if result[RESULT_STATUS]:
        for scenario in scenarios:

            schema = Schema({
                Required(TemplateFields.SCENARIO): dict,
            })
            error_msg = DICT_STRUCTURE_SCHEMA_ERROR % TemplateFields.SCENARIO
            _validate_dict_schema(schema, scenario, error_msg, result)

            if result[RESULT_STATUS]:
                validate_scenario(scenario[TemplateFields.SCENARIO], result)


def validate_scenario(scenario, result):

    schema = Schema({
        Required(TemplateFields.CONDITION): Any(str, six.text_type),
        Required(TemplateFields.ACTIONS): list
    })

    error_msg = SCHEMA_CONTENT_ERROR % (
        TemplateFields.SCENARIOS,
        '"%s" and "%s"' % (TemplateFields.CONDITION, TemplateFields.ACTIONS)
    )
    _validate_dict_schema(schema, scenario, error_msg, result)

    if result[RESULT_STATUS]:
        validate_actions_schema(scenario[TemplateFields.ACTIONS], result)


def validate_actions_schema(actions, result):

    if len(actions) <= 0:
        error_msg = ELEMENTS_MIN_NUM_ERROR % TemplateFields.ACTION
        LOG.error(error_msg)
        _update_result(result, error_msg)

    for action in actions:

        schema = Schema({
            Required(TemplateFields.ACTION): dict,
        })
        error_msg = DICT_STRUCTURE_SCHEMA_ERROR % TemplateFields.ACTION
        _validate_dict_schema(schema, action, error_msg, result)

        if result[RESULT_STATUS]:
            validate_action_schema(action[TemplateFields.ACTION], result)


def validate_action_schema(action, result):

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
    _validate_dict_schema(schema, action, error_msg, result)


def _validate_dict_schema(schema, value, error_msg, result):

    try:
        schema(value)
    except Error as e:
        LOG.error('%s %s' % (error_msg, e))
        _update_result(result, error_msg)


def _update_result(result, comment):

    result[RESULT_STATUS] = False
    result[RESULT_COMMENT] = comment
