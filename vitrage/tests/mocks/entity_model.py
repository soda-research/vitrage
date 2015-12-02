# Copyright 2015 - Alcatel-Lucent
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

__author__ = 'erosensw'

import copy
import exrex


class CommonEntityModel(object):

    def __init__(self, static_params, dynamic_params, values=None):
        self.param_gen = copy.copy(static_params)
        self.param_gen.update(dynamic_params)
        self.static_keys = static_params.keys()
        self.dynamic_keys = dynamic_params.keys()

        self.current = {k: None for k in self.param_gen.keys()}

        if values is not None:
            for v in values:
                self.set_param(v[0], v[1])

    def get_params(self):
        return self.current

    def set_param(self, key, value=None):
        if key in self.static_keys and self.current[key] is not None:
            return
        if value is None:
            self.current[key] = exrex.getone(self.param_gen[key])
        else:
            self.current[key] = value

    def generate_all_params(self):
        for k in self.param_gen.keys():
            self.set_param(k)

    def generate_dynamic_params(self):
        for k in self.dynamic_keys:
            self.set_param(k)
