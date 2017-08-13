#!/usr/bin/env bash
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


DEVSTACK_PATH="$BASE/new"


if [ "$1" = "api" ]; then
  TESTS="topology"
elif [ "$1" = "datasources" ]; then
  TESTS="datasources|test_events"
else
  TESTS="topology"
fi

cd $DEVSTACK_PATH/
sudo cp -rf vitrage/vitrage_tempest_tests/tests/resources/static_physical/static_physical_configuration.yaml /etc/vitrage/
sudo cp -rf vitrage/vitrage_tempest_tests/tests/resources/templates/api/* /etc/vitrage/templates/
sudo cp -rf vitrage/vitrage_tempest_tests/tests/resources/heat/heat_template.yaml /etc/vitrage/
sudo cp -rf vitrage/vitrage_tempest_tests/tests/resources/heat/policy.json-tempest /etc/heat/


sudo cp $DEVSTACK_PATH/tempest/etc/logging.conf.sample $DEVSTACK_PATH/tempest/etc/logging.conf

if [ "$DEVSTACK_GATE_USE_PYTHON3" == "True" ]; then
        export PYTHON=python3
fi

cd $DEVSTACK_PATH/tempest/; sudo -E testr init

env
echo "Listing existing Tempest tests"
sudo -E testr list-tests vitrage_tempest_tests
sudo -E testr list-tests vitrage_tempest_tests | grep -E "$TESTS" > /tmp/vitrage_tempest_tests.list
echo "Testing $1: $TESTS..."
sudo -E testr run --subunit --load-list=/tmp/vitrage_tempest_tests.list | subunit-trace --fails
