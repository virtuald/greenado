#
# Copyright 2014-2016 Dustin Spicuzza
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

from functools import wraps
import sys
import types

import greenlet

from tornado import gen
from tornado.stack_context import wrap as sc_wrap, NullContext
from tornado.ioloop import IOLoop

# Tornado 5.0 compatibility
try:
    from tornado.concurrent import TracebackFuture as _Future
except ImportError:
    from tornado.concurrent import Future as _Future

try:
    from tornado.concurrent import future_set_exc_info
except ImportError:
    def future_set_exc_info(future, exc_info):
        future.set_exc_info(exc_info)

import logging
logger = logging.getLogger('greenado')

class TimeoutError(Exception):
    """Exception raised by ``gyield`` in timeout."""

def gcall(f, *args, **kwargs):
    '''
        Calls a function, makes it asynchronous, and returns the result of
        the function as a :class:`tornado.concurrent.Future`. The wrapped
        function may use :func:`gyield` to pseudo-synchronously wait for a
        future to resolve.
        
        This is the same code that :func:`@greenado.groutine <groutine>`
        uses to wrap functions.

        :param f:       Function to call
        :param args:    Function arguments
        :param kwargs:  Function keyword arguments

        :returns: :class:`tornado.concurrent.Future`

        .. warning:: You should not discard the returned Future or exceptions
                     may be silently discarded, similar to a tornado coroutine.
                     See :func:`@gen.coroutine <tornado.gen.coroutine>` for
                     details.
    '''
    
    # When this function gets updated, update groutine.wrapper also!
    
    future = _Future()

    def greenlet_base():    
        try:
            result = f(*args, **kwargs)
        except Exception:
            future_set_exc_info(future, sys.exc_info())
        else:
            future.set_result(result)
    
    gr = greenlet.greenlet(sc_wrap(greenlet_base))
    with NullContext():
        gr.switch()
    
    return future


def generator(f):
    '''
        A decorator that allows you to use the 'yield' keyword in a function,
        without requiring callers to also yield this function.
        
        The yield keyword can be used inside a decorated function on any
        function call that returns a future object, such as functions
        decorated by :func:`@gen.coroutine <tornado.gen.coroutine>`, and most
        of the tornado API as of tornado 4.0.
        
        Similar to :func:`@gen.coroutine <tornado.gen.coroutine>`, in versions
        of Python before 3.3 you must raise :class:`tornado.gen.Return` to
        return a value from this function.
        
        This function must only be used by functions that either have a
        :func:`@greenado.groutine <groutine>` decorator, or functions that
        are children of functions that have the decorator applied.
        
        .. versionadded:: 0.1.7

        .. warning:: You should not discard the returned Future or exceptions
                     may be silently discarded, similar to a tornado coroutine.
                     See :func:`@gen.coroutine <tornado.gen.coroutine>` for
                     details.
    '''
    
    # Note: this code is vaguely similar to tornado's gen.coroutine/Runner,
    #       which is licensed under the Apache 2.0 license.
    
    @wraps(f)
    def wrapper(*args, **kwargs):
    
        assert greenlet.getcurrent().parent is not None, "functions decorated with generator() can only be called from functions that have the @greenado.groutine decorator in the call stack."
        
        try:
            result = f(*args, **kwargs)
        except (gen.Return, StopIteration) as e:
            result = getattr(e, 'value', None)
        else:
            if isinstance(result, types.GeneratorType):
                try:
                    future = next(result)
                    
                    while True:       
                        try:
                            value = gyield(future)
                        except Exception:
                            result.throw(*sys.exc_info()) 
                        else:
                            future = result.send(value)
                
                except (gen.Return, StopIteration) as e:
                    return getattr(e, 'value', None)
        
        return result
        
    
    return wrapper


def gmoment():
    '''
        Similar to :func:`tornado.gen.moment`, yields the IOLoop for a single
        iteration from inside a groutine.
    '''
    
    gr = greenlet.getcurrent()
    assert gr.parent is not None, "gmoment() can only be called from functions that have the @greenado.groutine decorator in the call stack."
    
    io_loop = IOLoop.current()
    
    def _finish():
        gr.switch()

    io_loop.add_callback(_finish)

    with NullContext():
        gr.parent.switch()


def groutine(f):
    '''
        A decorator that makes a function asynchronous and returns the result
        of the function as a :class:`tornado.concurrent.Future`. The wrapped
        function may use :func:`gyield` to pseudo-synchronously wait for a
        future to resolve.  
        
        The primary advantage to using this decorator is that it allows
        *all* called functions and their children to use :func:`gyield`, and
        doesn't require the use of generators.
        
        If you are calling a groutine-wrapped function from a function with
        a :func:`@greenado.groutine <groutine>` decorator, you will need to
        use :func:`gyield` to wait for the returned future to resolve.
        
        From a caller's perspective, this decorator is functionally
        equivalent to the :func:`@gen.coroutine <tornado.gen.coroutine>`
        decorator. You should not use this decorator and the
        :func:`@gen.coroutine <tornado.gen.coroutine>` decorator on the same
        function.

        .. warning:: You should not discard the returned Future or exceptions
                     may be silently discarded, similar to a tornado coroutine.
                     See :func:`@gen.coroutine <tornado.gen.coroutine>` for
                     details.
    '''

    @wraps(f)
    def wrapper(*args, **kwargs):
        
        # When this function gets updated, update gcall also!
        
        future = _Future()

        def greenlet_base():    
            try:
                result = f(*args, **kwargs)
            except Exception:
                future_set_exc_info(future, sys.exc_info())
            else:
                future.set_result(result)
        
        gr = greenlet.greenlet(sc_wrap(greenlet_base))
        with NullContext():
            gr.switch()
        
        return future
    
    return wrapper


def gsleep(timeout):
    '''
        This will yield and allow other operations to occur in the background
        before returning.

        :param timeout: Number of seconds to wait

        .. versionadded:: 0.1.9
    '''

    gr = greenlet.getcurrent()
    assert gr.parent is not None, "gsleep() can only be called from functions that have the @greenado.groutine decorator in the call stack."
    
    if timeout <= 0:
        raise ValueError("Invalid timeout value '%s'" % timeout)

    io_loop = IOLoop.current()
    done = [False]

    def on_timeout():
        done[0] = True
        gr.switch()

    io_loop.add_timeout(io_loop.time() + timeout, on_timeout)

    with NullContext():
        while not done[0]:
            gr.parent.switch()


def gyield(future, timeout=None):
    '''
        This is functionally equivalent to the 'yield' statements used in a
        :func:`@gen.coroutine <tornado.gen.coroutine>`, but doesn't require
        turning all your functions into generators -- so you can use the
        return statement normally, and exceptions won't be accidentally
        discarded.
        
        This can be used on any function that returns a future object, such
        as functions decorated by :func:`@gen.coroutine <tornado.gen.coroutine>`,
        and most of the tornado API as of tornado 4.0.
        
        This function must only be used by functions that either have a
        :func:`@greenado.groutine <groutine>` decorator, or functions that are
        children of functions that have the decorator applied.
        
        :param future:  A :class:`tornado.concurrent.Future` object
        :param timeout: Number of seconds to wait before raising a
                        :exc:`TimeoutError`. Default is no timeout.
                        `Parameter added in version 0.1.8.`

        :returns:       The result set on the future object
        :raises:        * If an exception is set on the future, the exception
                          will be thrown to the caller of gyield.
                        * If the timeout expires, :exc:`TimeoutError` will be
                          raised.
                          
        .. versionchanged:: 0.1.8
           Added timeout parameter
           
        .. versionchanged:: 0.2.0
           If a timeout occurs, the :exc:`TimeoutError` will not be set on the
           future object, but will only be raised to the caller.
           
        .. note: This cannot be used with :func:`tornado.gen.moment`, use 
                 :func:`gmoment` instead
    '''
    
    gr = greenlet.getcurrent()
    assert gr.parent is not None, "gyield() can only be called from functions that have the @greenado.groutine decorator in the call stack."
    
    # don't switch/wait if the future is already ready to go
    if not future.done():

        io_loop = IOLoop.current()
        wait_future = future

        if timeout != None and timeout > 0:
            # optimization: only do timeout related work if a timeout is happening..

            timeout_handle = None
            timeout_future = None

            def on_complete(result):
                if timeout_future.done():
                    # resolve the future so tornado doesn't complain
                    try:
                        result.result()
                    except Exception:
                        # If you don't want to see this error, then implement cancellation
                        # in the thing that the future came from
                        logger.warn("gyield() timeout expired, and this exception was ignored",
                                    exc_info=1)
                else: 
                    timeout_future.set_result(True)
                    io_loop.remove_timeout(timeout_handle)
                gr.switch()

            def on_timeout():
                timeout_future.set_exception(TimeoutError("Timeout after %s seconds" % timeout))
                gr.switch()

            wait_future = timeout_future = _Future()
            timeout_handle = io_loop.add_timeout(
                io_loop.time() + timeout,
                on_timeout
            )

        else:
            def on_complete(result):
                gr.switch()

        io_loop.add_future(future, on_complete)
        
        with NullContext():
            gr.parent.switch()
            
            while not wait_future.done():
                gr.parent.switch()
            
        wait_future.result()
    
    return future.result()
    
