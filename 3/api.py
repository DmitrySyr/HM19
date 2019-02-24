#!/usr/bin/env python
# -*- coding: utf-8 -*-

import abc
import json
import logging
import hashlib
import uuid
import re
import functools

from datetime import datetime
from optparse import OptionParser
from http.server import HTTPServer, BaseHTTPRequestHandler
from http import HTTPStatus

import scoring

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


"""*****************************************************************************
                       =====         Helpers        =====

*****************************************************************************"""

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

def find_field(request, field):
    """Helper function for taking field from request by it's name. """

    res = None
    def helper(request):
        nonlocal res
        if field in request:            
            res = request[field]
            return True
        return any(map(helper, (v for k, v in request.items() if isinstance(v, dict))))        

    helper(request)
    return res

"""*****************************************************************************
                   =====         All field classes =====

*****************************************************************************"""


class ValidationError(Exception):
    """Special kind of exception to underline assigment error
    in 'Field' like classes.
    """
    
    def __init__(self, message):
        super().__init__(message)
        
        
class Field:
    """Basic class for all fields of a request. """
    
    __slots__ = ['required', 'nullable', 'field_type', 'name']

    def __init__(self, field_type, required, nullable):
        self.required = required
        self.nullable = nullable
        self.field_type = field_type
        self.name = repr(self)
    
    def __set__(self, cls, value):   
        
        if (value is None) and self.required:
            name = str()
            for key, val in type(cls).__dict__.items():
                if val == self:
                    name = key
                    break
                    
            raise ValidationError('Field "{}" is required.'.format(name))
        
        if (value is None) and not self.nullable:
            name = str()
            for key, val in type(cls).__dict__.items():
                if val == self:
                    name = key
                    break
                    
            raise ValidationError('Value of field "{}" could not be null.'.format(name))
        
        if (not value is None) and (not isinstance(value, self.field_type)):
            name = str()
            for key, val in type(cls).__dict__.items():
                if val == self:
                    name = key
                    break
                    
            raise ValidationError('Assigning value "{}" for the field "{}" which '
                                  'should be "{}", not "{}"'.\
                             format(value, name, self.field_type, type(value)))
        
        if not value is None:
            setattr(cls, self.name, value)
            
        if (value is None) and (self.nullable):
            setattr(cls, self.name, self.field_type())
    
    def __get__(self, obj, obj_type = None):
        
        return obj.__dict__.get(self.name, self.field_type())

class CharField(Field):
    '''Class keeps any string field from request'''
    
    def __init__(self, *args):
        super().__init__(str, *args)
        
class EmailField(Field):
    '''Class keeps email field from request'''
    
    def __init__(self, *args):
        super().__init__(str, *args)
        
    def __set__(self, obj, value):
        
        if (not value is None) and (not re.search(r'\w.]+@{1}\w+\.\w{1,4}\b', value)):
            raise ValidationError('Wrong email: {}. Email format should '
            'be name@serve.domen'.format(value))
            
        super().__set__(obj, value)
        
class PhoneField(Field):
    ''''Class keeps phone field from request'''
    
    def __init__(self, *args):
        super().__init__(int, *args)            
        
    def __set__(self, obj, value):
        
        if isinstance(value, str):
            value = int(value)
        
        if (not value is None) and ((value // 10000000000 != 7) or ( value // 100000000000 != 0)):
            raise ValidationError('Wrong phone format: {}. Should be eleven numbers '
            'beginning with 7.'.format(value))
       
        super().__set__(obj, value)  
        
class ArgumentsField(Field):
    ''''Class keeps arguments field from request as a dict'''
    
    def __init__(self, *args):
        super().__init__(dict, *args)
         
        
class DateField(Field):
    ''''Class keeps Date field from request'''
    
    def __init__(self, *args):
        super().__init__(str, *args)            
        
    def __set__(self, obj, value):
        
        if (not value is None) and (value != '') and (not datetime.strptime(value, '%d.%m.%Y')):
            raise ValidationError('Wrong date format: {} .'.format(value))
       
        super().__set__(obj, value)     
        
class BirthDayField(Field):
    ''''Class keeps birthday date field from request'''
    
    def __init__(self, *args):
        super().__init__(str, *args)            
        
    def __set__(self, obj, value):        
        
        if (not value is None) and \
        ((datetime.now() - datetime.strptime(value, "%d.%m.%Y")).days/365 > 70):
            raise ValidationError('Wrong birthday date: {} (more than 70 years ago).'.format(value))        
       
        super().__set__(obj, value)
        
class GenderField(Field):
    ''''Class keeps gender field from request'''
    
    def __init__(self, *args):
        super().__init__(int, *args)            
        
    def __set__(self, obj, value): 
                        
        if (value is not None) and (not isinstance(value, int)):
            raise ValidationError('Requested field "gender" is not an int object.')        
            
        if (not value is None) and (not value in [UNKNOWN, MALE, FEMALE]):
            raise ValidationError('Wrong gender format: {} and type {}.'.format(value, type(value)))
        
        # As we have '0' as a accepted value, we should add some extra value for None
        # which will be converted to initial value of a type (0 for int)
        # and implemented all checks here before converting None to -1
        if (value is None) and self.required:
            name = str()
            for key, val in type(self).__dict__.items():
                if val == self:
                    name = key
                    break
    
            raise ValidationError('Field "{}" is required.'.format(name))
        
        if (value is None) and not self.nullable:
            name = str()
            for key, val in type(cls).__dict__.items():
                if val == self:
                    name = key
                    break
    
            raise ValidationError('Value of field "{}" could not be null.'.format(name))   
        
        if value is None:
            value = -1
       
        super().__set__(obj, value)
        
class ClientIDsField(Field):
    def __init__(self, *args):
        super().__init__(list, *args)            
        
    def __set__(self, obj, value):  
            
        if (not value is None) and (not all(map(lambda x: isinstance(x, int), value))):           
            raise ValidationError('ClientIDs should consist of integers.')
        
        if (not value is None) and (len(value) == 0):
            raise ValidationError('ClientIDs list is empty.') 
       
        super().__set__(obj, value)
   

"""*****************************************************************************
                =====         Implementing functions          =====

*****************************************************************************"""

def generate_fields_storage_class(request, name):
    """Dynamically generates class-storge for parsed request. """
    
    if name == 'BaseParse':
        _fields = ['account', 'login', 'token', 'arguments', 'method']
    elif name == 'online_score':        
        _fields = ['login', 'first_name', 'last_name', 'email', 'phone', 'birthday', 'gender']
    elif name == 'clients_interests': 
        _fields = ['client_ids', 'date']       
    
    def init(_fields, self):
        [setattr(self, i, type(self).find_field(i)) 
         for i in type(self).__dict__ 
         if i in _fields]
    
    @property
    def is_admin(self):
        return self.login == ADMIN_LOGIN
        
    attr = {}    
    attr['__init__'] = lambda self: self.init(self)
    attr['find_field'] = functools.partial(find_field, request)
    attr['is_admin'] = is_admin
    attr['init'] = functools.partial(init, _fields)
    
    attr['account'] = CharField(False, True)
    attr['login'] = CharField(True, True)
    attr['token'] = CharField(True, True)
    attr['arguments'] = ArgumentsField(True, True)
    attr['method'] = CharField(True, False) 
    attr['client_ids'] = ClientIDsField(True, False)
    attr['date'] = DateField(False, True)  
    attr['first_name'] = CharField(False, True)
    attr['last_name'] = CharField(False, True)
    attr['email'] = EmailField(False, True)
    attr['phone'] = PhoneField(False, True)
    attr['birthday'] = BirthDayField(False, True)
    attr['gender'] = GenderField(False, True)     
    
    return type(name, tuple(), attr)
    
def process_clients_interests(Request, store = None):
    """Process user request for clients_interests method"""
    
    req = Request()
    res = {i : scoring.get_interests(store, i) for i in req.client_ids}
    return res

def process_online_score(Request, store = None):
    """Process user request for online_score method"""
    
    req = Request()
    
    if (req.phone and req.email) or (req.first_name and req.last_name) or \
       (req.gender >= 0 and req.birthday):
        if req.is_admin:
            res = 42
        else:                    
            res = scoring.get_score(store=store, email=req.email, phone=req.phone
                                    , first_name=req.first_name, last_name=req.last_name
                                    , birthday=req.birthday, gender=req.gender)
    else:
        raise ValueError('There is no a valid paar in the arguments.')
    
    return {'score': res}

def method_handler(request, ctx, store):
    
    if ('body' not in request) or ('arguments' not in request['body']):
        return ERRORS[INVALID_REQUEST], INVALID_REQUEST
    
    try:                        
        BaseParse = generate_fields_storage_class(request, 'BaseParse')        
        base_parser = BaseParse()
        
        if not check_auth(base_parser):
            return ERRORS[FORBIDDEN], FORBIDDEN
        
        if len(base_parser.arguments) == 0:
            return ERRORS[INVALID_REQUEST], INVALID_REQUEST
        
        Request = generate_fields_storage_class(request, base_parser.method) 
                
        if base_parser.method == "online_score":
            res = process_online_score(Request, store)            
            ctx['has'] = [i for i in base_parser.arguments.keys() 
                          if not base_parser.arguments[i] is None]
             
        elif base_parser.method == "clients_interests":            
            res = process_clients_interests(Request, store)           
            ctx['nclients'] = len(res)
        else:
            raise ValueError('There is no proper method name in request.')
        
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
        except:
            code = BAD_REQUEST

        if request:
            path = self.path.strip("/")
            logging.info("%s: %s %s" % (path, data_string, context["request_id"]))
            if path in self.router:
                try:
                    response, code = self.router[path]({"body": request, "headers": self.headers}, 
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
    (opts, args) = op.parse_args()
    logging.basicConfig(filename=opts.log, level=logging.INFO,
                        format='[%(asctime)s] %(levelname).1s %(message)s', 
                        datefmt='%Y.%m.%d %H:%M:%S')
    server = HTTPServer(("localhost", opts.port), MainHTTPHandler)
    logging.info("Starting server at %s" % opts.port)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    server.server_close()
 