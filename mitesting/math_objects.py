from sympy import *
from sympy import Tuple, StrictLessThan, LessThan, StrictGreaterThan, GreaterThan
from sympy.core.relational import Relational
from sympy.printing import latex
import sympy
import re

def parse_expr(s, global_dict=None, local_dict=None):
    # until bug is fixed, call sympify after parse_expr
    # so that tuples are changed to Sympy Tuples
    from sympy.parsing.sympy_parser import \
        (standard_transformations, convert_xor, \
             implicit_multiplication)
    from sympy.parsing.sympy_parser import parse_expr as sympy_parse_expr
    from sympy import sympify

    transformations=standard_transformations+(convert_xor,implicit_multiplication)
    
    return sympify(sympy_parse_expr(s, local_dict=local_dict, transformations=transformations))


def create_greek_dict():
    from sympy.abc import (alpha, beta,  delta, epsilon, eta,
                           theta, iota, kappa, mu, nu, xi, omicron, pi,
                           rho, sigma, tau, upsilon, phi, chi, psi, omega)
    
    lambda_symbol = Symbol('lambda')
    gamma_symbol = Symbol('gamma')
    zeta_symbol = Symbol('zeta')
    greek_dict = {'alpha': alpha, 'alpha_symbol': alpha, 
                  'beta': beta,'beta_symbol': beta, 
                  'gamma_symbol': gamma_symbol, 
                  'delta': delta, 'delta_symbol': delta, 
                  'epsilon': epsilon, 'epsilon_symbol': epsilon,
                  'zeta_symbol': zeta_symbol, 
                  'eta': eta, 'eta_symbol': eta, 
                  'theta': theta, 'theta_symbol': theta, 
                  'iota': iota, 'iota_symbol': iota, 
                  'kappa': kappa, 'kappa_symbol': kappa, 
                  'lambda_symbol': lambda_symbol, 
                  'mu': mu, 'mu_symbol': mu,
                  'nu': nu, 'nu_symbol': nu,
                  'xi': xi,'xi_symbol': xi, 
                  'omicron': omicron,'omicron_symbol': omicron, 
                  'rho': rho, 'rho_symbol': rho, 
                  'sigma': sigma, 'sigma_symbol': sigma, 
                  'tau': tau, 'tau_symbol': tau, 
                  'upsilon': upsilon,'upsilon_symbol': upsilon,
                  'phi': phi, 'phi_symbol': phi, 
                  'chi': chi, 'chi_symbol': chi, 
                  'psi': psi, 'psi_symbol': psi, 
                  'omega': omega, 'omega_symbol': omega }

    return greek_dict
    
def create_symbol_name_dict():

    symbol_list = 'bigstar bigcirc clubsuit spadesuit heartsuit diamondsuit Diamond bigtriangleup bigtriangledown blacklozenge blacksquare blacktriangle blacktriangledown blacktriangleleft blacktriangleright Box circ lozenge star'.split(' ')
    symbol_name_dict = {}
    for symbol in symbol_list:
        symbol_name_dict[eval("Symbol('%s')" % symbol)] = '\\%s' % symbol

    return symbol_name_dict

def try_expand_expr(expr):
    try:
        if isinstance(expr, Tuple):
            # if is tuple, try to expand each element separately
            expr_expand_list = []
            for expr in expr:
                try:
                    expr_expand_list.append(expr.expand())
                except:
                    expr_expand_list.append(expr)
                expr_expand = Tuple(*expr_expand_list)
        else:
            expr_expand = expr.expand()
    except:
        expr_expand = expr
    return expr_expand
        

def check_tuple_equality(the_tuple1, the_tuple2, tuple_is_ordered=True):
    
    if tuple_is_ordered:
        return the_tuple1 == the_tuple2

    # if not ordered, check if match with any order
    try:
        if len(the_tuple1) != len(the_tuple2):
            return False
    except TypeError:
        # if one or other isn't tuple, return False
        return False

    tuple2_indices_used=[]
    for expr1 in the_tuple1:
        expr1_matches=False
        for (i, expr2) in enumerate(the_tuple2):
            if expr1 == expr2 and i not in tuple2_indices_used:
                tuple2_indices_used.append(i)
                expr1_matches=True
                break
            
        if not expr1_matches:
            return False
    return True


def is_strict_inequality(the_relational):
    if isinstance(the_relational, StrictLessThan):
        return True
    if isinstance(the_relational, StrictGreaterThan):
        return True
    return False

def is_nonstrict_inequality(the_relational):
    if isinstance(the_relational, LessThan):
        return True
    if isinstance(the_relational, GreaterThan):
        return True
    return False



def check_relational_equality(the_relational1, the_relational2):
    if the_relational1==the_relational2:
        return True

    if (is_strict_inequality(the_relational1) and \
            is_strict_inequality(the_relational2)) or \
            (is_nonstrict_inequality(the_relational1) and \
                 is_nonstrict_inequality(the_relational2)):
        if the_relational1.lts ==  the_relational2.lts and \
                the_relational1.gts ==  the_relational2.gts:
            return True
        else:
            return False
    
    if (isinstance(the_relational1, Equality) and \
            isinstance(the_relational2, Equality)) or \
            (isinstance(the_relational1, Unequality) and \
                 isinstance(the_relational2, Unequality)):
        # already checked this case above
        if the_relational1.lhs == the_relational2.lhs and \
                the_relational1.rhs == the_relational2.rhs:
            return True
        elif the_relational1.lhs == the_relational2.rhs and \
                the_relational1.rhs == the_relational2.lhs:
            return True
        else:
            return False

    return False

 
class math_object(object):
    def __init__(self, expression, n_digits=None, round_decimals=None, use_ln=False, expand_on_compare=False, tuple_is_ordered=True, collapse_equal_tuple_elements=False):
        self._expression=sympify(expression)
        self._n_digits=n_digits
        self._round_decimals=round_decimals
        self._use_ln=use_ln
        self._expand_on_compare = expand_on_compare
        self._tuple_is_ordered = tuple_is_ordered

        if isinstance(self._expression,Tuple) and collapse_equal_tuple_elements:
            tuple_list = []
            for expr in self._expression:
                if expr not in tuple_list:
                    tuple_list.append(expr)
            self._expression=Tuple(*tuple_list)
            # if just one element left, collapse to just an element
            if len(self._expression)==1:
                self._expression = self._expression[0]


    def return_expression(self):
        return self._expression
    def return_if_ordered(self):
        return self._tuple_is_ordered
    def convert_expression(self):
        expression=self._expression

        if self._n_digits:
            try:
                if isinstance(expression,Tuple):
                    expression = Tuple(*[expr.evalf(self._n_digits) for expr in expression])
                else:
                    expression = expression.evalf(self._n_digits)
            except:
                pass

        if self._round_decimals is not None:
            try:
                if isinstance(expression,Tuple):
                    expression = Tuple(*[expr.round(self._round_decimals) for expr in expression])
                    if self._round_decimals == 0:
                        expression =Tuple(*[int(expr) for expr in expression])
                else:
                    expression = expression.round(self._round_decimals)
                    if self._round_decimals == 0:
                        expression = int(expression)
            except:
                pass
        return expression
    def __unicode__(self):
        expression = self.convert_expression()
        symbol_name_dict = create_symbol_name_dict()
        
        if isinstance(expression,Tuple) and not self._tuple_is_ordered:
            # for unordered Tuple, just separate entries by commas
            output_list = [latex(expr, symbol_names=symbol_name_dict) for expr in expression]
            output = ",~ ".join(output_list)
        else:
            output = latex(expression, symbol_names=symbol_name_dict)
        if self._use_ln:
            output = re.sub('operatorname{log}', 'operatorname{ln}', output)
            output = re.sub('\\log', 'ln', output)
        # show one character functions as just normal math
        output = re.sub('\\\\operatorname\{(\w)\}','\\1',output)
                
        return output
    def __str__(self):
        return self.__unicode__()
    def __float__(self):
        expression = self.convert_expression()
        try:
            return float(expression)
        except:
            return expression
    def float(self):
        return self.__float__()

    def compare_with_expression(self, new_expr):
        from sympy import Tuple

        new_expr_expand=try_expand_expr(new_expr)

        expression_expand = try_expand_expr(self._expression)

        expressions_equal=False
        equal_if_expand=False
        if self._expand_on_compare:
            if isinstance(self._expression, Tuple):
                expressions_equal = check_tuple_equality \
                    (expression_expand, new_expr_expand, 
                     tuple_is_ordered=self._tuple_is_ordered)
            elif isinstance(self._expression, Relational):
                expressions_equal = check_relational_equality \
                    (expression_expand, new_expr_expand)
            else:
                if expression_expand == new_expr_expand:
                    expressions_equal=True
        else:
            if isinstance(self._expression, Tuple):
                if check_tuple_equality(self._expression, new_expr, 
                                        tuple_is_ordered=self._tuple_is_ordered):
                    expressions_equal = True
                elif check_tuple_equality(expression_expand, new_expr_expand, 
                                        tuple_is_ordered=self._tuple_is_ordered):
                    equal_if_expand=True
            elif isinstance(self._expression, Relational):
                if check_relational_equality(self._expression, new_expr):
                    expressions_equal = True
                elif check_relational_equality \
                    (expression_expand, new_expr_expand):
                    equal_if_expand=True
            else:
                if self._expression==new_expr:
                    expressions_equal=True
                elif  expression_expand == new_expr_expand:
                    equal_if_expand=True

        if expressions_equal:
            return 1
        if equal_if_expand:
            return -1
        return 0