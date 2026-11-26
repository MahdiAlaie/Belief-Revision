from belief_revision.logic import Implies,Not,And,Or, Var
from belief_revision.exact import exact_revision

a, b, q = Var("a") , Var("b"), Var("q")
rule = Implies(Or(a,b),q)
base = (a,b,rule)
new_information = Not(q)

print("Belief base B:")

for formula in base:
    print(f" - {formula}")
print( f" New information W: {new_information} \n")

result = exact_revision (base , new_information)

print("Minimal conflict kernel Kw(B):")
for kernel in result.kernels:
    print(" {" + "," .join(map(str,kernel)) + "}")

print (" \nOptimal deletion sets under uniform deletion cost:")
for deletion in result.optimal_deletions:
    print("D = {" + "," .join(map(str,deletion)) + "}")

print("\nResulting belief base(s):")
for output in result.outputs:
    print(" {" + "," .join(map(str,output))+ "}")