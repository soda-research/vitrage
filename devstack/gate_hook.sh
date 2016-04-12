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

export DEVSTACK_GATE_NEUTRON=1
export DEVSTACK_GATE_TEMPEST=1
export DEVSTACK_GATE_TEMPEST_ALL=1
export DEVSTACK_GATE_TEMPEST_FULL=0
export DEVSTACK_GATE_TEMPEST_ALL_PLUGINS=0
export DEVSTACK_GATE_TEMPEST_REGEX="vitrage_tempest_tests"

if [ -z ${DEVSTACK_LOCAL_CONFIG+x} ]; then
    DEVSTACK_LOCAL_CONFIG="enable_plugin vitrage git://git.openstack.org/openstack/vitrage"
fi

DEVSTACK_LOCAL_CONFIG+=$'\n'"enable_plugin ceilometer https://git.openstack.org/openstack/ceilometer"
DEVSTACK_LOCAL_CONFIG+=$'\n'"enable_plugin aodh git://git.openstack.org/openstack/aodh"
export DEVSTACK_LOCAL_CONFIG

if [ -z ${ENABLED_SERVICES+x} ]; then
    ENABLED_SERVICES=tempest
fi

ENABLED_SERVICES+=key,aodi-api,aodh-notifier,aodh-evaluator
ENABLED_SERVICES+=ceilometer-acompute,ceilometer-acentral,ceilometer-anotification,ceilometer-collector
ENABLED_SERVICES+=ceilometer-alarm-evaluator,ceilometer-alarm-notifier
ENABLED_SERVICES+=ceilometer-api
export ENABLED_SERVICES
export KEEP_LOCALRC=1

$BASE/new/devstack-gate/devstack-vm-gate.sh