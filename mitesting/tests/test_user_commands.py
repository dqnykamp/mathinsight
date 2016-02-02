from django.test import SimpleTestCase
from mitesting.user_commands import *
from sympy import diff, Tuple, sympify
from mitesting.sympy_customized import Symbol, TupleNoParen
import random


class RootsTests(SimpleTestCase):
    def setUp(self):
        random.seed()

    def test_roots_polys_with_real_roots(self):
        x = Symbol('x')
        for j in range(10):
            theroots=[]
            poly = 1;
            for i in range(5):
                root = sympify(random.randint(-10,10))
                theroots.append(root)
                poly *= x-root;

            # remove multiple roots
            theroots=list(set(theroots))
            theroots.sort()
            
            rt = roots_tuple(poly)
            self.assertEqual(rt,TupleNoParen(*theroots))
            
            rrt = real_roots_tuple(poly)
            self.assertEqual(rrt,TupleNoParen(*theroots))

    def test_roots_polys_with_complex_roots(self):
        from sympy import I
        x = Symbol('x')
        for j in range(10):
            theroots=[]
            therealroots=[]
            poly = 1;
            # few real roots
            for i in range(2):
                root = sympify(random.randint(-10,10))
                therealroots.append(root)
                theroots.append(root)
                poly *= x-root;
            # few complex roots
            for i in range(2):
                a = sympify(random.randint(-10,10))
                b = sympify(random.randint(1,10))
                root = a+b*I
                theroots.append(root)
                root = a-b*I
                theroots.append(root)
                poly *= a**2 - 2*a*x + b**2 + x**2

            # remove multiple roots
            therealroots=list(set(therealroots))
            therealroots.sort()
            theroots=list(set(theroots))
            theroots = sorted(theroots, key=lambda x: sympify(x).sort_key())

            rt = roots_tuple(poly)
            self.assertEqual(rt,TupleNoParen(*theroots))
            
            rrt = real_roots_tuple(poly)
            self.assertEqual(rrt,TupleNoParen(*therealroots))


class IndexTests(SimpleTestCase):
    def test_index_of_tuple(self):
        thetuple = Tuple(2,-3,2,13,-5)
        self.assertEqual(index(thetuple,2),0)
        self.assertEqual(index(thetuple,-3),1)
        self.assertEqual(index(thetuple,13),3)
        self.assertEqual(index(thetuple,-5),4)
        self.assertEqual(index(thetuple,12),-1)

    def test_index_of_list(self):
        thelist = [23, 0, -123, 5825.253, -123, 2]
        self.assertEqual(index(thelist,23),0)
        self.assertEqual(index(thelist,0),1)
        self.assertEqual(index(thelist,-123),2)
        self.assertEqual(index(thelist,5825.253),3)
        self.assertEqual(index(thelist,2),5)
        self.assertEqual(index(thelist,2232),-1)

    def test_index_of_symbolic_expressions(self):
        thetuple = sympify(sympify("(-3*x-2, sin(3*z/3), 3*exp(y**2)/2)"))
        for i in range(len(thetuple)):
            self.assertEqual(index(thetuple,thetuple[i]),i)

    def test_index_of_invalid_items(self):
        self.assertRaisesRegex(
            ValueError, "First argument of index must be a list or tuple",
            index,3,2)
        self.assertRaisesRegex(
            ValueError, "First argument of index must be a list or tuple",
            index,sympify("3*x"),3)

    def test_index_no_evaluate(self):
        x = Symbol('x')
        expr = index([-3,0,1],x, evaluate=False)
        self.assertEqual(expr.doit(), -1)
        self.assertEqual(expr.subs(x,0),1)


class SmallestFactorTests(SimpleTestCase):
    def test_smallest_factor(self):
        self.assertEqual(smallest_factor(323),17)
        self.assertRaisesRegex(ValueError,
                                "Argument to smallest_factor must be an integer",
                                smallest_factor, 323.2)

class MinMaxTests(SimpleTestCase):
    def test_min_max_multiple_args(self):
        self.assertEqual(max_including_tuples(-24,23), 23)
        self.assertEqual(min_including_tuples(-24,23), -24)
        self.assertEqual(max_including_tuples(-633,0,35,-231), 35)
        self.assertEqual(min_including_tuples(-633,0,35,-231), -633)

    def test_min_max_tuples(self):
        thetuple = Tuple(-24,23)
        self.assertEqual(max_including_tuples(thetuple), 23)
        self.assertEqual(min_including_tuples(thetuple), -24)
        thetuple = Tuple(-633,0,35,-231)
        self.assertEqual(max_including_tuples(thetuple), 35)
        self.assertEqual(min_including_tuples(thetuple), -633)


class InlineIfTests(SimpleTestCase):
    def test_inline_if(self):
        self.assertEqual(iif(3>2,7,11), 7)
        self.assertEqual(iif(3<2,7,11), 11)
        x = Symbol('x')
        self.assertEqual(iif(((x+1)*(x-1)).expand() == x**2-1,
                              3*x, 1-x), 3*x)

    def test_inline_if_function(self):
        x=Symbol('x')
        f = lambda x: iif(x < 1, 1-x, x**2+1)
        self.assertEqual(f(0),1)
        tenth=sympify('1/10')
        self.assertEqual(f(9*tenth),tenth)
        self.assertEqual(f(1),2)
        self.assertEqual(f(2),5)
        
class DiffSubsTests(SimpleTestCase):
    def test_diffsubs(self):
        x=Symbol('x')
        y=Symbol('y')
        z=Symbol('z')

        self.assertEqual(DiffSubs(x*y-1,x,z,1).doit(), y-z*y)
        from mitesting.sympy_customized import latex
        self.assertEqual(latex(DiffSubs(2*x,x,y,z)),
            r'\left. 2 x \vphantom{\Large I} \right|_{\substack{ x=y }}^{\substack{ x=z }}')

        from mitesting.sympy_customized import AddUnsort
        self.assertEqual(DiffSubs(2*x,x,1,2).as_difference(), AddUnsort(4,-2))

class ScalarMultipleTests(SimpleTestCase):
    def test_scalar_multiples(self):
        from sympy import oo
        x=Symbol('x')
        y=Symbol('y')
        u = (1,2)
        v = (3,6)
        self.assertEqual(scalar_multiple_deviation(u,v),0)

        u = Tuple(3*x,2*y)
        v = Tuple(3*x**2, 2*x*y)
        self.assertEqual(scalar_multiple_deviation(u,v),0)
        
        v = Tuple(3*x**2, 2*y)
        self.assertEqual(scalar_multiple_deviation(u,v),oo)

        u = TupleNoParen(1.52305, 8353.20343)
        v = TupleNoParen(u[0]*2353.3421, u[1]*2353.3421)
        sm = scalar_multiple_deviation(u,v) 
        self.assertTrue(sm >=0 and sm < 1E-15)

        u = Tuple(1.52305*x+3.253321*y, 8353.20343*sin(x*y))
        v = Tuple(u[0]*123.23413*x, u[1]*123.23413*x)
        sm = scalar_multiple_deviation(u,v) 
        self.assertTrue(sm >=0 and sm < 1E-15)

        u = Tuple(1,2,3)
        v = Tuple(4,5,6)
        sm1 = scalar_multiple_deviation(u,v) 
        sm2 = scalar_multiple_deviation(v,u) 
        self.assertEqual(sm1,sm2)
        self.assertTrue(sm1 > 1)
        
        u = Tuple(1,2,3)
        v = TupleNoParen(1,2,3)
        self.assertEqual(scalar_multiple_deviation(u,v),oo)
        v = Tuple(1,2)
        self.assertEqual(scalar_multiple_deviation(u,v),oo)
        v = 1
        self.assertEqual(scalar_multiple_deviation(u,v),oo)
        v = Tuple(0,0,0)
        self.assertEqual(scalar_multiple_deviation(u,v),oo)
        v = Tuple(1,2,0)
        self.assertEqual(scalar_multiple_deviation(u,v),oo)

        from sympy import ImmutableMatrix
        u = ImmutableMatrix(((1,2,3), (4,5,6)))
        v = 3*x*u
        self.assertEqual(scalar_multiple_deviation(u,v),0)

        v = u.transpose()
        self.assertEqual(scalar_multiple_deviation(u,v),oo)
        
        v = ImmutableMatrix(((1,2,3,4),(5,6,7,8)))
        self.assertEqual(scalar_multiple_deviation(u,v),oo)

    def test_no_evaluate(self):
        from sympy import oo
        x=Symbol('x')
        expr = scalar_multiple_deviation((1,2),x, evaluate=False)

        self.assertEqual(repr(expr), 'scalar_multiple_deviation((1, 2), x)')
        self.assertEqual(expr.doit(),oo)
        self.assertEqual(expr.subs(x,(4*x,16*x)), 3/4)
        
    def test_compare_matrix_as_vector(self):
        from mitesting.customized_commands import MatrixFromTuple
        
        the_tuple = Tuple(1,2,3)
        the_matrix = MatrixFromTuple(4,8,12)

        self.assertEqual(scalar_multiple_deviation(the_tuple,the_matrix),0)
        
        the_matrix = MatrixFromTuple(4,3,2)
        self.assertEqual(scalar_multiple_deviation(the_tuple,the_matrix),65/16)

                         
class CumsumTests(SimpleTestCase):
    def test_cumsum(self):
        x=Symbol('x')
        y=Symbol('y')
        z=Symbol('z')
        self.assertEqual(cumsum([1,2,3]), [1,3,6])
        
        self.assertEqual(cumsum(Tuple(x,y,z,2)), [x,x+y,x+y+z,x+y+z+2])
        
        
class MedianTests(SimpleTestCase):
    def test_median(self):
        self.assertEqual(median([30, 1,2]), 2)
        self.assertEqual(median([1,10,2,7]), 9/2)
        
        

class EigenTests(SimpleTestCase):
    def test_evals(self):
        from sympy import ImmutableMatrix, S, sqrt, I
        from mitesting.customized_commands import MatrixAsVector

        A=ImmutableMatrix([[1,-1],[2,4]])
        eigs=eigenvals_tuple(A)
        self.assertEqual(eigs, TupleNoParen(2,3))
        eigs=eigenvects_tuple(A)
        self.assertTrue(isinstance(eigs,TupleNoParen))
        self.assertEqual(len(eigs),2)
        self.assertTrue(isinstance(eigs[0],MatrixAsVector))
        self.assertTrue(isinstance(eigs[1],MatrixAsVector))
        self.assertTrue(abs(eigs[0][0]/eigs[0][1]+1) < 1E-12)
        self.assertTrue(abs(eigs[1][0]/eigs[1][1]+0.5) < 1E-12)
        
        
        A=ImmutableMatrix([[1,3],[2,1]])
        eigs=eigenvals_tuple(A)
        self.assertTrue(isinstance(eigs,TupleNoParen))
        self.assertEqual(len(eigs),2)
        self.assertTrue(abs(eigs[0]-(1-sqrt(6))) < 1E-12)
        self.assertTrue(abs(eigs[1]-(1+sqrt(6))) < 1E-12)
        eigs=eigenvects_tuple(A)
        self.assertTrue(isinstance(eigs,TupleNoParen))
        self.assertEqual(len(eigs),2)
        self.assertTrue(isinstance(eigs[0],MatrixAsVector))
        self.assertTrue(isinstance(eigs[1],MatrixAsVector)) 
        self.assertTrue(abs(eigs[0][0]/eigs[0][1]+sqrt(6)/2) < 1E-12)
        self.assertTrue(abs(eigs[1][0]/eigs[1][1]-sqrt(6)/2) < 1E-12)

        A=ImmutableMatrix([[1,3],[0,1]])
        eigs=eigenvals_tuple(A)
        es = TupleNoParen(1,1)
        self.assertEqual(eigs, es)
        eigs=eigenvects_tuple(A)
        self.assertEqual(eigs[0][0],1)
        self.assertEqual(eigs[0][1],0)

        A=ImmutableMatrix([[3,0],[0,3]])
        eigs=eigenvals_tuple(A)
        es = TupleNoParen(3,3)
        self.assertEqual(eigs, es)
        eigs=eigenvects_tuple(A)
        es = TupleNoParen(MatrixAsVector([[1],[0]]),MatrixAsVector([[0],[1]]))
        self.assertEqual(eigs,es)

                          
        A=ImmutableMatrix([[1,1],[-1,1]])
        eigs=eigenvals_tuple(A)
        es = TupleNoParen(1.0-1.0*I, 1.0+1.0*I)
        self.assertEqual(eigs, es)
        eigs=eigenvects_tuple(A)
        self.assertTrue(abs(eigs[0][0]/eigs[0][1]-I) < 1E-12)
        self.assertTrue(abs(eigs[1][0]/eigs[1][1]+I) < 1E-12)
