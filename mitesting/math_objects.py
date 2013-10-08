from sympy import *
from sympy import Tuple, StrictLessThan, LessThan, StrictGreaterThan, GreaterThan, Float, Symbol, Rational, Integer
from sympy.core.relational import Relational
from sympy.printing import latex
import sympy
import re

def underscore_to_camel(word):
    return ''.join(x.capitalize() for x in  word.split('_'))

def parse_expr(s, global_dict=None, local_dict=None, 
               split_symbols=False):
    
    # until bug is fixed, call sympify after parse_expr
    # so that tuples are changed to Sympy Tuples
    from sympy.parsing.sympy_parser import \
        (standard_transformations, convert_xor, \
             implicit_multiplication)
    from sympy.parsing.sympy_parser import split_symbols as split_symbols_trans
    from sympy.parsing.sympy_parser import parse_expr as sympy_parse_expr
    from sympy import sympify

    # Create new global dictionary so modifications don't affect original
    new_global_dict = {}
    if global_dict:
        new_global_dict.update(global_dict)

    # Since Symbol could be added by auto_symbol
    # and Integer, Float, or Rational could be added by auto_number
    # add them to the global dict if not present
    if 'Integer' not in new_global_dict:
        new_global_dict['Integer'] = Integer
    if 'Float' not in new_global_dict:
        new_global_dict['Float'] = Float
    if 'Rational' not in new_global_dict:
        new_global_dict['Rational'] = Rational
    if 'Symbol' not in new_global_dict:
        new_global_dict['Symbol'] = Symbol


    if split_symbols:
        transformations=standard_transformations+(convert_xor, split_symbols_trans, implicit_multiplication)
    else:
        transformations=standard_transformations+(convert_xor, implicit_multiplication)
    
    return sympify(sympy_parse_expr(s, global_dict=new_global_dict, local_dict=local_dict, transformations=transformations))

def parse_and_process(s, global_dict=None, local_dict=None, doit=True,
                      split_symbols=False):
    expression = parse_expr(s, global_dict=global_dict, local_dict=local_dict,
                            split_symbols=split_symbols)
    if doit:
        try: 
            expression=expression.doit()
        except (AttributeError, TypeError):
            pass
        
    return expression


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

def try_normalize_expr(expr):
    # normalize means expand and then ratsimp
    try:
        if isinstance(expr, Tuple) or isinstance(expr,list):
            # if is tuple or list, try to normalize each element separately
            expr_normalize_list = []
            for ex in expr:
                try:
                    expr_normalize_list.append(ex.expand().ratsimp())
                except:
                    expr_normalize_list.append(ex)
            if isinstance(expr,Tuple):    
                expr_normalize = Tuple(*expr_normalize_list)
            else:
                expr_normalize = expr_normalize_list
        else:
            expr_normalize = expr.expand().ratsimp()
    except:
        expr_normalize = expr
    return expr_normalize
        

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
    def __init__(self, expression, n_digits=None, round_decimals=None, use_ln=False, normalize_on_compare=False, split_symbols_on_compare=False, tuple_is_ordered=True, collapse_equal_tuple_elements=False, copy_properties_from=None, output_no_delimiters=None, **kwargs):
        self._expression=sympify(expression)
        self._n_digits=n_digits
        self._round_decimals=round_decimals
        self._use_ln=use_ln
        self._normalize_on_compare = normalize_on_compare
        self._split_symbols_on_compare = split_symbols_on_compare
        self._tuple_is_ordered = tuple_is_ordered
        self._kwargs = kwargs

        if output_no_delimiters is None:
            if not tuple_is_ordered:
                output_no_delimiters=True
            else:
                output_no_delimiters=False
        self._output_no_delimiters = output_no_delimiters
        
        if copy_properties_from:
            try:
                self._n_digits = copy_properties_from._n_digits 
            except:
                pass
            try:
                self._round_decimals = copy_properties_from._round_decimals
            except:
                pass
            try:
                self._use_ln = copy_properties_from._use_ln
            except:
                pass
            try:
                self._normalize_on_compare = copy_properties_from._normalize_on_compare
            except:
                pass
            try:
                self._split_symbols_on_compare = copy_properties_from._split_symbols_on_compare
            except:
                pass

            try:
                self._tuple_is_ordered = copy_properties_from._tuple_is_ordered
            except:
                pass
            try:
                self._output_list_no_delimiters = copy_properties_from._output_list_no_delimiters
            except:
                pass

        if isinstance(self._expression,Tuple) and collapse_equal_tuple_elements:
            tuple_list = []
            for expr in self._expression:
                if expr not in tuple_list:
                    tuple_list.append(expr)
            self._expression=Tuple(*tuple_list)
            # if just one element left, collapse to just an element
            if len(self._expression)==1:
                self._expression = self._expression[0]


    def __eq__(self, other):
        if isinstance(other, math_object):
            other=other._expression
        return self._expression.__eq__(other)
    def __ne__(self, other):
        if isinstance(other, math_object):
            other=other._expression
        return self._expression.__ne__(other)
    def __lt__(self, other):
        if isinstance(other, math_object):
            other=other._expression
        return self._expression.__lt__(other)
    def __le__(self, other):
        if isinstance(other, math_object):
            other=other._expression
        return self._expression.__le__(other)
    def __gt__(self, other):
        if isinstance(other, math_object):
            other=other._expression
        return self._expression.__gt__(other)
    def __ge__(self, other):
        if isinstance(other, math_object):
            other=other._expression
        return self._expression.__ge__(other)
    def __bool__(self):
        return bool(self._expression)
    __nonzero__=__bool__


    def return_expression(self):
        return self._expression
    def return_if_ordered(self):
        return self._tuple_is_ordered
    def return_split_symbols_on_compare(self):
        return self._split_symbols_on_compare

    def eval_to_precision(self, expression):
        if self._n_digits:
            n_digits=self._n_digits
            # expression = expression.xreplace \
            #     (dict((orig_float, \
            #                orig_float.evalf(n_digits)) \
            #               for orig_float in expression.atoms(Float))) 
                
            from sympy.simplify.simplify import bottom_up
            if isinstance(expression, list):
                new_expr=[]
                for expr in expression:
                    new_expr.append(bottom_up(expr.evalf(),
                                    lambda w: w.evalf(n_digits)
                                    if not w.is_Number 
                                    else Float(str(w.evalf(n_digits))),
                                    atoms=True))
                expression=new_expr
            else:
                expression =  bottom_up(expression.evalf(),
                                        lambda w: w.evalf(n_digits)
                                        if not w.is_Number 
                                        else Float(str(w.evalf(n_digits))),
                                        atoms=True)
                
        else:
            # even if not n_digits, find any floats and round to 14 digits
            # to overcome machine precision errors
            # in this case, only modify atoms that are Floats
            n_digits=14
            from sympy.simplify.simplify import bottom_up
            # have turned all lists to Tuples so can get rid of this condition?
            if isinstance(expression, list):
                new_expr=[]
                for expr in expression:
                    try:
                        new_expr.append(bottom_up(expr,
                                                  lambda w: w
                                                  if not w.is_Float 
                                                  else Float(str(w.evalf(n_digits))),
                                                  atoms=True))
                    except TypeError:
                        new_expr.append(expr)

                expression=new_expr
            else:
                try:
                    expression =  bottom_up(expression,
                                            lambda w: w
                                            if not w.is_Float 
                                            else Float(str(w.evalf(n_digits))),
                                            atoms=True)
                except TypeError:
                    pass
                    
            
        return expression

    def convert_expression(self):

        expression=self.eval_to_precision(self._expression)

        if self._round_decimals is not None:
            try:
                def round_or_int(w):
                    if not w.is_Float:
                        return w
                    w = w.round(self._round_decimals)
                    if self._round_decimals==0:
                        return int(w)
                    else:
                        return w

                from sympy.simplify.simplify import bottom_up
                expression =  bottom_up(expression,
                                        round_or_int,
                                        atoms=True)
                
            except TypeError:
                pass

        return expression

    def __unicode__(self):
        from sympy.geometry.line import LinearEntity
        expression = self.convert_expression()
        symbol_name_dict = create_symbol_name_dict()
        
        if self._output_no_delimiters and (isinstance(expression,Tuple)
                                           or isinstance(expression,list)):
            # just separate entries by commas
            output_list = [latex(expr, symbol_names=symbol_name_dict) for expr in expression]
            output = ",~ ".join(output_list)
        elif isinstance(expression, LinearEntity):
            xvar=self._kwargs.get('xvar','x')
            yvar=self._kwargs.get('yvar','y')
            output = "%s = 0" % latex(expression.equation(x=xvar,y=yvar))
            
            
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
        from sympy.geometry.line import LinearEntity

        new_expr_normalize=self.eval_to_precision(try_normalize_expr(new_expr))

        expression_normalize = self.eval_to_precision(try_normalize_expr(self._expression))

        new_expr = self.eval_to_precision(new_expr)
        print new_expr
        expression=self.eval_to_precision(self._expression)
        print expression

        expressions_equal=False
        equal_if_normalize=False
        if self._normalize_on_compare:
            if isinstance(expression, Tuple):
                expressions_equal = check_tuple_equality \
                    (expression_normalize, new_expr_normalize, 
                     tuple_is_ordered=self._tuple_is_ordered)
            elif isinstance(expression, Relational):
                expressions_equal = check_relational_equality \
                    (expression_normalize, new_expr_normalize)
            elif isinstance(expression, LinearEntity):
                try:
                    expressions_equal = expression_normalize.is_similar(new_expr_normalize)
                except AttributeError:
                    expressions_equal = False
            else:
                if expression_normalize == new_expr_normalize:
                    expressions_equal=True
        else:
            if isinstance(expression, Tuple):
                if check_tuple_equality(expression, new_expr, 
                                        tuple_is_ordered=self._tuple_is_ordered):
                    expressions_equal = True
                elif check_tuple_equality(expression_normalize, new_expr_normalize, 
                                        tuple_is_ordered=self._tuple_is_ordered):
                    equal_if_normalize=True
            elif isinstance(expression, Relational):
                if check_relational_equality(expression, new_expr):
                    expressions_equal = True
                elif check_relational_equality \
                    (expression_normalize, new_expr_normalize):
                    equal_if_normalize=True
            elif isinstance(expression, LinearEntity):
                try:
                    expressions_equal = expression.is_similar(new_expr)
                except AttributeError:
                    expressions_equal = False
                try:
                    equal_if_normalize = expression_normalize.is_similar(new_expr_normalize)
                except AttributeError:
                    equal_if_normalize = False
            else:
                if expression==new_expr:
                    expressions_equal=True
                elif  expression_normalize == new_expr_normalize:
                    equal_if_normalize=True

        if expressions_equal:
            return 1
        if equal_if_normalize:
            return -1
        return 0
