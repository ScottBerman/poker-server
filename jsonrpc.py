#!/usr/bin/env python3
""" async-friendly jsonrpc """

class JsonRpc(object):
    ERROR_PARSE = -32700
    ERROR_INVALID_REQUEST = -32600
    ERROR_METHOD_NOT_FOUND = -32601
    ERROR_INVALID_PARAMS = -32602
    ERROR_INTERNAL = -32603

    def __init__ (self, procedures):
        self.procedures = procedures

    def has_procedure(self, procedure):
        if isinstance(procedure, dict):
            return procedure["method"] in self.procedures
        else:
            return procedure in self.procedures

    async def handle (self, request):
        print("REQUEST: ", request)
        if not isinstance(request, dict):
            return self.build_error(id=None, code=JsonRpc.ERROR_PARSE, message="request is not a dict")

        if "jsonrpc" not in request or request["jsonrpc"] != "2.0":
            return self.build_error(id=None, code=JsonRpc.ERROR_INVALID_REQUEST, message="request is not jsonrpc 2.0")

        if "id" not in request: #no ID means it's a notificatoin, ignore
            return None

        id = request["id"]

        if "method" not in request:
            return self.build_error(id=id, code=JsonRpc.ERROR_INVALID_REQUEST, message="request has no method")

        method = request["method"]

        if method not in self.procedures:
            return self.build_error(id=id, code=JsonRpc.ERROR_METHOD_NOT_FOUND, message=f"method {method} not found")

        function = self.procedures[method]

        # try:
        if "params" in request:
            params = request["params"]
            if isinstance(params, list):
                result = await function(*params)
            elif isinstance(params, dict):
                result = await function(**params)
            else:
                result = await function(params)
        else: # no params
            result = await function()
        # except TypeError as e:
            # return self.build_error(id=id, code=JsonRpc.ERROR_INVALID_PARAMS, message=str(e))
        # except Exception as e:
            # raise
        
        #    return self.build_error(id=id, code=JsonRpc.ERROR_INTERNAL, message=str(e))

        return self.build_result(id=id, result=result)

    @classmethod
    def build_error (cls, id, code, message="", data=None):
        errval = {
            "code": code,
            "message": message
        }

        if (data):
            errval["data"] = data

        return cls.build_result(id=id, error=errval)

    @staticmethod
    def build_result (id, result=None, error=None):
        retval = {
            "jsonrpc": "2.0",
            "id": id
        }

        if error is not None:
            retval["error"] = error
        else: # result can be None
            retval["result"] = result

        return retval

    @staticmethod
    def build_request (id=None, method=None, params=None):
        assert (method is not None), "Method cannot be none"

        retval = {
            "jsonrpc": "2.0",
            "id": id,
            "method": method
        }

        if params is not None:
            retval["params"] = params

        return retval

