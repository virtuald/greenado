
import greenado

import pytest

from tornado import gen, concurrent
from tornado.ioloop import IOLoop


class DummyException(Exception):
    pass


def test_gyield_retval_1():
    '''Ensure that return values are propagated to the caller'''
    
    future = concurrent.Future()

    def callback():
        future.set_result(1234)

    def _inner():
        IOLoop.current().add_callback(callback)
        
        return greenado.gyield(future) + 1

    @greenado.groutine
    def _main():
        return _inner() + 1
    
    main_retval = IOLoop.current().run_sync(_main)
    assert main_retval == 1236


def test_gyield_retval_2():
    '''Ensure that return values are propagated to the caller'''
    
    future = concurrent.Future()

    @gen.coroutine
    def callback():
        raise gen.Return(1234)

    @greenado.groutine
    def _main():
        return greenado.gyield(callback()) + 1
        
    main_retval = IOLoop.current().run_sync(_main)
    assert main_retval == 1235


def test_gyield_error():
    '''Ensure errors are propagated to the gyield caller'''
    future = concurrent.Future()

    def callback():
        future.set_exception(DummyException())

    @greenado.groutine
    def _main():
        IOLoop.current().add_callback(callback)
        
        with pytest.raises(DummyException):
            greenado.gyield(future)
            
        return True

    main_result = IOLoop.current().run_sync(_main)
    assert main_result == True


def test_groutine_error1():
    '''Ensure errors in groutines are propagated to the groutine caller'''    

    @greenado.groutine
    def _main():
        raise DummyException()

    with pytest.raises(DummyException):
        IOLoop.current().run_sync(_main)
  

def test_groutine_error2():
    '''Ensure errors yielded in groutines are propagated to the groutine caller'''
    
    @gen.coroutine
    def callback():
        raise DummyException()

    def _inner():
        greenado.gyield(callback())
        assert False
    
    @greenado.groutine
    def _main():
        _inner()
        assert False

    with pytest.raises(DummyException):
        IOLoop.current().run_sync(_main)
    
    
def test_groutine_error3():
    '''Ensure errors in groutines are propagated to the caller'''
    
    @gen.coroutine
    def callback():
        raise DummyException()

    def _inner():
        try:
            greenado.gyield(callback())
        except DummyException:
            return 1234
        else:
            assert False
    
    @greenado.groutine
    def _main():
        return _inner()

    main_result = IOLoop.current().run_sync(_main)
    assert main_result == 1234
    
    