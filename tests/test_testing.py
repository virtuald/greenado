
import greenado

from greenado.testing import gen_test
from tornado.testing import AsyncTestCase

from tornado import gen

@gen.coroutine
def coroutine():
    raise gen.Return(1234)


class GreenadoTests(AsyncTestCase):
    
    @gen_test
    def test_without_timeout1(self):
        assert greenado.gyield(coroutine()) == 1234
        
    @gen_test
    @greenado.generator
    def test_without_timeout2(self):
        assert (yield coroutine()) == 1234
    
    @gen_test(timeout=5)
    def test_with_timeout1(self):
        assert greenado.gyield(coroutine()) == 1234
        
    @gen_test(timeout=5)
    @greenado.generator
    def test_with_timeout2(self):
        assert (yield coroutine()) == 1234
    
