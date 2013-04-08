from sympy import *
from sympy.printing import latex
import sympy
import re

def parse_expr(s, local_dict=None, rationalize=False, convert_xor=False):
    # until bug is fixed, call sympify after parse_expr
    # so that tuples are changed to Sympy Tuples
    from sympy.parsing.sympy_parser import parse_expr
    from sympy import sympify

    return sympy.sympify(sympy.parsing.sympy_parser.parse_expr(s, local_dict, rationalize, convert_xor))



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

class sympy_word(object):
    def __init__(self, the_word):
        self.word=the_word
    def __unicode__(self):
        output = latex(self.word, symbol_names=create_symbol_name_dict())
        return output

class math_object(object):
    def __init__(self, expression, n_digits=None, round_decimals=None, use_ln=False, allow_expand=False):
        self._expression=sympify(expression)
        self._n_digits=n_digits
        self._round_decimals=round_decimals
        self._use_ln=use_ln
        self._allow_expand = allow_expand
        
    def return_expression(self):
        return self._expression

    def convert_expression(self):
        expression=self._expression
        if self._n_digits:
            try:
                expression = expression.evalf(self._n_digits)
            except:
                pass

        if self._round_decimals is not None:
            try:
                expression = expression.round(self._round_decimals)
                if self._round_decimals == 0:
                    expression = int(expression)
            except:
                pass
        return expression
    def __unicode__(self):
        expression = self.convert_expression()
        output=""
        symbol_name_dict = create_symbol_name_dict()
        output = latex(expression, symbol_names=symbol_name_dict)
        if self._use_ln:
            output = re.sub('operatorname{log}', 'operatorname{ln}', output)
            output = re.sub('\\log', 'ln', output)
        return output
    def __float__(self):
        expression = self.convert_expression()
        try:
            return float(expression)
        except:
            return expression
    def float(self):
        return self.__float__()

    def compare_with_expression(self, new_expr):
        try:
            new_expr_expand = new_expr.expand()
        except:
            new_expr_expand = new_expr

        try:
            expression_expand = self._expression.expand()
        except:
            expression_expand = self._expression

        expressions_equal=False
        equal_if_expand=False
        if self._allow_expand:
            # check  both expanded and original in case expand gave error
            if expression_expand == new_expr_expand or \
                    self._expression==new_expr:
                expressions_equal=True
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


class LatexUnicodeMixin(object):
    def latex(self):
        from sympy.printing import latex
        return latex(self)
    def __unicode__(self):
        return self.latex()


class latexPow(Pow, LatexUnicodeMixin):
    pass

class latexMul(Mul, LatexUnicodeMixin):
    pass

class latexMul(Mul):
    def latex(self):
        from sympy.printing import latex
        return latex(self)
    def __unicode__(self):
        return self.latex()
 
  
class DerivedMul(Mul):
    def hello(self):
        print "hello"



class math_function(math_object):
    pass


# class function_one_var(math_function):
#     def initialize_from_string(self, input_string, input_var)
    
