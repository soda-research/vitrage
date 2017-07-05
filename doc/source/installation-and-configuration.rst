==============================
Installation and configuration
==============================

Vitrage Installation
====================

To Install Vitrage, use **either** devstack installation or manual installation

--------------------------
Enable Vitrage in Devstack
--------------------------

* `Enabling Vitrage in devstack <https://github.com/openstack/vitrage/blob/master/devstack/README.rst>`_

* `Enabling Vitrage in horizon <https://github.com/openstack/vitrage-dashboard/blob/master/README.rst>`_

---------------------------------------------------
Manual Installation of Vitrage (not using Devstack)
---------------------------------------------------
.. toctree::
   :maxdepth: 1

   install/index

External Monitor Installation
=============================

To install Nagios or Zabbix external monitors:

.. toctree::
   :maxdepth: 1

   nagios-devstack-installation
   zabbix_vitrage

Configuration
=============

.. toctree::
   :maxdepth: 1

   nagios-config
   static-config
   static-physical-config
   resource-state-config
   alarm-severity-config
   zabbix_vitrage
   notifier-snmp-plugin
