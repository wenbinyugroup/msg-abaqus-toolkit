from __future__ import print_function
import os

print(os.getcwd())

f = open('temp.txt', 'w')
f.write(os.getcwd())