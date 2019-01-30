#!/usr/bin/env python
# -*- coding: utf-8 -*-

import functools


def disable(func):
    '''
    Disable a decorator by re-assigning the decorator's name
    to this function. For example, to turn off memoization:

    >>> memo = disable

    '''
    return


def decorator(func):
    '''
    Decorate a decorator so that it inherits the docstrings
    and stuff from the function it's decorating.
    '''    
    return 


def countcalls(func):
    '''Decorator that counts calls made to the function decorated.'''
    
    @functools.wraps(func)
    def helper(*args, **kwargs):
        helper.calls += 1
        return func(*args, **kwargs)
        
    helper.calls = 0
    return helper


def memo(func):
    '''
    Memoize a function so that it caches all return values for
    faster future lookups.
    '''
    
    cash = dict()
    
    @functools.wraps(func)
    def helper(*args, **kwargs):
        key = tuple(sorted(args)) + tuple(sorted(kwargs.items()))
        if key not in cash:
            cash[key] = func(*args, **kwargs)
        return cash[key]
    
    return helper


def n_ary(func):
    '''
    Given binary function f(x, y), return an n_ary function such
    that f(x, y, z) = f(x, f(y,z)), etc. Also allow f(x) = x.
    '''
    @functools.wraps(func)
    def helper(x, *args):
        return x if not args else func(x, helper(*args))
    
    return helper

def decorator_with_args(decor):
    '''
    Allows arguments with decorators.
    '''
    @functools.wraps(decor)
    def helper(*dargs, **dwargs):
        def decorator(func):
            final_decor = decor(func, *dargs, **dwargs)
            functools.update_wrapper(final_decor, func)
            return final_decor
        return decorator
    return helper

@decorator_with_args
def trace(func, delimiter = '____'):
    '''Trace calls made to function decorated.

    @trace("____")
    def fib(n):
        ....

    >>> fib(3)
     --> fib(3)
    ____ --> fib(2)
    ________ --> fib(1)
    ________ <-- fib(1) == 1
    ________ --> fib(0)
    ________ <-- fib(0) == 1
    ____ <-- fib(2) == 2
    ____ --> fib(1)
    ____ <-- fib(1) == 1
     <-- fib(3) == 3

    '''    
    @functools.wraps(func)
    def helper(*arg, **kwarg):
        print(delimiter * helper.depth, '-->', func.__name__, '(', ', '.join(map(str, arg)), ', '.join(map(str, kwarg.items())), ')')
        
        helper.depth += 1
        
        
        result = func(*arg, **kwarg)
        
        print(delimiter * helper.depth, '<--', func.__name__, '(', ', '.join(map(str, arg)), \
                  ', '.join(map(str, kwarg.items())), ') == ', result)
        
        helper.depth -= 1
            
        return result
    
    helper.depth = 0
    return helper


@countcalls
@n_ary
@memo
def foo(a, b):
    return a + b


@countcalls
@n_ary
@memo
def bar(a, b):
    return a * b


@countcalls
@trace("____")
@memo
def fib(n):
    """Some doc"""
    return 1 if n <= 1 else fib(n-1) + fib(n-2)



def main():
    print (foo(4, 3))
    print (foo(4, 3, 2))
    print (foo(4, 3))
    print ("foo was called", foo.calls, "times")
    
    print (bar(4, 3))
    print (bar(4, 3, 2))
    print (bar(4, 3, 2, 1))
    print ("bar was called", bar.calls, "times")
    
    print (fib.__doc__)
    fib(3)
    print(fib.calls, 'calls made')
    

if __name__ == '__main__':
    main()
