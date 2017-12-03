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

from oslo_log import log

from vitrage.evaluator.template_fields import TemplateFields
from vitrage.evaluator.template_validation.content.base import \
    get_content_correct_result
from vitrage.evaluator.template_validation.content.definitions_validator \
    import DefinitionsValidator as DefValidator
from vitrage.evaluator.template_validation.content.scenario_validator import \
    ScenarioValidator

LOG = log.getLogger(__name__)


def content_validation(template, def_templates=None):

    if def_templates is None:
        def_templates = {}

    result = get_content_correct_result()
    entities_index = {}
    template_definitions = {}

    if TemplateFields.DEFINITIONS in template:
        template_definitions = template[TemplateFields.DEFINITIONS]

        if TemplateFields.ENTITIES in template_definitions:
            entities = template_definitions[TemplateFields.ENTITIES]
            result = DefValidator.validate_entities_definition(entities,
                                                               entities_index)

    # If there are duplicate definitions in several includes under the same
    # name, will regard the first one
    if result.is_valid_config and TemplateFields.INCLUDES in template:
        template_includes = template[TemplateFields.INCLUDES]
        result = \
            DefValidator.validate_definitions_with_includes(template_includes,
                                                            def_templates,
                                                            entities_index)

    relationship_index = {}

    if result.is_valid_config and \
            TemplateFields.RELATIONSHIPS in template_definitions:
        relationships = template_definitions[TemplateFields.RELATIONSHIPS]
        result = \
            DefValidator.validate_relationships_definitions(relationships,
                                                            relationship_index,
                                                            entities_index)

    if result.is_valid_config and TemplateFields.INCLUDES in template:
        template_includes = template[TemplateFields.INCLUDES]
        result = DefValidator.validate_relationships_definitions_with_includes(
            template_includes,
            def_templates,
            entities_index,
            relationship_index)

    if result.is_valid_config:
        scenarios = template[TemplateFields.SCENARIOS]
        definitions_index = entities_index.copy()
        definitions_index.update(relationship_index)
        result = ScenarioValidator(definitions_index).validate(scenarios)

    return result
