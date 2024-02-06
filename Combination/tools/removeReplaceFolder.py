import os, sys
from glob import glob
import time 

printonly = False

indoc = sys.argv[1]
tempdir = str(time.time())
command1 = 'mv '+indoc + ' '+tempdir
print ('doing command')
print (command1)
if not printonly: os.system(command1)

command3 = 'mkdir '+indoc
print (command3)
if not printonly: os.system(command3)

command2 = 'rm -rf '+tempdir
print (command2)
if not printonly: os.system(command2)


