'''Includes base class for requests classes and
   forms classes. 
'''

import logging
import re


from datetime import datetime
import api

################################################################################
###                             Special exceptions                           ###
################################################################################
        
class ValidationError(Exception):
    """Special kind of exception to underline assigment error
    in 'Field' like classes.
    """
    
    def __init__(self, message):
        super().__init__(message)

################################################################################
###                                  Helpers                                 ###
################################################################################

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


################################################################################
###                             Fields classes                               ###
################################################################################

        
class Field:
    """Basic class for all fields of a request. """
    
    __slots__ = ['required', 'nullable', 'field_type', 'name']

    def __init__(self, field_type, required = False, nullable = True):
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
        
        if (not value is None) and (not re.search(r'[\w.]+@{1}\w+\.\w{1,4}\b', value)):
            raise ValidationError('Wrong email: {}. Email format should '
            'be name@server.domen'.format(value))
            
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
        
        if (not value is None) and (not isinstance(value, str)):
            value = str(value)
        
        if (not value is None) and \
           ((datetime.now() - datetime.strptime(value, "%d.%m.%Y")).days > (70 * 365)):
            raise ValidationError('Wrong birthday date: {} (more than 70 years ago).'.format(value))          
       
        super().__set__(obj, value)
        
class GenderField(Field):
    ''''Class keeps gender field from request'''
    
    def __init__(self, *args):
        super().__init__(int, *args)            
        
    def __set__(self, obj, value): 
                        
        if (value is not None) and (not isinstance(value, int)):
            raise ValidationError('Requested field "gender" is not an int object.')        
            
        if (not value is None) and (not value in api.GENDERS):
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

        
################################################################################
###                           Requests bases classes                         ###
################################################################################

class RequestMeta(type):
    """Request meta class is designed to get all defined fields from
    the class and make list of it. This list will be used to initialize
    all neccessary fields.
    """
    
    def __new__(mcls, name, bases, attrs):
        
        declared_fields = []

        for attr_key, attr_value in attrs.items():
            if isinstance(attr_value, Field):
                declared_fields.append(attr_key)
                
        attrs['_declared_fields'] = declared_fields

        return type.__new__(mcls, name, bases, attrs)

class RequestBase(object, metaclass = RequestMeta):
    """Adding common methods to all requests classes"""  
    
    
    def __init__(self, arguments):   
        _validation_errors = []
        _wrong_field_names = []        
                       
        for name in self._declared_fields:
            try:
                setattr(self, name, find_field(arguments, name))
            except ValidationError as e:
                _validation_errors.append(e.args[0]) 
                _wrong_field_names.append(name)
                
            setattr(self, '_validation_errors', _validation_errors)
            setattr(self, '_wrong_field_names', _wrong_field_names)        