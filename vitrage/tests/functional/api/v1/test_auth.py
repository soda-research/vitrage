# Copyright 2016 - Nokia Corporation
# Copyright 2014 OpenStack Foundation
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# noinspection PyPackageRequirements
from vitrage.tests.functional.api.v1 import FunctionalTest


class AuthTest(FunctionalTest):

    def __init__(self, *args, **kwds):
        super(AuthTest, self).__init__(*args, **kwds)
        self.auth = 'keystone'

    def test_in_keystone_mode_not_authenticated(self):
        resp = self.post_json('/topology/', params=None, expect_errors=True)
        self.assertEqual('401 Unauthorized', resp.status)
