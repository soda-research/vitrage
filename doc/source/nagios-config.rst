===========================
Nagios Plugin Configuration
===========================

Configure Access to Nagios
--------------------------

The following should be set in **/etc/vitrage/vitrage.conf**, under [nagios] section:

+------------------+---------------------------------------------------------+-------------------------------+
| Name             | Description                                             | Default Value                 |
+==================+=========================================================+===============================+
| user             | Nagios user                                             |                               |
+------------------+---------------------------------------------------------+-------------------------------+
| password         | Nagios password                                         |                               |
+------------------+---------------------------------------------------------+-------------------------------+
| url              | Nagios url for querying the data                        |                               |
+------------------+---------------------------------------------------------+-------------------------------+
| config_file      | Nagios configuration file                               | /etc/vitrage/nagios_conf.yaml |
+------------------+---------------------------------------------------------+-------------------------------+
| changes_interval | Interval of checking changes in the configuration files | 30 seconds                    |
+------------------+---------------------------------------------------------+-------------------------------+

**Note:** To avoid issues with paging, it is recommended for the URL to be of
the form *http://<nagios site url>/cgi-bin/status.cgi*, which returns all the
nagios tests.

**Example**

 ::

  [nagios]
  user = omdadmin
  password = omd
  url = http://10.20.30.40/monitoring/nagios/cgi-bin/status.cgi
  config_file = /etc/vitrage/nagios_conf.yaml
    

Configure Nagios Host Mapping
-----------------------------

Nagios tests are defined in a table with columns: Host, Service, Status, Last Check, etc.

Nagios "Host" is not necessarily a resource of type host. It can also be an instance, switch, or other resource types. **nagios_conf.yaml** is used to map Nagios host type to a Vitrage resource.

**Format**
::

 nagios:
  - nagios_host: <Host as appears in Nagios>
    type: <resource type in Vitrage>
    name: <resource name in Vitrage>

  - nagios_host: <Host as appears in Nagios>
    type: <resource type in Vitrage>
    name: <resource name in Vitrage>

  ...


**Example**

The following file will map compute-1 to a nova.host named compute-1; and compute-2 to a nova.host named host2

::

 nagios:
  - nagios_host: compute-1
    type: nova.host
    name: compute-1

  - nagios_host: compute-2
    type: nova.host
    name: host2



**Default Configuration**

A default nagios_conf.yaml will be installed with Vitrage. Its content is still TBD, but it will be similar to the following example.

All Nagios hosts named host* or * -devstack will be mapped in Vitrage to resoruces of type nova.host with the same name; and all Nagios hosts named instance* will be mapped to nova.instance resources.

::

 nagios:
  - nagios_host: host-(.*)
    type: nova.host
    name: ${nagios_host}

  - nagios_host: (.*)-devstack
    type: nova.host
    name: ${nagios_host}

  - nagios_host: instance-(.*)
    type: nova.instance
    name: ${nagios_host}

