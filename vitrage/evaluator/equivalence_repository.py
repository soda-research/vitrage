# Copyright 2017 - ZTE Corporation
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

from vitrage.common.exception import VitrageError
from vitrage.evaluator.equivalence_data import EquivalenceData
from vitrage.utils import file as file_utils


class EquivalenceRepository(object):
    def __init__(self):
        self.entity_equivalences = {}

    def load_files(self, directory):
        equivalence_defs = file_utils.load_yaml_files(directory)

        for equivalence_def in equivalence_defs:
            equivalence_data = EquivalenceData(equivalence_def)
            for equivalence in equivalence_data.equivalences:
                self._add_equivalence(equivalence)
        return self.entity_equivalences

    def _add_equivalence(self, equivalence):
        for entity in equivalence:
            if entity in self.entity_equivalences:
                # TODO(yujunz): log error and continue processing the rest
                raise VitrageError('one entity should not be included in '
                                   'multiple equivalence definitions')
            self.entity_equivalences[entity] = equivalence
