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

import itertools
from oslo_log import log

from oslo_utils import uuidutils

from vitrage.common.utils import get_portion
from vitrage.evaluator.base import Template
from vitrage.evaluator.equivalence_repository import EquivalenceRepository
from vitrage.evaluator.template_fields import TemplateFields
from vitrage.evaluator.template_loading.scenario_loader import ScenarioLoader
from vitrage.evaluator.template_loading.template_loader import TemplateLoader
from vitrage.evaluator.template_validation.content.base import \
    get_template_schema
from vitrage.evaluator.template_validation.content.template_content_validator \
    import content_validation
from vitrage.evaluator.template_validation.template_syntax_validator import \
    def_template_syntax_validation
from vitrage.evaluator.template_validation.template_syntax_validator import \
    EXCEPTION
from vitrage.evaluator.template_validation.template_syntax_validator import \
    syntax_validation
from vitrage.graph.filter import check_filter as check_subset
from vitrage.utils import datetime as datetime_utils
from vitrage.utils import file as file_utils

LOG = log.getLogger(__name__)

EdgeKeyScenario = namedtuple('EdgeKeyScenario', ['label', 'source', 'target'])
DEF_TEMPLATES_DIR_OPT = 'def_templates_dir'


class ScenarioRepository(object):
    def __init__(self, conf, worker_index=None, workers_num=None):
        """Create an instance of ScenarioRepository

        :param conf:
        :param worker_index: Index of the current evaluator worker
        :param workers_num: Total number of evaluator workers
        """
        self._templates = {}
        self._def_templates = {}
        self._all_scenarios = []
        self.entity_equivalences = EquivalenceRepository().load_files(
            conf.evaluator.equivalences_dir)
        self.relationship_scenarios = defaultdict(list)
        self.entity_scenarios = defaultdict(list)
        self._load_def_template_files(conf)
        self._load_templates_files(conf)
        self._enable_worker_scenarios(worker_index, workers_num)
        self.actions = self._create_actions_collection()

    @property
    def templates(self):
        return self._templates

    @property
    def def_templates(self):
        return self._def_templates

    @def_templates.setter
    def def_templates(self, def_templates):
        self._def_templates = def_templates

    @templates.setter
    def templates(self, templates):
        self._templates = templates

    def get_scenarios_by_vertex(self, vertex):

        entity_key = vertex.properties

        scenarios = []
        for scenario_key, value in self.entity_scenarios.items():
            if check_subset(entity_key, dict(scenario_key)):
                scenarios += [(e, s) for e, s in value if s.enabled]
        return scenarios

    def get_scenarios_by_edge(self, edge_description):

        key = self._create_edge_scenario_key(edge_description)
        scenarios = []

        for scenario_key, value in self.relationship_scenarios.items():

            check_label = key.label == scenario_key.label
            if check_label \
                    and check_subset(dict(key.source),
                                     dict(scenario_key.source)) \
                    and check_subset(dict(key.target),
                                     dict(scenario_key.target)):
                scenarios += [(e, s) for e, s in value if s.enabled]

        return scenarios

    def add_template(self, template_def):

        result = syntax_validation(template_def)

        if not result.is_valid_config:
            LOG.info('Unable to load template, syntax err: %s'
                     % result.comment)
        else:
            result = content_validation(template_def, self._def_templates)
            if not result.is_valid_config:
                LOG.info('Unable to load template, content err: %s'
                         % result.comment)

        template_uuid = uuidutils.generate_uuid()
        current_time = datetime_utils.utcnow()
        self.templates[str(template_uuid)] = Template(template_uuid,
                                                      template_def,
                                                      current_time,
                                                      result)
        if result.is_valid_config:
            template_data = \
                TemplateLoader().load(template_def, self._def_templates)
            for scenario in template_data.scenarios:
                for equivalent_scenario in self._expand_equivalence(scenario):
                    self._add_scenario(equivalent_scenario)

    def add_def_template(self, def_template):
        result, template_schema = get_template_schema(def_template)

        if result.is_valid_config:
            result = def_template_syntax_validation(def_template)
            if not result.is_valid_config:
                LOG.info('Unable to load definition template, syntax err: %s'
                         % result.comment)

        if result.is_valid_config:
            def_validator = \
                template_schema.validators.get(TemplateFields.DEFINITIONS)
            result = \
                def_validator.def_template_content_validation(def_template)

            if result.is_valid_config:
                current_time = datetime_utils.utcnow()
                include_uuid = uuidutils.generate_uuid()
                self._def_templates[str(include_uuid)] = Template(include_uuid,
                                                                  def_template,
                                                                  current_time,
                                                                  result)
            else:
                LOG.info('Unable to load definition template, content err: %s'
                         % result.comment)

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
                equivalent_scenario = \
                    ScenarioLoader.build_equivalent_scenario(scenario,
                                                             symbol_name,
                                                             entity_key)
                scenarios_out.append(equivalent_scenario)
        return scenarios_out

    def _add_scenario(self, scenario):
        for entity in scenario.entities.values():
            self._add_entity_scenario(scenario, entity)
        for relationship in scenario.relationships.values():
            self._add_relationship_scenario(scenario, relationship)
        self._all_scenarios.append(scenario)

    def _load_def_template_files(self, conf):

        if DEF_TEMPLATES_DIR_OPT in conf.evaluator:

            def_templates_dir = conf.evaluator.def_templates_dir
            def_templates = file_utils.load_yaml_files(def_templates_dir)

            for def_template in def_templates:
                self.add_def_template(def_template)

    def _load_templates_files(self, conf):

        templates_dir = conf.evaluator.templates_dir

        files = \
            file_utils.list_files(templates_dir, '.yaml', with_pathname=True)

        template_defs = []
        for f in files:
            template_defs.append(self._load_template_file(f))

        for template_def in template_defs:
            self.add_template(template_def)

    @staticmethod
    def _load_template_file(file_name):
        try:
            config = file_utils.load_yaml_file(file_name,
                                               with_exception=True)
            if config:
                return config
        except Exception as e:
            return {TemplateFields.METADATA: {TemplateFields.NAME: file_name},
                    EXCEPTION: str(e)}

    @staticmethod
    def _create_scenario_key(properties):
        return frozenset(properties)

    def _add_relationship_scenario(self, scenario, edge_desc):

        key = self._create_edge_scenario_key(edge_desc)
        self.relationship_scenarios[key].append((edge_desc, scenario))

    @staticmethod
    def _create_edge_scenario_key(edge_desc):
        try:
            source_set = frozenset(edge_desc.source.properties.items())
            target_set = frozenset(edge_desc.target.properties.items())
        except Exception as e:
            LOG.error('frozenset for edge failed - Source:%s Target:%s',
                      str(edge_desc.source),
                      str(edge_desc.target))
            raise e
        return EdgeKeyScenario(edge_desc.edge.label, source_set, target_set)

    def _add_entity_scenario(self, scenario, entity):

        key = frozenset(list(entity.properties.items()))
        self.entity_scenarios[key].append((entity, scenario))

    def _enable_worker_scenarios(self, worker_ind, n):
        """Enable a portion of the scenarios"""
        self._all_scenarios.sort(key=lambda scenario: scenario.id)

        scenarios = self._all_scenarios if \
            worker_ind is None or n is None else\
            get_portion(self._all_scenarios, n, worker_ind)
        for s in scenarios:
            s.enabled = True

    def _create_actions_collection(self):
        action_lists = (s.actions for s in self._all_scenarios)
        actions = (a for a in itertools.chain(*action_lists))
        return {a.id: a for a in actions}

    def log_enabled_scenarios(self):
        scenarios = [s for s in self._all_scenarios if s.enabled]
        LOG.info("Scenarios:\n%s", sorted([s.id for s in scenarios]))
