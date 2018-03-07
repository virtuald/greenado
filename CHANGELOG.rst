0.2.5 - 2018-03-06
------------------
* Fix compatibility with Tornado >= 5.0

0.2.4 - 2016-06-06
------------------
* Reorder gyield to optimize non-timeout case

0.2.3 - 2016-05-13
------------------
* tornado.gen.moment doesn't work, use gmoment instead

0.2.2 - 2016-04-20
------------------
* Retain current StackContext when using gcall or groutine

0.2.1 - 2016-04-19
------------------
* Fix :exc:`.StackContextInconsistentError` when using gyield inside of a
  :class:`tornado.stack_context.StackContext` context block

0.2.0 - 2016-04-06
------------------
* Breaking change: Changed behavior of gyield timeout to throw, instead of
  setting an exception on the yielded future

0.1.9 - 2015-08-05
------------------
* Added gsleep

0.1.8 - 2014-10-23
------------------
* Added sphinx documentation
* Added timeout parameter to :func:`.gyield` (thanks Paul Fultz)

0.1.7 - 2014-09-11
------------------
* Added :func:`greenado.concurrent.generator` decorator to allow usage of the
  yield keyword instead of gyield

0.1.6 - 2014-09-04
------------------
* Use :class:`tornado.concurrent.TracebackFuture` to show correct stack traces
  when exceptions occur
* Add CHANGELOG.md

0.1.5 - 2014-08-28
------------------
* Add a :func:`.gen_test` implementation

0.1.4 - 2014-08-28
------------------
* Fix bug with nested groutines + double yield

0.1.3 - 2014-08-28
------------------
* Add :func:`.gcall` to the API

0.1.2 - 2014-08-28
------------------
* Short-circuit futures that have already completed

0.1.1 - 2014-08-28
------------------
* Initial working version
