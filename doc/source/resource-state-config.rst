============================
Resource State Configuration
============================

Overview
--------

Vitrage retrieves information from diverse data-sources regarding resources in
the cloud, and stores and combines this information into a unified system
model. An important property of a resource is its **state**. This state can
be used both in the Vitrage templates to trigger actions, and in the Horizon UI
for color-coding purposes. Therefore, it is important that within the Vitrage
data model, state names are normalized.

Since each data-source might represent state differently, for each
data-source we can supply it's own mapping to the normalized state supported
in Vitrage. This page explains how to handle this mapping for a given
data-source.


Configure Access to Resource State
----------------------------------

The resource state configuration is handled via config files. The location of
these files can be determined in **/etc/vitrage/vitrage.conf**. Under the
[entity_graph] section, set:

+------------------------+------------------------------------+----------------------------------+
| Name                   | Description                        | Default Value                    |
+========================+====================================+==================================+
| datasources_values_dir | Directory path from where to load  | /etc/vitrage/datasources_values/ |
|                        | the values configurations          |                                  |
+------------------------+------------------------------------+----------------------------------+


Configure Resource State Mapping
--------------------------------

The resource state configuration files configure how the state of each
resource is normalized. Some guidelines for creating a config file:

- Normalized state values, to which states should be mapped, can be found in
  normalized_resource_state.py (NormalizedResourceState class).
- Each normalized state also comes with a priority, so
  that if a resource is given different states from different sources (e.g.,
  a host state set both by nagios and Vitrage), the state with the
  highest priority will be used as the **aggregated state**.
- The *UNRECOGNIZED* state will be used for states with no corresponding
  normalized state. This state *must* appear in the config file.
- The config file is in YAML format.
- The config filename must be <datasource name>.yaml, for the relevant
  datasource.
- Defining a config file for each datasource is recommended, but not mandatory.
  Datasources with no such configuration will use the values as-is.

Once the file is modified, you must restart **vitrage-graph** service to load
the changes.

Default Configuration
+++++++++++++++++++++

Default configurations for resource states will be installed with Vitrage for
all the pre-packaged data-sources.




Format
++++++
::

    category: RESOURCE
    values:
      - normalized value:
          name: <normalized resource state>
          priority: <resource state priority - an integer>
          original values:
            - name: <Original resource state name>
            - name: ... # can list several states for one normalized
      - normalized value:
          name: ... # can list several normalized states
          ...


  ...


Example
+++++++

The following is mapping resource values.
Original values 'DELETED' and 'TERMINATED' will be mapped to normalized value 'TERMINATED'.
Original values 'ACTIVE' and 'RUNNING' to normalized value 'RUNNING'.

::

  category: RESOURCE
  values:
    - normalized value:
        name: TERMINATED
        priority: 30
        original values:
          - name: DELETED
          - name: TERMINATED
    - normalized value:
        name: RUNNING
        priority: 20
        original values:
          - name: ACTIVE
          - name: RUNNING
    - normalized value:
        name: UNRECOGNIZED
        priority: 10
        original values:
