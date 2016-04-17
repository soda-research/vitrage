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

from oslo_log import log
from six.moves import reduce
from vitrage.common.constants import edge_labels
from vitrage.common.constants import entities_categories
from vitrage.evaluator.actions.base import ActionType
from vitrage.evaluator.actions.base import actionTypes
from vitrage.evaluator.template import Template
from vitrage.evaluator.template_fields import TemplateFields

LOG = log.getLogger(__name__)


def content_validation(template):

    template_definitions = template[TemplateFields.DEFINITIONS]

    entity_ids = []
    for entity in template_definitions[TemplateFields.ENTITIES]:

        entity_vals = entity[TemplateFields.ENTITY]
        if not validate_entity_definition(entity_vals, entity_ids):
            return False
        entity_ids.append(entity_vals[TemplateFields.TEMPLATE_ID])

    relationship_ids = []
    for relationship in template_definitions[TemplateFields.RELATIONSHIPS]:

        relationship_vals = relationship[TemplateFields.RELATIONSHIP]

        if not validate_relationship(relationship_vals,
                                     relationship_ids,
                                     entity_ids):
            return False
        relationship_ids.append(relationship_vals[TemplateFields.TEMPLATE_ID])

    scenarios = template[TemplateFields.SCENARIOS]
    return validate_scenarios(scenarios, entity_ids, relationship_ids)


def validate_entity_definition(entity, entities_ids):

    category = entity[TemplateFields.CATEGORY]
    if category not in entities_categories:
        LOG.error('Invalid entity category: %s. Category must be from types: '
                  '%s' % (category, entities_categories))

    template_id = entity[TemplateFields.TEMPLATE_ID]
    if template_id in entities_ids:
        LOG.error('Duplicate template_id definition. template id: %s is '
                  'not unique.' % template_id)
        return False

    return True


def validate_relationship(relationship, relationships_ids, entities_ids):

    template_id = relationship[TemplateFields.TEMPLATE_ID]
    if template_id in (entities_ids or relationships_ids):
        LOG.error('Duplicate template_id definition. template id: %s is not '
                  'unique.' % template_id)
        return False

    relationship_type = relationship[TemplateFields.RELATIONSHIP_TYPE]
    if relationship_type not in edge_labels:
        LOG.error('Invalid relation type: %s. Action type must be from types: '
                  '%s' % (relationship_type, edge_labels))
        return False

    target = relationship[TemplateFields.TARGET]
    source = relationship[TemplateFields.SOURCE]

    return validate_template_id(entities_ids,
                                target) and validate_template_id(entities_ids,
                                                                 source)


def validate_scenarios(scenarios, entities_id, relationship_ids):

    for scenario in scenarios:

        scenario_values = scenario[TemplateFields.SCENARIO]

        condition = scenario_values[TemplateFields.CONDITION]
        if not validate_scenario_condition(condition, relationship_ids):
            return False

        actions = scenario_values[TemplateFields.ACTIONS]
        return validate_scenario_actions(actions, entities_id)


def validate_scenario_condition(condition, template_ids):

    try:
        Template.convert_to_dnf_format(condition)
    except Exception:
        LOG.error('Failed to convert condition: "%s" to DNF format'
                  % condition)
        return False

    values_to_replace = ' and ', ' or ', ' not ', '(', ')'
    condition = reduce(lambda cond, v: cond.replace(v, ' '),
                       values_to_replace,
                       condition)

    for condition_var in condition.split(' '):
        if not validate_template_id(template_ids, condition_var):
            return False

    return True


def validate_scenario_actions(actions, entities_ids):

    for action in actions:
        action_vals = action[TemplateFields.ACTION]
        if not validate_scenario_action(action_vals, entities_ids):
            return False

    return True


def validate_scenario_action(action, entities_ids):

    action_type = action[TemplateFields.ACTION_TYPE]

    if action_type == ActionType.RAISE_ALARM:
        return validate_raise_alarm_action(action, entities_ids)
    elif action_type == ActionType.SET_STATE:
        return validate_set_state_action(action, entities_ids)
    elif action_type == ActionType.ADD_CAUSAL_RELATIONSHIP:
        return validate_add_causal_relationship_action(action, entities_ids)
    else:
        LOG.error('Invalid action type: %s. Action type must be from types: %s'
                  % (action_type, actionTypes))
        return False


def validate_raise_alarm_action(action, entities_ids):

    properties = action[TemplateFields.PROPERTIES]

    if TemplateFields.ALARM_NAME not in properties:
        LOG.error('raise_alarm action must contain alarm_name field in '
                  'properties block.')
        return False

    if TemplateFields.SEVERITY not in properties:
        LOG.error('raise_alarm action must contain severity field in '
                  'properties block.')
        return False

    action_target = action[TemplateFields.ACTION_TARGET]
    if TemplateFields.TARGET not in action_target:
        LOG.error('raise_alarm action must have target definition')
    validate_template_id(entities_ids, action_target[TemplateFields.TARGET])

    return True


def validate_set_state_action(action, entities_ids):

    properties = action[TemplateFields.PROPERTIES]

    if TemplateFields.STATE not in properties:
        LOG.error('set_state action must contain state field in properties '
                  'block.')
        return False

    action_target = action[TemplateFields.ACTION_TARGET]
    if TemplateFields.TARGET not in action_target:
        LOG.error('set_state action must have target definition')
        return False

    target = action_target[TemplateFields.TARGET]
    return validate_template_id(entities_ids, target)


def validate_add_causal_relationship_action(action, entities_ids):

    action_target = action[TemplateFields.ACTION_TARGET]

    if TemplateFields.TARGET not in action_target:
        LOG.error('add_causal_relationship action must have target definition')
        return False

    target = action_target[TemplateFields.TARGET]
    if not validate_template_id(entities_ids, target):
        return False

    if TemplateFields.SOURCE not in action_target:
        LOG.error('add_causal_relationship action must have source definition')
        return False

    source = action_target[TemplateFields.SOURCE]
    return validate_template_id(entities_ids, source)


def validate_template_id(ids, id_to_check):

    if id_to_check not in ids:
        LOG.error('Invalid id: %s. The id does not appear in the definition '
                  'block.' % id_to_check)
        return False

    return True
