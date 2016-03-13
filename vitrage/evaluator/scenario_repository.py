# Copyright 2016 - Nokia
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
from collections import defaultdict
from collections import namedtuple
from oslo_log import log

from vitrage.common import file_utils
from vitrage.evaluator.template import RELATIONSHIP
from vitrage.evaluator.template import Template
from vitrage.evaluator.template_fields import TemplateFields
from vitrage.evaluator.template_syntax_validator import syntax_valid


LOG = log.getLogger(__name__)


EdgeKeyScenario = namedtuple('EdgeKeyScenario', ['label', 'source', 'target'])


class ScenarioRepository(object):

    def __init__(self, conf):
        self.templates = defaultdict(list)
        self.relationship_scenarios = defaultdict(list)
        self.entity_scenarios = defaultdict(list)
        self._load_templates_files(conf)

    def get_scenarios_by_vertex(self, vertex):

        entity_key = frozenset(vertex.properties.items())

        scenarios = []
        for scenario_key, value in self.entity_scenarios.items():
            if scenario_key.issubset(entity_key):
                scenarios += value
        return scenarios

    def get_scenarios_by_edge(self, edge_description):

        key = self._create_edge_scenario_key(edge_description)
        scenarios = []

        for scenario_key, value in self.relationship_scenarios.items():

            check_label = key.label == scenario_key.label
            check_source_issubset = scenario_key.source.issubset(key.source)
            check_target_issubset = scenario_key.target.issubset(key.target)

            if check_label and check_source_issubset and check_target_issubset:
                scenarios += value

        return scenarios

    def add_template(self, template_def):

        if syntax_valid(template_def):
            template = Template(template_def)
            self.templates[template.name] = template
            self._add_template_scenarios(template)
        else:
            metadata = template_def.get(TemplateFields.METADATA, None)
            if metadata:
                template_id = metadata.get(TemplateFields.ID, None)
                LOG.info('Unable to load template: %s' % template_id)
            else:
                LOG.info('Unable to load template with invalid metadata')

    def _load_templates_files(self, conf):

        templates_dir = conf.evaluator.templates_dir
        template_defs = file_utils.load_yaml_files(templates_dir)

        for template_def in template_defs:
            self.add_template(template_def)

    def _add_template_scenarios(self, template):
        for scenario in template.scenarios:
            self._handle_condition(scenario)

    def _handle_condition(self, scenario):
        for clause in scenario.condition:
            self._handle_clause(clause, scenario)

    def _handle_clause(self, clause, scenario):
        for condition_var in clause:
            if condition_var.type == RELATIONSHIP:
                edge_desc = condition_var.variable
                self._add_relationship(scenario, edge_desc)
                self._add_entity(scenario, edge_desc.source)
                self._add_entity(scenario, edge_desc.target)
            else:  # Entity
                self._add_entity(scenario, condition_var.variable)

    @staticmethod
    def _create_scenario_key(properties):
        return frozenset(properties)

    def _add_relationship(self, scenario, edge_desc):

        key = self._create_edge_scenario_key(edge_desc)
        scenarios = self.relationship_scenarios[key]

        if not self.contains(scenarios, scenario):
            self.relationship_scenarios[key].append((edge_desc, scenario))

    @staticmethod
    def _create_edge_scenario_key(edge_desc):

        return EdgeKeyScenario(edge_desc.edge.label,
                               frozenset(edge_desc.source.properties.items()),
                               frozenset(edge_desc.target.properties.items()))

    def _add_entity(self, scenario, entity):

        key = frozenset(list(entity.properties.items()))
        scenarios = self.entity_scenarios[key]

        if not self.contains(scenarios, scenario):
            self.entity_scenarios[key].append((entity, scenario))

    @staticmethod
    def contains(scenarios, scenario):
        return any(s[1].id == scenario.id for s in scenarios)
