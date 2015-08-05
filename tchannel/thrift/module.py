from __future__ import (
    absolute_import, division, print_function, unicode_literals
)

import inspect
import types

from .reflection import get_service_methods, get_module_name


def from_thrift_module(service, thrift_module, hostport=None,
                       thrift_class_name=None):

    # start with a request maker instance
    maker = ThriftRequestMaker(
        service=service,
        thrift_module=thrift_module,
        hostport=hostport,
        thrift_class_name=thrift_class_name
    )

    # create methods that mirror thrift client
    # and each return ThriftRequest
    methods = _create_methods(thrift_module)

    # then attach to instane
    for name, method in methods.iteritems():
        method = types.MethodType(method, maker, ThriftRequestMaker)
        setattr(maker, name, method)

    return maker


class ThriftRequestMaker(object):

    def __init__(self, service, thrift_module,
                 hostport=None, thrift_class_name=None):

        self.service = service
        self.thrift_module = thrift_module
        self.hostport = hostport

        if thrift_class_name is not None:
            self.thrift_class_name = thrift_class_name
        else:
            self.thrift_class_name = get_module_name(self.thrift_module)

    def _make_request(self, method_name, args, kwargs):

        endpoint = self._get_endpoint(method_name)
        result_type = self._get_result_type(method_name)
        call_args = self._get_call_args(method_name, args, kwargs)

        request = ThriftRequest(
            service=self.service,
            endpoint=endpoint,
            result_type=result_type,
            call_args=call_args,
            hostport=self.hostport
        )

        return request

    def _get_endpoint(self, method_name):

        endpoint = '%s::%s' % (self.thrift_class_name, method_name)

        return endpoint

    def _get_args_type(self, method_name):

        args_type = getattr(self.thrift_module, method_name + '_args')

        return args_type

    def _get_result_type(self, method_name):

        result_type = getattr(self.thrift_module, method_name + '_result')

        return result_type

    def _get_call_args(self, method_name, args, kwargs):

        args_type = self._get_args_type(method_name)

        params = inspect.getcallargs(
            getattr(self.thrift_module.Iface, method_name),
            self,
            *args,
            **kwargs
        )
        params.pop('self')  # self is already known

        call_args = args_type()
        for name, value in params.items():
            setattr(call_args, name, value)

        return call_args


class ThriftRequest(object):

    # TODO - add __slots__
    # TODO - implement __repr__

    def __init__(self, service, endpoint, result_type,
                 call_args, hostport=None):

        self.service = service
        self.endpoint = endpoint
        self.result_type = result_type
        self.call_args = call_args
        self.hostport = hostport


def _create_methods(thrift_module):

    # TODO - this method isn't needed, instead, do:
    #
    # for name in get_service_methods(...):
    #   method = _create_method(...)
    #     # ...
    #

    methods = {}
    method_names = get_service_methods(thrift_module.Iface)

    for method_name in method_names:

        method = _create_method(method_name)
        methods[method_name] = method

    return methods


def _create_method(method_name):

    # TODO - copy over entire signature using @functools.wraps(that_function)
    # or wrapt on Iface.<method>

    def method(self, *args, **kwargs):
        # TODO switch to __make_request
        return self._make_request(method_name, args, kwargs)

    return method
