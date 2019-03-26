#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json
import logging
import hashlib
import uuid

from datetime import datetime
from optparse import OptionParser
from http.server import HTTPServer, BaseHTTPRequestHandler

from server.scoring import get_interests, get_score
import server.class_blocks as cb
from server.class_blocks import ValidationError
from server.store import Store

SALT = "Otus"
ADMIN_LOGIN = "admin"
ADMIN_SALT = "42"
OK = 200
BAD_REQUEST = 400
FORBIDDEN = 403
NOT_FOUND = 404
INVALID_REQUEST = 422
INTERNAL_ERROR = 500
ERRORS = {
    BAD_REQUEST: "Bad Request",
    FORBIDDEN: "Forbidden",
    NOT_FOUND: "Not Found",
    INVALID_REQUEST: "Invalid Request",
    INTERNAL_ERROR: "Internal Server Error",
}
UNKNOWN = 0
MALE = 1
FEMALE = 2
GENDERS = {
    UNKNOWN: "unknown",
    MALE: "male",
    FEMALE: "female",
}


################################################################################
###                                  Helpers                                 ###
################################################################################

def check_auth(_parser):
    
    if _parser.login == ADMIN_LOGIN:
        string_to_encode = datetime.now().strftime("%Y%m%d%H") + ADMIN_SALT
        digest = hashlib.sha512(string_to_encode.encode()).hexdigest()
    else:
        string_to_encode = _parser.account + _parser.login + SALT
        digest = hashlib.sha512(string_to_encode.encode()).hexdigest()
    if digest == _parser.token:
        return True
    
    return False


################################################################################
###                             Requests classes                             ###
################################################################################


class InterestsRequest(cb.RequestBase):
    client_ids = cb.ClientIDsField(True, False)
    date = cb.DateField(False, True)
    
    @property
    def is_valid(self):        
        return len(self._wrong_field_names) == 0
    

class ScoreRequest(cb.RequestBase):
    first_name = cb.CharField(False, True)
    last_name = cb.CharField(False, True)
    email = cb.EmailField(False, True)
    phone = cb.PhoneField(False, True)
    birthday = cb.BirthDayField(False, True)
    gender = cb.GenderField(False, True)
    
    @property
    def is_valid(self):
        return len(self._wrong_field_names) == 0 and \
               any(((self.first_name and self.last_name),
                    (self.email and self.phone),
                    (self.birthday and self.gender is not None)))
               

class MethodRequest(cb.RequestBase):
    account = cb.CharField(False, True)
    login = cb.CharField(True, True)
    token = cb.CharField(True, True)
    arguments = cb.ArgumentsField(True, True)
    method = cb.CharField(True, True)
    
    @property
    def is_valid(self):
        for i in ('login', 'token', 'arguments', 'method'):        
            if getattr(self, i) is None:                
                self._wrong_field_names.append(i)
                self._validation_errors.append(f"Field {i} is not in the request.")
                       
        return len(self._wrong_field_names) == 0
    
    @property
    def is_admin(self):
        return self.login == ADMIN_LOGIN

################################################################################
###                        Implementing functions                            ###
################################################################################

    
def process_clients_interests(arguments, ctx, store=None):
    """Process user request for clients_interests method"""
    
    req = InterestsRequest(arguments) 
    
    if not req.is_valid:
        raise ValidationError(req._validation_errors)
    
    res = {i: get_interests(store, i) for i in req.client_ids}      
    ctx['nclients'] = len(res)
        
    return res


def process_online_score(arguments, ctx, store=None):
    """Process user request for online_score method"""
    
    req = ScoreRequest(arguments)
    
    if req.is_valid:   
        res = get_score(store=store, email=req.email, phone=req.phone,
                                first_name=req.first_name, last_name=req.last_name,
                                birthday=req.birthday, gender=req.gender)
    else:  
        err = f"One paar of arguments should be valid in the following order \
        (name: actual value) \
        first_name: {req.first_name!r} and last_name: {req.last_name!r} or \
        email: {req.email!r} and phone: {req.phone!r} or \
        birthday: {req.birthday!r} and gender: {req.gender!r}."
        raise ValidationError(err)
    
    ctx['has'] = [i for i in arguments.keys() 
                  if arguments[i] or (type(arguments[i]) == int and arguments[i] == 0)]
    
    return {'score': res}


def method_handler(request, ctx, store):
    if ('body' not in request) or ('arguments' not in request['body']):
        return ERRORS[INVALID_REQUEST], INVALID_REQUEST
    
    try:
        base_parser = MethodRequest(request['body'])        
        
        if not base_parser.is_valid:
            raise ValidationError(base_parser._validation_errors)
        
        if not check_auth(base_parser):
            return ERRORS[FORBIDDEN], FORBIDDEN        
        
        if len(base_parser.arguments) == 0:
            return ERRORS[INVALID_REQUEST], INVALID_REQUEST        
                
        if base_parser.method == "online_score":
            if base_parser.is_admin:
                res = {'score': 42}
            else:
                res = process_online_score(base_parser.arguments, ctx, store)            
             
        elif base_parser.method == "clients_interests":            
            res = process_clients_interests(base_parser.arguments, ctx, store)            
        else:
            res = NOT_FOUND
        
    except ValidationError as e:
        logging.error(repr(e))
        return e.args[0], INVALID_REQUEST    
    except ValueError as e:
        logging.error(repr(e))
        return e.args[0], INVALID_REQUEST
    except Exception as e:
        logging.error(repr(e))
        return e.args[0], INTERNAL_ERROR
        
    return res, OK


class MainHTTPHandler(BaseHTTPRequestHandler):
    
    router = {
        "method": method_handler
    }
   
    store = None
   
    def get_request_id(self, headers):
        return headers.get('HTTP_X_REQUEST_ID', uuid.uuid4().hex)

    def do_POST(self):
        response, code = {}, OK
        context = {"request_id": self.get_request_id(self.headers)}
        request = None
        try:
            data_string = self.rfile.read(int(self.headers['Content-Length']))            
            request = json.loads(data_string)
        except Exception:
            code = BAD_REQUEST

        if request:
            path = self.path.strip("/")
            logging.info("%s: %s %s" % (path, data_string, context["request_id"]))
            if path in self.router:
                try:
                    response, code = self.router[path]({"body": request, 
                                                        "headers": self.headers}, 
                                                       context, self.store)
                except Exception as e:
                    logging.exception("Unexpected error: %s" % e)
                    code = INTERNAL_ERROR
            else:
                code = NOT_FOUND

        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        if code not in ERRORS:
            r = {"response": response, "code": code}
        else:
            r = {"error": response or ERRORS.get(code, "Unknown Error"), "code": code}
        context.update(r)
        logging.info(context)
        self.wfile.write(json.dumps(r).encode())
        return


if __name__ == "__main__":
    op = OptionParser()
    op.add_option("-p", "--port", action="store", type=int, default=8080)
    op.add_option("-l", "--log", action="store", default=None)
    op.add_option("--redishost", action="store", type=str, default='127.0.0.1')
    op.add_option("--redisport", action="store", type=int, default=6379)
    op.add_option("--redisbase", action="store", type=int, default=0)
    op.add_option("--redistmout", action="store", type=int, default=10)
    (opts, args) = op.parse_args()
    logging.basicConfig(filename=opts.log, level=logging.INFO,
                        format='[%(asctime)s] %(levelname).1s %(message)s', 
                        datefmt='%Y.%m.%d %H:%M:%S')
    MainHTTPHandler.store = Store(host=opts.redishost, port=opts.redisport,
                           db=opts.redisbase, socket_timeout=opts.redistmout) 
    
    server = HTTPServer(("localhost", opts.port), MainHTTPHandler)
    logging.info("Starting server at %s" % opts.port)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    server.server_close()