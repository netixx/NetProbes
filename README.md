NetProbes
=========

This project intends to propose a way to test your network in a distributed fashion.

It does so by establishing a network of probes running on each node you wish to test.
Once probes are up and running, it is up to you to connect the probes together and start the test.

General layout is as follows :

1. install the application on the computers/servers you wish to test
2. use the commander to command one probe with add, do and remove commands
3. launch tests an get the results !

You can write your own tests in the tests package, as long as they implement the methods defineds in (probe.)tests.Test !

Synchronisation between the probes is done via http, so be sure that this is allowed between probes. **This is required for the project to work!!**

##Notice##

Developpment is in progress and results are currently unknown!!

Implementation is based on python 3 and does not require (as of today) any external package other than the basic python installation.
