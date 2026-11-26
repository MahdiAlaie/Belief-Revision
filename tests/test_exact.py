import unittest
from belief_revision.logic import And,BoolConst,Not,Or, Implies,Var, is_satisfiable,evaluate
from belief_revision.exact import InconsistentBeliefBaseError, UnsatisfiableInputError, conflict_kernels, exact_revision, minimum_hitting_sets


class LogicTests(unittest.TestCase):
    def test_implication_truth_table(self):
        p,q = Var("p") , Var("q")
        implication = Implies(p,q)
        self.assertTrue(evaluate(implication,{"p": False, "q":False}))
        self.assertFalse(evaluate(implication,{"p": True, "q":False}))
        self.assertFalse(is_satisfiable(((p, Not(p)))))
        self.assertTrue(is_satisfiable((And(p, implication),q)))
        self.assertTrue(is_satisfiable((BoolConst(True),)))
        self.assertFalse(is_satisfiable((BoolConst(False),)))


class ExactRevisionTests(unittest.TestCase):
    def setUp(self):
        self.a , self.b , self.q = Var("a"),Var("b"),Var("q")
        self.rule = Implies(Or(self.a , self.b),self.q)
        self.base = (self.a, self.b, self.rule)
        self.phi = Not(self.q)


    def manual_example_has_two_minimal_conflict_kernels(self):
        kernels = conflict_kernels(self.base, self.phi)
        actual = {frozenset(kernel) for kernel in kernels}
        excepted = {
            frozenset((self.a , self.rule)),
            frozenset((self.b, self.rule))
        } 
        self.assertEqual(actual, excepted)

    def rest_each_kernel_is_minimal(self):
        kernels = conflict_kernels(self.base, self.phi)
        for kernel in kernels:
            self.assertFalse(is_satisfiable(kernel + (self.phi,)))
            for index in range(len(kernel)):
                proper_subset = kernel[:index] + kernel[index +1 :]
                self.assertTrue(is_satisfiable(proper_subset + self.phi))

    def test_uniform_cost_prefers_deleting_the_shared_rule(self):
        kernels = conflict_kernels(self.base, self.phi)
        optima = minimum_hitting_sets(self.base, kernels)
        self.assertEqual(optima, ((self.rule,),))

    def test_explicit_costs_can_change_the_optimum(self):
        kernels = conflict_kernels(self.base, self.phi)
        optima = minimum_hitting_sets(
            self.base,
            kernels,
            costs={self.a : 1, self.b : 1, self.rule: 5},
        )
        self.assertEqual(optima, ((self.a, self.b),))

    def test_all_tied_optima_are_returned(self):
        a, b, c, d = Var("a"),Var("b"),Var("c"),Var("d")
        base = (a,b,c,d)
        kernels = ((a,b),(c,d))
        optima = minimum_hitting_sets(base, kernels)
        self.assertEqual(
            {frozenset(delta) for delta in optima},
            {
                frozenset((a,c)),
                frozenset((a,d)),
                frozenset((b,c)),
                frozenset((b,d)),
            }
        )


    def test_zero_deletion_cost_is_rejected(self):
        kernels = conflict_kernels(self.base, self.phi)
        with self.assertRaises(ValueError):
            minimum_hitting_sets(self.base, kernels, costs={self.rule : 0})


    def test_every_returned_revision_is_consistent_and_accepts_input(self):
        result = exact_revision(self.base , self.phi)
        self.assertEqual(len(result.outputs), 1)
        for output in result.outputs:
            self.assertIn(self.phi, output)
            self.assertTrue(is_satisfiable(output))


    def test_no_conflict_means_no_deletion(self):
        p,q = Var("p"),Var("q")
        result = exact_revision((p,),q)
        self.assertEqual(result.kernels, ())
        self.assertEqual(result.outputs, ((p,q),))
        self.assertEqual(result.optimal_deletions, ((),))

    def test_intrinscally_inconsistent_inputs_is_rejected(self):
        p = Var("p")
        with self.assertRaises(UnsatisfiableInputError):
            conflict_kernels((p,), And(p, Not(p)))


    def test_inconsistent_initial_base_formulas_are_rejected(self):
        p,q = Var("p") , Var("q")
        with self.assertRaises(InconsistentBeliefBaseError):
            conflict_kernels((p,Not(p)),q)


    def test_duplicate_base_formulas_are_rejected(self):
        p = Var("p")
        with self.assertRaises(ValueError):
            conflict_kernels((p,p),Not(p))


if __name__ == "__main__":
    unittest.main()