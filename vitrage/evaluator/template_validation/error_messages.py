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
from vitrage.common.constants import entities_categories

error_msgs = {

    # General 1-19
    1: '"template_id" field contains incorrect string value',
    2: 'value must be from dict type',
    3: 'value must be from list type',

    # definitions section 20-39
    20: 'definitions section must contain "entities" Field.',
    21: '"definitions" is mandatory section in template file.',

    # Entities syntax error messages 40-59
    40: '"type" field in entity definition must be a string',
    41: 'Entity definition must contain "template_id" Field.',
    42: 'Entity definition must contain "category" Field.',
    43: 'At least one entity must be defined.',
    44: 'Entity must refer to dictionary.',
    45: 'Invalid entity category. Category must be from types: '
        '%s' % entities_categories,
    46: 'Entity field is required.',

    # metadata section syntax error messages 60-79
    60: 'metadata section must contain "id" field.',
    61: '"description" field in metadata section must be a string',
    62: '"metadata" is mandatory section in template file.',

    # scenarios section 80-99
    80: '"scenarios" is mandatory section in template file.',
    81: 'At least one scenario must be defined.',
    82: 'scenario field is required.',
    83: 'Entity definition must contain "condition" field.',
    84: 'Entity definition must contain "actions" field.',

    # relationships syntax error messages 100-119
    100: 'Relationship must refer to dictionary.',
    101: 'Relationship field is required.',
    102: 'Relationship definition must contain "source" field.',
    103: 'Relationship definition must contain "target" field.',
    104: 'Relationship definition must contain "template_id" field.',

    # actions syntax error messages 120-139
    121: 'At least one action must be defined.',
    122: 'Action field is required.',
    123: 'Relationship definition must contain "action_type" Field.',
    124: 'Relationship definition must contain "action_target" Field.',
}
