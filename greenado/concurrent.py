#
# Copyright 2014 Dustin Spicuzza
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

from functools import partial, wraps

import greenlet

from tornado import concurrent, gen
from tornado.ioloop import IOLoop


def groutine(f):
    '''
        A decorator that allows functions that are called by this function
        to use gyield to call asynchronous calls.
        
        The primary advantage to using this decorator is that it allows
        *all* called functions and their children to use gyield, and doesn't
        require the use of generators.
        
        From a caller's perspective, this decorator is functionally
        equivalent to the tornado.gen.coroutine decorator.  
    '''

    @wraps(f)
    def wrapper(*args, **kwargs):
        
        future = concurrent.Future()

        def greenlet_base():    
            try:
                future.set_result(f(*args, **kwargs))
            except Exception as e:
                future.set_exception(e)
        
        gr = greenlet.greenlet(greenlet_base)        
        gr.switch()
        
        return future
    
    return wrapper


def gyield(future):
    '''
        This is functionally equivalent to the 'yield' statements used in a
        tornado coroutine, but doesn't require turning all your functions
        into generators -- so you can use the return statement normally, and
        exceptions won't be accidentally discarded.
        
        This can be used on any function that returns a future object, such
        as functions decorated by gen.coroutine, and most of the tornado API
        as of tornado 4.0.
        
        This function must only be used by functions that either have a
        greenlet_coroutine decorator, or functions that are children of
        functions that have the decorator applied.
        
        :param future: A `tornado.concurrent.Future` object
        :returns: The result yielded from the future object
    '''
    
    gr = greenlet.getcurrent()
    assert gr.parent is not None, "gyield() can only be called from functions that have the @greenado.groutine decorator in the call stack."
    
    # don't switch/wait if the future is already ready to go
    if not future.done():
        
        def on_complete(result):
            gr.switch()
        
        IOLoop.current().add_future(future, on_complete)
        gr.parent.switch()
    
    return future.result()
    
