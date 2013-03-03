ECLiPSe-wrapper
===============

A wrapper that enables readline-like user input editing on the 
[ECLiPSe](http://eclipseclp.org/) constraint-solving framework. 

Setup
-----

Install pexpect from here: http://www.noah.org/wiki/Pexpect

`$ wget http://pexpect.sourceforge.net/pexpect-2.3.tar.gz`  
`$ tar xzf pexpect-2.3.tar.gz`  
`$ cd pexpect-2.3`  
`$ sudo python ./setup.py install`  

Install curses:

`$ sudo apt-get install libncurses5-dev`  

Then use it by:
`$ ./eclwrapper.py <eclipse_exe> <additional arguments> ...`
