
from sympy import Tuple, sympify, Abs, ImmutableMatrix, Derivative, Symbol
from sympy.core.relational import Relational, Equality, Unequality
from mitesting.customized_commands import evalf_expression, round_expression, normalize_floats
from mitesting.sympy_customized import bottom_up, latex
from django.utils.safestring import mark_safe

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
        sign_flip_partial_credit: give partial credit for answers that
            are correct except for sign flips
        sign_flip_partial_credit_percent: by what percent the credit will be
            multiplied by for sign flip
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
        if copy_parameters_from is not None:
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
    def __hash__(self):
        return hash(self._expression)
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
    def return_sign_flip_partial_credit(self):
        return self._parameters.get('sign_flip_partial_credit')
    def return_sign_flip_partial_credit_percent(self):
        return self._parameters.get('sign_flip_partial_credit_percent')
    def return_evaluate_level(self):
        from mitesting.sympy_customized import EVALUATE_FULL
        return self._parameters.get('evaluate_level', EVALUATE_FULL)
    def return_assume_real_variables(self):
        return self._parameters.get('assume_real_variables', False)
    def return_expression_type(self):
        return self._parameters.get('expression_type')

    def eval_to_comparison_precision(self, expression, 
                                     additional_rounding=None,
                                     evaluate=None):
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
                expression = round_expression(
                    expression, round_on_compare, evaluate=evaluate)
                modified = True
            elif round_on_compare > 0:
                expression = evalf_expression(
                    expression, round_on_compare, evaluate=evaluate)
                modified = True

        if not modified:
            expression = normalize_floats(expression, evaluate=evaluate)
            
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
        - n_sign_flips: number of sign flips found

        """
        round_level_required=self._parameters.get('round_on_compare')
        round_level_used=round_level_required
        round_absolute=self._parameters.get('round_absolute', False)

        results = {'fraction_equal': 0, 'fraction_equal_on_normalize': 0,
                   'round_level_used': round_level_used,
                   'round_level_required': round_level_required,
                   'round_absolute': round_absolute,
                   'n_sign_flips': 0}

        sub_results=self.compare_with_expression_sub(new_expr)

        results["fraction_equal"] = sub_results["fraction_equal"]
        results["fraction_equal_on_normalize"] = \
                        sub_results["fraction_equal_on_normalize"]

        # if completely correct, return results
        if results["fraction_equal"] == 1:
            return results

        round_partial_credit_digits = 0
        if round_level_required is not None:
            try:
                round_partial_credit_digits=int(self._parameters.get(
                    "round_partial_credit_digits", 0))
            except TypeError:
                pass
            
        check_sign_flips=self._parameters.get(
            "sign_flip_partial_credit", False)
        
        # if there is no possibility
        # of partial credit from extra rounding or sign flips
        # then we're done
        if not round_partial_credit_digits and not check_sign_flips:
            return results

        round_partial_credit_fraction = 0.0
        sign_flip_partial_credit_fraction = 0.0
        
        if round_partial_credit_digits:
            
            # round off at most 10 more digits for partial credit
            round_partial_credit_digits=min(10,round_partial_credit_digits)
            
            # don't go below 1 significant digit
            if not round_absolute:
                round_partial_credit_digits = min(round_level_required-1,
                                                  round_partial_credit_digits)

            # multiply credit by round_partial_credit_fraction
            # for each extra digit of rounding
            try:
                round_partial_credit_fraction = \
                    min(1.0, max(0.0, self._parameters.get(
                        "round_partial_credit_percent")/100.0))
            except TypeError:
                pass

        if check_sign_flips:
            try:
                sign_flip_partial_credit_fraction = \
                    min(1.0, max(0.0, self._parameters.get(
                        "sign_flip_partial_credit_percent")/100.0))
            except TypeError:
                pass
            

        max_credit=1.0
        credit_so_far = results["fraction_equal"]
        n_flips_so_far = 0
        correct_with_rounding = False
        
        if check_sign_flips:
            sub_results=self.compare_with_expression_sub(
                new_expr, check_sign_flips=check_sign_flips)
            n_flips = sub_results["n_flips"]
            credit_with_flips = sub_results["fraction_equal_flips"] \
                        * sign_flip_partial_credit_fraction**n_flips
            if credit_with_flips > credit_so_far:
                credit_so_far = credit_with_flips
                n_flips_so_far = n_flips
                
        for i in range(round_partial_credit_digits):
            additional_rounding = i+1
            max_credit *= round_partial_credit_fraction
            
            sub_results=self.compare_with_expression_sub(
                new_expr, additional_rounding=additional_rounding,
                check_sign_flips=check_sign_flips)
            credit = sub_results["fraction_equal"]
            
            credit_with_flips = 0
            n_flips=0
            if check_sign_flips:
                n_flips = sub_results["n_flips"]
                credit_with_flips = sub_results["fraction_equal_flips"] \
                            * sign_flip_partial_credit_fraction**n_flips

            used_flips = False
            if credit_with_flips > credit:
                credit = credit_with_flips
                user_flips = True
                
            credit *= max_credit
            
            if credit > credit_so_far:
                results['round_level_used'] = round_level_required \
                                              - additional_rounding
                if used_flips:
                    n_flips_so_far = n_flips
                else:
                    n_flips_so_far = 0
                credit_so_far = credit

            # even if no credit for additional rounding
            # record fact that found a match with additional rounding
            elif credit_so_far==0 and sub_results["fraction_equal"]==1 and not correct_with_rounding:
                correct_with_rounding=True
                results['round_level_used'] = round_level_required \
                                              - additional_rounding

        results['fraction_equal'] = credit_so_far
        results["n_sign_flips"] = n_flips_so_far
        
        return results


    def compare_with_expression_sub(self, new_expr, additional_rounding=None,
                                    check_sign_flips=False):
        """
        Compare expression of object with new_expression.
        Returns a dictionary with items:
        -fraction_equal
          1  if expressions are considered equal.
             If normalize_on_compare is set, then expressions are considered
             equal if their normalized expressions to the same.
             Otherwise, expressions themselves must be the same.
          0  if the expressions are not the same
          p  number p, 0 < p < 1, if expressions are partially equal,
             where p indicates the fraction of expressions that are equal
        -fraction_equal_on_normalize
         (set if larger than fraction_equal)
          1  the normalized expressions are the same.
          p  number p, 0 < p < 1, if the normalized expressions are
             partially equal, then
             p indicates the fraction of normalized expressions that are equal
          0  the normalized expressions are not equal
        - fraction_equal_flips
          (set if check_sign_flips and if larger than fraction_equal)
          1  if expressions are considered equal after sign flips
             If normalize_on_compare is set, then expressions are considered
             equal if their normalized expressions (after flips) to the same.
             Otherwise, expressions themselves (after flips) must be the same.
          0  if the expressions are not the same
          p  number p, 0 < p < 1, if expressions are partially equal,
             where p indicates the fraction of expressions that are equal
        - n_flips: number of sign flips required to get fraction correct
        - fraction_equal_on_normalize_flips
          (set if check_sign_flips and if larger than fraction_equal_flips)
          1  the normalized expressions (after flips) are the same.
          0  if the expressions are not the same
          p  number p, 0 < p < 1, if the normalized expressions are
             partially equal, then
             p indicates the fraction of normalized expressions that are equal
        - n_flips_on_normalize: number of sign flips required to get
             fraction correct on nomralize

        In all determinations of equality, expressions are rounded to
        the precision determined by round_on_compare and round_absolute, if set,
        minus any additional rounding specified.
        """

        from mitesting.sympy_customized import EVALUATE_NONE

        expression=self._expression

        evaluate_level = self.return_evaluate_level()

        if evaluate_level != EVALUATE_NONE:
            comparison_evaluate = None
        else:
            comparison_evaluate = False

        # replace Symbol('lamda') with Symbol('lambda')
        def replace_lamda(w):
            if w == Symbol('lamda'):
                return Symbol('lambda')
            elif w == Symbol('lamda', real=True):
                return Symbol('lambda', real=True)
            else:
                return w

        expression = bottom_up(expression, replace_lamda,
                               evaluate=comparison_evaluate, atoms=True)
        new_expr = bottom_up(new_expr, replace_lamda,
                             evaluate=comparison_evaluate, atoms=True)

        # As long as evaluate is not False
        # convert customized ln command to customized log command
        # also convert sympy log to customized log command
        if evaluate_level != EVALUATE_NONE:
            from .user_commands import log, ln
            from sympy import log as sympy_log
            def replace_logs(w):
                if w.func == ln or w.func == sympy_log:
                    return log(*w.args)
                else:
                    return w
            expression = bottom_up(expression, replace_logs)
            new_expr = bottom_up(new_expr, replace_logs)


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
        new_expr = self.eval_to_comparison_precision(
            new_expr, additional_rounding=additional_rounding,
            evaluate=comparison_evaluate)
        expression = self.eval_to_comparison_precision(
            expression, additional_rounding=additional_rounding,
            evaluate=comparison_evaluate)

        tuple_is_unordered = self._parameters.get('tuple_is_unordered',False)
        match_partial_on_compare = self._parameters.get(
            'match_partial_on_compare',False)
        
        results = {'fraction_equal': 0, 'fraction_equal_on_normalize': 0,
                   'fraction_equal_flips': 0, 'n_flips': 0,
                   'fraction_equal_on_normalize_flips': 0,
                   'n_flips_on_normalize': 0 }

        if self._parameters.get('normalize_on_compare'):
            sub_results = check_equality \
                (expression_normalize, new_expr_normalize, \
                 tuple_is_unordered=tuple_is_unordered, \
                 partial_matches = match_partial_on_compare,
                 check_sign_flips=check_sign_flips)
            results["fraction_equal"] = sub_results["fraction_equal"]
            if check_sign_flips:
                results["fraction_equal_flips"] = \
                                sub_results["fraction_equal_flips"]
                results["n_flips"] = sub_results["n_flips"]
            
            # if not exactly equal, check without normalizing
            # just in case normalizing made answers diverge
            if results["fraction_equal"] != 1:
                sub_results = check_equality \
                    (expression, new_expr, \
                     tuple_is_unordered=tuple_is_unordered, \
                     partial_matches = match_partial_on_compare,
                     check_sign_flips=check_sign_flips)
                results["fraction_equal"] = max(results["fraction_equal"],
                                                sub_results["fraction_equal"])

                # if check sign flips, then check if get fewer flips or
                # better result without normalizing
                if check_sign_flips:
                    if sub_results["fraction_equal_flips"] \
                       > results["fraction_equal_flips"]:
                        results["fraction_equal_flips"] = \
                                        sub_results["fraction_equal_flips"]
                        results["n_flips"] = sub_results["n_flips"]
                    elif sub_results["fraction_equal_flips"] \
                         == results["fraction_equal_flips"]:
                        results["n_flips"] = min(results["n_flips"],
                                                 sub_results["n_flips"])
                        
                    
        else:
            sub_results = check_equality \
                (expression, new_expr, \
                 tuple_is_unordered=tuple_is_unordered, \
                 partial_matches = match_partial_on_compare,
                 check_sign_flips = check_sign_flips)
            results["fraction_equal"] = sub_results["fraction_equal"]
            if check_sign_flips:
                results["fraction_equal_flips"] = \
                                sub_results["fraction_equal_flips"]
                results["n_flips"] = sub_results["n_flips"]

            if results["fraction_equal"] != 1:
                sub_results = check_equality \
                    (expression_normalize, new_expr_normalize, \
                     tuple_is_unordered=tuple_is_unordered, \
                     partial_matches = match_partial_on_compare,
                     check_sign_flips=check_sign_flips)
                results["fraction_equal_on_normalize"] = \
                                        sub_results["fraction_equal"]
                if check_sign_flips:
                    results["fraction_equal_on_normalize_flips"] = \
                                    sub_results["fraction_equal_flips"]
                    results["n_flips_on_normalize"] = sub_results["n_flips"]


        return results

        

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
    Convert any subclass of ImmutableMatrix to ImmutableMatrix.
    Convert any subclass of Derivative to Derivative
    Convert customized log commands to sympy log
    Use doit, expand, then ratsimp to simplify rationals, then expand again
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

    from .user_commands import log, ln
    from sympy import log as sympy_log
    def replace_logs_to_sympy(w):
        if w.func == ln or w.func == log:
            return sympy_log(*w.args)
        else:
            return w

    def normalize_transformations(w):
        # same as
        #    lambda w: w.doit().expand().ratsimp().expand()
        # except catch Polynomial error that could be triggered by ratsimp()
        # and catch attribute error for objects like Interval
        from sympy import PolynomialError
        w=w.doit()
        try:
            w= w.expand()
        except (AttributeError, TypeError):
            pass
        if w.has(sympy_log):
            from sympy import logcombine
            try:
                w = logcombine(w)
            except TypeError:
                pass
        try:
            w=w.ratsimp().expand()
        except (AttributeError,PolynomialError,UnicodeEncodeError, TypeError):
            pass
        return w

    expr=bottom_up(expr, 
                   lambda w: w if not isinstance(w,ImmutableMatrix) \
                   else ImmutableMatrix(*w.args),
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


    # replace logs with sympy log
    expr = bottom_up(expr, replace_logs_to_sympy)
    # transformations to try to normalize
    expr= bottom_up(expr, normalize_transformations)
    # remove any cofficients of 1.0
    #expr=bottom_up(expr, _remove_one_coefficient)
    
    return(expr)

def check_equality(expression1, expression2, tuple_is_unordered=False, \
                   partial_matches=False, check_sign_flips=False):
    """ 
    Determine if expression1 and expression2 are equal.
    If tuple_is_unordered is set, then tuples are compared regardless of order.

    Returns dictionary with items:
    - fraction_equal:
      1   if correct
      0   if completely incorrect
      p   number p, 0 < p < 1 indicating fraction correct 
          in case is partially correct
    - fraction_equal_flips
      1   if correct
      0   if completely incorrect
      p   number p, 0 < p < 1 indicating fraction correct 
          in case is partially correct
    - n_flips: number of sign flips required to get fraction correct

    In general, if two objects latex the same, they should compare 
    as being equal.
    - vectors compare equal to tuples and Tuples but not TupleNoParens
    - open intervals compare equal to tuples and Tuples but not TupleNoParens
    - closed intervals copare equal to lists
    However, open intervals do not compare equal to vectors.

    These equalities are already implemented at the class level, 
    here we implement for partial matches and unordered tuples.

    """
        
    from sympy.geometry.line import LinearEntity
 
    if isinstance(expression1, Tuple) or isinstance(expression2, Tuple) \
       or isinstance(expression1, list) or isinstance(expression2, list):
        return check_tuple_equality(expression1, expression2, 
                                    tuple_is_unordered=tuple_is_unordered,
                                    partial_matches=partial_matches,
                                    check_sign_flips=check_sign_flips)

    if isinstance(expression1, set) or isinstance(expression2, set):
        return check_set_equality(expression1, expression2, 
                                  partial_matches=partial_matches,
                                  check_sign_flips=check_sign_flips)

    if isinstance(expression1, ImmutableMatrix) or \
       isinstance(expression2, ImmutableMatrix):
        return check_matrix_equality(expression1, expression2, 
                                     partial_matches=partial_matches,
                                     check_sign_flips=check_sign_flips)

    try:
        if expression1.is_Relational or expression2.is_Relational:
            return check_relational_equality(expression1, expression2,
                                             check_sign_flips=check_sign_flips)
    except AttributeError:
        pass

    if isinstance(expression1, LinearEntity) or \
         isinstance(expression2, LinearEntity):
        results = {'fraction_equal': 0, 'fraction_equal_flips': 0, 'n_flips': 0}
        try:
            if expression1.is_similar(expression2):
                results["fraction_equal"] = 1
        except AttributeError:
            pass
        return results
        

    from sympy.core.function import Application
    
    if isinstance(expression1, Application) and \
       isinstance(expression2, Application):
        return check_function_equality(expression1, expression2, 
                                       partial_matches=partial_matches,
                                       check_sign_flips=check_sign_flips)

    return check_equality_direct(expression1, expression2,
                                 check_sign_flips=check_sign_flips)


def check_equality_direct(expression1, expression2, check_sign_flips=False):
    """ 
    Determine if expression1 and expression2 are equal with no manipulations
    other than checking for sign flips

    Returns dictionary with items:
    - fraction_equal:
      1   if correct
      0   otherwise
    - fraction_equal_flips
      1   if correct with sign flips
      0   otherwise
    - n_flips: number of sign flips required to get fraction correct

    """

    results = {'fraction_equal': 0, 'fraction_equal_flips': 0, 'n_flips': 0}

    if expression1 == expression2:
        results["fraction_equal"] = 1
        return results

    if check_sign_flips:
        from .utils import find_equality_with_sign_errors
        sub_results = find_equality_with_sign_errors(expression1, expression2)
        if sub_results["success"]:
            results["fraction_equal_flips"] = 1
            results["n_flips"] = sub_results["num_applications"]

    return results

    
def check_tuple_equality(the_tuple1, the_tuple2, tuple_is_unordered=False, \
                         partial_matches=False, check_sign_flips=False):
    """
    Check if two Tuples or lists are equal, 
    converting vectors and open intervals to Tuples,
    closed intervals to lists,
    and other non-Tuples/lists to length 1 TupleNoParens.

    If tuple_is_unordered is set, then check if elements match
    regardless of order.
    If partial_matches is set, then check if just some elements
    match and return the fraction that match.  For ordered tuples, 
    the matching elements must be in the same order.

    If one tuple is a Tuple and the other is a TupleNoParen, regard as unequal

    Returns dictionary with items:
    - fraction_equal:
      1   if exact match
      p   number p, 0 < p < 1, if partial_matches is set and fracction
          p of elements match.  Denominator of fraction is max length of 
          both tuples
      0   otherwise
    - fraction_equal_flips
      1   if exact match
      p   number p, 0 < p < 1, if partial_matches is set and fracction
          p of elements match.  Denominator of fraction is max length of 
          both tuples
      0   otherwise
    - n_flips: number of sign flips required to get fraction correct

    """

    from .sympy_customized import TupleNoParen, Interval
    from .customized_commands import MatrixAsVector

    results = {'fraction_equal': 0, 'fraction_equal_flips': 0, 'n_flips': 0}
    
    # convert vectors, open intervals, and tuples to Tuples
    # closed intervals to lists,
    # and other non-Tuples/lists to length 1 TupleNoParens.
    if not isinstance(the_tuple1, Tuple) and not isinstance(the_tuple1,list):
        if isinstance(the_tuple1, MatrixAsVector) or \
           isinstance(the_tuple1, tuple):
            the_tuple1 = Tuple(*the_tuple1)
        elif isinstance(the_tuple1, Interval):
            if the_tuple1.left_open:
                if the_tuple1.right_open:
                    the_tuple1 = Tuple(the_tuple1.left,the_tuple1.right)
                else:
                    return results
            else:
                if the_tuple1.right_open:
                    return results
                else:
                    the_tuple1 = [the_tuple1.left,the_tuple1.right]
        else:
            the_tuple1 = TupleNoParen(the_tuple1)

    if not isinstance(the_tuple2, Tuple) and not isinstance(the_tuple2,list):
        if isinstance(the_tuple2, MatrixAsVector) or \
           isinstance(the_tuple2, tuple):
            the_tuple2 = Tuple(*the_tuple2)
        elif isinstance(the_tuple2, Interval):
            if the_tuple2.left_open:
                if the_tuple2.right_open:
                    the_tuple2 = Tuple(the_tuple2.left,the_tuple2.right)
                else:
                    return results
            else:
                if the_tuple2.right_open:
                    return results
                else:
                    the_tuple2 = [the_tuple2.left,the_tuple2.right]
        else:
            the_tuple2 = TupleNoParen(the_tuple2)


    # if not same class, then not considered equal.
    # Tuples and TupleNoParens are considered different
    if the_tuple1.__class__ != the_tuple2.__class__:
        return results

    nelts1=len(the_tuple1)
    nelts2=len(the_tuple2)


    # if tuple_is_unordered isn't set, demand exact equality
    if not tuple_is_unordered:
        
        # check how many elements match in order from the beginning
        n_matches=0
        n_matches_flip=0
        n_flips=0
        for i in range(min(nelts1, nelts2)):
            sub_results = check_equality(the_tuple1[i], the_tuple2[i],
                                         check_sign_flips=check_sign_flips)

            n_matches += sub_results["fraction_equal"]

            if check_sign_flips:
                n_matches_flip += sub_results["fraction_equal_flip"]
                n_flips += sub_results["n_flips"]

        # if tuple lengths are equal and all match, then exact equality
        if nelts1==nelts2 and nelts1==n_matches:
            results["fraction_equal"] = 1
            return results

        if check_sign_flips:
            if nelts1==nelts2 and nelts1==n_matches_flip:
                results["fraction_equal_flip"] = 1
                results["n_flips"] = n_flips

        if not partial_matches:
            return results


        # if partial matches, find length of largest common subsequence

        from sympy import zeros
        C = zeros(nelts1+1,nelts2+1)
        C_sign_flips = zeros(nelts1+1,nelts2+1)
        C_n_flips = zeros(nelts1+1,nelts2+1)
        for i in range(nelts1):
            for j in range(nelts2):
                sub_results = check_equality(the_tuple1[i], the_tuple2[j],
                                             check_sign_flips=check_sign_flips)
                C[i+1,j+1] = max(C[i,j]+sub_results['fraction_equal'],
                                 C[i+1,j],C[i,j+1])
                
                if check_sign_flips:
                    # For sign flips, it is more complicated,
                    # as have to keep track of minimum number of sign flips
                    # to get the maximum match.
                    # This algorithm does not find the best possible score
                    # (as we don't have access to penalty for sign flips).
                    # Instead, if finds the best possible match, giving
                    # the minimum number of flips for that match
                    
                    C1 = C_sign_flips[i,j] + \
                         sub_results['fraction_equal_flips']
                    N1 = C_n_flips[i,j] + sub_results['n_flips']
                    C2 = C_sign_flips[i+1,j]
                    N2 = C_n_flips[i+1,j]
                    C3 = C_sign_flips[i,j+1]
                    N3 = C_n_flsip[i,j+1]
                    
                    if C1 > C2:
                        if C1 > C3:
                            C_sign_flips[i+1,j+1] = C1
                            C_n_flips[i+1,j+1] = N1
                        elif C1 == C3:
                            C_sign_flips[i+1,j+1] = C1
                            C_n_flips[i+1,j+1] = min(N1,N3)
                        else:
                            C_sign_flips[i+1,j+1] = C3
                            C_n_flips[i+1,j+1] = N3
                    elif C1==C2:
                        if C1 > C3:
                            C_sign_flips[i+1,j+1] = C1
                            C_n_flips[i+1,j+1] = min(N1,N2)
                        elif C1==C3:
                            C_sign_flips[i+1,j+1] = C1
                            C_n_flips[i+1,j+1] = min(N1,N2,N3)
                        else:
                            C_sign_flips[i+1,j+1] = C3
                            C_n_flips[i+1,j+1] = N3
                    else:
                        if C2 > C3:
                            C_sign_flips[i+1,j+1] = C2
                            C_n_flips[i+1,j+1] = N2
                        elif C2 == C3:
                            C_sign_flips[i+1,j+1] = C2
                            C_n_flips[i+1,j+1] = min(N2,N3)
                        else:
                            C_sign_flips[i+1,j+1] = C3
                            C_n_flips[i+1,j+1] = N3

                    
        
        max_matched = float(C[nelts1,nelts2])  # float so don't get sympy rational

        results["fraction_equal"] = max_matched/max(nelts1,nelts2)

        if check_sign_flips:
            max_matched_sign_flips = float(C_sign_flips[nelts1,nelts2]) 
            results["fraction_equal_flips"] = \
                max_matched_sign_flips/max(nelts1,nelts2)
            results["n_flips"] = C_n_flips[nelts1,nelts2]
            
        return results

    # if not ordered, check if match with any order
    
    # loop through all elements of tuple 1
    # for each element, look for a matching element of tuple 2
    # that has not been used yet.
    tuple2_indices_used=[]
    n_matches=0
    tuple2_indices_used_flip=[]
    n_flip_matches=0
    n_flips=0
    for expr1 in the_tuple1:
        best_match_ind=-1
        best_match=0
        best_flip_match_ind=-1
        best_flip_match=0
        best_n_flips=0
        for (i, expr2) in enumerate(the_tuple2):
            if i in tuple2_indices_used and i in tuple2_indices_used_flip:
                continue
            
            sub_results = check_equality(expr1,expr2,
                                         check_sign_flips=check_sign_flips)
            
            if i not in tuple2_indices_used and \
               sub_results["fraction_equal"] > best_match:
                best_match = sub_results["fraction_equal"]
                best_match_ind = i
                
            if check_sign_flips and i not in tuple2_indices_used_flip and \
               (sub_results["fraction_equal_flips"] > best_flip_match or
                (sub_results["fraction_equal_flips"] == best_flip_match
                 and sub_results["n_flips"] < best_n_flips)):
                
                best_flip_match= sub_results["fraction_equal_flips"]
                best_flip_match_ind = i
                best_n_flips = sub_results["n_flips"]
                
                
        if best_match_ind != -1:
            n_matches += best_match
            tuple2_indices_used.append(best_match_ind)
        if best_flip_match_ind != -1:
            n_flip_matches += best_flip_match
            tuple2_indices_used_flip.append(best_flip_match_ind)
            n_flips += best_n_flips
            
    if nelts1==nelts2 and nelts1==n_matches:
        results["fraction_equal"] = 1

    if check_sign_flips and nelts1==nelts2 and nelts1==n_flip_matches:
        results["fraction_equal_flips"] = 1
        results["n_flips"] = n_flips
        
    if not partial_matches:
        return results

    results["fraction_equal"] = float(n_matches)/max(nelts1,nelts2)
    if check_sign_flips:
        results["fraction_equal_flips"] =\
                                    float(n_flip_matches)/max(nelts1,nelts2)
        results["n_flips"] = n_flips

    return results
            


def check_set_equality(the_set1, the_set2, partial_matches=False,
                       check_sign_flips=False):
    """
    Check if two sets are equal, converting non-sets to length 1 Set

    If partial_matches is set, then check if just some elements
    match and return the fraction that match. 

    Returns dictionary with items:
    - fraction_equal:
      1   if exact match
      p   number p, 0 < p < 1, if partial_matches is set and fracction
          p of elements match.  Denominator of fraction is max length of 
          both sets
      0   otherwise
    - fraction_equal_flips
      1   if exact match
      p   number p, 0 < p < 1, if partial_matches is set and fracction
          p of elements match.  Denominator of fraction is max length of 
          both sets
      0   otherwise
    - n_flips: number of sign flips required to get fraction correct

    """

    results = {'fraction_equal': 0, 'fraction_equal_flips': 0, 'n_flips': 0}

    # if either isn't a set, replace with a set of length 1
    if not isinstance(the_set1, set):
        the_set1 = {the_set1}
    if not isinstance(the_set2, set):
        the_set2 = {the_set2}

    results = check_equality_direct(the_set1, the_set2,
                                    check_sign_flips=check_sign_flips)

    if results["fraction_equal"] == 1 or not partial_matches:
        return results

    results["fraction_equal"] = len(the_set1.intersection(the_set2)) \
                                  /max(len(the_set1),len(the_set2))

    if check_sign_flips:
        # to check for sign flips, just turn to unordered tuples logic
        sub_results = check_tuple_equality(
            tuple(the_set1), tuple(the_set2),
            tuple_is_unordered=True, 
            partial_matches=partial_matches, check_sign_flips=True)
        
        results["fraction_equal_flips"]=sub_results["fraction_equal_flips"]
        results["n_flips"] = sub_results["n_flips"]

    return results
    
    
def check_matrix_equality(the_matrix1, the_matrix2, partial_matches=False,
                          check_sign_flips=False):
    """
    Check if two matrices are equal

    If partial_matches is set and matrices are the same size,
    then check if just some elements match 
    and return the fraction that match. 

    Returns dictionary with items:
    - fraction_equal:
      1   if exact match
      p   number p, 0 < p < 1, if partial_matches is set and fracction
          p of elements match.  Denominator of fraction is max length of 
          both matrices
      0   otherwise
    - fraction_equal_flips
      1   if exact match
      p   number p, 0 < p < 1, if partial_matches is set and fracction
          p of elements match.  Denominator of fraction is max length of 
          both matrices
      0   otherwise
    - n_flips: number of sign flips required to get fraction correct

    """

    results = {'fraction_equal': 0, 'fraction_equal_flips': 0, 'n_flips': 0}

    # if not the same class, then not equal.
    # This means MatrixAsVector and Matrix are not equal
    if the_matrix1.__class__ != the_matrix2.__class__:
        return results
    
    results = check_equality_direct(the_matrix1, the_matrix2,
                                    check_sign_flips=check_sign_flips)

    if results["fraction_equal"] == 1 or not partial_matches:
        return results

    if the_matrix1.shape != the_matrix2.shape:
        return results
        
    n_matches=0
    n_flip_matches=0
    n_flips=0
    for row in range(the_matrix1.rows):
        for col in range(the_matrix1.cols):
            sub_results= check_equality(
                the_matrix1[row,col],the_matrix2[row,col],
                check_sign_flips=check_sign_flips)
            n_matches += sub_results["fraction_equal"]
            if check_sign_flips:
                n_flip_matches += sub_results["fraction_equal_flips"]
                n_flips += sub_results["n_flips"]

    
    results["fraction_equal"] = n_matches/(the_matrix1.rows*the_matrix1.cols)

    if check_sign_flips:
        results["fraction_equal_flips"] = \
                    n_flip_matches/(the_matrix1.rows*the_matrix1.cols)
        results["n_flips"] = n_flips

    return results


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



def check_relational_equality(the_relational1, the_relational2,
                              check_sign_flips=False):
    """ 
    Check if two relations are equivalent.

    Returns dictionary with items:
    - fraction_equal:
      1   if equivalent
      0   otherwise
    - fraction_equal_flips
      1   if equivalent after sign flips
      0   otherwise
    - n_flips: number of sign flips required to get fraction correct

    """

    # if relations are exactly the same, we're done
    results = check_equality_direct(the_relational1, the_relational2,
                                    check_sign_flips=check_sign_flips)

    if results["fraction_equal"] == 1:
        return results

    
    # if relations aren't the same, they could be inequalities
    # with the sides reversed.
    # Check if both strict or both not strict
    # and that the larger and small sides are equal
    if (is_strict_inequality(the_relational1) and \
            is_strict_inequality(the_relational2)) or \
            (is_nonstrict_inequality(the_relational1) and \
                 is_nonstrict_inequality(the_relational2)):
        sub_results1 = check_equality_direct(
            the_relational1.lts, the_relational2.lts,
            check_sign_flips=check_sign_flips)
        sub_results2 = check_equality_direct(
            the_relational1.gts, the_relational2.gts,
            check_sign_flips=check_sign_flips)
        if sub_results1["fraction_equal"] == 1 and \
           sub_results2["fraction_equal"] == 1 :
            results["fraction_equal"] = 1
            return results
        
        if check_sign_flips:
            if sub_results1["fraction_equal_flips"] == 1 and \
               sub_results2["fraction_equal_flips"] == 1:
                n_flips_tot = sub_results1["n_flips"] + \
                              sub_results2["n_flips"]
                if results["fraction_equal_flips"] ==1:
                    results["n_flips"] = min(result["n_flips"], n_flips_tot)
                else:
                    results["n_flips"] = n_flips_tot
                    
        return results

    
    # if both equalities or inequalities, they could be the same
    # except with sides reversed
    if (isinstance(the_relational1, Equality) and \
            isinstance(the_relational2, Equality)) or \
            (isinstance(the_relational1, Unequality) and \
                 isinstance(the_relational2, Unequality)):
        # just need to check if the sides are reversed.
        # (If the sides were the same, initial check would have shown
        # them to be equal.)
        sub_results1 = check_equality_direct(
            the_relational1.lhs, the_relational2.rhs,
            check_sign_flips=check_sign_flips)
        sub_results2 = check_equality_direct(
            the_relational1.rhs, the_relational2.lhs,
            check_sign_flips=check_sign_flips)
        if sub_results1["fraction_equal"] == 1 and \
           sub_results2["fraction_equal"] == 1 :
            results["fraction_equal"] = 1
            return results

        if check_sign_flips:
            if sub_results1["fraction_equal_flips"] == 1 and \
               sub_results2["fraction_equal_flips"] == 1:
                n_flips_tot = sub_results1["n_flips"] + \
                              sub_results2["n_flips"]
                if results["fraction_equal_flips"] ==1:
                    results["n_flips"] = min(result["n_flips"], n_flips_tot)
                else:
                    results["n_flips"] = n_flips_tot
                    
        return results

    # if have different types of relations, they must be unequal
    return results


def check_function_equality(the_function1, the_function2,
                            partial_matches=False,
                            check_sign_flips=False):
    """ 
    Check if two functions are equal.

    To be equal required that
    1. func attribute is identical
    2. the arguments compare equal as tuples

    Returns dictionary with items:
    - fraction_equal:
      1   if exact match
      p   number p, 0 < p < 1, if partial_matches is set, the func attributes
          match and and fraction p of arguments match.  
          Denominator of fraction is max length of both argument tuples
      0   otherwise
    - fraction_equal_flips
      1   if exact match after sign flips
      p   number p, 0 < p < 1, if partial_matches is set, the func attributes
          match and and fraction p of arguments match.  
          Denominator of fraction is max length of both argument tuples
      0   otherwise
    - n_flips: number of sign flips required to get fraction correct


    We cannot rely on canonical sorting of arguments
    since we may consider some expressions
    that are not exactly the same to be equivalent.
    Hence, for a function in which order does not matter, 
    one should compare arguments as unordered tuple.

    For now, just maintain a list of functions for which we consider
    the arguments to be unordered.
    
    """

    # if relations are exactly the same, we're done
    results = check_equality_direct(the_function1, the_function2,
                                    check_sign_flips=check_sign_flips)

    if results["fraction_equal"] == 1:
        return results

    # if different func attribute, then they are different
    if the_function1.func != the_function2.func:
        return results

    from mitesting.sympy_customized import And, Or

    functions_unordered_arguments = [And, Or]
    
    if the_function1.func in functions_unordered_arguments:
        unordered_arguments=True
    else:
        unordered_arguments=False

    return check_tuple_equality(the_function1.args, the_function2.args, \
                                tuple_is_unordered=unordered_arguments, \
                                partial_matches=partial_matches,
                                check_sign_flips=check_sign_flips)

