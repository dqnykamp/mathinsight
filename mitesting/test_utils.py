from __future__ import print_function
from __future__ import unicode_literals
from __future__ import absolute_import
from __future__ import division

from django.test import SimpleTestCase
from mitesting.utils import *

class TestUtils(SimpleTestCase):
    def test_greek_dict(self):
        gd = create_greek_dict()
        from sympy.abc import omega
        self.assertEqual(gd['omega'], omega)
        self.assertEqual(gd['omega_symbol'], omega)

    def test_sympy_global_dict(self):
        greek_dict = create_greek_dict()
        global_dict = return_sympy_global_dict()
        self.assertEqual(global_dict, greek_dict)

        from mitesting.customized_commands import Abs
        global_dict = return_sympy_global_dict(["Abs"])
        global_dict2 = greek_dict;
        global_dict2['Abs']=Abs
        self.assertEqual(global_dict, global_dict2)

        global_dict = return_sympy_global_dict(["Abs", "floor, ceiling"])
        from sympy import floor, ceiling
        global_dict2['ceiling']=ceiling
        global_dict2['floor']=floor
        self.assertEqual(global_dict, global_dict2)

        global_dict = return_sympy_global_dict(["Abs", "floor, ceiling",
                                                "min, max, Min, Max",
                                                "nothingvalid"])
        from mitesting.customized_commands import min_including_tuples,\
            max_including_tuples
        global_dict2['min']=min_including_tuples
        global_dict2['Min']=min_including_tuples
        global_dict2['max']=max_including_tuples
        global_dict2['Max']=max_including_tuples
        self.assertEqual(global_dict, global_dict2)
