#!/usr/bin/env python
# -*- coding: utf-8 -*-

import abc
import json
import datetime
import logging
import hashlib
import uuid
from optparse import OptionParser
from http.server import HTTPServer, BaseHTTPRequestHandler
from http import HTTPStatus
import re

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


class CharField:   
    def __init__(self, required, nullable):
        self.required = required
        self.nullable = nullable
        
    def __call__(self, name, request):
        
        try:
            res = request.get(name, None)
        except Exception as e:
            logging.error(repr(e))
            raise ValueError("Request dosn't include field {}.".format(name))
        
        if not isinstance(name, str):
            raise TypeError('Requested field {} is not a string object'.format(name))
        
        if (res is None) and self.required:
            raise ValueError('Requested field {} is required, but doesnt exists'.format(name))
        
        if (res is None) and not self.nullable:
            raise ValueError('Requested field {} couldnt be null, but doesnt exists'.format(name))
        
        if (res is not None) and (not isinstance(res, str)):
            raise ValueError('Resulted value {} for the field {} should be string, not {}'.\
                             format(res, name, type(name)))        
                
        return res

class ArgumentsField(object):
    def __init__(self, required, nullable):
        self.required = required
        self.nullable = nullable
        
    def __call__(self, name, request):
        
        if (not isinstance(name, str)) & (not isinstance(request, dict)):
            raise ValueError('Key:string and request:dict should be passed to the arguments checker.')
        
        try:
            res = request.get(name, None)
        except Exception as e:
            logging.error(repr(e))
            raise ValueError("Request dosn't include field {}.".format(name))
        
        if not isinstance(name, str):
            raise TypeError('Requested field {} is not a string object'.format(name))
        
        if (res is None) and self.required:
            raise ValueError('Requested field {} is required, but doesnt exists'.format(name))
        
        if (res is None) and not self.nullable:
            raise ValueError('Requested field {} couldnt be null, but doesnt exists'.format(name))
        
        if not isinstance(res, dict):
            raise ValueError('Resulted value should be dict, not {}'.format(type(name)))         
                
        return res


class EmailField(CharField):
    def __init__(self, required, nullable):
        self.required = required
        self.nullable = nullable     
        
    def __call__(self, request):
        
        if not isinstance(request, dict):
            raise ValueError('Request:dict should be passed to the checker.')
        
        try:
            res = request['body']['arguments'].get("email", None)
        except Exception as e:
            logging.error(repr(e))
            raise ValueError("Request doesn't include email.")
                
        if (res is not None) and (not isinstance(res, str)):
            raise TypeError('Requested field "email" is not a string object, but {}'.format(type(res)))
      
        if (res is None) and self.required:
            raise ValueError('Requested field "email" is required, but doesnt exists')
      
        if (res is None) and not self.nullable:
            raise ValueError('Requested field "email" couldnt be null, but doesnt exists')          
       
        if (not res is None) and (not re.search(r'\w@{1}\w', res)):
            raise ValueError('Wrong email format: there is no "@" in it.')
          
        return res


class PhoneField(object):
    def __init__(self, required, nullable):
        self.required = required
        self.nullable = nullable
        
    def __call__(self, request):
        
        if not isinstance(request, dict):
            raise ValueError('Request:dict should be passed to the checker.')
        
        try:
            res = request['body']['arguments'].get("phone", None)
        except Exception as e:
            logging.error(repr(e))
            raise ValueError("Request dosn't include PhoneField.")
    
        if (res is not None) and (not isinstance(res, str)) and (not isinstance(res, int)):
            raise TypeError('Requested field "phone" is not a string or int object')
        
        if (res is None) and self.required:
            raise ValueError('Requested field "phone" is required, but doesnt exists')
        
        if (res is None) and not self.nullable:
            raise ValueError('Requested field "phone" couldnt be null, but doesnt exists')          
        
        if ((isinstance(res, str)) and (not re.fullmatch(r'7\d{10}', res))):
            raise ValueError('Wrong phone format.')
        
        if (isinstance(res, int)) and ((res // 10000000000 != 7) or ( res // 100000000000 != 0)):
            raise ValueError('Wrong phone format.')
       
        return res


class DateField(object):
    def __init__(self, required, nullable):
        self.required = required
        self.nullable = nullable
        
    def __call__(self, request):
        
        if not isinstance(request, dict):
            raise ValueError('Request:dict should be passed to the checker.')
        
        try:
            res = request['body']['arguments'].get("date", None)
        except Exception as e:
            logging.error(repr(e))
            raise ValueError("Request dosn't include DateField.")
    
        if (not res is None) and (not isinstance(res, str)):
            raise TypeError('Requested field "Date" is not a string object')
        
        if (res is None) and self.required and (not self.nullable):
            raise ValueError('Requested field "Date" is required, but doesnt exists')
        
        if (res is None) and (not self.nullable):
            raise ValueError('Requested field "Date" couldnt be null, but doesnt exists')  
        
        if (not res is None) and (res != '') and (not re.fullmatch(r'\d{2}.\d{2}.\d{4}', res)):
            raise ValueError('Wrong date format.')
                
        return res



class BirthDayField(object):
    def __init__(self, required, nullable):
        self.required = required
        self.nullable = nullable
        
    def __call__(self, request):
        
        if not isinstance(request, dict):
            raise ValueError('Request:dict should be passed to the checker.')
        
        try:
            res = request['body']['arguments'].get("birthday", None)
        except Exception as e:
            logging.error(repr(e))
            raise ValueError("Request dosn't include BirthDayField.")
    
        if (res is not None) and (not isinstance(res, str)):
            raise TypeError('Requested field "birthday" is not a string object')
        
        if not res and self.required:
            raise ValueError('Requested field "birthday" is required, but doesnt exists')
        
        if not res and not self.nullable:
            raise ValueError('Requested field "birthday" couldnt be null, but doesnt exists')  
        
        if (res is not None) and (res != '') and (not re.fullmatch(r'\d{2}.\d{2}.\d{4}', res)):
            raise ValueError('Wrong birthday format.')
        
        if (res is not None) and \
        (-int(res.split('.')[-1].strip()) + int(datetime.datetime.now().strftime("%Y")) > 70):
            raise ValueError('Wrong birthday value (more than 70 years ago).')
        
        return res


class GenderField(object):
    def __init__(self, required, nullable):
        self.required = required
        self.nullable = nullable
        
    def __call__(self, request):
       
        if not isinstance(request, dict):
            raise ValueError('Request:dict should be passed to the checker.')
       
        try:
            res = request['body']['arguments'].get("gender", None)
        except Exception as e:
            logging.error(repr(e))
            raise ValueError("Request dosn't include GenderField.")
       
        if (res is not None) and (not isinstance(res, int)):
            raise ValueError('Requested field "gender" is not an int object')
        
        if not res and self.required:
            raise ValueError('Requested field "gender" is required, but doesnt exists')
       
        if not res and not self.nullable:
            raise ValueError('Requested field "gender" couldnt be null, but doesnt exists')  
       
        if (not res is None) and (res != 0 and res != 1 and res != 2):
            raise ValueError('Wrong gender format.')
        
        return res



class ClientIDsField(object):
    def __init__(self, required):
        self.required = required
        
    def __call__(self, request):
        
        try:
            res = request['body']['arguments'].get("client_ids", None)
        except Exception as e:
            logging.error(repr(e))
            raise ValueError("Request doesn't include ClientIDsField.")
        
        if (res is None) and (self.required):
            raise ValueError('Value ClientIDs is null but it is required.')
        
        if (not res is None) and (not isinstance(res, list)):
            raise ValueError('Required value ClientID is not a list, but {}.'.format(type(res)))
        
        if (not res is None) and (not all(list(map(lambda x: isinstance(x, int), res)))):           
            raise ValueError('ClientIDs should consist of integers.')
        
        if (not res is None) and (len(res) == 0):
            raise ValueError('ClientIDs list is empty.')        
        
        return res


class ClientsInterestsRequest(object):
    def __init__(self, request, store = None):
        self.client_ids = ClientIDsField(required=True)(request)        
        self.date = DateField(required=False, nullable=True)(request)       
        self.store = store
        
    def __call__(self):
        res = {i : scoring.get_interests(self.store, i) for i in self.client_ids}
        return res


class OnlineScoreRequest(object):
    def __init__(self, request):
        self.first_name = CharField(required=False, nullable=True)('first_name'
                                                                   , request['body']['arguments'])        
        self.last_name = CharField(required=False, nullable=True)('last_name'
                                                                   , request['body']['arguments'])       
        self.email = EmailField(required=False, nullable=True)(request)        
        self.phone = PhoneField(required=False, nullable=True)(request)       
        self.birthday = BirthDayField(required=False, nullable=True)(request)       
        self.gender = GenderField(required=False, nullable=True)(request)       
        
    def __call__(self, store, method_request):
       
        if (self.phone and self.email) or (self.first_name and self.last_name) or \
           ((self.gender or self.gender == 0) and self.birthday):
            if method_request.login == ADMIN_LOGIN:
                res = 42
            else:                    
                res = scoring.get_score(store=store, email=self.email, phone=self.phone
                                        , first_name=self.first_name, last_name=self.last_name
                                        , birthday=self.birthday, gender=self.gender)
        else:
            res = None
            
        if res is None:
            raise ValueError('There is no a valid paar in the arguments.')
        
        return {'score': res}
    
 
class MethodRequest(object):
    def __init__(self, request):
        self.account = CharField(required=False, nullable=True)('account', request['body'])
        logging.info('logging account {}'.format(self.account))
        self.login = CharField(required=True, nullable=True)('login', request['body'])
        self.token = CharField( required=True, nullable=True)('token', request['body'])
        self.arguments = ArgumentsField(required=True, nullable=True)('arguments', request['body'])
        self.method = CharField(required=True, nullable=False)('method', request['body'])

def check_auth(method_request):
    if method_request.login == ADMIN_LOGIN:
        string_to_encode = datetime.datetime.now().strftime("%Y%m%d%H") + ADMIN_SALT
        digest = hashlib.sha512(string_to_encode.encode()).hexdigest()
    else:
        string_to_encode = method_request.account + method_request.login + SALT
        digest = hashlib.sha512(string_to_encode.encode()).hexdigest()
    if digest == method_request.token:
        return True
    
    return False


def method_handler(request, ctx, store):
    
    if ('body' not in request) or ('arguments' not in request['body']):
        return ERRORS[INVALID_REQUEST], INVALID_REQUEST
    
    try:
        method_request = MethodRequest(request)
        
        if not check_auth(method_request):
            return ERRORS[FORBIDDEN], FORBIDDEN  
        
        if len(request['body']['arguments']) == 0:
            return ERRORS[INVALID_REQUEST], INVALID_REQUEST        
        
        if method_request.method == "online_score":
            req = OnlineScoreRequest(request)
            res = req(store, method_request)
            ctx['has'] = [attr for attr in dir(req) \
                          if (getattr(req, attr) is not None) \
                          and (not callable(getattr(req, attr))) \
                          and (not attr.startswith("__"))]
            
        elif method_request.method == "clients_interests":
            res = ClientsInterestsRequest(request)()
            ctx['nclients'] = len(res)
            
        else:
            raise ValueError('There is no proper method name in request.')
        
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
                    response, code = self.router[path]({"body": request, "headers": self.headers}, context, self.store)
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
                        format='[%(asctime)s] %(levelname).1s %(message)s', datefmt='%Y.%m.%d %H:%M:%S')
    server = HTTPServer(("localhost", opts.port), MainHTTPHandler)
    logging.info("Starting server at %s" % opts.port)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    server.server_close()
