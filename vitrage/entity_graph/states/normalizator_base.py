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

import abc
from collections import namedtuple

import six


ImportantStates = namedtuple('ImportantStates', ['unknown', 'undefined'])


@six.add_metaclass(abc.ABCMeta)
class NormalizatorBase(object):

    def __init__(self):
        pass

    @abc.abstractmethod
    def important_states(self):
        pass

    @abc.abstractmethod
    def state_properties(self):
        pass

    @abc.abstractmethod
    def set_aggregated_state(self, new_vertex, normalized_state):
        pass

    @abc.abstractmethod
    def set_undefined_state(self, new_vertex):
        pass

    @abc.abstractmethod
    def default_states(self):
        pass

    @abc.abstractmethod
    def get_state_class_instance(self):
        pass
