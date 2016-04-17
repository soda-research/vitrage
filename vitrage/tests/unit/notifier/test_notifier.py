# Copyright 2016 - Alcatel-Lucent
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

"""
test_vitrage graph
----------------------------------

Tests for `vitrage` graph driver
"""

from vitrage.common.constants import EntityCategory
from vitrage.common.constants import NotifierEventTypes as NType
from vitrage.common.constants import VertexProperties as VProps
from vitrage.entity_graph.processor.notifier import _get_notification_type
from vitrage.evaluator.actions import evaluator_event_transformer as evaluator
from vitrage.graph import Vertex
from vitrage.tests import base


resource = Vertex('123', {
    VProps.CATEGORY: EntityCategory.RESOURCE,
    VProps.TYPE: 'some_resource_type',
    VProps.IS_DELETED: False,
    VProps.IS_PLACEHOLDER: False,
}
)

deduced_alarm = Vertex('123', {
    VProps.CATEGORY: EntityCategory.ALARM,
    VProps.TYPE: evaluator.VITRAGE_TYPE,
    VProps.IS_DELETED: False,
    VProps.IS_PLACEHOLDER: False,
}
)


non_deduced_alarm = Vertex('123', {
    VProps.CATEGORY: EntityCategory.ALARM,
    VProps.TYPE: 'TEST_ALARM',
    VProps.IS_DELETED: False,
    VProps.IS_PLACEHOLDER: True,
}
)

deleted_alarm = Vertex('123', {
    VProps.CATEGORY: EntityCategory.ALARM,
    VProps.TYPE: evaluator.VITRAGE_TYPE,
    VProps.IS_DELETED: True,
    VProps.IS_PLACEHOLDER: False,
}
)

placeholder_alarm = Vertex('123', {
    VProps.CATEGORY: EntityCategory.ALARM,
    VProps.TYPE: evaluator.VITRAGE_TYPE,
    VProps.IS_DELETED: False,
    VProps.IS_PLACEHOLDER: True,
}
)


class GraphTest(base.BaseTest):
    def test_notification_type_new_alarm(self):
        ret = _get_notification_type(None, deduced_alarm, True)
        self.assertEqual(NType.ACTIVATE_DEDUCED_ALARM_EVENT, ret,
                         'new alarm should notify activate')

        ret = _get_notification_type(None, non_deduced_alarm, True)
        self.assertIsNone(ret, 'alarm that is not a deduced alarm')

    def test_notification_type_deleted_alarm(self):
        ret = _get_notification_type(deduced_alarm, deleted_alarm, True)
        self.assertEqual(NType.DEACTIVATE_DEDUCED_ALARM_EVENT, ret,
                         'deleted alarm should notify deactivate')

    def test_notification_type_resource_vertex(self):
        ret = _get_notification_type(None, resource, True)
        self.assertIsNone(ret, 'any non alarm vertex should be ignored')

    def test_notification_type_updated_alarm(self):
        ret = _get_notification_type(deduced_alarm, deduced_alarm, True)
        self.assertIsNone(ret, 'A not new alarm vertex should be ignored')

        ret = _get_notification_type(deleted_alarm, deduced_alarm, True)
        self.assertEqual(NType.ACTIVATE_DEDUCED_ALARM_EVENT, ret,
                         'old alarm become not deleted should notify activate')

        ret = _get_notification_type(placeholder_alarm, deduced_alarm, True)
        self.assertEqual(NType.ACTIVATE_DEDUCED_ALARM_EVENT, ret,
                         'placeholder become active should notify activate')

    def test_notification_type_placeholder_alarm(self):
        ret = _get_notification_type(None, placeholder_alarm, True)
        self.assertIsNone(ret, 'A not new alarm vertex should be ignored')
