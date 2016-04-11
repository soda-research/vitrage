============================
Resource State Configuration
============================

Configure Access to Resource State
----------------------------------

The following should be set in **/etc/vitrage/vitrage.conf**, under entity_graph section:

+------------------------+------------------------------------+----------------------------------+
| Name                   | Description                        | Default Value                    |
+========================+====================================+==================================+
| datasources_values_dir | Directory path from where to load  | /etc/vitrage/datasources_values/ |
|                        | the values configurations          |                                  |
+------------------------+------------------------------------+----------------------------------+


Configure Resource State Mapping
--------------------------------

Resource state configuration is made to configure how states of specific resource are normalized.
For each normalized state a priority is set as well, so that when resource will have the original state and the Vitrage state, Vitrage will know what state is more important.
UNRECOGNIZED state has to be configured in each resource state configuration file.

The file name has to be in the same name as it's plugin name.
State configuration yaml file has to be defined for all the plugins which were chosen to be used in Vitrage.

**Format**
::

  category: RESOURCE
  values:
    - normalized value:
        name: <Normalized resource value name - must be from NormalizedResourcevalue class>
        priority: <Resource value priority - an integer>
        original values:
          - name: <Original resource value name>
          - name: <Original resource value name>
    - normalized value:
          name: <Normalized resource value name - must be from NormalizedResourcevalue class>
          priority: <Resource value priority - an integer>
          original values:
            - name: <Original resource value name>
            - name: <Original resource value name>

  ...


**Example**

The following is mapping resource values.
Original values 'DELETED' and 'TERMINATED' will be mapped to normalized value 'TERMINATED'.
Original values 'ACTIVE' and 'RUNNING' to normalized value 'RUNNING'.

::

  category: RESOURCE
  values:
    - normalized value:
        name: TERMINATED
        priority: 20
        original values:
          - name: DELETED
          - name: TERMINATED
    - normalized value:
          name: RUNNING
          priority: 10
          original values:
            - name: ACTIVE
            - name: RUNNING



**Default Configuration**

Default configurations for resource values will be installed with Vitrage.



