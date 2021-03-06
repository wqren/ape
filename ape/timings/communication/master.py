from ape.timings.communication.mpi import commtime_dict_mpi
from ape.timings.communication.gpu import commtime_dict_togpu, commtime_dict_fromgpu
from ape.timings.communication.util import function_from_group_dict
from ape.util import prod, merge
from ape.theano_util import bytes_of_dtype

commtime_dict_fns = (commtime_dict_mpi, commtime_dict_togpu,
                     commtime_dict_fromgpu)

def commtime_dict(network, *args, **kwargs):
    """ Estimate communicaiton times within a network

    Currently supported types:
        'mpi', 'togpu', 'fromgpu'

    inputs:
        network - dict like {(A, B): {'type': 'mpi'}}

    outputs:
        network - dict like {(A, B): {'type': 'mpi', 'intercept':1, 'slope':2}}
    """
    networks = [fn(network, *args, **kwargs) for fn in commtime_dict_fns]
    return merge(*networks)

def _commtime_dict_interface(network):
    """
    inputs
        network - dict like {(A, B): {'type': 'mpi'}}

    outputs
        network - dict like {(A, B): {'type': 'mpi', 'intercept':1, 'slope':2}}
    """
    pass


def make_commtime_function(cdict, known_shapes):
    """ Create callable function from a dict of intercept/slopes, known shapes

    inputs:
        cdict - dict mapping {(sender, receiver) : {'intercept':i, 'slope':s}}

        input_shapes - dict from input variables to shapes {TensorVar : shape}

    outputs:
        commtime - function :: (ApplyNode, sender, receiver) -> time (float)
    """

    bytes_fn = function_from_group_dict(cdict)
    known_shapes = {str(key): known_shapes[key] for key in known_shapes}

    def bytes(var):
        """ Compute the bytes that a theano variable holds """
        shape = known_shapes[str(var)]
        return prod(shape)*bytes_of_dtype(var.dtype)

    def commtime(var, sender, receiver):
        """ Returns the communication time to transmit a variable """
        if sender == receiver:
            return 0
        if (sender, receiver) not in cdict:
            return 1e9
        nbytes = bytes(var)
        intercept = cdict[sender, receiver]['intercept']
        slope     = cdict[sender, receiver]['slope']
        return slope*nbytes + intercept

    return commtime

