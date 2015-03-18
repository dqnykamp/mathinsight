from __future__ import print_function
from __future__ import unicode_literals
from __future__ import absolute_import
from __future__ import division
from django.utils.encoding import python_2_unicode_compatible

from sympy import Tuple, sympify, Abs, Matrix, Derivative
from sympy.core.relational import Relational, Equality, Unequality
from mitesting.customized_commands import evalf_expression, round_expression, normalize_floats
from mitesting.sympy_customized import bottom_up, latex, Symbol
from django.utils.safestring import mark_safe

@python_2_unicode_compatible
class math_object(object):
    def __init__(self, expression, **parameters):
        """
        parameters implemented
        round_on_compare: number of digits or decimals to keep for all numerical
            quantities (including symbols like pi) on comparison.  
            If not set set, then rationals, integers, and numerical
            symbols are left as is.
            If round_on_compare < 0 and round_absolute is True,
            then also convert numbers to integers.
        round_absolute: if True, then round_on_compare determines
            number of decimals to keep.  Otherwise, round_on_compare determines
            number of significant digits
        round_partial_credit_digits: for how many digits of accuracy
            less than round_on_compare will partial credit be given.
        round_partial_credit_percent: by what percent the credit will be
            multiplied by for each digit of accuracy less than round_on_compare
        normalize_on_compare: if True, then check for equality based
            on normalized versions of expressions.  Currently,
            normalizations involves trying to expand and call
            ratsimp to simplify rational expressions.
        match_partial_on_compare: if True, then check for 
            partial equality on tuples and sets, returning fraction of 
            elements that match
        split_symbols_on_compare: flag set to indicate that answers
            to be compared to this object should have symbols split
            when parsing.  If this flag is true, then only effect on
            math_object is that return_split_symbols_on_compare()
            returns True.
        tuple_is_unordered: if flag set to True, then answer will
            match expression if entries in tuples match 
            regardless of order
        evaluate_level: if EVALUATE_NONE, then don't process the expression
            before displaying or comparing with another expression
            Value can be retrieved with return_evaluate_level.
        assume_real_variables: if True, then expression was marked as
            assuming undefined variables were real.
            Value can be retrieved with return_assume_real_variables
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
    def return_split_symbols_on_compare(self):
        return self._parameters.get('split_symbols_on_compare', False)
    def return_round_on_compare(self):
        return self._parameters.get('round_on_compare')
    def return_round_absolute(self):
        return self._parameters.get('round_absolute', False)
    def return_round_partial_credit_digits(self):
        return self._parameters.get('round_partial_credit_digits')
    def return_round_partial_credit_percent(self):
        return self._parameters.get('round_partial_credit_percent')
    def return_evaluate_level(self):
        from mitesting.sympy_customized import EVALUATE_FULL
        return self._parameters.get('evaluate_level', EVALUATE_FULL)
    def return_assume_real_variables(self):
        return self._parameters.get('assume_real_variables', False)
    def return_expression_type(self):
        return self._parameters.get('expression_type')

    def eval_to_comparison_precision(self, expression, 
                                     additional_rounding=None):
        """
        If parameter round_on_compare is set, 
        evaluate all numbers and numbersymbols (like pi) 
        of expression to floats 
        with either round_on_compare digits of precision (if not round_absolute)
        or to round_on_compare decimals (if round_absolute)
        It will convert floats to integers if round_absolute and 
        round_on_compare <= 0.
        If additional rounding is set, round_on_compare is reduced by 
        that amount.
        If round_on_compare is not set, 
        then normalize all floats to 14 digits of precision
        to increase consistency of floats in presence of roundoff errors.
        """

        modified=False
        round_on_compare = self._parameters.get('round_on_compare')
        if round_on_compare is not None:
            if additional_rounding:
                try:
                    round_on_compare -= int(additional_rounding)
                except ValueError:
                    pass
            
            round_absolute = self._parameters.get('round_absolute', False)
            
            if round_absolute:
                expression = round_expression(expression, 
                                              round_on_compare)
                modified = True
            elif round_on_compare > 0:
                expression = evalf_expression(expression, round_on_compare)
                modified = True

        if not modified:
            expression = normalize_floats(expression)
            
        return expression


    def __repr__(self):
        return "math_object(%s)" % self._expression


    def __str__(self):
        """
        Return latex version of expression as string
        Use symbol_name_dict from create_symbol_name_dict to convert
        some symbols into their corresponding latex expressions.

        In addition, if expression is a LinearEntity, then display as equation
        of line set to zero.
        """

        from sympy.geometry.line import LinearEntity
        expression = self._expression
        symbol_name_dict = create_symbol_name_dict()
        
        if isinstance(expression, LinearEntity):
            xvar=self._parameters.get('xvar','x')
            yvar=self._parameters.get('yvar','y')
            output = "%s = 0" % latex(expression.equation(x=xvar,y=yvar),
                                      symbol_names=symbol_name_dict)
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
                
        return output

    def __int__(self):
        """
        Attempts to convert expression to an int.
        """
        return int(self._expression)

    def __float__(self):
        """
        Attempts to convert expression to a float.
        """
        return float(self._expression)

    def float(self):
        return self.__float__()

    def compare_with_expression(self, new_expr): 
        """
        Compare expression of object with new_expression.
        Returns dictionary with keys:
        - fraction_equal: the fraction of expressions that are equal.
          If normalized_on_compare is set, then equality is based on
          normalized expressions,
          otherwise it is based on expressions themselves
        - fraction_equal_on_normalize: the fraction of normalized expressions
          that are equal (only if normalize_on_compare is not set)
        - round_level_used: number of digits or decimals used to determine
          fraction_equal
        - round_level_required: number of digits or decimals needed 
          for full credit
        - round_absolute: if True, rounding based on number of decimals kept.
          Otherwise, rounding based on number of significant digits.
        """
        round_level_required=self._parameters.get('round_on_compare')
        round_level_used=round_level_required
        round_absolute=self._parameters.get('round_absolute', False)

        results = {'fraction_equal': 0, 'fraction_equal_on_normalize': 0,
                   'round_level_used': round_level_used,
                   'round_level_required': round_level_required,
                   'round_absolute': round_absolute }

        equality=self.compare_with_expression_sub(new_expr)
        
        if equality > 0:
            results['fraction_equal']=equality
        else:
            results['fraction_equal_on_normalize']=abs(equality)

        round_partial_credit_digits=self._parameters.get(\
                                            "round_partial_credit_digits")

        if equality==1 or not round_partial_credit_digits:
            return results

        # round off at most 10 more digits for partial credit
        try:
            round_partial_credit_digits=min(10,int(round_partial_credit_digits))
        except ValueError:
            return results

        # don't go below 1 significant digit
        if not round_absolute:
            round_partial_credit_digits = min(round_level_required-1,
                                              round_partial_credit_digits)

        round_partial_credit_percent=self._parameters.get(\
                                            "round_partial_credit_percent")

        # multiply credit by round_partial_credit_fraction
        # for each extra digit of rounding
        try:
            round_partial_credit_fraction = \
                min(1.0, max(0.0, round_partial_credit_percent/100.0))
        except TypeError:
            round_partial_credit_fraction = 0.0

        max_credit=1.0
        credit_so_far = max(0,equality)
        correct_with_rounding = False

        for i in range(round_partial_credit_digits):
            additional_rounding = i+1
            max_credit *= round_partial_credit_fraction
            
            equality=self.compare_with_expression_sub(new_expr, \
                                        additional_rounding=additional_rounding)
            credit = equality*max_credit
            
            if credit > credit_so_far:
                results['fraction_equal'] = credit
                results['round_level_used'] = round_level_required \
                                              - additional_rounding
                credit_so_far = credit

            # even if no credit for additional rounding
            # record fact that found a match with additional rounding
            elif credit_so_far==0 and equality==1 and not correct_with_rounding:
                correct_with_rounding=True
                results['round_level_used'] = round_level_required \
                                              - additional_rounding

        return results


    def compare_with_expression_sub(self, new_expr, additional_rounding=None):
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
        the precision determined by round_on_compare and round_absolute, if set,
        minus any additional rounding specified.
        """

        from mitesting.sympy_customized import EVALUATE_NONE

        expression=self._expression

        # As long as evaluate is not False
        # convert customized ln command to customized log command
        if self._parameters.get("evaluate_level") != EVALUATE_NONE:
            from .user_commands import log, ln
            expression = bottom_up(expression, 
                lambda w: w if not w.func==ln else log(*w.args))
            new_expr = bottom_up(new_expr, 
                lambda w: w if not w.func==ln else log(*w.args))

        # Calculate the normalized expressions for both expressions,
        # rounded to precision as specified by 
        # round_on_compare and round_absolute (with additional rounding)
        new_expr_normalize=self.eval_to_comparison_precision(\
                                    try_normalize_expr(new_expr),\
                                    additional_rounding=additional_rounding)
        expression_normalize = self.eval_to_comparison_precision(\
                                try_normalize_expr(expression),\
                                    additional_rounding=additional_rounding)


        # As long as evaluate is not False
        # evaluate both expressions to precision as specified by
        # round_on_compare and round_absolute (with additional rounding)
        if self._parameters.get("evaluate_level") != EVALUATE_NONE:
            new_expr = self.eval_to_comparison_precision(new_expr,
                                additional_rounding=additional_rounding)
            expression = self.eval_to_comparison_precision(expression, 
                                additional_rounding=additional_rounding)

        tuple_is_unordered = self._parameters.get('tuple_is_unordered',False)
        match_partial_on_compare = self._parameters.get(
            'match_partial_on_compare',False)
        expressions_equal=0
        equal_if_normalize=0
        if self._parameters.get('normalize_on_compare'):
            expressions_equal = check_equality \
                (expression_normalize, new_expr_normalize, \
                 tuple_is_unordered=tuple_is_unordered, \
                 partial_matches = match_partial_on_compare)
        else:
            expressions_equal = check_equality \
                (expression, new_expr, \
                 tuple_is_unordered=tuple_is_unordered, \
                 partial_matches = match_partial_on_compare)
            if expressions_equal==0:
                equal_if_normalize = check_equality \
                    (expression_normalize, new_expr_normalize, \
                     tuple_is_unordered=tuple_is_unordered, \
                     partial_matches = match_partial_on_compare)

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
        symbol_name_dict[eval("Symbol('%s', real=True)" % symbol)] = '\\%s' % symbol

    symbol_name_dict[Symbol('heart')] = '\\heartsuit'
    symbol_name_dict[Symbol('club')] = '\\clubsuit'
    symbol_name_dict[Symbol('diamond')] = '\\diamondsuit'
    symbol_name_dict[Symbol('spade')] = '\\spadesuit'
    symbol_name_dict[Symbol('heart', real=True)] = '\\heartsuit'
    symbol_name_dict[Symbol('club', real=True)] = '\\clubsuit'
    symbol_name_dict[Symbol('diamond', real=True)] = '\\diamondsuit'
    symbol_name_dict[Symbol('spade', real=True)] = '\\spadesuit'

    return symbol_name_dict


def try_normalize_expr(expr):
    """
    Attempt to normalize expression.
    If relational, subtract rhs from both sides.
    Convert any subclass of Matrix to Matrix.
    Convert any subclass of Derivative to Derivative
    Use, doit, expand, then ratsimp to simplify rationals, then expand again
    """
    
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

    def normalize_transformations(w):
        # same as
        #    lambda w: w.doit().expand().ratsimp().expand()
        # except catch Polynomial error that could be triggered by ratsimp()
        # and catch attribute error for objects like Interval
        from sympy import PolynomialError
        w=w.doit()
        try:
            w= w.expand()
        except AttributeError:
            pass
        try:
            w=w.ratsimp().expand()
        except (AttributeError,PolynomialError):
            pass
        return w

    expr=bottom_up(expr, 
        lambda w: w if not isinstance(w,Matrix) else Matrix(w),
                   nonbasic=True)

    from sympy import Derivative
    expr=bottom_up(expr, 
        lambda w: w if not isinstance(w,Derivative) else Derivative(*w.args))

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


    # transformations to try to normalize
    expr= bottom_up(expr, normalize_transformations)
    # remove any cofficients of 1.0
    expr=bottom_up(expr, _remove_one_coefficient)
    
    return(expr)

def check_equality(expression1, expression2, tuple_is_unordered=False, \
                   partial_matches=False):
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
 
    if isinstance(expression1, Tuple) or isinstance(expression2, Tuple) \
       or isinstance(expression1, list) or isinstance(expression2, list):
        return check_tuple_equality(expression1, expression2, 
                                    tuple_is_unordered=tuple_is_unordered,
                                    partial_matches=partial_matches)

    if isinstance(expression1, set) or isinstance(expression2, set):
        return check_set_equality(expression1, expression2, 
                                  partial_matches=partial_matches)

    if isinstance(expression1, Matrix) or isinstance(expression2, Matrix):
        return check_matrix_equality(expression1, expression2, 
                                  partial_matches=partial_matches)

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
                         partial_matches=False):
    """
    Check if two Tuples or lists are equal, 
    converting non-Tuples/lists to length 1 TupleNoParen.

    If tuple_is_unordered is set, then check if elements match
    regardless of order.
    If partial_matches is set, then check if just some elements
    match and return the fraction that match.  For ordered tuples, 
    the matching elements must be in the same order.

    If one tuple is a Tuple and the other is a TupleNoParen, regard as unequal

    Return 
    1   if exact match
    p   number p, 0 < p < 1, if partial_matches is set and fracction
        p of elements match.  Denominator of fraction is max length of 
        both tuples
    0   otherwise
    """

    from .sympy_customized import TupleNoParen

    # if either isn't a tuple, replace with a TupleNoParen of length 1
    if not isinstance(the_tuple1, Tuple) and not isinstance(the_tuple1,tuple)\
       and not isinstance(the_tuple1,list):
        the_tuple1 = TupleNoParen(the_tuple1)
    if not isinstance(the_tuple2, Tuple) and not isinstance(the_tuple2,tuple)\
       and not isinstance(the_tuple2,list):
        the_tuple2 = TupleNoParen(the_tuple2)

    # if not same class, then not considered equal.
    # Tuples and TupleNoParens are considered different
    if the_tuple1.__class__ != the_tuple2.__class__:
        return 0

    # if tuple_is_unordered isn't set, demand exact equality
    if not tuple_is_unordered:
        if the_tuple1 == the_tuple2:
            return 1
        if not partial_matches:
            return 0

        # find length of largest common subsequence
        m = len(the_tuple1)
        n = len(the_tuple2)

        from sympy import zeros
        C = zeros(m+1,n+1)
        for i in range(m):
            for j in range(n):
                if the_tuple1[i] == the_tuple2[j]:
                    C[i+1,j+1] = C[i,j] +1
                else:
                    C[i+1,j+1] = max(C[i+1,j],C[i,j+1])
        
        max_matched = float(C[m,n])  # float so don't get sympy rational
        return max_matched/max(m,n)


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

    if not partial_matches:
        return 0
    else:
        return n_matches/max(len(the_tuple1),len(the_tuple2))


def check_set_equality(the_set1, the_set2, partial_matches=False):
    """
    Check if two sets are equal, converting non-sets to length 1 Set

    If partial_matches is set, then check if just some elements
    match and return the fraction that match. 

    Return 
    1   if exact match
    p   number p, 0 < p < 1, if partial_matches is set and fracction
        p of elements match.  Denominator of fraction is max length of 
        both sets
    0   otherwise
    """

    # if either isn't a set, replace with a set of length 1
    if not isinstance(the_set1, set):
        the_set1 = {the_set1}
    if not isinstance(the_set2, set):
        the_set2 = {the_set2}

    if the_set1 == the_set2:
        return 1

    if not partial_matches:
        return 0
    
    return len(the_set1.intersection(the_set2))/max(len(the_set1),len(the_set2))

    
def check_matrix_equality(the_matrix1, the_matrix2, partial_matches=False):
    """
    Check if two matrices are equal

    If partial_matches is set and matrices are the same size,
    then check if just some elements match 
    and return the fraction that match. 

    Return 
    1   if exact match
    p   number p, 0 < p < 1, if partial_matches is set and fracction
        p of elements match.  Denominator of fraction is max rows*cols
        of both matrices
    0   otherwise
    """

    # if not the same class, then not equal.
    # This means MatrixAsVector and Matrix are not equal
    if the_matrix1.__class__ != the_matrix2.__class__:
        return 0
    
    if the_matrix1 == the_matrix2:
        return 1

    if not partial_matches or the_matrix1.shape != the_matrix2.shape:
        return 0
        
    n_matches=0
    for row in range(the_matrix1.rows):
        for col in range(the_matrix2.cols):
            try:
                if the_matrix1[row,col] == the_matrix2[row,col]:
                    n_matches +=1
            except IndexError:
                pass

    return n_matches/(the_matrix1.rows*the_matrix1.cols)
    

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
