# tcp_bridge.pl
a tcollector that acts as local tcp bridge for opentsdb style metrics directly fed to tcollector

I was asked to debug a tcp variant of the udp_bridge.py that is packaged with standard tcollectors.  Unable to identify the problem immediately, I wrote a clean sheet perl version to validate what should be happening.  This exercise enabled me to later correct the python version, which will hopefully be submitted upstream after some additional cleanup.

With permission of Jonathan Creasy (the original author), I am posting the fixed tcp_bridge.py.  It has also been committed to the tcollector repo, but also published here with alternate license.
