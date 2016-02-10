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


class Scenario(object):

    TYPE_ENTITY = 'entity'
    TYPE_RELATE = 'relationship'

    def __init__(self):
        pass

    def get_condition(self):
        """Returns the condition for this scenario.

        Each condition should be formatted in DNF (Disjunctive Normal Form),
        e.g., (X and Y) or (X and Z) or (X and V and not W)...
        where X, Y, Z, V, W are either entities or relationships
        For details: https://en.wikipedia.org/wiki/Disjunctive_normal_form

        :return: condition
        """
        entity = 'replace with vertex'

        relationship = 'replace with edge'

        mock_entity = (entity, self.TYPE_ENTITY, True)
        mock_relationship = (relationship, self.TYPE_RELATE, False)

        # single "and" clause between entity and relationship
        return [(mock_entity, mock_relationship)]

    def get_actions(self):
        """Returns the action specifications for this scenario.

        :return: list of actions to perform
        :rtype: ActionSpecs
        """
        action_spec = ActionSpecs()
        return [action_spec]


class ActionSpecs(object):

    def get_type(self):
        return 'action type str'

    def get_targets(self):
        """Returns dict of template_ids to apply action on

        :return: dict of string:template_id
        :rtype: dict
        """

        # e.g., for adding edge, need two ids. for alarms, will need only one.
        return {'source': 'source template_id',
                'target': 'target template_id'}

    def get_properties(self):
        """Returns the properties relevant to the action.

        :return: dictionary of properties relevant to the action.
        :rtype: dict
        """
        return {'prop_key': 'prop_val'}
