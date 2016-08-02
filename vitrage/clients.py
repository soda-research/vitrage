# Copyright 2016 - Nokia
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

from oslo_config import cfg
from oslo_log import log

from ceilometerclient import client as cm_client
from cinderclient import client as cin_client
from neutronclient.v2_0 import client as ne_client
from novaclient import client as n_client


from vitrage import keystone_client

LOG = log.getLogger(__name__)

OPTS = [
    cfg.StrOpt('aodh_version', default='2', help='Aodh version'),
    cfg.FloatOpt('nova_version', default='2.11', help='Nova version'),
    cfg.StrOpt('cinder_version', default='2', help='Cinder version'),
]


def ceilometer_client(conf):
    """Get an instance of ceilometer client"""
    auth_config = conf.service_credentials
    try:
        client = cm_client.get_client(
            version=conf.aodh_version,
            session=keystone_client.get_session(conf),
            region_name=auth_config.region_name,
            interface=auth_config.interface,
        )
        LOG.info('Ceilometer client created')
        return client
    except Exception as e:
        LOG.exception('Create Ceilometer client - Got Exception: %s', e)


def nova_client(conf):
    """Get an instance of nova client"""
    auth_config = conf.service_credentials
    try:
        client = n_client.Client(
            version=conf.nova_version,
            session=keystone_client.get_session(conf),
            region_name=auth_config.region_name,
            interface=auth_config.interface,
        )
        LOG.info('Nova client created')
        return client
    except Exception as e:
        LOG.exception('Create Nova client - Got Exception: %s', e)


def cinder_client(conf):
    """Get an instance of cinder client"""
    auth_config = conf.service_credentials
    try:
        client = cin_client.Client(
            version=conf.cinder_version,
            session=keystone_client.get_session(conf),
            region_name=auth_config.region_name,
            interface=auth_config.interface,
        )
        LOG.info('Cinder client created')
        return client
    except Exception as e:
        LOG.exception('Create Cinder client - Got Exception: %s', e)


def neutron_client(conf):
    """Get an instance of neutron client"""
    auth_config = conf.service_credentials
    try:
        client = ne_client.Client(
            session=keystone_client.get_session(conf),
            region_name=auth_config.region_name,
            interface=auth_config.interface,
        )
        LOG.info('Neutron client created')
        return client
    except Exception as e:
        LOG.exception('Create Neutron client - Got Exception: %s', e)
