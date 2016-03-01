========================
Vitrage Templates Format
========================

Overview
========
In Vitrage we use configuration files, called "templates", to express rules regarding raising deduced alarms, setting deduced states, and detecting/setting RCA links.
This page describes the format of the Vitrage templates, with some examples and open questions on extending this format.

Template Structure
==================
The template is written in YAML language, with the following structure.
 ::

  metadata: ...
  definitions:
	entities:
		- entity: ...
		- entity: ...
	relationships:
		- relationship: ...
		- relationship: ...
  scenarios:
	scenario:
        condition: <if statement true do the action>
        actions:
            - action: ...


The template is divided into three main sections:

- *Metadata:* Contains the template ID, and list of search words/tags to help with future indexing (optional)
- *Definitions:* This section contains the atomic definitions referenced later on, for entities and relationships
   - *Entities –* describes the resources and alarms which are relevant to the template scenario (conceptually, corresponds to a vertex in the entity graph)
   - *Relationships –* the relationships between the entities (conceptually, corresponds to an edge in the entity graph)
- *Scenarios:* A list of if-then scenarios to consider. Each scenario is comprised of:
   - *Condition –* the condition to be met. This condition will be phrased using the entities and relationships previously defined.
   - *Actions –* an action list to execute when the condition is met

Condition Format
----------------
The condition which needs to be met will be phrased using the entities and relationships previously defined. An expression is some logical combination of entities and relationships.
Expression can be combined using the following logical operators:

- "and" - indicates both expressions must be satisfied in order for the condition to be met.
- "or" - indicates at least one expression must be satisfied in order for the condition to be met (non-exclusive or).
- "not" - indicates the following expression must not be satisfied in order for the condition to be met.
- parentheses "()"  - clause indicating the scope of an expression.

The following are examples of valid expressions, where X, Y and Z are relationships:

- X
- X and Y
- X and Y and Z
- X and not Y
- X and not (Y or Z)
- X and not X

**NOTE:** Most templates will require only the "and" operator, which will be the first operator supported for Mitaka.

Examples
========

Example 1: Basic RCA and Deduced Alarm/State
--------------------------------------------
The following template demonstrates

1. How to raise a deduced alarm. Specifically, if there is high CPU load on a host, raise alarm indicating CPU performance problems on contained instances.
2. How to link alarms for purposes of root cause analysis (RCA). Specifically, if there is high CPU load on the host and CPU performance problems on the hosted instances, we link them with a "causes" relationship.
3. How to use a single template for several different scenarios.

 ::

    metadata:
        id=host_high_cpu_load_to_instance_cpu_suboptimal
    definitions:
        entities:
            - entity:
                category: ALARM
                type: HOST_HIGH_CPU_LOAD
                template_id: 1
            - entity:
                category: ALARM
                type: INSTANCE_CPU_SUBOPTIMAL_PERFORMANCE
                template_id: 2
            - entity:
                category: RESOURCE
                type: HOST
                template_id: 3
            - entity:
                category: RESOURCE
                type: INSTANCE
                template_id: 4
        relationships:
            - relationship:
                source: 1
                target: 3
                relationship_type: on
                template_id : alarm_on_host
            - relationship:
                source: 2
                target: 4
                relationship_type: on
                template_id : alarm_on_instance
            - relationship:
                source: 3
                target: 4
                relationship_type: contains
                template_id : host_contains_instance
    scenarios:
        scenario:
            condition: alarm_on_host and host_contains_instance
            actions:
                - action:
                   action_type: raise_alarm
                   properties:
                      alarm_type: INSTANCE_CPU_SUBOPTIMAL_PERFORMANCE
                   action_target:
                      target: 4
                - action:
                   action_type: set_state
                   properties:
                      state: SUBOPTIMAL
                   action_target:
                      target: 4
         scenario:
            condition: alarm_on_host and alarm_on_instance and host_contains_instance
            actions:
                - action:
                   type: add_causal_relationship
                   action_target:
                      source: 1
                      target: 2

Example 2: Deduced state based on alarm
---------------------------------------
The following template will change the state of a resource to "ERROR" if there is any alarm of severity "CRITICAL" on it. Also note that entity ids can be strings as well.

 ::

    metadata:
        id=deduced_state_for_all_with_alarm
    definitions:
        entities:
            - entity:
                category: RESOURCE
                template_id: a_resource # entity ids are any string
            - entity:
                category: ALARM
                severity: CRITICAL
                template_id: high_alarm # entity ids are any string
        relationships:
            - relationship:
                source: high_alarm
                target: a_resource
                relationship_type: on
                template_id : high_alarm_on_resource
    scenarios:
        scenario:
            condition: high_alarm_on_resource
            actions:
                - action:
                   action_type : set_state
                   properties:
                      state: ERROR
                   action_target:
                      target: a_resource

Example 3: Deduced alarm based on state
---------------------------------------
This template will cause an alarm to be raised on any Host in state "ERROR"

Note that in this template, there are no relationships. The condition is just that the entity exists.

 ::

    metadata:
        id=deduced_alarm_for_all_host_in_error
    definitions:
        entities:
            - entity:
                category: RESOURCE
                type: HOST
                state: ERROR
                template_id: 1
    scenarios:
        scenario:
            condition: 1
            actions:
                - action:
                   action_type: raise_alarm
                   properties:
                      alarm_type: HOST_IN_ERROR_STATE
                   action_target:
                      target: 1

Example 4: Deduced Alarm triggered by several options
-----------------------------------------------------
This template will raise a deduced alarm on an instance, which can be caused by an alarm on the hosting zone or an alarm on the hosting host.

 ::

    metadata:
        id=deduced_alarm_two_possibile_triggers
    definitions:
        entities:
            - entity:
                category: ALARM
                Type: ZONE_CONNECTIVITY_PROBLEM
                template_id: 1
            - entity:
                category: ALARM
                Type: HOST_CONNECTIVITY_PROBLEM
                template_id: 2
            - entity:
                category: RESOURCE
                type: ZONE
                template_id: 3
            - entity:
                category: RESOURCE
                type: HOST
                template_id: 4
            - entity:
                category: RESOURCE
                type: INSTANCE
                template_id: 5
        relationships:
            - relationship:
                source: 1
                target: 3
                relationship_type: on
                template_id : alarm_on_zone
            - relationship:
                source: 2
                target: 4
                relationship_type: on
                template_id : alarm_on_host
            - relationship:
                source: 3
                target: 4
                relationship_type: contains
                template_id : zone_contains_host
            - relationship:
                source: 4
                target: 5
                relationship_type: contains
                template_id : host_contains_instance
    scenarios:
        scenario:
            condition: (alarm_on_host and host_contains_instance) or (alarm_on_zone and zone_contains_host and host_contains_instance)
            actions:
                - action:
                   action_type : raise_alarm
                   properties:
                      alarm_type: INSTANCE_CONNECTIVITY_PROBLEM
                   action_target:
                      target: 5

Open Issues / TBD
=================

Inequality
----------
Consider a template that has two entities of the same category+type, say E1 and E2 both are instances like this:

 ::

    metadata:
        id=two_similar_instances
    definitions:
        entities:
            - entity:
                category: RESOURCE
                type: HOST
                template_id: host
            - entity:
                category: RESOURCE
                type: INSTANCE
                template_id: instance1
            - entity:
                category: RESOURCE
                type: INSTANCE
                template_id: instance2
            ...
        relationships:
            - relationship:
                source: host
                target: instance1
                relationship_type: contains
                template_id: link1
            - relationship:
                source: host
                target: instance2
                relationship_type: contains
                template_id: link2

            ...

There are three options of how to interpret this template:

- *instance1 == instance2.* This option is not a reasonable one, as in this case the template can be written with only *instance1*
- *instance1 != instance2.*
- *instance1 != instance2 or instance1 == instance2.* In other words, either option is fine.

Thus, we need a way to distinguish between options 2 & 3 (as option 1 can be expressed by using only instance1). This can be done in two ways:
1. Introducing another logical operator "neq", to be used between expressions:

 ::

    condition: (instance1 neq instance2) and...

2. Using this as a relationship type "neq":

 ::

    relationship:
        source: instance1
        target: instance2
        relationship_type: neq


Cardinality
-----------
To support cardinality, for example to express we want a host to have two instances on it, we could take different approaches.

1. One approach would rely on the "neq" relationship described above. Similar to the example given in the previous section, stating that the two instances on the host are not equal is equivalent to a cardinality of two.
2. A different approach would be to expand the definition of the "relationship" clause. By default cardinality=1 (which will support backward compatibility)

For example, we might use the one of the following formats

::

    - relationship: # option A
        source: host
        target: instance
        target_cardinality: 2 # means there are two instances, but only one host
        relationship_type: contains
        template_id: host_contains_two_instances_A

    - relationship: # option B, same meaning as option A but split into two lines
        source: host
        target: instance
        cardinality_for: instance
        cardinality: 2
        relationship_type: contains
        template_id: host_contains_two_instances_B
