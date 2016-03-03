============================
Resource State Configuration
============================

Configure Access to Resource State
----------------------------------

The following should be set in **/etc/vitrage/vitrage.conf**, under entity_graph section:

+----------------------+------------------------------------+--------------------------------+
| Name                 | Description                        | Default Value                  |
+======================+====================================+================================+
| states_plugins_dir   | Directory path from where to load  | /etc/vitrage/states_plugins/   |
|                      | the states configurations          |                                |
+----------------------+------------------------------------+--------------------------------+


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
  states:
    - normalized state:
        name: <Normalized resource state name - must be from NormalizedResourceState class>
        priority: <Resource state priority - an integer>
        original states:
          - name: <Original resource state name>
          - name: <Original resource state name>
    - normalized state:
          name: <Normalized resource state name - must be from NormalizedResourceState class>
          priority: <Resource state priority - an integer>
          original states:
            - name: <Original resource state name>
            - name: <Original resource state name>

  ...


**Example**

The following is mapping resource states.
Original states 'DELETED' and 'TERMINATED' will be mapped to normalized state 'TERMINATED'.
Original states 'ACTIVE' and 'RUNNING' to normalized state 'RUNNING'.

::

  category: RESOURCE
  states:
    - normalized state:
        name: TERMINATED
        priority: 20
        original states:
          - name: DELETED
          - name: TERMINATED
    - normalized state:
          name: RUNNING
          priority: 10
          original states:
            - name: ACTIVE
            - name: RUNNING



**Default Configuration**

Default configurations for resource states will be installed with Vitrage.



