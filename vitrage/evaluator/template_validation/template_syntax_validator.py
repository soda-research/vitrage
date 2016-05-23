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
import re
import six

from oslo_log import log
from voluptuous import All
from voluptuous import Any
from voluptuous import Error
from voluptuous import Invalid
from voluptuous import Required
from voluptuous import Schema

from vitrage.evaluator.template_fields import TemplateFields
from vitrage.evaluator.template_validation.error_messages import error_msgs
from vitrage.evaluator.template_validation.utils import Result

LOG = log.getLogger(__name__)


RESULT_DESCRIPTION = 'Template syntax validation'
CORRECT_RESULT_MESSAGE = 'Template syntax is OK'


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
        Required(TemplateFields.DEFINITIONS, msg=error_msgs[21]): dict,
        Required(TemplateFields.METADATA, msg=error_msgs[62]): dict,
        Required(TemplateFields.SCENARIOS, msg=error_msgs[80]): list
    })
    return _validate_dict_schema(schema, template_conf)


def validate_metadata_section(metadata):

    any_str = Any(str, six.text_type)

    schema = Schema({
        Required(TemplateFields.ID, msg=error_msgs[60]): any_str,
        TemplateFields.DESCRIPTION: any_str
    })
    return _validate_dict_schema(schema, metadata)


def validate_definitions_section(definitions):

    schema = Schema({
        Required(TemplateFields.ENTITIES, error_msgs[20]): list,
        TemplateFields.RELATIONSHIPS: list
    })
    result = _validate_dict_schema(schema, definitions)

    if result.is_valid:
        result = validate_entities(definitions[TemplateFields.ENTITIES])

        relationships = definitions.get(TemplateFields.RELATIONSHIPS, None)
        if result.is_valid and relationships:
            return validate_relationships(relationships)

    return result


def validate_entities(entities):

    if not entities:
        LOG.error(error_msgs[43])
        return _get_fault_result(error_msgs[43])

    for entity in entities:

        schema = Schema({
            Required(TemplateFields.ENTITY, msg=error_msgs[46]): dict,
        })
        result = _validate_dict_schema(schema, entity)

        if result.is_valid:
            result = validate_entity_dict(entity[TemplateFields.ENTITY])

        if not result.is_valid:
            return result

    return result


def validate_entity_dict(entity_dict):

    any_str = Any(str, six.text_type)
    schema = Schema({
        Required(TemplateFields.CATEGORY, msg=error_msgs[42]): any_str,
        TemplateFields.TYPE: any_str,
        Required(TemplateFields.TEMPLATE_ID, msg=error_msgs[41]):
            All(_validate_template_id_value())
    }, extra=True)

    return _validate_dict_schema(schema, entity_dict)


def validate_relationships(relationships):

    for relationship in relationships:

        schema = Schema({
            Required(TemplateFields.RELATIONSHIP, msg=error_msgs[101]): dict,
        })
        result = _validate_dict_schema(schema, relationship)

        if result.is_valid:
            relationship_dict = relationship[TemplateFields.RELATIONSHIP]
            result = validate_relationship_dict(relationship_dict)

            if not result.is_valid:
                return result
    return result


def validate_relationship_dict(relationship_dict):

    any_str = Any(str, six.text_type)
    schema = Schema({
        Required(TemplateFields.SOURCE, msg=error_msgs[102]): any_str,
        Required(TemplateFields.TARGET, msg=error_msgs[103]): any_str,
        TemplateFields.RELATIONSHIP_TYPE: Any(str, six.text_type),
        Required(TemplateFields.TEMPLATE_ID, msg=error_msgs[104]):
            All(_validate_template_id_value())
    })
    return _validate_dict_schema(schema, relationship_dict)


def validate_scenarios_section(scenarios):

    if not scenarios:
        LOG.error(error_msgs[81])
        return _get_fault_result(error_msgs[81])

    for scenario in scenarios:

        schema = Schema({
            Required(TemplateFields.SCENARIO, msg=error_msgs[82]): dict,
        })
        result = _validate_dict_schema(schema, scenario)

        if result.is_valid:
            result = validate_scenario(scenario[TemplateFields.SCENARIO])

            if not result.is_valid:
                return result

    return result


def validate_scenario(scenario):

    any_str = Any(str, six.text_type)
    schema = Schema({
        Required(TemplateFields.CONDITION, msg=error_msgs[83]): any_str,
        Required(TemplateFields.ACTIONS, msg=error_msgs[84]): list
    })
    result = _validate_dict_schema(schema, scenario)

    if result.is_valid:
        return validate_actions_schema(scenario[TemplateFields.ACTIONS])

    return result


def validate_actions_schema(actions):

    if not actions:
        LOG.error(error_msgs[121])
        return _get_fault_result(error_msgs[121])

    for action in actions:

        schema = Schema({
            Required(TemplateFields.ACTION, msg=error_msgs[122]): dict,
        })
        result = _validate_dict_schema(schema, action)

        if result.is_valid:
            result = validate_action_schema(action[TemplateFields.ACTION])

        if not result.is_valid:
            return result

    return result


def validate_action_schema(action):

    any_str = Any(str, six.text_type)
    schema = Schema({
        Required(TemplateFields.ACTION_TYPE, msg=error_msgs[123]): any_str,
        TemplateFields.PROPERTIES: dict,
        Required(TemplateFields.ACTION_TARGET, msg=error_msgs[124]): dict
    })
    return _validate_dict_schema(schema, action)


def _validate_dict_schema(schema, value):

    try:
        schema(value)
    except Error as e:
        LOG.error(e)
        return _get_fault_result(e)

    return _get_correct_result()


def _get_fault_result(comment):
    return Result(RESULT_DESCRIPTION, False, comment)


def _get_correct_result():
    return Result(RESULT_DESCRIPTION, True, 'Template syntax is OK')


def _validate_template_id_value(msg=None):
    def f(v):
        if re.match("_*[a-zA-Z]+\\w*", str(v)):
            return str(v)
        else:
            raise Invalid(msg or error_msgs[1])
    return f
