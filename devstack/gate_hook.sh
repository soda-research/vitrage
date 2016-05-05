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
export DEVSTACK_GATE_TEMPEST_REGEX=""

export PROJECTS="openstack/aodh $PROJECTS"

if [ -z ${DEVSTACK_LOCAL_CONFIG+x} ]; then
    DEVSTACK_LOCAL_CONFIG="enable_plugin vitrage git://git.openstack.org/openstack/vitrage"
fi
DEVSTACK_LOCAL_CONFIG+=$'\n'"enable_plugin vitrage-dashboard git://git.openstack.org/openstack/vitrage-dashboard"
DEVSTACK_LOCAL_CONFIG+=$'\n'"enable_plugin ceilometer git://git.openstack.org/openstack/ceilometer"
DEVSTACK_LOCAL_CONFIG+=$'\n'"enable_plugin aodh git://git.openstack.org/openstack/aodh"
DEVSTACK_LOCAL_CONFIG+=$'\n'"disable_service ceilometer-alarm-evaluator,ceilometer-alarm-notifier"
DEVSTACK_LOCAL_CONFIG+=$'\n'"disable_service n-net"
DEVSTACK_LOCAL_CONFIG+=$'\n'"[[post-config|\$NOVA_CONF]]"
DEVSTACK_LOCAL_CONFIG+=$'\n'"[DEFAULT]"
DEVSTACK_LOCAL_CONFIG+=$'\n'"notification_topics = notifications,vitrage_notifications"
DEVSTACK_LOCAL_CONFIG+=$'\n'"notification_driver=messagingv2"
DEVSTACK_LOCAL_CONFIG+=$'\n'"[[post-config|\$NEUTRON_CONF]]"
DEVSTACK_LOCAL_CONFIG+=$'\n'"[DEFAULT]"
DEVSTACK_LOCAL_CONFIG+=$'\n'"notification_topics = notifications,vitrage_notifications"
DEVSTACK_LOCAL_CONFIG+=$'\n'"notification_driver=messagingv2"
DEVSTACK_LOCAL_CONFIG+=$'\n'"[[post-config|\$CINDER_CONF]]"
DEVSTACK_LOCAL_CONFIG+=$'\n'"[DEFAULT]"
DEVSTACK_LOCAL_CONFIG+=$'\n'"notification_topics = notifications,vitrage_notifications"
DEVSTACK_LOCAL_CONFIG+=$'\n'"notification_driver=messagingv2"
export DEVSTACK_LOCAL_CONFIG

if [ -z ${ENABLED_SERVICES+x} ]; then
    ENABLED_SERVICES=tempest
fi
ENABLED_SERVICES+=,vitrage-api,vitrage-graph
ENABLED_SERVICES+=,q-svc,q-dhcp,q-meta,q-agt,q-l3
ENABLED_SERVICES+=,key,aodi-api,aodh-notifier,aodh-evaluator
ENABLED_SERVICES+=,ceilometer-alarm-evaluator,ceilometer-alarm-notifier
ENABLED_SERVICES+=,ceilometer-api
export ENABLED_SERVICES

export KEEP_LOCALRC=1

$BASE/new/devstack-gate/devstack-vm-gate.sh
