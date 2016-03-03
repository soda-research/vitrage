=========================
Alarm State Configuration
=========================

Configure Access to Alarm State
-------------------------------

The following should be set in **/etc/vitrage/vitrage.conf**, under entity_graph section:

+----------------------+------------------------------------+--------------------------------+
| Name                 | Description                        | Default Value                  |
+======================+====================================+================================+
| states_plugins_dir   | Directory path from where to load  | /etc/vitrage/states_plugins/   |
|                      | the states configurations          |                                |
+----------------------+------------------------------------+--------------------------------+


Configure Alarm State Mapping
-----------------------------

Alarm state configuration is made to configure how states of specific alarm are normalized.
For each normalized state a priority is set as well, so that when alarm will have the original state and the Vitrage state, Vitrage will know what state is more important.
UNKNOWN state has to be configured in each alarm state configuration file.

The file name has to be in the same name as it's plugin name.
State configuration yaml file has to be defined for all the plugins which were chosen to be used in Vitrage.

**Format**
::

    category: ALARM
    states:
      - normalized state:
          name: <Normalized alarm state name - must be from NormalizedAlarmState class>
          priority: <Alarm state priority - an integer>
          original states:
            - name: <Original alarm state name>
            - name: <Original alarm state name>
      - normalized state:
          name: <Normalized alarm state name - must be from NormalizedAlarmState class>
          priority: <Alarm state priority - an integer>
          original states:
            - name: <Original alarm state name>
            - name: <Original alarm state name>


  ...


**Example**

The following file will map alarm states.
Original states 'CRITICAL' and 'DOWN' will be mapped to normalized state 'CRITICAL'.
Normalized state 'SEVER' has no original states.
Original state 'WARNING' is mapped to normalized state 'WARNING', etc.

::

    category: ALARM
    states:
      - normalized state:
          name: CRITICAL
          priority: 50
          original states:
            - name: CRITITCAL
            - name: DOWN
      - normalized state:
          name: SEVER
          priority: 40
          original states:
      - normalized state:
          name: WARNING
          priority: 30
          original states:
            - name: WARNING
      - normalized state:
          name: UNKNOWN
          priority: 20
          original states:
            - name: UNKNOWN
      - normalized state:
          name: OK
          priority: 10
          original states:
            - name: OK
            - name: UP



**Default Configuration**

Default configurations for alarms states will be installed with Vitrage.



