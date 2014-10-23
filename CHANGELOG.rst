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
