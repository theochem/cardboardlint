"""Examples of poor python style."""

from math import sin
import math

__all__ = ['math', 'sin']

sin = math.sin

def add(a,b):
    '''Adds stuff.'''
    return a+b
    print('never executed')
