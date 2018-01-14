#    Copyright 2016 - Nokia
#    Copyright 2014 IBM Corp.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

import inspect

from vitrage.hacking import checks
from vitrage.tests import base


class HackingTestCase(base.BaseTest):
    def test_assert_true_instance(self):
        self.assertEqual(1, len(list(checks.assert_true_instance(
            "self.assertTrue(isinstance(e, "
            "exception.BuildAbortException))"))))

        self.assertEqual(
            0, len(list(checks.assert_true_instance("self.assertTrue()"))))

    def test_assert_equal_type(self):
        self.assertEqual(1, len(list(checks.assert_equal_type(
            "self.assertEqual(type(als['QuicAssist']), list)"))))

        self.assertEqual(
            0, len(list(checks.assert_equal_type("self.assertTrue()"))))

    def test_no_translate_logs(self):
        for log in checks._all_log_levels:
            bad = 'LOG.%s(_("Bad"))' % log
            self.assertEqual(1, len(list(checks.no_translate_logs(bad))))
            # Catch abuses when used with a variable and not a literal
            bad = 'LOG.%s(_(msg))' % log
            self.assertEqual(1, len(list(checks.no_translate_logs(bad))))

    def test_no_direct_use_of_unicode_function(self):
        self.assertEqual(1, len(list(checks.no_direct_use_of_unicode_function(
            "unicode('the party don't start til the unicode walks in')"))))
        self.assertEqual(1, len(list(checks.no_direct_use_of_unicode_function(
            """unicode('something '
                       'something else"""))))
        self.assertEqual(0, len(list(checks.no_direct_use_of_unicode_function(
            "six.text_type('party over')"))))
        self.assertEqual(0, len(list(checks.no_direct_use_of_unicode_function(
            "not_actually_unicode('something completely different')"))))

    def test_no_contextlib_nested(self):
        self.assertEqual(1, len(list(checks.check_no_contextlib_nested(
            "with contextlib.nested("))))

        self.assertEqual(1, len(list(checks.check_no_contextlib_nested(
            "with nested("))))

        self.assertEqual(0, len(list(checks.check_no_contextlib_nested(
            "with foo as bar"))))

    def test_dict_constructor_with_list_copy(self):
        self.assertEqual(1, len(list(checks.dict_constructor_with_list_copy(
            "    dict([(i, connect_info[i])"))))

        self.assertEqual(1, len(list(checks.dict_constructor_with_list_copy(
            "    attrs = dict([(k, _from_json(v))"))))

        self.assertEqual(1, len(list(checks.dict_constructor_with_list_copy(
            "        type_names = dict((value, key) for key, value in"))))

        self.assertEqual(1, len(list(checks.dict_constructor_with_list_copy(
            "   dict((value, key) for key, value in"))))

        self.assertEqual(1, len(list(checks.dict_constructor_with_list_copy(
            "foo(param=dict((k, v) for k, v in bar.items()))"))))

        self.assertEqual(1, len(list(checks.dict_constructor_with_list_copy(
            " dict([[i,i] for i in range(3)])"))))

        self.assertEqual(1, len(list(checks.dict_constructor_with_list_copy(
            "  dd = dict([i,i] for i in range(3))"))))

        self.assertEqual(0, len(list(checks.dict_constructor_with_list_copy(
            "        create_kwargs = dict(snapshot=snapshot,"))))

        self.assertEqual(0, len(list(checks.dict_constructor_with_list_copy(
            "      self._render_dict(xml, data_el, data.__dict__)"))))

    def test_check_python3_xrange(self):
        func = checks.check_python3_xrange
        self.assertEqual(1, len(list(func('for i in xrange(10)'))))
        self.assertEqual(1, len(list(func('for i in xrange    (10)'))))
        self.assertEqual(0, len(list(func('for i in range(10)'))))
        self.assertEqual(0, len(list(func('for i in six.moves.range(10)'))))
        self.assertEqual(0, len(list(func('testxrange(10)'))))

    def test_dict_iteritems(self):
        self.assertEqual(1, len(list(checks.check_python3_no_iteritems(
            "obj.iteritems()"))))

        self.assertEqual(0, len(list(checks.check_python3_no_iteritems(
            "six.iteritems(obj)"))))

        self.assertEqual(0, len(list(checks.check_python3_no_iteritems(
            "obj.items()"))))

    def test_dict_iterkeys(self):
        self.assertEqual(1, len(list(checks.check_python3_no_iterkeys(
            "obj.iterkeys()"))))

        self.assertEqual(0, len(list(checks.check_python3_no_iterkeys(
            "six.iterkeys(obj)"))))

        self.assertEqual(0, len(list(checks.check_python3_no_iterkeys(
            "obj.keys()"))))

    def test_dict_itervalues(self):
        self.assertEqual(1, len(list(checks.check_python3_no_itervalues(
            "obj.itervalues()"))))

        self.assertEqual(0, len(list(checks.check_python3_no_itervalues(
            "six.itervalues(ob)"))))

        self.assertEqual(0, len(list(checks.check_python3_no_itervalues(
            "obj.values()"))))

    def test_no_mutable_default_args(self):
        self.assertEqual(1, len(list(checks.no_mutable_default_args(
            " def fake_suds_context(calls={}):"))))

        self.assertEqual(1, len(list(checks.no_mutable_default_args(
            "def get_info_from_bdm(virt_type, bdm, mapping=[])"))))

        self.assertEqual(0, len(list(checks.no_mutable_default_args(
            "defined = []"))))

        self.assertEqual(0, len(list(checks.no_mutable_default_args(
            "defined, undefined = [], {}"))))

    def test_no_log_warn(self):
        self.assertEqual(0, len(list(checks.no_log_warn('LOG.warning("bl")'))))
        self.assertEqual(1, len(list(checks.no_log_warn('LOG.warn("foo")'))))

    def test_asserttruefalse(self):
        true_fail_code1 = """
               test_bool = True
               self.assertEqual(True, test_bool)
               """
        true_fail_code2 = """
               test_bool = True
               self.assertEqual(test_bool, True)
               """
        true_pass_code = """
               test_bool = True
               self.assertTrue(test_bool)
               """
        false_fail_code1 = """
               test_bool = False
               self.assertEqual(False, test_bool)
               """
        false_fail_code2 = """
               test_bool = False
               self.assertEqual(test_bool, False)
               """
        false_pass_code = """
               test_bool = False
               self.assertFalse(test_bool)
               """
        self.assertEqual(1, len(
            list(checks.check_assert_true_false(true_fail_code1))))
        self.assertEqual(1, len(
            list(checks.check_assert_true_false(true_fail_code2))))
        self.assertEqual(0, len(
            list(checks.check_assert_true_false(true_pass_code))))
        self.assertEqual(1, len(
            list(checks.check_assert_true_false(false_fail_code1))))
        self.assertEqual(1, len(
            list(checks.check_assert_true_false(false_fail_code2))))
        self.assertFalse(list(checks.check_assert_true_false(false_pass_code)))

    def test_factory(self):
        class Register(object):
            def __init__(self):
                self.funcs = []

            def __call__(self, _func):
                self.funcs.append(_func)

        register = Register()
        checks.factory(register)
        for name, func in inspect.getmembers(checks, inspect.isfunction):
            if name != 'factory':
                self.assertIn(func, register.funcs)
