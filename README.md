NetProbes : distributed troubleshooting 
=========

This project intends to propose a way to test your network in a distributed fashion. The idea is to be able to cooperate with other nodes running the NetProbes program in order to inspect the state of the network, performing a distributed network troubleshooting via active measurement.

NetProbes performs distributed troubleshooting so by establishing a overlay of probes running on each node you wish to potentially participate in the test. Once probes are up and running, upon dection of an anomaly, you can leverage the established overlay to connect the relevant probes together and start the test. 

NetProbes perform measurement that can then be clustered (in absence of topology information) or classified (in presence of topology information). Clustering allows to assess the severity of an impairment, whereas classification helps identifying the problem root cause.


##Notice##

Implementation is based on python 3 and does not require (as of today) any external package other than the basic python installation.

Development is in progress and thorough tests have been performed of the current codebase. Shall you wish to have an idea of experimental results, please refer to:

François Espinet, Diana Joumblatt and Dario Rossi, "Zen and the art of network troubleshooting: a hands on experimental study". In Traffic Monitoring and Analysis (TMA'15), Barcellona, Spain, Apr 2015. 


##Technical details##

General workflow is as follows :

1. install the application on the computers/servers you wish to test
2. use the commander to control any given probe (with add, do and remove commands)
3. launch the tests an get the results

You can write your own tests in the `(probe.)tests` package. There are two kinds of tests:

* `(probe.)interfaces.StandaloneTest` : test that do not require the cooperation of the targets of the tests (eg: ping)
* `(probe.)interfaces.ProbeTest` : test that require cooperation (eg: open TCP connection)

Those tests should respectively be placed in the `(probe.)tests.standalone` and `(probe.)tests.probes` packages. They can both use methods provided by the `(probe.)WatcherServices` and must implement the prescripted interfaces.

Communication between the probes is done via the classes in `(probe.)inout.protocol` and `(probe.)inout.codec` which are respectively in charge of sending/receiving data accross the network and translating python objects into data suitable for transmission. The both have interfaces defined in the `(probe.)interfaces.inout` package.

In the current implementation, overlay communication  is done via HTTP (as it is generally available in any network settings and it is the less blocked protocol in a world where the IP narrow waist has liftet up to HTTP).
Be sure that HTTP communication is allowed between probes -- as otherwise no test can be run!

Further information can be found under the docs/rapport/pdfs folder (french only)

