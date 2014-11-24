from __future__ import print_function
from __future__ import unicode_literals
from __future__ import absolute_import
from __future__ import division
from django.utils.encoding import python_2_unicode_compatible

from sympy import Tuple, Symbol, sympify, Abs
from sympy.core.relational import Relational, Equality, Unequality
from sympy.printing import latex
from mitesting.customized_commands import evalf_expression, round_expression, normalize_floats

@python_2_unicode_compatible
class math_object(object):
    def __init__(self, expression, **parameters):
        """
        parameters implemented
        n_digits: number of digits of precision to keep for all numerical
            quantities (including symbols like pi) on display
            or on comparison.  If neither n_digits or round_decimals
            is set, then rationals, integers, and numerical
            symbols are left as is.
        round_decimals: number of decimals to keep for all numerical
            quantities (including symbols like pi) on display
            or on comparison.  
            If round_decimals < 0, then also convert numbers to integers.
            If neither n_digits or round_decimals
            is set, then rationals, integers, and numerical
            symbols are left as is.
        use_ln: convert log to ln on display
        normalize_on_compare: if True, then check for equality based
            on normalized versions of expressions.  Currently,
            normalizations involves trying to expand and call
            ratsimp to simplify rational expressions.
        match_partial_tuples_on_compare: if True, then check for 
            partial equality on tuples, returning fraction of 
            elements that match
        split_symbols_on_compare: flag set to indicate that answers
            to be compared to this object should have symbols split
            when parsing.  If this flag is true, then only effect on
            math_object is that return_split_symbols_on_compare()
            returns True.
        tuple_is_unordered: if flag set to True, then answer will
            match expression if entries in tuples match 
            regardless of order
        collapse_equal_tuple_elements: if flag set to True, 
            then duplicate entries of tuple are eliminated.  
            If resulting tuple has only one element, 
            the expression is replaced by just that element.
        output_no_delimiters: if flag set to True, then tuples or lists
            are printed just with entries separated by commas.
        evaluate_level: if EVALUATE_NONE, then don't process the expression
            before displaying or comparing with another expression
            Value can be retrieved with return_evaluate_level.            
        copy_parameters_from: objects from which to copy parameters.
            If set to an object with a dictionary with a _parameters attribute,
            all parameters are passed into function are ignored 
            and values from the object are used instead.
        xvar: string to use in place of x to label equations.
            Currently, just used for lines.
        yvar: string to use in place of y to label equations.
            Currently, just used for lines.
        
        """

        self._expression=sympify(expression)
        self._parameters = parameters

        # overwrite all parameters from copy_parameters_from object
        # if it exists
        copy_parameters_from = self._parameters.get('copy_parameters_from')
        if copy_parameters_from:
            try:
                self._parameters = copy_parameters_from._parameters
            except:
                pass

        # If have Tuple and collapse_equal_tuple_elements is set
        # then delete any duplicate Tuple elements.
        # Order of resulting Tuple is based on first occurrence of each element.
        if isinstance(self._expression,Tuple) and \
                self._parameters.get('collapse_equal_tuple_elements'):
            tuple_list = []
            for expr in self._expression:
                if expr not in tuple_list:
                    tuple_list.append(expr)
            self._expression=Tuple(*tuple_list)
            # if just one element left, collapse to just an element
            if len(self._expression)==1:
                self._expression = self._expression[0]

    # define a bunch of comparison operators on math_objects
    # so they can be treated like expressions
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

    def __add__(self, other):
        if isinstance(other, math_object):
            other=other._expression
        return self._expression + other
    def __radd__(self, other):
        return self.__add__(other)
    def __sub__(self, other):
        if isinstance(other, math_object):
            other=other._expression
        return self._expression - other
    def __rsub__(self, other):
        if isinstance(other, math_object):
            other=other._expression
        return other-self._expression
    def __mul__(self, other):
        if isinstance(other, math_object):
            other=other._expression
        return self._expression*other
    def __rmul__(self, other):
        return self.__mul__(other)
    def __div__(self, other):
        if isinstance(other, math_object):
            other=other._expression
        return self._expression/other
    def __truediv__(self, other):
        return self.__div__(other)
    def __rdiv__(self, other):
        if isinstance(other, math_object):
            other=other._expression
        return other/self._expression
    def __rtruediv__(self, other):
        return self.__rdiv__(other)
    def __pow__(self, other):
        if isinstance(other, math_object):
            other=other._expression
        return self._expression**other
    def __rpow__(self, other):
        if isinstance(other, math_object):
            other=other._expression
        return other**self._expression


    # when compare or combine with sympy expressions, use expression
    def _sympy_(self):
        return self._expression



    def return_expression(self):
        return self._expression
    def return_if_unordered(self):
        return self._parameters.get('tuple_is_unordered',False)
    def return_if_use_ln(self):
        return self._parameters.get('use_ln',False)
    def return_if_output_no_delimiters(self):
        return self._parameters.get('output_no_delimiters',False)
    def return_split_symbols_on_compare(self):
        return self._parameters.get('split_symbols_on_compare', False)
    def return_n_digits(self):
        return self._parameters.get('n_digits')
    def return_round_decimals(self):
        return self._parameters.get('round_decimals')
    def return_evaluate_level(self):
        from mitesting.sympy_customized import EVALUATE_FULL
        return self._parameters.get('evaluate_level', EVALUATE_FULL)

    def eval_to_precision(self, expression):
        """
        If parameter n_digits or round_decimals is set, 
        evaluate all numbers and numbersymbols (like pi) 
        of expression to floats 
        with n_digits of precision or round_decimals decimals.
        Since rounding to decimals is last, it will convert
        floats to integers is round_decimals <= 0.
        If neither option is set, 
        then normalize all floats to 14 digits of precision
        to increase consistency of floats in presence of roundoff errors.
        """

        modified=False
        n_digits = self._parameters.get('n_digits')
        if n_digits:
            expression = evalf_expression(expression, n_digits)
            modified = True
        round_decimals = self._parameters.get('round_decimals')
        if round_decimals is not None:
            expression = round_expression(expression, 
                                          round_decimals)
            modified = True
        if not modified:
            expression = normalize_floats(expression)
            
        return expression

    def convert_expression(self):
        """ 
        Run eval_to_precision on object's expression
        """
        
        expression=self.eval_to_precision(self._expression)
            
        return expression


    def __repr__(self):
        return "math_object(%s)" % self._expression


    def __str__(self):
        """
        Return latex version of expression as string
        Use symbol_name_dict from create_symbol_name_dict to convert
        some symbols into their corresponding latex expressions.
        In addition, process the output in the following ways.
        1. If output_no_delimeters is set, then output tuples and lists
           just as elements separate by commas
        2. If expression is a LinearEntity, then display as equation
           of line set to zero.
        3. If use_ln is set, then substitute ln for log
        """
        from sympy.geometry.line import LinearEntity
        from mitesting.sympy_customized import EVALUATE_NONE
        if self._parameters.get('evaluate_level') == EVALUATE_NONE:
            expression = self._expression
        else:
            expression = self.convert_expression()
        symbol_name_dict = create_symbol_name_dict()
        
        if self._parameters.get('output_no_delimiters') \
                and (isinstance(expression,Tuple) \
                         or isinstance(expression,list)):
            # just separate entries by commas
            output_list = [latex(expr, symbol_names=symbol_name_dict) \
                               for expr in expression]
            output = ",~ ".join(output_list)
        elif isinstance(expression, LinearEntity):
            xvar=self._parameters.get('xvar','x')
            yvar=self._parameters.get('yvar','y')
            output = "%s = 0" % latex(expression.equation(x=xvar,y=yvar))
        else:
            try:
                output = latex(expression, symbol_names=symbol_name_dict)
            except RuntimeError:
                # for now, since dividing by one creates infinite recursion
                # in latex printer, use sstr print
                from sympy.printing import sstr
                output = sstr(expression)
            except:
                output = "[error]"
        if self._parameters.get('use_ln'):
            import re
            output = re.sub(r'\log', 'ln', output)
                
        return output

    def __float__(self):
        """
        When outputting float, first convert expression,
        which rounds expression corresponding to parameters
        n_digits and/or round_decimals.
        Attempts to convert expression to a float.
        """
        expression = self.convert_expression()
        return float(expression)

    def float(self):
        return self.__float__()

    def compare_with_expression(self, new_expr):
        """
        Compare expression of object with new_expression.
        Returns:
        1  if expressions are considered equal.
           If normalize_on_compare is set, then expressions are considered
           equal if their normalized expressions to the same.
           Otherwise, expressions themselves must be the same.
        -1 if normalize_on compare is not set, the expressions themselves
           are not the same, but their normalized expressions are the same.
        0  if the expressions not the same and the normalized expressions
           are not the same
        p  number p, 0 < p < 1, if expressions are partially equal,
           where p indicates the fraction of expressions that are equal
        -p number p, 0 < p < 1, if normalize_on compare is not set,
           the expressions themselves are not the same,
           but their normalized expressions are partially equal, then
           p indicates the fraction of normalized expressions that are equal
        In all determinations of equality, expressions are rounded to
        the precision determined by n_digits and round_decimals, if set.
        """

        from mitesting.sympy_customized import EVALUATE_NONE

        expression=self._expression

        # As long as evaluate is not False
        # convert customized ln command to customized log command
        if self._parameters.get("evaluate_level") != EVALUATE_NONE:
            from .customized_commands import log, ln
            from .sympy_customized import bottom_up
            expression = bottom_up(expression, 
                lambda w: w if not w.func==ln else log(*w.args))
            new_expr = bottom_up(new_expr, 
                lambda w: w if not w.func==ln else log(*w.args))

        # Calculate the normalized expressions for both expressions,
        # rounded to precision as specified by n_digits and round_decimals
        new_expr_normalize=self.eval_to_precision(try_normalize_expr(new_expr))
        expression_normalize = self.eval_to_precision(\
            try_normalize_expr(expression))


        # As long as evaluate is not False
        # evaluate both expressions to precision as specified
        # by n_digits and round_decimals
        if self._parameters.get("evaluate_level") != EVALUATE_NONE:
            new_expr = self.eval_to_precision(new_expr)
            expression = self.eval_to_precision(expression)

        tuple_is_unordered = self._parameters.get('tuple_is_unordered',False)
        match_partial_tuples_on_compare = self._parameters.get(
            'match_partial_tuples_on_compare',False)
        expressions_equal=0
        equal_if_normalize=0
        if self._parameters.get('normalize_on_compare'):
            expressions_equal = check_equality \
                (expression_normalize, new_expr_normalize, \
                 tuple_is_unordered=tuple_is_unordered, \
                 partial_tuple_matches = \
                 match_partial_tuples_on_compare)
        else:
            expressions_equal = check_equality \
                (expression, new_expr, \
                 tuple_is_unordered=tuple_is_unordered, \
                 partial_tuple_matches = \
                 match_partial_tuples_on_compare)
            if expressions_equal==0:
                equal_if_normalize = check_equality \
                    (expression_normalize, new_expr_normalize, \
                     tuple_is_unordered=tuple_is_unordered, \
                     partial_tuple_matches = \
                     match_partial_tuples_on_compare)

        if expressions_equal:
            return expressions_equal
        if equal_if_normalize:
            return -1*equal_if_normalize
        return 0

        

def create_symbol_name_dict():
    """
    Create a dictionary used by latex printer to convert symbols to
    latex expressions.
    """

    symbol_list = 'bigstar bigcirc clubsuit spadesuit heartsuit diamondsuit Diamond bigtriangleup bigtriangledown blacklozenge blacksquare blacktriangle blacktriangledown blacktriangleleft blacktriangleright Box circ lozenge star'.split(' ')
    symbol_name_dict = {}
    for symbol in symbol_list:
        symbol_name_dict[eval("Symbol('%s')" % symbol)] = '\\%s' % symbol

    symbol_name_dict[Symbol('heart')] = '\\heartsuit'
    symbol_name_dict[Symbol('club')] = '\\clubsuit'
    symbol_name_dict[Symbol('diamond')] = '\\diamondsuit'
    symbol_name_dict[Symbol('spade')] = '\\spadesuit'

    return symbol_name_dict


def try_normalize_expr(expr):
    """
    Attempt to normalize expression.
    If relational, subtract rhs from both sides.
    Use, doit, expand, then ratsimp to simplify rationals, then expand again
    """
    
    try:
        if expr.is_Relational:
            from sympy import StrictLessThan, LessThan, Equality, Unequality

            # in attempt to normalize relational
            # 1. subtract sides so rhs is zero (lhs for less than inequalities)
            # 2. try to find coefficient of first term and divide by it

            lmr = (expr.lhs - expr.rhs).expand()
            
            if lmr.is_Add:
                term = lmr.args[0]
            else:
                term = lmr
            coeff = term.as_coeff_Mul()[0]
            if not(isinstance(expr, Equality) or isinstance(expr,Unequality)):
                coeff = Abs(coeff)
            if coeff:
                lmr = lmr/coeff

            if isinstance(expr, StrictLessThan) or isinstance(expr,LessThan):
                expr = expr.func(0, -lmr)
            else:
                expr = expr.func(lmr,0)
    except AttributeError:
        pass


    def _remove_one_coefficient(expr):
        # remove a coefficent of a Mul that is just 1.0
        from sympy import Mul
        if expr.is_Mul and expr.args[0]==1:
            if len(expr.args[1:])==1:
                return expr.args[1]
            else:
                return Mul(*expr.args[1:])
        else:
            return expr

    from mitesting.sympy_customized import bottom_up

    # transformations to try to normalize
    expr= bottom_up(expr, lambda w: w.doit().expand().ratsimp().expand())
    # remove any cofficients of 1.0
    expr=bottom_up(expr, _remove_one_coefficient)
    
    return(expr)

def check_equality(expression1, expression2, tuple_is_unordered=False, \
                   partial_tuple_matches=False):
    """ 
    Determine if expression1 and expression2 are equal.
    If tuple_is_unordered is set, then tuples are compared regardless of order.
    Returns:
    1   if correct
    0   if completely incorrect
    p   number p, 0 < p < 1 indicating fraction correct 
        in case is partially correct
    """
        
    from sympy.geometry.line import LinearEntity
 
    if isinstance(expression1, Tuple) or isinstance(expression2, Tuple):
        return check_tuple_equality(expression1, expression2, 
                                    tuple_is_unordered=tuple_is_unordered,
                                    partial_tuple_matches=
                                    partial_tuple_matches)
    try:
        if expression1.is_Relational or expression2.is_Relational:
            return 1*check_relational_equality(expression1, expression2)
    except AttributeError:
        pass

    if isinstance(expression1, LinearEntity) or \
         isinstance(expression2, LinearEntity):
        try:
            return 1*expression1.is_similar(expression2)
        except AttributeError:
            return 0

    if expression1 == expression2:
        return 1
    else:
        return 0

def check_tuple_equality(the_tuple1, the_tuple2, tuple_is_unordered=False, \
                         partial_tuple_matches=False):
    """
    Check if two Tuples are equal, converting non-Tuples to length 1 Tuples.
    (Hence doesn't work for tuples just for Tuples)

    If tuple_is_unordered is set, then check if elements match
    regardless of order.
    If partial_tuple_matches is set, then check if just some elements
    match and return the fraction that match.  For ordered tuples, 
    the matching elements must be in the same order.

    Return 
    1   if exact match
    p   number p, 0 < p < 1, if partial_tuple_matches is set and fracction
        p of elements mtach.  Denominator of fraction is max length of 
        both tuples
    """

    # if either isn't a tuple, replace with a tuple of length 1
    if not isinstance(the_tuple1, Tuple):
        the_tuple1 = Tuple(the_tuple1)
    if not isinstance(the_tuple2, Tuple):
        the_tuple2 = Tuple(the_tuple2)
    
    # if tuple_is_unordered isn't set, demand exact equality
    if not tuple_is_unordered:
        if the_tuple1 == the_tuple2:
            return 1
        if not partial_tuple_matches:
            return 0
        else:

            def max_ordered_subsequence(t1, t2):
                max_matched=0
                for (i1,start_element) in enumerate(t1):
                    try: 
                        i2 = t2.index(start_element)
                    except ValueError:
                        continue
                    matched = 1 + max_ordered_subsequence(t1[i1+1:],t2[i2+1:])
                    max_matched=max(max_matched,matched)
                return max_matched


            # if partial matches, then look for maximum number of matches
            # that occur in the same order
            max_matched = max_ordered_subsequence(the_tuple1,the_tuple2)
            return max_matched/max(len(the_tuple1),len(the_tuple2))


    # if not ordered, check if match with any order
    
    # loop through all elements of tuple 1
    # for each element, look for a matching element of tuple 2
    # that has not been used yet.
    tuple2_indices_used=[]
    n_matches=0
    for expr1 in the_tuple1:
        for (i, expr2) in enumerate(the_tuple2):
            if expr1 == expr2 and i not in tuple2_indices_used:
                tuple2_indices_used.append(i)
                n_matches +=1
                break

    if len(the_tuple1) == len(the_tuple2) and n_matches==len(the_tuple1):
        return 1

    if not partial_tuple_matches:
        return 0
    else:
        return n_matches/max(len(the_tuple1),len(the_tuple2))



# given inheritance structure of sympy
# have to separate check for greater and less than
def is_strict_inequality(the_relational):
    from sympy import StrictLessThan, StrictGreaterThan
    if isinstance(the_relational, StrictLessThan):
        return True
    if isinstance(the_relational, StrictGreaterThan):
        return True
    return False
def is_nonstrict_inequality(the_relational):
    from sympy import LessThan, GreaterThan
    if isinstance(the_relational, LessThan):
        return True
    if isinstance(the_relational, GreaterThan):
        return True
    return False



def check_relational_equality(the_relational1, the_relational2):
    """ 
    Check if two relations are equivalent.
    """

    # if relations are exactly the same, we're done
    if the_relational1==the_relational2:
        return True

    # if relations aren't the same, they could be inequalities
    # with the sides reversed.
    # Check if both strict or both not strict
    # and that the larger and small sides are equal
    if (is_strict_inequality(the_relational1) and \
            is_strict_inequality(the_relational2)) or \
            (is_nonstrict_inequality(the_relational1) and \
                 is_nonstrict_inequality(the_relational2)):
        if the_relational1.lts ==  the_relational2.lts and \
                the_relational1.gts ==  the_relational2.gts:
            return True
        else:
            return False
    
    # if both equalities or inequalities, they could be the same
    # except with sides reversed
    if (isinstance(the_relational1, Equality) and \
            isinstance(the_relational2, Equality)) or \
            (isinstance(the_relational1, Unequality) and \
                 isinstance(the_relational2, Unequality)):
        # just need to check if the sides are reversed.
        # (If the sides were the same, initial check would have shown
        # them to be equal.)
        if the_relational1.lhs == the_relational2.rhs and \
                the_relational1.rhs == the_relational2.lhs:
            return True
        else:
            return False

    # if have different types of relations, they must be unequal
    return False
