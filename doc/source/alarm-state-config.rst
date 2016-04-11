============================
Alarm Severity Configuration
============================

Overview
--------

Vitrage retrieves information from diverse data-sources regarding alarms in
the cloud, and stores and combines this information into a unified system
model. An important property of an alarm is its **severity**. This severity can
be used both in the Vitrage templates to trigger actions, and in the Horizon UI
for color-coding purposes. Therefore, it is important that within the Vitrage
data model, severity names are normalized.

Since each data-source might represent severity differently, for each
data-source we can supply it's own mapping to the normalized severity supported
in Vitrage. This page explains how to handle this mapping for a given
data-source.


Configure Access to Alarm Severity
----------------------------------

The alarm severity configuration is handled via config files. The location of
these files can be determined in **/etc/vitrage/vitrage.conf**. Under the
[entity_graph] section, set:

+----------------------+------------------------------------+--------------------------------+
| Name                 | Description                        | Default Value                  |
+======================+====================================+================================+
| states_plugins_dir   | Directory path from where to load  | /etc/vitrage/states_plugins/   |
|                      | the states configurations          |                                |
+----------------------+------------------------------------+--------------------------------+


Configure Alarm State Mapping
-----------------------------

The alarm severity configuration files configure how the severity of each
alarm is normalized. There are several guidelines for creating a config file:

- Normalized alarm states which can be mapped to can be found in
  normalized_alarm_severity.py (NormalizedAlarmSeverity class).
- Each normalized severity also comes with a priority, so
  that if an alarm is given different severities from different sources (e.g.,
  a host alarm raised both by nagios and Vitrage), the severity with the
  highest priority will be used as the **aggregated state**.
- The *UNKNOWN* severity will be used for severities with no corresponding
  normalized severity. This severity *must* appear in the config file.
- The config file is in YAML format.
- The config filename must be <datasource name>.yaml, for the relevant
  datasource.
- Defining a config file for each datasource is recommended, but not mandatory.
  Datasources with no such configuration will use the states as-is.


Default Configuration
+++++++++++++++++++++

Default configurations for alarms severities will be installed with Vitrage for
all the pre-packaged data-sources.




Format
++++++
::

    category: ALARM
    states:
      - normalized state:
          name: <normalized alarm severity>
          priority: <Alarm severity priority - an integer>
          original states:
            - name: <Original alarm severity name>
            - name: ... # can list several severities for one normalized
      - normalized state:
          name: ... # can list several normalized severities
          ...


  ...


Example
+++++++

The following file will map alarm severities.
Original severities 'CRITICAL' and 'DOWN' will be mapped to normalized state
'CRITICAL'. Normalized state 'SEVERE' has no original severity.
Original state 'WARNING' is mapped to normalized state 'WARNING', etc.

::

    category: ALARM
    states:
      - normalized state:
          name: CRITICAL
          priority: 50
          original states:
            - name: CRITICAL
            - name: DOWN
      - normalized state:
          name: SEVERE
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
