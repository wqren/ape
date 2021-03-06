from ape import ape_dir
from ape.env_manip import pack_many
from ape.timings.util import graph_iter
from ape.theano_util import shape_of_variables
import os
import ast
from ape.util import dearrayify
import theano

def _compute_time_on_machine(runfile, i, o, input_shapes, machine, niter):
    """ Computes computation time of funciton graph on a remote machine

    Returns average duration of the computation (time)

    inputs:
        runfile - The program to run on the remote machine
        i       - A Theano graph
        o       - A Theano graph
        input_shapes - A dict mapping input variable to array shape
        machine - A machine on which to run the graph
        niter - The number of times to run the computation in sampling

    outputs:
        A dict mapping apply node to average runtime

    >>> _compute_time_on_machine(runfile, i, o, {x: (10, 10)}, 'receiver.univ.edu', 10)
    {dot(x, Add(x, y)): 0.133, Add(x, y): .0012}

    See Also
    --------
        comptime_dict_cpu
        comptime_dict_gpu
    """

    file = open('_machinefile.txt', 'w')
    file.write(machine)
    file.close()

    # stringify the keys

    variables = theano.gof.graph.variables(i, o)
    if len(set(map(str, variables))) != len(variables):
        raise ValueError("Not all variables have unique names"
                         "Look into theano.gof.utils.give_variables_names")


    known_shapes = shape_of_variables(i, o, input_shapes)

    known_shapes_str = str({str(k):v for k,v in known_shapes.items()})

    stdin, stdout, stderr = os.popen3('''mpiexec -np 1 -machinefile _machinefile.txt python %s%s "%s" %d'''%(ape_dir, runfile, known_shapes_str, niter))

    # Send the fgraphs as strings (they will be unpacked on the other end)

    nodes = theano.gof.graph.list_of_nodes(i, o)
    fgraphs = graph_iter(nodes)
    pack_many(fgraphs, stdin) # This writes to stdin
    stdin.close() # send termination signal

    # Receive the output from the compute node
    # return stdout.read() + stderr.read()
    message = stdout.read()
    times = ast.literal_eval(message)
    return  dict(zip(map(str, nodes), times))
