
import functools

import greenado

from tornado.ioloop import TimeoutError
from tornado.testing import get_async_test_timeout


def gen_test(func=None, timeout=None):
    '''
        An implementation of :func:`tornado.testing.gen_test` for
        :func:`@greenado.groutine <greenado.concurrent.groutine>`
        
        Example::
        
            def something_that_yields():
                greenado.gyield(something())
        
            class MyTest(AsyncTestCase):
                @greenado.testing.gen_test
                def test_something(self):
                    something_that_yields()
    '''
    
    if func is None:
        return functools.partial(gen_test, timeout=timeout)
    
    if timeout is None:
        timeout = get_async_test_timeout()
    
    @functools.wraps(func)
    def wrapper(self, *args, **kwargs):
        return self.io_loop.run_sync(
            functools.partial(greenado.gcall, func, self, *args, **kwargs),
            timeout=timeout)
    
    return wrapper
        