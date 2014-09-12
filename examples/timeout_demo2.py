#!/usr/bin/env python

'''
    This demo shows a periodic function executing while the groutine yields
    execution waiting for a 3 second timeout to occur.
    
    This is the same as timeout_demo.py, but this uses a generator and the
    yield keyword instead of gyield.
'''

from __future__ import print_function

import greenado

from tornado import concurrent, gen
from tornado.ioloop import IOLoop, PeriodicCallback

from functools import partial
from datetime import timedelta


def periodic():
    print("Periodic") 


def on_timeout(future):
    print("Timeout occurred")
    future.set_result(1234)

@greenado.generator
def call_yield(future):
    
    print("Waiting for timeout")
    
    # Only decorator required is the generator decorator
    yield future
    
    print("Wait completed.")
    
def call_call_yield(future):
    '''Note that this function doesn't require a decorator'''
    call_yield(future)

@greenado.groutine
def main(cb):
    
    future = concurrent.Future()
    
    IOLoop.current().add_timeout(timedelta(seconds=3), partial(on_timeout, future))
    
    # Tornado 4+:
    #IOLoop.current().call_later(3, on_timeout, future)
    
    call_call_yield(future)
    
    # once we're done, stop the periodic callback
    cb.stop()


if __name__ == '__main__':
    
    cb = PeriodicCallback(periodic, 500)
    cb.start()
    
    IOLoop.instance().run_sync(partial(main, cb))

    print("Done.")
