import theano
from theano_to_milp import (make_ilp, dummy_compute_cost, dummy_comm_cost,
        dummy_ability, compute_schedule)
from master import compile
from timings import (load_dict, make_runtime_function, compute_runtimes,
        save_dict)
from env_manip import variables_with_names

x = theano.tensor.matrix('x')
y = theano.tensor.matrix('y')
z = theano.tensor.dot(x, x) + y[:,0].sum() - x*y
variables_with_names([x,y], [z]) # give names to all variables between x,y and z

times = load_dict('times.dat')
compute_cost = make_runtime_function(times)

env = theano.Env([x, y], [z])
input_shapes ={x:(5,5), y:(5,5)}
machine_ids = ["ankaa.cs.uchicago.edu", "mimosa.cs.uchicago.edu"]

code = compile(env, machine_ids, compute_cost, dummy_comm_cost,
        dummy_ability, input_shapes, 100)

f = open('results.py', 'w'); f.write(code); f.close()

