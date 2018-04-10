# coding=utf-8

import pytest

def func(x):  
  return x + 1 
  
def test_func():  
  assert func(2) == 3
