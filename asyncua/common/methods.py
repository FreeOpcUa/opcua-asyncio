"""
High level method related functions
"""

from asyncio import iscoroutinefunction

from asyncua import ua


async def call_method(parent, methodid, *args):
    """
    Call an OPC-UA method. methodid is browse name of child method or the
    nodeid of method as a NodeId object
    arguments are variants or python object convertible to variants.
    which may be of different types
    returns a list of values or a single value depending on the output of the method
    : param: parent `Node`
    """
    result = await call_method_full(parent, methodid, *args)

    if len(result.OutputArguments) == 0:
        return None
    elif len(result.OutputArguments) == 1:
        return result.OutputArguments[0]
    else:
        return result.OutputArguments


async def call_method_full(parent, methodid, *args):
    """
    Call an OPC-UA method. methodid is browse name of child method or the
    nodeid of method as a NodeId object
    arguments are variants or python object convertible to variants.
    which may be of different types
    returns a CallMethodResult object with converted OutputArguments
    : param: parent `Node`
    """
    if isinstance(methodid, (str, ua.uatypes.QualifiedName)):
        methodid = (await parent.get_child(methodid)).nodeid
    elif hasattr(methodid, 'nodeid'):
        methodid = methodid.nodeid

    result = await _call_method(parent.server, parent.nodeid, methodid, to_variant(*args))
    result.OutputArguments = [var.Value for var in result.OutputArguments]
    return result


async def _call_method(server, parentnodeid, methodid, arguments):
    """
    :param server: `UaClient` or `InternalSession`
    :param parentnodeid:
    :param methodid:
    :param arguments:
    :return:
    """
    request = ua.CallMethodRequest()
    request.ObjectId = parentnodeid
    request.MethodId = methodid
    request.InputArguments = arguments
    methodstocall = [request]
    results = await server.call(methodstocall)
    res = results[0]
    res.StatusCode.check()
    return res


def uamethod(func):
    """
    Method decorator to automatically convert
    arguments and output to and from variants
    """

    if iscoroutinefunction(func):
        async def wrapper(parent, *args):
            func_args = _format_call_inputs(parent, *args)
            result = await func(*func_args)
            return _format_call_outputs(result)

    else:
        def wrapper(parent, *args):
            func_args = _format_call_inputs(parent, *args)
            result = func(*func_args)
            return _format_call_outputs(result)
    return wrapper


def _format_call_inputs(parent, *args):
        if isinstance(parent, ua.NodeId):
        return (parent, *[arg.Value for arg in args])
        else:
            self = parent
            parent = args[0]
            args = args[1:]
        return (self, parent, *[arg.Value for arg in args])


def _format_call_outputs(result):
        if result is None:
            return []
        elif isinstance(result, ua.CallMethodResult):
            result.OutputArguments = to_variant(*result.OutputArguments)
            return result
        elif isinstance(result, ua.StatusCode):
            return result
        elif isinstance(result, tuple):
            return to_variant(*result)
        else:
            return to_variant(result)


def to_variant(*args):
    uaargs = []
    for arg in args:
        if not isinstance(arg, ua.Variant):
            arg = ua.Variant(arg)
        uaargs.append(arg)
    return uaargs
