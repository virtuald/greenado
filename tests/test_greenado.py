
from contextlib import contextmanager
import greenado

import pytest

from tornado import gen, concurrent, stack_context
from tornado.ioloop import IOLoop
import time


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

    @gen.coroutine
    def callback():
        raise gen.Return(1234)

    @greenado.groutine
    def _main():
        return greenado.gyield(callback()) + 1
        
    main_retval = IOLoop.current().run_sync(_main)
    assert main_retval == 1235
    
def test_gyield_retval_3():
    '''Ensure that return values are propagated to the caller via gcall'''
    
    future = concurrent.Future()

    def callback():
        future.set_result(1234)

    def _inner():
        IOLoop.current().add_callback(callback)
        
        return greenado.gyield(future) + 1

    def _main():
        return greenado.gcall(_inner)
    
    main_retval = IOLoop.current().run_sync(_main)
    assert main_retval == 1235


def test_generator_retval_1():
    '''Ensure that return values are propagated to the caller'''
    
    future = concurrent.Future()

    def callback():
        future.set_result(1234)
    
    @greenado.generator
    def _inner():
        IOLoop.current().add_callback(callback)
        
        retval = (yield future) + 1
        raise gen.Return(retval)

    @greenado.groutine
    def _main():
        return _inner() + 1
    
    main_retval = IOLoop.current().run_sync(_main)
    assert main_retval == 1236


def test_generator_retval_2():
    '''Ensure that return values are propagated to the caller'''

    @gen.coroutine
    def callback():
        raise gen.Return(1234)

    @greenado.groutine
    @greenado.generator
    def _main():
        retval = (yield callback()) + 1
        raise gen.Return(retval)
        
    main_retval = IOLoop.current().run_sync(_main)
    assert main_retval == 1235
    
def test_generator_retval_3():
    '''Ensure that return values are propagated to the caller via gcall'''
    
    future = concurrent.Future()

    def callback():
        future.set_result(1234)

    @greenado.generator
    def _inner():
        IOLoop.current().add_callback(callback)
        
        retval = (yield future) + 1
        raise gen.Return(retval)

    def _main():
        return greenado.gcall(_inner)
    
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

def test_gyield_timeout_error():
    '''Ensure that timeout throws an exception after time runs out'''
    
    future = concurrent.Future()

    def _inner():
        try:
            greenado.gyield(future, 2)
            return 0
        except greenado.TimeoutError:
            return 1

    @greenado.groutine
    def _main():
        return _inner() + 1
    
    start_time = time.time()
    main_retval = IOLoop.current().run_sync(_main)
    assert main_retval == 2
    assert time.time() > start_time + 2

    # ensures that the yielded future is still usable
    future.set_exception(ValueError("Some error"))

def test_gyield_timeout_success():
    future = concurrent.Future()

    def callback():
        future.set_result(1234)

    def _inner():
        IOLoop.current().add_callback(callback)

        return greenado.gyield(future, timeout=5) + 1

    @greenado.groutine
    def _main():
        return _inner() + 1
    
    main_retval = IOLoop.current().run_sync(_main)
    assert main_retval == 1236

def test_generator_error():
    '''Ensure errors are propagated to the yield caller'''
    
    future = concurrent.Future()

    def callback():
        future.set_exception(DummyException())

    @greenado.groutine
    @greenado.generator
    def _main():
        IOLoop.current().add_callback(callback)
        
        with pytest.raises(DummyException):
            yield future
            
        raise gen.Return(True)

    main_result = IOLoop.current().run_sync(_main)
    assert main_result == True


def test_groutine_error_1():
    '''Ensure errors in groutines are propagated to the groutine caller'''    

    @greenado.groutine
    def _main():
        raise DummyException()

    with pytest.raises(DummyException):
        IOLoop.current().run_sync(_main)
  

def test_groutine_error_2():
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
    
    
def test_groutine_error_3a():
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


def test_groutine_error_3b():
    '''Ensure errors in groutines are propagated to the caller'''
    
    @gen.coroutine
    def callback():
        raise DummyException()

    @greenado.generator
    def _inner():
        try:
            yield callback()
        except DummyException:
            raise gen.Return(1234)
        else:
            assert False
    
    @greenado.groutine
    def _main():
        return _inner()

    main_result = IOLoop.current().run_sync(_main)
    assert main_result == 1234


def test_gcall_error():
    '''Ensure errors in groutines are propagated to the groutine caller'''    

    def _inner():
        raise DummyException()
    
    def _main():
        return greenado.gcall(_inner)

    with pytest.raises(DummyException):
        IOLoop.current().run_sync(_main)
    
    
def test_nested_groutine():
    '''Ensure nested groutines work'''

    @gen.coroutine
    def callback():
        raise gen.Return(1234)

    @greenado.groutine
    def nested_groutine():
        return greenado.gyield(callback()) + 1

    @greenado.groutine
    def _main():
        return greenado.gyield(nested_groutine()) + 1
        
    main_retval = IOLoop.current().run_sync(_main)
    assert main_retval == 1236


def test_nested_groutine_with_double_gyield_1():
    '''Ensure nested groutine + 2 or more gyield works'''

    future1 = concurrent.Future()
    future2 = concurrent.Future()

    def callback1():
        future1.set_result(1234)
        
    def callback2():
        future2.set_result(4321)
        
    @greenado.groutine
    def nested_groutine():
        IOLoop.current().add_callback(callback1)
        result = greenado.gyield(future1) + 1
        
        IOLoop.current().add_callback(callback2)
        result += greenado.gyield(future2) + 1
        
        return result

    @greenado.groutine
    def _main():
        return greenado.gyield(nested_groutine()) + 1
    
    main_retval = IOLoop.current().run_sync(_main)
    assert main_retval == 5558


def test_nested_groutine_with_double_gyield_2():
    '''Ensure nested groutine + 2 or more yield works'''

    future1 = concurrent.Future()
    future2 = concurrent.Future()

    def callback1():
        future1.set_result(1234)
        
    def callback2():
        future2.set_result(4321)
        
    @greenado.groutine
    @greenado.generator
    def nested_groutine():
        IOLoop.current().add_callback(callback1)
        result = (yield future1) + 1
        
        IOLoop.current().add_callback(callback2)
        result += (yield future2) + 1
        
        raise gen.Return(result)

    @greenado.groutine
    @greenado.generator
    def _main():
        retval = (yield nested_groutine()) + 1
        raise gen.Return(retval)
    
    main_retval = IOLoop.current().run_sync(_main)
    assert main_retval == 5558


def test_generator_immediate_return_1():
    '''Immediate gen.Return'''
    
    @greenado.groutine
    @greenado.generator
    def _main():
        raise gen.Return(1234)
    
    main_retval = IOLoop.current().run_sync(_main)
    assert main_retval == 1234


def test_generator_immediate_return_2():
    '''Immediate return'''
    
    @greenado.groutine
    @greenado.generator
    def _main():
        return 1234
    
    main_retval = IOLoop.current().run_sync(_main)
    assert main_retval == 1234


def test_generator_delayed_error():
    '''Errors that occur after a yield statement'''
    
    future = concurrent.Future()

    def callback():
        future.set_result(1234)

    @greenado.generator
    def _inner():
        IOLoop.current().add_callback(callback)
        yield future
        raise DummyException()
        
    @greenado.groutine
    def _main():
        with pytest.raises(DummyException):
            _inner()
            
        return True
    
    main_retval = IOLoop.current().run_sync(_main)
    assert main_retval == True

def test_gmoment():
    
    state = [0]
    
    @greenado.groutine
    def _moment():
        state[0] += 1
        greenado.gmoment()
        state[0] += 1
        return True

    @greenado.groutine
    def _main():
        assert state[0] == 0
        state[0] += 1
        r = _moment()
        assert state[0] == 2
        greenado.gyield(r)
        assert state[0] == 3
        return True

    main_retval = IOLoop.current().run_sync(_main)
    assert main_retval == True

def test_gsleep_1():
    
    @greenado.groutine
    def _main():
        with pytest.raises(ValueError):
            greenado.gsleep(-1)
            
        return True
    
    main_retval = IOLoop.current().run_sync(_main)
    assert main_retval == True


def test_gsleep_2():
    
    @greenado.groutine
    def _main():
        now = time.time()
        greenado.gsleep(.5)
        assert time.time() > now + .5
            
        return True
    
    main_retval = IOLoop.current().run_sync(_main)
    assert main_retval == True

@contextmanager
def _mgr():
    yield

def test_stack_context_gcall():

    def _fn():
        greenado.gsleep(0.1)
        return True

    @greenado.groutine
    def _main():
        with stack_context.StackContext(_mgr):
            greenado.gyield(greenado.gcall(_fn))
        return True

    main_retval = IOLoop.current().run_sync(_main)
    assert main_retval == True

def test_stack_context_groutine():

    @greenado.groutine
    def _fn():
        greenado.gsleep(0.1)
        return True

    @greenado.groutine
    def _main():
        with stack_context.StackContext(_mgr):
            greenado.gyield(_fn())
        return True

    main_retval = IOLoop.current().run_sync(_main)
    assert main_retval == True


def test_stack_context_gsleep():

    @greenado.groutine
    def _main():
        with stack_context.StackContext(_mgr):
            greenado.gsleep(0.1)
        return True

    main_retval = IOLoop.current().run_sync(_main)
    assert main_retval == True


def test_stack_context_gyield_1():
    @greenado.groutine
    def _main():
        f = gen.Future()

        def _doit():
            f.set_result(True)

        with stack_context.NullContext():
            IOLoop.current().add_callback(_doit)

        with stack_context.StackContext(_mgr):
            return greenado.gyield(f)

    main_retval = IOLoop.current().run_sync(_main)
    assert main_retval == True




def _current_stackcontext():
    return stack_context._state.contexts[1]

def test_sc_correctness_groutine1():

    @greenado.groutine
    def _gthing(sc, fwait):

        assert _current_stackcontext() is sc
        greenado.gyield(fwait)
        assert _current_stackcontext() is sc

        return True

    def _main():
        fwait = gen.Future()
        sc = stack_context.StackContext(_mgr)
        
        assert _current_stackcontext() is None

        with sc:
            assert _current_stackcontext() is sc
            f = _gthing(sc, fwait)
            assert _current_stackcontext() is sc
            fwait.set_result(True)
            assert _current_stackcontext() is sc

        assert _current_stackcontext() is None

        return f

    main_retval = IOLoop.current().run_sync(_main)
    assert main_retval == True

def test_sc_correctness_groutine2():

    @greenado.groutine
    def _gthing(fwait):

        assert _current_stackcontext() is None
        sc = stack_context.StackContext(_mgr)

        with sc:
            assert _current_stackcontext() is sc
            greenado.gyield(fwait)
            assert _current_stackcontext() is sc

        return True

    def _main():
        fwait = gen.Future()

        assert _current_stackcontext() is None

        f = _gthing(fwait)
        assert _current_stackcontext() is None

        fwait.set_result(True)
        assert _current_stackcontext() is None

        return f

    main_retval = IOLoop.current().run_sync(_main)
    assert main_retval == True


def test_sc_correctness_gcall1():

    def _gthing(sc, fwait):

        assert _current_stackcontext() is sc
        greenado.gyield(fwait)
        assert _current_stackcontext() is sc

        return True

    def _main():
        fwait = gen.Future()
        sc = stack_context.StackContext(_mgr)

        assert _current_stackcontext() is None

        with sc:
            assert _current_stackcontext() is sc
            f = greenado.gcall(_gthing, sc, fwait)
            assert _current_stackcontext() is sc
            fwait.set_result(True)
            assert _current_stackcontext() is sc

        assert _current_stackcontext() is None

        return f

    main_retval = IOLoop.current().run_sync(_main)
    assert main_retval == True

def test_sc_correctness_gcall2():

    def _gthing(fwait):

        assert _current_stackcontext() is None
        sc = stack_context.StackContext(_mgr)

        with sc:
            assert _current_stackcontext() is sc
            greenado.gyield(fwait)
            assert _current_stackcontext() is sc

        return True

    def _main():
        fwait = gen.Future()

        assert _current_stackcontext() is None

        f = greenado.gcall(_gthing, fwait)
        assert _current_stackcontext() is None

        fwait.set_result(True)
        assert _current_stackcontext() is None

        return f

    main_retval = IOLoop.current().run_sync(_main)
    assert main_retval == True


