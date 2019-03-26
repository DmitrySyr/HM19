import functools
import unittest

from server.class_blocks import (CharField, ValidationError, EmailField, 
                          PhoneField, ArgumentsField, DateField,
                          BirthDayField, GenderField, ClientIDsField,)


def cases(cases):
    def decorator(f):
        @functools.wraps(f)
        def wrapper(*args):
            for c in cases:
                new_args = args + (c if isinstance(c, tuple) else (c,))
                f(*new_args)
        return wrapper
    return decorator


def make_test_class(cls, **kwargs): 
    attr = dict()
    attr['field'] = cls(**kwargs)
    setattr(attr['field'], 'label', 'test')
    attr['__init__'] = lambda self, value: setattr(self, 'field', value)
    return type('Helper', (object,), attr)


class TestCharField(unittest.TestCase):

    @cases(['', 'account', 'name', 'field'])
    def test_good_if_nullable(self, value):
        make_test_class(CharField, nullable=True, required=True)(value)

    @cases(['account', 'name', 'field'])
    def test_good_if_not_nullable(self, value):
        make_test_class(CharField, nullable=False, required=True)(value)

    @cases(['', None])
    def test_raises_if_not_nullable(self, value):
        with self.assertRaises(ValidationError):
            make_test_class(CharField, nullable=False, required=True)(value)

    @cases([None, '', 0, [0], {0, 1}, 3.14, {'abc': 123}])
    def test_raises_for_bad_values(self, value):
        with self.assertRaises(ValidationError):
            make_test_class(CharField, nullable=False, required=True)(value)


class TestEmailField(unittest.TestCase):

    @cases([None, '', 'account@mk.bk'])
    def test_good_if_nullable(self, value):
        make_test_class(EmailField, nullable=True, required=True)(value)

    @cases(['account@mk.bk', 'ds.ds@gmail.com', 'ott.ott.ott@mail.ru',
            'rete98098@nm7878.com.fooo'])
    def test_good_if_not_nullable(self, value):
        make_test_class(EmailField, nullable=False, required=True)(value)

    @cases(['', None])
    def test_raises_if_not_nullable(self, value):
        with self.assertRaises(ValidationError):
            make_test_class(EmailField, nullable=False, required=True)(value)

    @cases([None, '', 0, [0], {0, 1}, 3.14, {'abc': 123}, '@mail.ru', 
            'din@mail', '@mail.', 'rthj8787@bk.'])
    def test_raises_for_bad_values(self, value):
        with self.assertRaises(ValidationError):
            make_test_class(EmailField, nullable=False, required=True)(value)


class TestPhoneField(unittest.TestCase):

    @cases([None, '', '71234567890'])
    def test_good_if_nullable(self, value):
        make_test_class(PhoneField, nullable=True, required=True)(value)

    @cases(['71234567890', 71234567890])
    def test_good_if_not_nullable(self, value):
        make_test_class(PhoneField, nullable=False, required=True)(value)

    @cases(['', None, 0])
    def test_raises_if_not_nullable(self, value):
        with self.assertRaises(ValidationError):
            make_test_class(PhoneField, nullable=False, required=True)(value)

    @cases([None, '', 0, [0], {0, 1}, 3.14, {'abc': 123}, '@mail.ru', 
            7123456789, 712345678909, 81234567890,
            '7123456789', '712345678909', '81234567890',])
    def test_raises_for_bad_values(self, value):
        with self.assertRaises(ValidationError):
            make_test_class(PhoneField, nullable=False, required=True)(value)

class TestArgumentsField(unittest.TestCase):

    @cases([None, {}])
    def test_good_if_nullable(self, value):
        make_test_class(ArgumentsField, nullable=True, required=True)(value)

    @cases([{'a': [123], 'b': True}])
    def test_good_if_not_nullable(self, value):
        make_test_class(ArgumentsField, nullable=False, required=True)(value)

    @cases(['', None, 0, {}])
    def test_raises_if_not_nullable(self, value):
        with self.assertRaises(ValidationError):
            make_test_class(ArgumentsField, nullable=False, required=True)(value)

    @cases([None, '', 0, [0], {0, 1}, 3.14, '@mail.ru', 
            7123456789, 712345678909, 81234567890,
            '7123456789', '712345678909', '81234567890',
            {},])
    def test_raises_for_bad_values(self, value):
        with self.assertRaises(ValidationError):
            make_test_class(ArgumentsField, nullable=False, required=True)(value)


class TestDateField(unittest.TestCase):

    @cases([None, '', '23.12.1970'])
    def test_good_if_nullable(self, value):
        make_test_class(DateField, nullable=True, required=True)(value)

    @cases(['01.01.2014', '23.12.1970'])
    def test_good_if_not_nullable(self, value):
        make_test_class(DateField, nullable=False, required=True)(value)

    @cases(['', None, 0, {}])
    def test_raises_if_not_nullable(self, value):
        with self.assertRaises(ValidationError):
            make_test_class(DateField, nullable=False, required=True)(value)

    @cases([None, '', 0, [0], {0, 1}, 3.14, '@mail.ru', 
            7123456789, 712345678909, 81234567890,
            '7123456789', '712345678909', '81234567890',
            {}, '2014', '01.24.2000', '01.01.99999', '32.03.2011'])
    def test_raises_for_bad_values(self, value):
        with self.assertRaises(ValidationError):
            make_test_class(DateField, nullable=False, required=True)(value)

class TestBirthDayField(unittest.TestCase):

    @cases([None, '', '23.12.1970'])
    def test_good_if_nullable(self, value):
        make_test_class(BirthDayField, nullable=True, required=True)(value)

    @cases(['01.01.2014', '23.12.1970'])
    def test_good_if_not_nullable(self, value):
        make_test_class(BirthDayField, nullable=False, required=True)(value)

    @cases(['', None, 0, {}])
    def test_raises_if_not_nullable(self, value):
        with self.assertRaises(ValidationError):
            make_test_class(BirthDayField, nullable=False, required=True)(value)

    @cases([None, '', 0, [0], {0, 1}, 3.14, '@mail.ru', 
            7123456789, 712345678909, 81234567890,
            '7123456789', '712345678909', '81234567890',
            {}, '2014', '01.24.2000', '01.01.99999', '32.03.2011',
            '01.01.1900'])
    def test_raises_for_bad_values(self, value):
        with self.assertRaises(ValidationError):
            make_test_class(BirthDayField, nullable=False, required=True)(value)

class TestGenderField(unittest.TestCase):

    @cases([None, 0])
    def test_good_if_nullable(self, value):
        make_test_class(GenderField, nullable=True, required=True)(value)

    @cases([0, 1, 2])
    def test_good_if_not_nullable(self, value):
        make_test_class(GenderField, nullable=False, required=True)(value)

    @cases(['', None, -1, {}])
    def test_raises_if_not_nullable(self, value):
        with self.assertRaises(ValidationError):
            make_test_class(GenderField, nullable=False, required=True)(value)

    @cases([None, '', [0], {0, 1}, 3.14, '@mail.ru', 
            7123456789, 712345678909, 81234567890,
            '7123456789', '712345678909', '81234567890',
            {}, '2014', '01.24.2000', '01.01.99999', '32.03.2011',
            '01.01.1900', -1, 4.5, 1.0, 0.00, 3, 4])
    def test_raises_for_bad_values(self, value):
        with self.assertRaises(ValidationError):
            make_test_class(GenderField, nullable=False, required=True)(value)

class TestClientIDsField(unittest.TestCase):

    @cases([None, []])
    def test_good_if_nullable(self, value):
        make_test_class(ClientIDsField, nullable=True, required=True)(value)

    @cases([[0, 1], [2], [0], [1, 2, 3, 4, 5]])
    def test_good_if_not_nullable(self, value):
        make_test_class(ClientIDsField, nullable=False, required=True)(value)

    @cases(['', None, -1, {}, []])
    def test_raises_if_not_nullable(self, value):
        with self.assertRaises(ValidationError):
            make_test_class(ClientIDsField, nullable=False, required=True)(value)

    @cases([None, '', [], {0, 1}, 3.14, '@mail.ru', 
            7123456789, 712345678909, 81234567890,
            '7123456789', '712345678909', '81234567890',
            {}, '2014', '01.24.2000', '01.01.99999', '32.03.2011',
            '01.01.1900', -1, 4.5, 1.0, 0.00, 3, 4,
            ['a', 2, 3], [0, 2, 45, 3.14], [4, 5, {}],
            [5, 6, set()], [1, 2, [3], 5], [4, 5, -3]])
    def test_raises_for_bad_values(self, value):
        with self.assertRaises(ValidationError):
            make_test_class(ClientIDsField, nullable=False, required=True)(value)

        

if __name__ == "__main__":
    unittest.main()