================================
Template Directory Configuration
================================

Overview
--------
Vitrage uses configuration files called ``templates``, to express rules
regarding raising deduced alarms, setting deduced states, and detecting/setting
RCA links.

Configuration
-------------
The templates, definition templates and entity equivalence directories should be defined in the
Vitrage configuration file, **/etc/vitrage/vitrage.conf** under the ``[evaluator]`` section.


+-------------------+------------------------------------------------------------------+--------------------------------------+
| Name              | Description                                                      | Default Value                        |
+===================+==================================================================+======================================+
| templates_dir     | A path for the templates used by the evaluator                   | /etc/vitrage/templates               |
+-------------------+------------------------------------------------------------------+--------------------------------------+
| def_templates_dir | A path for the  definition template files used by the evaluator. | /etc/vitrage/templates/def_templates |
|                   | These are template files that contain only definitions and       |                                      |
|                   | can be included and used in regular template files to create     |                                      |
|                   | scenarios.                                                       |                                      |
+-------------------+------------------------------------------------------------------+--------------------------------------+
|equivalences_dir   | A path for for entity equivalences used by the evaluator.        | /etc/vitrage/templates/equivalences  |
+-------------------+------------------------------------------------------------------+--------------------------------------+

.. code:: yaml


    [evaluator]

    templates_dir = /etc/vitrage/templates
    def_templates_dir = /etc/vitrage/templates/def_templates
    equivalences_dir = /etc/vitrage/templates/equivalences
