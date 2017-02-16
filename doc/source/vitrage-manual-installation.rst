===========================
Vitrage Manual Installation
===========================

Install Vitrage
===============

Install vitrage and python-vitrageclient
----------------------------------------

To install the Ocata release:

.. code:: bash

    sudo pip install vitrage==1.5.1
    sudo pip install python-vitrageclient==1.1.1


Or, to install the latest version:

.. code:: bash

    sudo pip install vitrage
    sudo pip install python-vitrageclient


Configure Vitrage
=================

Create the Vitrage folders
--------------------------

Create /etc/vitrage folder and sub folders, **with permission 755**

.. code:: bash

    mkdir /etc/vitrage
    chmod 755 /etc/vitrage

    mkdir /etc/vitrage/static_datasources
    chmod 755 /etc/vitrage/static_datasources

    mkdir /etc/vitrage/templates
    chmod 755 /etc/vitrage/templates

    sudo mkdir /var/log/vitrage
    sudo chmod 755 /var/log/vitrage

Copy `policy.json`_ to /etc/vitrage/

Copy `api-paste.ini`_ to /etc/vitrage/

Copy the `datasources_values`_ folder with its content

**Note:** You don't need to copy all files in this folder, only the ones that
belong to datasources you plan to use. The only file that **must** be copied
is vitrage.yaml

.. _policy.json: ../../etc/vitrage/policy.json
.. _api-paste.ini: ../../etc/vitrage/api-paste.ini
.. _datasources_values: ../../etc/vitrage/datasources_values

Create the vitrage.conf file
----------------------------

Create /etc/vitrage/vitrage.conf file with the following information:

.. code:: bash

    [DEFAULT]
    # debug = False
    transport_url = <transport-url>
    # notifiers = nova

    [service_credentials]
    auth_url = http://<ip>:5000
    region_name = RegionOne
    project_name = admin
    password = <password>
    project_domain_id = default
    user_domain_id = default
    username = admin
    auth_type = password

    [keystone_authtoken]
    auth_uri = http://<ip>:5000
    project_domain_name = Default
    project_name = service
    user_domain_name = Default
    password = <password>
    username = vitrage
    auth_url = http://<ip>:35357
    auth_type = password


Set the list of datasource you would like to use for Vitrage.
**Note:** In order for a datasource to be supported, the underlying component
(like Neutron, Heat, Zabbix, etc.) should be installed separately.

.. code:: bash

    [datasources]
    types = nova.host,nova.instance,nova.zone,static,aodh,cinder.volume,neutron.network,neutron.port,heat.stack,doctor


Configure notifications from other datasources
==============================================

Notifications from Aodh
-----------------------
In order to configure notifications from Aodh to Vitrage, set the following in
`/etc/aodh/aodh.conf`:

.. code:: bash

   [oslo_messaging_notifications]
   driver = messagingv2
   topics = notifications,vitrage_notifications


Notifications from other OpenStack components
---------------------------------------------

In order to configure notifications from OpenStack components (Nova, Cinder,
Neutron, Heat and Aodh) to Vitrage, set the following in their conf files:

.. code:: bash

   [DEFAULT]
   notification_topics = notifications,vitrage_notifications
   notification_driver=messagingv2


Initialize Vitrage
==================

Create the Vitrage account
--------------------------

.. code:: bash

    openstack user create vitrage --password password --domain=Default
    openstack role add admin --user vitrage --project service
    openstack role add admin --user vitrage --project admin

Create the Vitrage endpoint
---------------------------

.. code:: bash

    openstack service create rca --name vitrage --description="Root Cause Analysis Service"
    openstack endpoint create --region <region> --publicurl http://<ip>:8999 --internalurl http://<ip>:8999 --adminurl http://<ip>:8999 vitrage


Start the Vitrage Services
==========================

Run the following commands:

.. code:: bash

    vitrage-graph
    vitrage-api
    vitrage-notifier


Install the Vitrage Dashboard
=============================

Follow vitrage-dashboard_ installation procedure

.. _vitrage-dashboard: https://github.com/openstack/vitrage-dashboard/tree/master/doc/source/installation.rst
