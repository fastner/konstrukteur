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
import jasy.asset.Manager


@share
def build(profile, regenerate = False):
	""" Build static website """
	
	def getPartUrl(part, type):
		folder = ""
		if type == "css":
			folder = profile.getCssFolder()
		#outputPath = folder
		outputPath = os.path.relpath("%s/%s" % (profile.getDestinationPath(), folder), profile.getWorkingPath())
		filename = profile.expandFileName("%s/%s-{{id}}.%s" % (outputPath, part, type))

		return filename

	profile.addCommand("part.url", getPartUrl, "url")

	for permutation in profile.permutate():
		konstrukteur.Konstrukteur.build(regenerate, profile)
