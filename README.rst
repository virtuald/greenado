greenado
========

.. image:: https://travis-ci.org/virtuald/greenado.png?branch=master
    :target: https://travis-ci.org/virtuald/greenado
    :alt: Test status

.. image:: https://coveralls.io/repos/virtuald/greenado/badge.png
    :target: https://coveralls.io/r/virtuald/greenado
    :alt: Test coverage status

.. image:: https://readthedocs.org/projects/greenado/badge/?version=latest
    :target: https://readthedocs.org/projects/greenado/?badge=latest
    :alt: Documentation

Greenado is a utility library that provides greenlet-based coroutines for
tornado. In tornado, coroutines allow you to perform asynchronous operations
without using callbacks, providing a pseudo-synchronous flow in your 
functions.

When using Tornado's :func:`@gen.coroutine <tornado.gen.coroutine>` in a
large codebase, you will notice that they tend to be 'infectious' from
the bottom up. In other words, for them to be truly useful, callers of
the coroutine should 'yield' to them, which requires them to be a
coroutine. In turn, their callers need to 'yield', and so on.

Instead, greenado coroutines infect from the top down, and only requires
the :func:`@greenado.groutine <greenado.concurrent.groutine>` decorator
*somewhere* in the call hierarchy, but it doesn't really matter where.
Once the decorator is used, you can use :func:`greenado.gyield() <greenado.concurrent.gyield>`
to pseudo-synchronously wait for asynchronous events to occur. This reduces
complexity in large codebases, as you only need to use the decorator at
the very top of your call trees, and nowhere else.

Documentation
=============

Documentation can be found at http://greenado.readthedocs.org/en/latest/

Installation & Requirements
===========================

Installation is easiest using pip:

.. code-block:: bash

    $ pip install greenado 

greenado should work using tornado 3.2, but I only actively use it in
tornado 4+

I have only tested greenado on Linux & OSX, but I imagine that it would
work correctly on platforms that tornado and greenlet support.

Example usage
=============

In the below examples, 'main_function' is your toplevel function
in the call hierarchy that needs to call things that eventually call
some asynchronous operation in tornado.

Normal tornado coroutine usage might look something like this:

.. code-block:: python

    from tornado import gen

    @gen.coroutine
    def do_long_operation():
        retval = yield long_operation()
        raise gen.Return(retval)

    @gen.coroutine
    def call_long_operation():
        retval = yield do_long_operation()
        raise gen.Return(retval)

    @gen.coroutine
    def main_function():
        retval = yield call_long_operation()

With greenado, it looks something like this instead:

.. code-block:: python

    import greenado

    def do_long_operation():
        retval = greenado.gyield(long_operation())
        return retval

    def call_long_operation():
        retval = do_long_operation()
        return retval

    @greenado.groutine
    def main_function():
        retval = call_long_operation()

Functions wrapped by :func:`@greenado.groutine <greenado.concurrent.groutine>` return a
:class:`tornado.concurrent.Future` object which you must either yield, call
result(), or use :meth:`IOLoop.add_future <tornado.ioloop.IOLoop.add_future>` on, otherwise you may risk
swallowing exceptions.

Why can't I use the yield keyword?
----------------------------------

Well, actually, if you use yet another decorator, you still can! Check out
this example:

.. code-block:: python

    import greenado

	@greenado.generator
    def do_long_operation():
        retval = yield long_operation()
        return retval

    def call_long_operation():
        retval = do_long_operation()
        return retval

    @greenado.groutine
    def main_function():
        retval = call_long_operation()

You'll note that this is very similar to the coroutines available from
tornado (and in fact, the implementation is mostly the same), but the
difference is that (once again) you don't need to do anything special
to call the do_long_operation function, other than make sure that
:func:`@greenado.groutine <greenado.concurrent.groutine>` is in the call stack somewhere.


Testing
=======

greenado.testing contains a function called gen_test which can be used 
exactly like :func:`tornado.testing.gen_test`:

.. code-block:: python

    import greenado
    
    from greenado.testing import gen_test
    from tornado.testing import AsyncTestCase
    
    def something_that_yields():
        greenado.gyield(something())
    
    class MyTest(AsyncTestCase):
        @gen_test
        def test_something(self):
            something_that_yields()


Contributing new changes
========================

1. Fork this repository
2. Create your feature branch (`git checkout -b my-new-feature`)
3. Test your changes (`tests/run_tests.sh`)
4. Commit your changes (`git commit -am 'Add some feature'`)
5. Push to the branch (`git push origin my-new-feature`)
6. Create new Pull Request

Credit
======

Greenado is similar to and inspired by https://github.com/mopub/greenlet-tornado
and https://github.com/Gawen/tornalet, but does not require that you use it from
a tornado web handler as they do.

Authors
=======

Dustin Spicuzza (dustin@virtualroadside.com)
