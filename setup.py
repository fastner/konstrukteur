#!/usr/bin/env python3

#
# Konstrukteur - Static website generator
# Copyright 2013 Sebastian Fastner
#

import sys

if sys.version < "3.2":
	print("Konstrukteur requires Python 3.2 or higher")
	sys.exit(1)

# Prefer setuptools (aka distribute) over distutils 
# - Distutils comes with Python3 but is not capable of installing requires, extras, etc.
# - Distribute is a fork of the Setuptools project (http://packages.python.org/distribute/)
try:
	from setuptools import setup
	uses = "distribute"
except ImportError:
	print("Konstrukteur prefers distribute over distutils for installing dependencies!")
	from distutils.core import setup
	uses = "distutils"



if uses == "distribute":

	extra = {

		#"test_suite" : "jasy.test",

		"install_requires" : [ 
			"jasy==1.5-beta4",
			"pystache>=0.5.3", 
			"beautifulsoup4>=4.3.2",

			# Requirements of watchdog lib
			"pathtools>=0.1.1",
			"PyYAML>=3.09",
			"argh>=0.8.1"
		],

#		"extras_require" : {
#			"jsdoc" : ["misaka"],
#			"daemon" : ["watchdog"],
#			"sprites" : ["Pillow"],
#			"doc" : ["sphinx"]
#		}

	}

else:

	extra = {}



# Integrate batch script for win32 only
extra["scripts"] = [ "bin/konstrukteur" ]
if sys.platform == "win32":
	extra["scripts"] += [ "bin/konstrukteur.bat" ]

# Import konstrukteur for version info etc.
import konstrukteur

# Run setup
setup(
	name = 'konstrukteur',
	version = konstrukteur.__version__,

	author = 'Sebastian Software',
	author_email = 'team@sebastian-software.de',

	maintainer = 'Sebastian Software',
	maintainer_email = 'team@sebastian-software.de',

	url = 'http://github.com/fastner/konstrukteur',
	download_url = "http://pypi.python.org/packages/source/k/konstrukteur/konstrukteur-%s.zip" % konstrukteur.__version__,

	license = "MIT",
	platforms = 'any',

	description = "Static website generator",
	long_description = """Konstrukteur is a static website generator based upon jasy.""",

	# Via: http://pypi.python.org/pypi?%3Aaction=list_classifiers
	classifiers = [

		'Development Status :: 4 - Beta',
		'Environment :: Console',
		'Intended Audience :: Developers',
		'License :: OSI Approved :: MIT License',
		'License :: Freely Distributable',
		'Operating System :: OS Independent',
		'Programming Language :: Python',
		'Programming Language :: Python :: 3',
		'Programming Language :: Python :: 3.2',
		'Programming Language :: Python :: 3.3',
		'Topic :: Software Development :: Code Generators',
		'Topic :: Software Development :: Internationalization',
		"Topic :: Internet :: WWW/HTTP"

	],

	packages = [
		"konstrukteur",
		"konstrukteurlibs/watchdog/src/watchdog",
		"konstrukteurlibs/watchdog/src/watchdog/utils",
		"konstrukteurlibs/watchdog/src/watchdog/observers",
	],

	data_files = [
		("konstrukteur", [
				"LICENSE.md",
				"README.md"
			]
		)
	],

	**extra
)