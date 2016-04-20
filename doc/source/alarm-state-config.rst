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

+------------------------+------------------------------------+----------------------------------+
| Name                   | Description                        | Default Value                    |
+========================+====================================+==================================+
| datasources_values_dir | Directory path from where to load  | /etc/vitrage/datasources_values/ |
|                        | the values configurations          |                                  |
+------------------------+------------------------------------+----------------------------------+


Configure Alarm Severity Mapping
--------------------------------

The alarm severity configuration files configure how the severity of each
alarm is normalized. There are several guidelines for creating a config file:

- Normalized alarm values which can be mapped to can be found in
  normalized_alarm_severity.py (NormalizedAlarmSeverity class).
- Each normalized severity also comes with a priority, so
  that if an alarm is given different severities from different sources (e.g.,
  a host alarm raised both by nagios and Vitrage), the severity with the
  highest priority will be used as the **aggregated severity**.
- The *UNKNOWN* severity will be used for severities with no corresponding
  normalized severity. This severity *must* appear in the config file.
- The config file is in YAML format.
- The config filename must be <datasource name>.yaml, for the relevant
  datasource.
- Defining a config file for each datasource is recommended, but not mandatory.
  Datasources with no such configuration will use the values as-is.

Once the file is modified, you must restart **vitrage-graph** service to load
the changes.

Default Configuration
+++++++++++++++++++++

Default configurations for alarms severities will be installed with Vitrage for
all the pre-packaged data-sources.




Format
++++++
::

    category: ALARM
    values:
      - normalized value:
          name: <normalized alarm severity>
          priority: <Alarm severity priority - an integer>
          original values:
            - name: <Original alarm severity name>
            - name: ... # can list several severities for one normalized
      - normalized value:
          name: ... # can list several normalized severities
          ...


  ...


Example
+++++++

The following file will map alarm severities.
Original severities 'CRITICAL' and 'DOWN' will be mapped to normalized value
'CRITICAL'. Normalized value 'SEVERE' has no original severity.
Original value 'WARNING' is mapped to normalized value 'WARNING', etc.

::

    category: ALARM
    values:
      - normalized value:
          name: CRITICAL
          priority: 50
          original values:
            - name: CRITICAL
            - name: DOWN
      - normalized value:
          name: SEVERE
          priority: 40
          original values:
      - normalized value:
          name: WARNING
          priority: 30
          original values:
            - name: WARNING
      - normalized value:
          name: UNKNOWN
          priority: 20
          original values:
            - name: UNKNOWN
      - normalized value:
          name: OK
          priority: 10
          original values:
            - name: OK
            - name: UP
