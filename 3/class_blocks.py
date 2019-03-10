'''Includes base class for requests classes and
   forms classes. 
'''

import abc
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
###                             Fields classes                               ###
################################################################################

        
class Field:
    """Basic class for all fields of a request. """
    
    __slots__ = ['required', 'nullable', 'field_type', 'name']

    def __init__(self, field_type, required=False, nullable=True, null_values=(None,)):
        self.required = required
        self.nullable = nullable
        self.field_type = field_type
        self.name = repr(self)
        self.null_values = null_values
    
    @abc.abstractclassmethod
    def validate(self, value):        
        pass        
    
    def __set__(self, cls, value):
        if (value is None) and self.required and not self.nullable:
            raise ValidationError('Field "{}" is required.'
                                  .format(self.label))
        
        if not self.nullable and value in self.null_values:
            raise ValidationError('Value of field "{}" could not be null.'
                                  .format(self.label))
        
        if (value is not None) and (not isinstance(value, self.field_type)):                            
            raise ValidationError('Assigning value "{}" for the field "{}" which '
                                  'should be "{}", not "{}"'.
                                  format(value, self.label, self.field_type, 
                                         type(value)))
        
        if value not in self.null_values:
            self.validate(value)                
        
        if value is not None:
            setattr(cls, self.name, value)   
    
    def __get__(self, obj, obj_type=None):
        return obj.__dict__.get(self.name, None)


class CharField(Field):
    '''Class keeps any string field from request'''
    
    def __init__(self, required, nullable):
        super().__init__(str, required, nullable, null_values=(None, ''))
        
    def validate(self, value):
        pass        
       
        
class EmailField(Field):
    '''Class keeps email field from request'''
    
    def __init__(self, required, nullable):
        super().__init__(str, required, nullable, null_values=(None, ''))
        
    def validate(self, value):
        if not re.search(r'[\w.]+@{1}\w+\.\w{1,4}\b', value):
            raise ValidationError('Wrong email: {}. Email format should '
                                  'be name@server.domen'.format(value))
        
        
class PhoneField(Field):
    ''''Class keeps phone field from request'''
    
    def __init__(self, required, nullable):
        super().__init__((str, int), required, nullable, null_values=(None, ''))
    
    def validate(self, value):
        if isinstance(value, str):            
            try:
                value = int(value)
            except Exception:
                raise ValidationError('Wrong phone format: {}.'.format(value)) 

        if value // 10000000000 != 7 or value // 100000000000 != 0:
            raise ValidationError('Wrong phone format: {}. Should be eleven numbers '
                                  'beginning with 7.'.format(value))    

        
class ArgumentsField(Field):
    ''''Class keeps arguments field from request as a dict'''
    
    def __init__(self, required, nullable):
        super().__init__(dict, required, nullable, null_values=(None, dict()))
        
    def validate(self, value):
        pass
         
        
class DateField(Field):
    ''''Class keeps Date field from request'''
    
    def __init__(self, required, nullable):
        super().__init__(str, required, nullable, null_values=(None, ''))
        
    def validate(self, value):  
        try:
            if not datetime.strptime(value, '%d.%m.%Y'):
                raise ValidationError('Wrong date format: {} .'.format(value)) 
        except Exception as e:
            raise ValidationError('Wrong date format: {} .'.format(value)) 
        
        
class BirthDayField(Field):
    ''''Class keeps birthday date field from request'''
    
    def __init__(self, required, nullable):
        super().__init__(str, required, nullable, null_values=(None, ''))        
        
    def validate(self, value):
        try:
            if (datetime.now() - datetime.strptime(value, "%d.%m.%Y")).days > (70 * 365):
                raise ValidationError('Wrong birthday date: {} '
                                      '(more than 70 years ago).'.format(value)) 
        except Exception:
            raise ValidationError('Wrong birthday date: {} '
                                  '(more than 70 years ago).'.format(value))      
        
        
class GenderField(Field):
    ''''Class keeps gender field from request'''
    
    def __init__(self, required, nullable):
        super().__init__(int, required, nullable, null_values=(None, ))        
        
    def validate(self, value):
        if value not in api.GENDERS:
            raise ValidationError('Wrong gender format: {} and type {}.'.format(value, type(value)))
        
        
class ClientIDsField(Field):
    def __init__(self, required, nullable):
        super().__init__(list, required, nullable, null_values=(None, []))   
        
    def validate(self, value):
        if not all(map(lambda x: isinstance(x, int), value)):           
            raise ValidationError('ClientIDs should consist of integers.') 
        
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
                attr_value.label = attr_key
                
        attrs['_declared_fields'] = declared_fields

        return type.__new__(mcls, name, bases, attrs)


class RequestBase(object, metaclass=RequestMeta):
    """Adding common methods to all requests classes"""  
    
    def __init__(self, arguments):   
        _validation_errors = []
        _wrong_field_names = []        
                       
        for name in self._declared_fields:
            try:
                setattr(self, name, arguments.get(name, None))
            except ValidationError as e:
                _validation_errors.append(e.args[0]) 
                _wrong_field_names.append(name)
                
            setattr(self, '_validation_errors', _validation_errors)
            setattr(self, '_wrong_field_names', _wrong_field_names)