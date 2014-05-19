NetProbes : distributed troubleshooting
=========

This project intends to propose a way to test your network in a distributed fashion. The idea is to be able to cooperate with other peers running the NetProbes program in order to inspect the state of the network.

It does so by establishing a overlay of probes running on each node you wish to test.
Once probes are up and running, it is up to you to connect the probes together and start the test.

General workflow is as follows :

1. install the application on the computers/servers you wish to test
2. use the commander to command one probe with add, do and remove commands
3. launch tests an get the results !

You can write your own tests in the `(probe.)tests` package. There are two kinds of tests:

* `(probe.)interfaces.StandaloneTest` : test that do not require the cooperation of the targets of the tests (eg: ping)
* `(probe.)interfaces.ProbeTest` : test that require cooperation (eg: open TCP connection)

Those tests should respectively be placed in the `(probe.)tests.standalone` and `(probe.)tests.probes` packages. They can both use methods provided by the `(probe.)WatcherServices` and must implement the prescripted interfaces.


##Notice##

Developpment is in progress and results are currently unknown!!

Implementation is based on python 3 and does not require (as of today) any external package other than the basic python installation.


##Technical details##

Communication between the probes is done via the classes in `(probe.)inout.protocol` and `(probe.)inout.codec` which are respectively in charge of sending/receiving data accross the network and translating python objects into data suitable for transmission. The both have interfaces defined in the `(probe.)interfaces.inout` package.

In the current implementation, synchronisation between the probes is done via http (as it is the least blocked protocol), so be sure that this is allowed between probes. **This is required for the project to work!!**


