#import os, json
#from jasy.core.Util import executeCommand
#import jasy.core.Console as Console
#import urllib.parse

# Little helper to allow python modules in current jasylibrarys path
import sys, os.path, inspect
filename = inspect.getframeinfo(inspect.currentframe()).filename
path = os.path.dirname(os.path.abspath(filename))
sys.path.append(path)

import konstrukteur.Konstrukteur

@share
def build(regenerate = False):
	""" Build static website """
	
	konstrukteur.Konstrukteur.build(regenerate)
