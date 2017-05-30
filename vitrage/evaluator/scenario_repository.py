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

from oslo_utils import uuidutils

from vitrage.evaluator.base import Template
from vitrage.evaluator.equivalence_repository import EquivalenceRepository
from vitrage.evaluator.template_data import TemplateData
from vitrage.evaluator.template_validation.template_content_validator import \
    content_validation
from vitrage.evaluator.template_validation.template_syntax_validator import \
    syntax_validation
from vitrage.utils import datetime as datetime_utils
from vitrage.utils import file as file_utils

LOG = log.getLogger(__name__)

EdgeKeyScenario = namedtuple('EdgeKeyScenario', ['label', 'source', 'target'])


class ScenarioRepository(object):
    def __init__(self, conf):
        self._templates = {}
        self.entity_equivalences = EquivalenceRepository().load_files(
            conf.evaluator.equivalences_dir)
        self.relationship_scenarios = defaultdict(list)
        self.entity_scenarios = defaultdict(list)
        self._load_templates_files(conf)

    @property
    def templates(self):
        return self._templates

    @templates.setter
    def templates(self, templates):
        self._templates = templates

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

        current_time = datetime_utils.utcnow()

        result = syntax_validation(template_def)
        if not result.is_valid_config:
            LOG.info('Unable to load template: %s' % result.comment)
        else:
            result = content_validation(template_def)
            if not result.is_valid_config:
                LOG.info('Unable to load template: %s' % result.comment)

        template_uuid = uuidutils.generate_uuid()
        self.templates[str(template_uuid)] = Template(template_uuid,
                                                      template_def,
                                                      current_time,
                                                      result)
        if result.is_valid_config:
            template_data = TemplateData(template_def)
            for scenario in template_data.scenarios:
                for equivalent_scenario in self._expand_equivalence(scenario):
                    self._add_scenario(equivalent_scenario)

    def _expand_equivalence(self, scenario):
        equivalent_scenarios = [scenario]
        for symbol_name, entity in scenario.entities.items():
            entity_key = frozenset(entity.properties.items())
            if entity_key not in self.entity_equivalences:
                continue
            equivalent_scenarios = self._expand_on_symbol(
                equivalent_scenarios,
                symbol_name,
                self.entity_equivalences[entity_key] - {entity_key})
        return equivalent_scenarios

    @staticmethod
    def _expand_on_symbol(scenarios_in, symbol_name, entity_keys):
        scenarios_out = list(scenarios_in)
        for entity_key in entity_keys:
            for scenario in scenarios_in:
                equivalent_scenario = TemplateData.ScenarioData.\
                    build_equivalent_scenario(scenario,
                                              symbol_name,
                                              entity_key)
                scenarios_out.append(equivalent_scenario)
        return scenarios_out

    def _add_scenario(self, scenario):
        for entity in scenario.entities.values():
            self._add_entity_scenario(scenario, entity)
        for relationship in scenario.relationships.values():
            self._add_relationship_scenario(scenario, relationship)

    def _load_templates_files(self, conf):

        templates_dir = conf.evaluator.templates_dir
        template_defs = file_utils.load_yaml_files(templates_dir)

        for template_def in template_defs:
            self.add_template(template_def)

    @staticmethod
    def _create_scenario_key(properties):
        return frozenset(properties)

    def _add_relationship_scenario(self, scenario, edge_desc):

        key = self._create_edge_scenario_key(edge_desc)
        self.relationship_scenarios[key].append((edge_desc, scenario))

    @staticmethod
    def _create_edge_scenario_key(edge_desc):
        return EdgeKeyScenario(edge_desc.edge.label,
                               frozenset(edge_desc.source.properties.items()),
                               frozenset(edge_desc.target.properties.items()))

    def _add_entity_scenario(self, scenario, entity):

        key = frozenset(list(entity.properties.items()))
        self.entity_scenarios[key].append((entity, scenario))
