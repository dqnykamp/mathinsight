
from django.test import SimpleTestCase
from mitesting.sympy_customized import bottom_up, parse_expr, \
    parse_and_process, EVALUATE_NONE, EVALUATE_PARTIAL, EVALUATE_FULL, latex    
from mitesting.customized_commands import normalize_floats
from sympy import diff, Tuple, sympify, Integer, Symbol

class BottomUpTests(SimpleTestCase):
    
    def test_rounds_numbers_to_integers(self):
        expr = bottom_up(sympify("2.0*x"), lambda w: w if not w.is_Number else Integer(w.round()), atoms=True)
        self.assertEqual(str(expr), "2*x")

    def test_evalf_accepted_each_atom(self):
        expr = bottom_up(sympify("sin(x/3)"), lambda w: w if not w.is_Number else w.evalf(4), atoms=True)
        self.assertEqual(str(expr), "sin(0.3333*x)")

    def test_substitute_list_tuple(self):
        x=Symbol('x')
        y=Symbol('y')
        z=Symbol('z')
        expr = bottom_up((x,y,z), lambda w: w if not w==x else Tuple(x,y), atoms=True)
        self.assertEqual(expr, ((x,y),y,z))

        expr = bottom_up((x,y,z), lambda w: w if not w==x else [x,y], atoms=True)
        self.assertEqual(expr, ([x,y],y,z))

        self.assertRaises(AttributeError, 
                          bottom_up, x**2, 
                          lambda w: w if not w==x else Tuple(x,y),
                          atoms=True)

class ParseExprTests(SimpleTestCase):


    def test_basics_with_empty_local_dict(self):
        x = Symbol('x')
        y = Symbol('y')
        self.assertEqual(parse_expr("5x", local_dict={}), 5*x)
        local_dict = {}
        self.assertEqual(parse_expr("3y^2", local_dict=local_dict),
                          3*y**2)
        # verify local_dict is still empty
        self.assertEqual(local_dict, {})
        self.assertEqual(parse_expr("log(x)", local_dict={}),
                          Symbol('log')*x)

    def test_basics_with_no_local_dict(self):
        x = Symbol('x')
        self.assertEqual(parse_expr("5x"), 5*x)
        self.assertEqual(parse_expr("3x^2"), 3*x**2)
        self.assertEqual(parse_expr("log(x)"), Symbol('log')*x)
        
    def test_implicit_convert_xor(self):
        x = Symbol('x')
        self.assertEqual(parse_expr("3x^2/5", local_dict={}), 
                          x**2*sympify("3/5"))
        self.assertEqual(
            normalize_floats(parse_expr("3x^2/5.", local_dict={})), 
            normalize_floats(0.6*x**2))

    def test_implicit_multiplication(self):
        x = Symbol('x')
        y = Symbol('y')
        self.assertEqual(parse_expr("5x"), 5*x)
        self.assertEqual(parse_expr("5 x"), 5*x)
        self.assertEqual(parse_expr("5*x"), 5*x)
        self.assertEqual(parse_expr("5 x y"), 5*x*y)

    def test_assume_real(self):
        x = Symbol('x')
        y = Symbol('y')
        x_real = Symbol('x', real=True)
        y_real = Symbol('y', real=True)
        
        self.assertEqual(parse_expr("5 x y-y^3/x"), 5*x*y-y**3/x)
        self.assertEqual(parse_expr("5 x y-y^3/x", assume_real_variables=False),
                         5*x*y-y**3/x)
        self.assertEqual(parse_expr("5 x y-y^3/x", assume_real_variables=True),
                         5*x_real*y_real-y_real**3/x_real)
        

    def test_split_symbols(self):
        x = Symbol('x')
        y = Symbol('y')
        xy = Symbol('xy')
        self.assertEqual(parse_expr("5xy"), 5*xy)
        self.assertEqual(parse_expr("5xy", split_symbols=False), 5*xy)
        self.assertEqual(parse_expr("5xy", split_symbols=True), 5*x*y)

        expr=parse_expr("x61y", split_symbols=True)
        self.assertEqual(expr, 61*x*y)

        x = Symbol('x', real=True)
        y = Symbol('y', real=True)
        xy = Symbol('xy', real=True)
        expr=parse_expr("5xy", assume_real_variables=True)
        self.assertEqual(expr, 5*xy)
        expr=parse_expr("5xy", split_symbols=False, assume_real_variables=True)
        self.assertEqual(expr, 5*xy)
        expr=parse_expr("5xy", split_symbols=True, assume_real_variables=True)
        self.assertEqual(expr, 5*x*y)


    def test_rationals_floats(self):
        x = Symbol('x')
        self.assertEqual(parse_expr("3x^2/5"), x**2*sympify("3/5"))
        self.assertEqual(
            normalize_floats(parse_expr("3x^2/5.")), 
            normalize_floats(0.6*x**2))

    def test_e_with_split_symbols(self):
        from sympy import E, exp
        x = Symbol('x')
        self.assertEqual(parse_expr("3*x*e^x", local_dict={'e': E}),
                          3*x*exp(x))
        self.assertEqual(parse_expr("3x*e^x", local_dict={'e': E}),
                          3*x*exp(x))
        self.assertEqual(parse_expr("3xe^x", split_symbols=True,
                                     local_dict={'e': E}),
                          3*x*exp(x))
        
    def test_with_tuples(self):
        x = Symbol('x')
        y = Symbol('y')
        self.assertEqual(parse_expr("(x,y)"), Tuple(x,y))


    def test_lambda_symbol(self):
        lambda_symbol = Symbol('lambda')
        x = Symbol('x')
        y = Symbol('y')
        self.assertEqual(parse_expr("lambda"), lambda_symbol)
        self.assertEqual(parse_expr("x-lambda+y"), -lambda_symbol+x+y)
        self.assertEqual(parse_expr("lambda(x)(y)"), lambda_symbol*x*y)

    def test_lambda_symbol_substitutions(self):
        x = Symbol('x')
        y = Symbol('y')
        lambda_symbol = Symbol('lambda')
        sub_dict = {'lambda': 2*x*y}
        self.assertEqual(parse_expr("lambda^2+x+y"), lambda_symbol**2+x+y)
        self.assertEqual(parse_expr("lambda^2+x+y", global_dict=sub_dict),
                         4*x**2*y**2+x+y)
        self.assertEqual(parse_expr("lambda^2+x+y", local_dict=sub_dict),
                         4*x**2*y**2+x+y)
        self.assertEqual(parse_expr("lambda^2+x+y", local_dict=sub_dict,
                                    global_dict=sub_dict), 4*x**2*y**2+x+y)

    def test_as_symbol(self):
        as_symbol = Symbol('as')
        x = Symbol('x')
        y = Symbol('y')
        self.assertEqual(parse_expr("as"), as_symbol)
        self.assertEqual(parse_expr("x-as+y"), -as_symbol+x+y)
        self.assertEqual(parse_expr("as(x)(y)"), as_symbol*x*y)

    def test_as_symbol_substitutions(self):
        x = Symbol('x')
        y = Symbol('y')
        as_symbol = Symbol('as')
        sub_dict = {'as': 2*x*y}
        self.assertEqual(parse_expr("as^2+x+y"), as_symbol**2+x+y)
        self.assertEqual(parse_expr("as^2+x+y", global_dict=sub_dict),
                         4*x**2*y**2+x+y)
        self.assertEqual(parse_expr("as^2+x+y", local_dict=sub_dict),
                         4*x**2*y**2+x+y)

    def test_greek_unicode(self):
        s1 = "alpha^2*beta/(gamma-epsilon^2)+ delta^2(zeta)eta^3/theta -(iota^2-kappa^2)^2/(lambda/mu-nu+xi)+ pi^2rho^3/(sigma+tau^2) + phi*psi^3/omega"
        s2 = "α^2*β/(γ-ε^2)+δ^2(ζ)η^3/θ-(ι^2-κ^2)^2/(λ/μ-ν+ξ)+π^2ρ^3/(σ+τ^2) + φ*ψ^3/ω"
        expr1 = parse_expr(s1, split_symbols=True)
        expr2 = parse_expr(s2, split_symbols=True)
        self.assertEqual(expr1,expr2)
        
        s1="ϵϕ"
        s2='εφ'
        expr1 = parse_expr(s1, split_symbols=True)
        expr2 = parse_expr(s2, split_symbols=True)
        self.assertEqual(expr1,expr2)
        

    def test_if_symbol(self):
        if_symbol = Symbol('if')
        x = Symbol('x')
        y = Symbol('y')
        self.assertEqual(parse_expr("if"), if_symbol)
        self.assertEqual(parse_expr("x-if+y"), -if_symbol+x+y)
        self.assertEqual(parse_expr("if(x)(y)"), if_symbol*x*y)

    def test_if_symbol_substitutions(self):
        x = Symbol('x')
        y = Symbol('y')
        if_symbol = Symbol('if')
        sub_dict = {'if': 2*x*y}
        self.assertEqual(parse_expr("if^2+x+y"), if_symbol**2+x+y)
        self.assertEqual(parse_expr("if^2+x+y", global_dict=sub_dict),
                         4*x**2*y**2+x+y)
        self.assertEqual(parse_expr("if^2+x+y", local_dict=sub_dict),
                         4*x**2*y**2+x+y)

    def test_if_as_iif(self):
        from mitesting.user_commands import iif
        x = Symbol('x')
        sub_dict = {'if': iif}
        self.assertEqual(parse_expr('if(4>3,x,y)', local_dict=sub_dict),x)
        self.assertEqual(parse_expr('if(-4>3,y,x^2)', 
                                    local_dict=sub_dict),x**2)
        f = parse_expr('if(x=1,2,if(x>1,3,0))',local_dict=sub_dict)
        self.assertEqual(f.subs(x,1),2)
        self.assertEqual(f.subs(x,-1),0)
        self.assertEqual(f.subs(x,2),3)
        

    def test_no_evaluate(self):
        expr_no_evaluate = parse_expr("x - lambda + x + 2*lambda",
                                      evaluate=False)
        expr = parse_expr("x - lambda + x + 2*lambda")
        expr_with_evaluate = parse_expr("x + x - lambda + 2*lambda",
                                        evaluate=True)
        self.assertNotEqual(expr_no_evaluate, expr)
        self.assertEqual(expr, expr_with_evaluate)
        self.assertEqual(repr(expr_no_evaluate),'x - lambda + x + 2*lambda')

        expr1=parse_expr("2+y*x", evaluate=False)
        expr2=parse_expr("2+y*x")
        expr3=parse_expr("x*y+2", evaluate=False)
        expr4=parse_expr("foo", local_dict={'foo': expr1})
        self.assertNotEqual(expr1,expr2)
        self.assertEqual(expr2,expr3)
        self.assertNotEqual(expr1,expr3)
        self.assertEqual(expr2,expr4)
        self.assertNotEqual(expr1,expr4)
        self.assertEqual(repr(expr1), '2 + y*x')
        self.assertEqual(repr(expr4), 'x*y + 2')

        expr=parse_expr("1*x*1", evaluate=False)
        self.assertEqual(repr(expr), '1*x*1')
        self.assertEqual(latex(expr), '1 x 1')
        
        expr=parse_expr("0+x+0", evaluate=False)
        self.assertEqual(repr(expr), '0 + x + 0')
        self.assertEqual(latex(expr), '0 + x + 0')
        

        # test with leading minus sign in Mul
        expr=parse_expr("4*(-4*x+1)", evaluate=False)
        self.assertEqual(repr(expr), '4*(-4*x + 1)')
        self.assertEqual(latex(expr), '4 \\left(-4 x + 1\\right)')

        expr=parse_expr("-1*(-4*x+1)", evaluate=False)
        self.assertEqual(repr(expr), '-1*(-4*x + 1)')
        self.assertEqual(latex(expr), '-1 \\left(-4 x + 1\\right)')

        
        # parentheses around negative numbers or expressions with negative sign
        expr=parse_expr("4*2*-1*x*-x",evaluate=False)
        self.assertEqual(repr(expr), '4*2*(-1)*x*(-x)')
        self.assertEqual(latex(expr), '4 \\cdot 2 \\left(-1\\right) x \\left(- x\\right)')

        # subtracting and adding a negative
        from sympy import Integral
        expr=parse_expr("5*Integral(t,(t,0,1))+(-1)*Integral(t^2,(t,1,2))", 
                        evaluate=False,
                        local_dict={'Integral': Integral})
        self.assertEqual(latex(expr), 
                '5 \\int_{0}^{1} t\\, dt - 1 \\int_{1}^{2} t^{2}\\, dt')

        expr=parse_expr("5*Integral(t,(t,0,1))-Integral(t^2,(t,1,2))",
                        evaluate=False,
                        local_dict={'Integral': Integral})
        self.assertEqual(latex(expr), 
                    '5 \\int_{0}^{1} t\\, dt - \\int_{1}^{2} t^{2}\\, dt')

        expr=parse_expr("5*x*y*3-3*y*x*5-7-x", evaluate=False)
        self.assertEqual(latex(expr), '5 x y 3 - 3 y x 5 - 7 - x')

        expr=parse_expr("-5*x*x*3-3*x-x*3-3-x", evaluate=False)
        self.assertEqual(latex(expr), '-5 x x 3 - 3 x - x 3 - 3 - x')

        expr=parse_expr("5*x*x*3+-3*x+-x*3+-3+-x", evaluate=False)
        self.assertEqual(latex(expr), '5 x x 3 - 3 x - x 3 - 3 - x')

        expr=parse_expr("5*x*x*3--3*x--x*3--3--x", evaluate=False)
        self.assertEqual(latex(expr), '5 x x 3 + 3 x + x 3 + 3 + x')

        expr=parse_expr("1*x*x/(x*x)-1*x*x/(x*x)+-1*x*x/(-x*x)", evaluate=False)
        self.assertEqual(latex(expr), 
            '\\frac{1 x x}{x x} - \\frac{1 x x}{x x} - \\frac{1 x x}{- x x}')

        expr=parse_expr("-t/x", evaluate=False)
        self.assertEqual(latex(expr), '\\frac{- t}{x}')

        expr=parse_expr("x-(y-z)", evaluate=False)
        self.assertEqual(latex(expr), 'x - \\left(y - z\\right)')

        # should be equal to evaluate if looks the same
        expr1=parse_expr("-5z^2-5", evaluate=False)
        expr2=parse_expr("-5z^2-5")
        self.assertEqual(expr1,expr2)

        expr_base=parse_expr("-14*x^3+2")
        expr1=parse_expr("expr_base.as_ordered_terms()[1]+expr_base.as_ordered_terms()[0]", local_dict={'expr_base': expr_base}, evaluate=False)
        expr2=parse_expr("2-14*x^3", evaluate=False)
        self.assertEqual(expr1,expr2)

        expr1=parse_expr("1-5x", evaluate=False)
        expr2=parse_expr("1-1*5*x", evaluate=False)
        self.assertNotEqual(expr1,expr2)

        from sympy import Gt, Lt, Ge, Le
        from mitesting.sympy_customized import And, Or
        expr1=parse_expr("2<3", evaluate=False)
        self.assertEqual(expr1, Lt(2,3,evaluate=False))

        expr1=parse_expr("2>3 and 5<=-1 or 3>=3", evaluate=False)
        self.assertEqual(expr1, Or(And(Gt(2,3,evaluate=False), Le(5,-1,evaluate=False)), Ge(3,3,evaluate=False)))
        

        expr1=parse_expr("5/1", evaluate=False)
        self.assertEqual(latex(expr1), '\\frac{5}{1}')

        expr1=parse_expr("-(x-y)", evaluate=False)
        self.assertEqual(latex(expr1), r'-\left(x - y\right)')


    def test_no_evaluate_functions(self):
        from mitesting.user_commands import roots_tuple, index
        from mitesting.sympy_customized import TupleNoParen
        from sympy import Abs

        x=Symbol('x')
        
        expr=parse_expr("roots_tuple((x-3)*(x-1),x)", 
                        local_dict={'roots_tuple': roots_tuple}, evaluate=False)
        self.assertEqual(expr, roots_tuple((x-3)*(x-1),x, evaluate=False))
        self.assertEqual(expr.doit(), TupleNoParen(1,3))
        
        expr=parse_expr("index([3,-2,6],-2)", local_dict={'index': index }, 
                        evaluate=False)
        self.assertEqual(expr, index([3,-2,6],-2, evaluate=False))
        self.assertEqual(expr.doit(), 1)

        expr=parse_expr("Abs(-1)/Abs(x*Abs(-5))", local_dict={"Abs": Abs},
                        evaluate=False)
        self.assertEqual(expr, Abs(-1,evaluate=False)/Abs(x*Abs(-5, evaluate=False),evaluate=False))
        self.assertEqual(expr.doit(), 1/Abs(5*x))

    
    def test_no_evaluate_strange_Eq_behavior(self):
        # This fails if parse_expr doesn't add evaluate=False to Eq.
        # For some reason, it compares the Matrix to zero

        from mitesting.user_commands import scalar_multiple_deviation
        from sympy import Matrix, Eq
        A=Matrix([1,2])
        x=Symbol('x')
        expr = parse_expr('smd(A,x)=0', evaluate=False,
                          local_dict={'smd': scalar_multiple_deviation,
                                      'A': A})
        self.assertEqual(expr, Eq(scalar_multiple_deviation(A,x,evaluate=False),0,evaluate=False))


    def test_factorial(self):
        from sympy import factorial
        expr = parse_expr("x!")
        self.assertEqual(expr, factorial(Symbol('x')))
        expr = parse_expr("5!")
        self.assertEqual(expr, 120)

    def test_boolean(self):
        self.assertEqual(parse_expr("True and True"), True)
        self.assertEqual(parse_expr("True and not True"), False)
        self.assertEqual(parse_expr("False or not True"), False)
        self.assertEqual(parse_expr("not False or not True"), True)

        local_dict = {'a': sympify(1), 'b': sympify(2), 'c': sympify(3),
                       'd': sympify(4)}
        expr = parse_expr("a and b and c and d", local_dict=local_dict)
        self.assertEqual(expr, True)
        local_dict['b'] = sympify(0)
        expr = parse_expr("a and b and c and d", local_dict=local_dict)
        self.assertEqual(expr, False)

        self.assertEqual(latex(parse_expr("a and b")), r'a ~\text{and}~ b')
        self.assertEqual(latex(parse_expr("a or b")), r'a ~\text{or}~ b')

    def test_parse_and_process(self):
        x=Symbol('x')
        y=Symbol('y')
        expr = parse_and_process("2x")
        self.assertEqual(2*x, expr)
        expr = parse_and_process("xy", split_symbols=True)
        self.assertEqual(expr, x*y)
        expr = parse_and_process("var1*var2", 
                                 local_dict = {'var1':x, 'var2': y})
        self.assertEqual(expr, x*y)

    def test_parse_and_process_evaluate_level(self):
        from sympy import Derivative
        local_dict = {'Derivative': Derivative}
        x=Symbol('x')
        y=Symbol('y')
        expr = parse_and_process("x+2+y*x+x*y", 
                                 evaluate_level=EVALUATE_NONE)
        self.assertNotEqual(expr, 2+x+x)
        self.assertEqual(repr(expr), 'x + 2 + y*x + x*y')
        
        expr = parse_and_process("Derivative(x^2,x)", local_dict= local_dict,
                                 evaluate_level = EVALUATE_PARTIAL)
        self.assertEqual(Derivative(x**2,x), expr)
        expr = parse_and_process("Derivative(x^2,x)", local_dict= local_dict,
                                 evaluate_level = EVALUATE_FULL)
        self.assertEqual(2*x, expr)
        expr = parse_and_process("Derivative(x^2,x)", local_dict= local_dict)
        self.assertEqual(2*x, expr)

    def test_prevent_octal(self):
        expr = parse_expr("0123")
        self.assertEqual(expr, 123)

        expr = parse_expr("0193")
        self.assertEqual(expr, 193)
 
        expr = parse_expr("0.123")
        self.assertEqual(expr, 0.123)
        
        expr = parse_expr("0.000791")
        self.assertEqual(expr, 0.000791)
        
        expr = parse_expr("4.04")
        self.assertEqual(expr, 4.04)

        expr = parse_expr("1230")
        self.assertEqual(expr, 1230)

        expr = parse_expr("0009505")
        self.assertEqual(expr, 9505)
        
        expr = parse_expr("89-088")
        self.assertEqual(expr,1)

        expr = parse_expr("72x/072 - x + 081")
        self.assertEqual(expr, 81)

    def test_prevent_hexadecimal(self):
        expr = parse_expr("0x99")
        self.assertEqual(expr, 0)
        
        expr = parse_expr("10x99")
        self.assertEqual(expr, 10*Symbol("x99"))
        
    def test_prevent_auto_j_as_imaginary(self):
        j=Symbol('j')
        J=Symbol('J')
        expr = parse_expr("5j")
        self.assertEqual(expr, 5*j)

        expr = parse_expr("7J")
        self.assertEqual(expr, 7*J)

    def test_prevent_auto_l_as_long(self):
        l=Symbol('l')
        L=Symbol('L')
        expr = parse_expr("5l")
        self.assertEqual(expr, 5*l)

        expr = parse_expr("7L")
        self.assertEqual(expr, 7*L)


    def test_split_with_function(self):
        from sympy import Function
        x=Symbol('x')
        a=Symbol('a')
        f=Function(str('f'))
        fsym=Symbol('f')
        
        expr = parse_expr('af(x)', split_symbols=True)
        self.assertEqual(expr, a*fsym*x)

        expr = parse_expr('af(x)', split_symbols=True, 
                          local_dict={'f': f})
        self.assertEqual(expr, a*f(x))


    def test_callable_symbol(self):
        from mitesting.sympy_customized import SymbolCallable
        
        x=Symbol('x')
        a=Symbol('a')
        f=SymbolCallable(str('f'))
        fsym=Symbol(str('f'))

        self.assertEqual(f,fsym)
        
        expr = parse_expr('af(x)', split_symbols=True)
        self.assertEqual(expr, a*fsym*x)

        expr = parse_expr('af(x)', split_symbols=True, 
                          local_dict={'f': f})
        self.assertEqual(expr, a*f(x))
        self.assertEqual(expr, a*fsym(x))

        expr = parse_expr('afx', split_symbols=True, 
                          local_dict={'f': f})
        self.assertEqual(expr, a*f*x)
        
        expr = parse_expr('f in {fsym,y,z}', local_dict={'f': f, 'fsym': fsym})
        self.assertEqual(expr, True)


    def test_callable_symbol_commutative(self):
        # symbol callable is commutative even with argument such an equality
        from mitesting.sympy_customized import SymbolCallable
        
        P=SymbolCallable('P')

        local_dict = {'P': P}
        expr = parse_expr("P(R=1)", local_dict=local_dict)
        self.assertTrue(expr.is_commutative)
        
        expr = parse_expr("P(A)/P(R=1)", local_dict=local_dict)
        self.assertEqual(latex(expr), 
            '\\frac{P{\\left (A \\right )}}{P{\\left (R = 1 \\right )}}')
    


    def test_relational(self):
        from sympy import Eq, Ne, Lt, Ge
        from mitesting.sympy_customized import Or, And
        
        x=Symbol('x')
        y=Symbol('y')
        
        expr = parse_expr("x=y")
        self.assertEqual(expr, Eq(x,y))

        expr = parse_expr("x==y")
        self.assertEqual(expr, False)

        expr = parse_expr("x==y", evaluate=False)
        self.assertEqual(latex(expr), "x == y")
        self.assertEqual(expr.doit(), False)
        self.assertEqual(expr.subs(y,x).doit(), True)

        expr = parse_expr("x != y")
        self.assertEqual(expr, Ne(x,y))
 
        expr = parse_expr("x !== y")
        self.assertEqual(expr, True)
       
        expr = parse_expr("x!==y", evaluate=False)
        self.assertEqual(latex(expr), "x != y")
        self.assertEqual(expr.doit(), True)
        self.assertEqual(expr.subs(y,x).doit(), False)

        expr = parse_expr("x < y")
        self.assertEqual(expr, Lt(x,y))

        expr = parse_expr("x >= y")
        self.assertEqual(expr, Ge(x,y))

        expr = parse_expr("x=y or x^2 != y")
        self.assertEqual(expr,Or(Eq(x,y),Ne(x**2,y)))
        
        expr = parse_expr("(x=1)=(y=2)")
        self.assertEqual(expr,Eq(Eq(x,1),Eq(y,2)))

        a=Symbol('a')
        b=Symbol('b')
        c=Symbol('c')
        z=Symbol('z')
        expr = parse_expr("x-1=y+c and (y/a=x(z) or a^2 != (b+2)(c-1)/2)")
        self.assertEqual(expr, And(Eq(x-1,y+c), Or(Eq(y/a,x*z), Ne(a**2,(b+2)*(c-1)/2))))

    def test_multiple_relational(self):
        from sympy import Eq, Ne, Lt, Le, Gt, Ge
        from mitesting.sympy_customized import Or, And
        from mitesting.customized_commands import Gts, Lts

        a=Symbol('a')
        b=Symbol('b')
        c=Symbol('c')
        x=Symbol('x')
        y=Symbol('y')
        z=Symbol('z')
 
        expr=parse_expr("a < b <=c <x")
        self.assertEqual(expr, And(Lt(a,b), Le(b,c), Lt(c,x)))

        expr=parse_expr("a < b <=c <x", replace_symmetric_intervals=True)
        self.assertEqual(expr, And(Lt(a,b), Le(b,c), Lt(c,x)))

        expr=parse_expr("a>b >= c >=x")
        self.assertEqual(expr, And(Gt(a,b), Ge(b,c), Ge(c,x)))

        expr=parse_expr("a < b <=c <x", evaluate=False)
        self.assertEqual(expr, Lts((a,b,c,x), (True, False, True), evaluate=False))
        self.assertEqual(latex(expr), "a < b \leq c < x")
        

        expr=parse_expr("a>b >= c >=x", evaluate=False)
        self.assertEqual(expr, Gts((a,b,c,x), (True, False, False), evaluate=False))
        self.assertEqual(latex(expr), "a > b \geq c \geq x")
        
        

        
    def test_conditional_probability_expression(self):
        from mitesting.customized_commands import conditional_probability_expression
        from mitesting.sympy_customized import SymbolCallable

        A=Symbol("A")
        B=Symbol("B")
        P=SymbolCallable("P")

        expr=parse_expr("A|B")
        self.assertEqual(expr, conditional_probability_expression(A,B))
        self.assertEqual(latex(expr), "A ~|~ B")

        expr=parse_expr("P(A|B)", local_dict={'P': P})
        self.assertEqual(expr, P(conditional_probability_expression(A,B)))
        self.assertEqual(latex(expr), "P{\\left (A ~|~ B \\right )}")


    def test_absolute_values(self):
        from sympy import Abs

        x=Symbol('x')
        y=Symbol('y')
        z=Symbol('z')
        
        self.assertEqual(parse_expr("|x+y|"), Abs(x+y))
        self.assertEqual(parse_expr("x|y|x|z|x"), x**3*Abs(y)*Abs(z))
        self.assertEqual(parse_expr("|x+y|"), Abs(x+y))
        self.assertRaises(SyntaxError, parse_expr,"|x+|y||")
        self.assertEqual(parse_expr("|x+(|y|)|"), Abs(x+Abs(y)))

        from mitesting.customized_commands import conditional_probability_expression
        from mitesting.sympy_customized import SymbolCallable

        A=Symbol("A")
        B=Symbol("B")
        P=SymbolCallable("P")
        expr=parse_expr("|P(A|B)|", local_dict={'P': P})
        self.assertEqual(expr, Abs(P(conditional_probability_expression(A,B))))


    def test_tuple_no_parens(self):
        from mitesting.sympy_customized import TupleNoParen

        a=Symbol('a')
        b=Symbol('b')
        c=Symbol('c')

        expr = parse_expr("(a,b,c)")
        self.assertEqual(expr, Tuple(a,b,c))
        self.assertNotEqual(expr, TupleNoParen(a,b,c))

        expr = parse_expr("a,b,c")
        self.assertEqual(expr, TupleNoParen(a,b,c))
        self.assertNotEqual(expr, Tuple(a,b,c))

        local_dict = {'t1': Tuple(a,b,c), 't2': TupleNoParen(a,b,c),
                      't3': (a,b,c)}

        expr=parse_expr("t1", local_dict=local_dict)
        self.assertEqual(expr, Tuple(a,b,c))

        expr=parse_expr("t2", local_dict=local_dict)
        self.assertEqual(expr, TupleNoParen(a,b,c))

        expr=parse_expr("t3", local_dict=local_dict)
        self.assertEqual(expr, Tuple(a,b,c))

        def f(x,y):
            return Tuple(x+y,x-y)
        local_dict = {'f': f}
        expr=parse_expr("f(a,b)", local_dict=local_dict)
        self.assertEqual(expr, Tuple(a+b,a-b))

        def f(x,y):
            return TupleNoParen(x+y,x-y)
        local_dict = {'f': f}
        expr=parse_expr("f(a,b)", local_dict=local_dict)
        self.assertEqual(expr, TupleNoParen(a+b,a-b))

        tuple1=parse_expr("a,b,c")
        tuple2=parse_expr("t[:2]", local_dict={'t': tuple1})
        self.assertEqual(tuple2, TupleNoParen(a,b))

        tuple1=parse_expr("(a,b,c)")
        tuple2=parse_expr("t[:2]", local_dict={'t': tuple1})
        self.assertEqual(tuple2, Tuple(a,b))
        
        tuple1=parse_expr("(a,(b,a),c)")
        tuple2=parse_expr("t[1]", local_dict={'t': tuple1})
        self.assertEqual(tuple2, Tuple(b,a))
        
        

        


    def test_derivative_prime_notation(self):
        from sympy import Function, Derivative
        from mitesting.sympy_customized import SymbolCallable, \
            DerivativePrimeNotation, DerivativePrimeSimple
        
        f=Function(str('f'))
        g=SymbolCallable(str('g'))
        x=Symbol('x')
        y=Symbol('y')
        
        fn=Function(str('fn'))
        
        local_dict={'f': f, 'g': g, 'fn': fn}
        
        expr=parse_expr("f'(x)+g'(y)", local_dict=local_dict)
        self.assertEqual(expr, DerivativePrimeSimple(f(x),x)
                         +DerivativePrimeSimple(g(y),y))
        self.assertEqual(latex(expr), "f'(x) + g'(y)")

        expr=parse_expr("yf'(x)", local_dict=local_dict, split_symbols=True)
        self.assertEqual(expr, y*DerivativePrimeSimple(f(x),x))

        expr=parse_expr("yf'(x)", local_dict=local_dict)
        self.assertEqual(expr, DerivativePrimeSimple(Function('yf')(x),x))

        expr=parse_expr("2f'(x)", local_dict=local_dict)
        self.assertEqual(expr, 2*DerivativePrimeSimple(f(x),x))

        expr=parse_expr("fn'(x)", local_dict=local_dict)
        self.assertEqual(expr, DerivativePrimeSimple(fn(x),x))

        expr=parse_expr("fn'(x)", local_dict=local_dict, split_symbols=True)
        self.assertEqual(expr, DerivativePrimeSimple(fn(x),x))

        expr=parse_expr("f0'(x)", local_dict=local_dict)
        self.assertEqual(expr, DerivativePrimeSimple(Function('f0')(x),x))

        self.assertRaises(SyntaxError, parse_expr,"f0'(x)", 
                          local_dict=local_dict, split_symbols=True)

        expr=parse_expr("2f'(x*y)", local_dict=local_dict)
        self.assertEqual(expr, 2*DerivativePrimeNotation(f,x*y))
        from sympy import Subs
        self.assertEqual(expr.doit(), 2*Subs(Derivative(f(x),x),x,x*y))
        
        expr2=parse_expr("2f'(x*y, dummy_variable==='t')", local_dict=local_dict)
        self.assertEqual(expr,expr2)
        self.assertEqual(expr.doit(),expr2.doit())
        
        expr3=parse_expr("2f'(x*y, dummy_variable==='s')", local_dict=local_dict)
        self.assertEqual(expr3,expr2)
        self.assertEqual(expr3.doit(),expr2.doit())
        


    def test_derivative_simplified_notation(self):
        from sympy import Function, Derivative
        from mitesting.sympy_customized import SymbolCallable, \
            DerivativeSimplifiedNotation
        
        f=Function(str('f'))
        g=SymbolCallable(str('g'))
        x=Symbol(str('x'))
        y=Symbol('y')
        fn=Function(str('fn'))
        xx=Symbol('xx')
        local_dict={'f': f, 'g': g, 'fn': fn, 'xx': xx}
        
        expr=parse_expr("df/dx+dg/dy", local_dict=local_dict)
        self.assertEqual(expr, DerivativeSimplifiedNotation(f(x),x)
                         +DerivativeSimplifiedNotation(g(y),y))
        self.assertEqual(latex(expr), "\\frac{d f}{d x} + \\frac{d g}{d y}")

        expr=parse_expr("ydf/dxy", local_dict=local_dict, split_symbols=True)
        self.assertEqual(expr, y**2*DerivativeSimplifiedNotation(f(x),x))
        
        expr=parse_expr("ydf/dxy", local_dict=local_dict)
        self.assertEqual(expr, Symbol('ydf')/Symbol('dxy'))

        expr=parse_expr("3dfn/dxx", local_dict=local_dict)
        self.assertEqual(expr, 3*DerivativeSimplifiedNotation(fn(xx),xx))

        expr=parse_expr("df/dx+dg/dy")
        self.assertEqual(expr, DerivativeSimplifiedNotation(f(x),x)
                         +DerivativeSimplifiedNotation(g(y),y))
        self.assertEqual(latex(expr), "\\frac{d f}{d x} + \\frac{d g}{d y}")

        expr=parse_expr("dvar/dy", local_dict={'var': x})
        self.assertEqual(expr, DerivativeSimplifiedNotation(x(y),y))
        self.assertEqual(latex(expr), "\\frac{d x}{d y}")

        expr=parse_expr("dx/dx")
        self.assertEqual(expr, DerivativeSimplifiedNotation(x(x),x))
        self.assertEqual(latex(expr), "\\frac{d x}{d x}")
        self.assertEqual(expr.doit(),1)

        expr=parse_expr("dvar/dx", local_dict={'var': x})
        self.assertEqual(expr, DerivativeSimplifiedNotation(x(x),x))
        self.assertEqual(latex(expr), "\\frac{d x}{d x}")
        self.assertEqual(expr.doit(),1)

        expr=parse_expr("dvar/dx", local_dict={'var': x*x})
        self.assertEqual(expr, Derivative(x**2,x))
        self.assertEqual(latex(expr), "\\frac{d}{d x} x^{2}")
        self.assertEqual(expr.doit(), 2*x)

        from sympy import sin, cos
        expr=parse_expr("dvar/dx", local_dict={'var': sin })
        self.assertEqual(expr, DerivativeSimplifiedNotation(sin(x),x))
        self.assertEqual(latex(expr), "\\frac{d}{d x} \\sin{\\left (x \\right )}")
        self.assertEqual(expr.doit(), cos(x))

        expr=parse_expr("dvar/dx", local_dict={'var': sin(x) })
        self.assertEqual(expr, Derivative(sin(x),x))

        expr=parse_expr("dvar/dx", local_dict={'var': x+y+1 })
        self.assertEqual(expr, Derivative(x+y+1,x))
        


    def test_subs_relational(self):
        from sympy import Eq
        x=Symbol('x')
        self.assertEqual(parse_expr("2*z", local_dict={"z": Eq(x,3)}),2*Eq(x,3))


    def test_implicit_mult_with_attribute(self):
        self.assertEqual(parse_expr("(1/2).evalf()"), 0.5)

    def test_contains(self):
        from mitesting.sympy_customized import Interval, FiniteSet, Or
        x=Symbol('x')
        expr=parse_expr("x in (1,2)")
        self.assertEqual(expr, Interval(1,2, left_open=True, right_open=True).contains(x))
        self.assertEqual(latex(expr), r'x > 1 ~\text{and}~ x < 2')

        expr=parse_expr("x in (1,2)", evaluate=False)
        self.assertEqual(expr, Interval(1,2, left_open=True, right_open=True).contains(x, evaluate=False))
        self.assertEqual(latex(expr), r'x \in \left(1, 2\right)')

        expr=parse_expr("1 in [1,2]")
        self.assertEqual(expr, True)

        expr=parse_expr("1 in [1,2]", evaluate=False)
        self.assertEqual(expr, Interval(1,2).contains(1, evaluate=False))
        self.assertEqual(latex(expr), r'1 \in \left[1, 2\right]')

        expr=parse_expr("x in {1,2,3}")
        self.assertEqual(expr, FiniteSet(1,2,3).contains(x))

        expr=parse_expr("x in {1,2,x}")
        self.assertEqual(expr, True)

        expr=parse_expr("x in {1,2,x}", evaluate=False)
        self.assertEqual(expr, FiniteSet(1,2,x).contains(x, evaluate=False))
        self.assertEqual(latex(expr), r'x \in \left\{1, 2, x\right\}')

        a=Symbol('a')
        b=Symbol('b')
        expr=parse_expr("x in {a,b} or x in (1,2]")
        self.assertEqual(expr, Or(FiniteSet(a,b).contains(x),Interval(1,2, left_open=True).contains(x)))

        from mitesting.user_commands import iif
        expr=parse_expr("if(x in {a,b}, 1, 0)", local_dict={'x': a, 'if': iif})
        self.assertEqual(expr,1)
        

    def test_intervals(self):
        from mitesting.sympy_customized import Interval
        a=Symbol('a')
        b=Symbol('b')

        self.assertEqual(parse_expr("(a,b)"), Tuple(a,b))
        self.assertEqual(parse_expr("[a,b]"), [a,b])
        

        self.assertRaisesRegex(ValueError, "Only real intervals",
                                parse_expr, "(a,b)", 
                                replace_symmetric_intervals=True)
        self.assertRaisesRegex(ValueError, "Only real intervals",
                                parse_expr, "[a,b]", 
                                replace_symmetric_intervals=True)
        self.assertRaisesRegex(ValueError, "Only real intervals",
                                parse_expr, "(a,b]")
        self.assertRaisesRegex(ValueError, "Only real intervals",
                                parse_expr, "[a,b)")

        a=Symbol('a', real=True)
        b=Symbol('b', real=True)

        expr=parse_expr("(a,b)", replace_symmetric_intervals=True,
                        assume_real_variables=True)
        self.assertEqual(expr, Interval(a,b,left_open=True,
                                                      right_open=True))
        expr=parse_expr("[a,b]", replace_symmetric_intervals=True,
                        assume_real_variables=True)
        self.assertEqual(expr, Interval(a,b))

        expr=parse_expr("(a,b]", assume_real_variables=True)
        self.assertEqual(expr, Interval(a,b, left_open=True))
        expr=parse_expr("(a,b]", replace_symmetric_intervals=True,
                        assume_real_variables=True)
        self.assertEqual(expr, Interval(a,b, left_open=True))

        expr=parse_expr("[a,b)", assume_real_variables=True)
        self.assertEqual(expr, Interval(a,b, right_open=True))
        expr=parse_expr("[a,b)", replace_symmetric_intervals=True,
                        assume_real_variables=True)
        self.assertEqual(expr, Interval(a,b, right_open=True))


    def test_parse_subscripts(self):
        x=Symbol('x')
        y=Symbol('y')
        n=Symbol('n')
        m=Symbol('m')
        
        expr1=parse_expr("x_n")
        expr2=parse_expr("x_n", parse_subscripts=True)
        expr3=parse_expr("x_n", parse_subscripts=True, 
                         assume_real_variables=True)
        expr4=parse_expr("x_n", parse_subscripts=True, evaluate=False)
        
        self.assertEqual(expr1,Symbol("x_n"))
        self.assertEqual(expr2,Symbol("x_n"))
        self.assertEqual(expr1,expr2)
        self.assertEqual(expr3,Symbol("x_n", real=True))
        self.assertEqual(expr4,Symbol("x_n"))

        expr1=parse_expr("x_(n+1)")
        expr2=parse_expr("x_(n+1)", parse_subscripts=True)
        self.assertEqual(expr1,Symbol("x_")*(n+1))
        self.assertEqual(expr2,Symbol("x_n + 1"))
        self.assertEqual(latex(expr2), "x_{n + 1}")

        expr=parse_expr("xx_nn", parse_subscripts=True, 
                        local_dict={'xx': y, 'nn': m })
        self.assertEqual(expr, Symbol('y_m'))

        expr=parse_expr("xx_nn", parse_subscripts=True, split_symbols=True,
                        local_dict={'xx': y, 'nn': m })
        self.assertEqual(expr, Symbol('y_m'))

        expr=parse_expr("xx_nn", parse_subscripts=True,
                        local_dict={'xx': y, 'nn': m, 'xx_nn': Symbol('a')})
        self.assertEqual(expr, Symbol('a'))

        expr=parse_expr("xx_nn", parse_subscripts=True, split_symbols=True,
                        local_dict={'xx': y, 'nn': m, 'xx_nn': Symbol('a')})
        self.assertEqual(expr, Symbol('a'))

        expr=parse_expr("y+xx_nn/2", parse_subscripts=True)
        self.assertEqual(expr, y+Symbol('xx_nn')/2)

        expr=parse_expr("y+xx_nn/2", parse_subscripts=True, split_symbols=True)
        self.assertEqual(expr, y+x*n*Symbol('x_n')/2)

        expr=parse_expr("y+xx_nn/2", parse_subscripts=True, split_symbols=True,
                        local_dict={'nn': Symbol('nn')})
        self.assertEqual(expr, y+x*Symbol('x_nn')/2)

        expr=parse_expr("y+xx_nn/2", parse_subscripts=True, split_symbols=True,
                        local_dict={'xx': Symbol('xx')})
        self.assertEqual(expr, y+n*Symbol('xx_n')/2)

        expr=parse_expr("y+xx_nn/2", parse_subscripts=True, split_symbols=True,
                        local_dict={'xx': Symbol('xx'), 'nn': Symbol('nn')})
        self.assertEqual(expr, y+Symbol('xx_nn')/2)

        expr=parse_expr("y+xx_(nm)/2", parse_subscripts=True, 
                        split_symbols=True)
        self.assertEqual(expr, y+x*Symbol('x_m n')/2)

        expr=parse_expr("y+xx_(nm)/2", parse_subscripts=True, 
                        split_symbols=True, local_dict={'nm': Symbol('nm')})
        self.assertEqual(expr, y+x*Symbol('x_nm')/2)


        expr=parse_expr("y+6xx_nn/2", parse_subscripts=True)
        self.assertEqual(expr, y+3*Symbol('xx_nn'))

        expr=parse_expr("y+xx_28/2", parse_subscripts=True, split_symbols=True)
        self.assertEqual(expr, y+x*Symbol('x_28')/2)

        expr=parse_expr("y+xx_28n/2", parse_subscripts=True, split_symbols=True)
        self.assertEqual(expr, y+x*n*Symbol('x_28')/2)
 
        expr=parse_expr("y+xx_28n/2", parse_subscripts=True)
        self.assertEqual(expr, y+Symbol('xx_28 n')/2)


        expr=parse_expr("a1_b", parse_subscripts=True, split_symbols=True)
        self.assertEqual(expr,  Symbol('a1_b'))

        expr=parse_expr("1a_b", parse_subscripts=True, split_symbols=True)
        self.assertEqual(expr,  Symbol('a_b'))

        S1= Symbol('SS_1')
        expr=parse_expr("xS_1y", parse_subscripts=True, split_symbols=True,
                        local_dict={'S_1': S1})
        self.assertEqual(expr, x*S1*y)
