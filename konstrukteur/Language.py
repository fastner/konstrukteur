#
# Konstrukteur - Static website generator
# Copyright 2013 Sebastian Fastner
#

from jasy import datadir
import jasy.core.Console as Console
import xml.etree.ElementTree
import os

__all__ = ["LocaleParser"]

CLDR_DIR = os.path.join(datadir, "cldr")

def camelCaseToUpper(input):
	if input.upper() == input:
		return input

	result = []
	for char in input:
		conv = char.upper()
		if char == conv and len(result) > 0:
			result.append("_")

		result.append(conv)

	return "".join(result)

class LocaleParser():
	"""Parses CLDR locales into JavaScript files"""

	def __init__(self, locale):
		Console.info("Parsing CLDR files for %s..." % locale)
		Console.indent()

		splits = locale.split("_")

		# Store for internal usage
		self.__locale = locale
		self.__language = splits[0]
		self.__territory = splits[1] if len(splits) > 1 else None

		# This will hold all data extracted data
		self.__data = {}

		# Add info section
		self.__data["info"] = {
			"LOCALE" : self.__locale,
			"LANGUAGE" : self.__language,
			"TERRITORY" : self.__territory
		}

		# Add keys (fallback to C-default locale)
		path = "%s.xml" % os.path.join(CLDR_DIR, "keys", self.__language)
		try:
			Console.info("Processing %s..." % os.path.relpath(path, CLDR_DIR))
			tree = xml.etree.ElementTree.parse(path)
		except IOError:
			path = "%s.xml" % os.path.join(CLDR_DIR, "keys", "C")
			Console.info("Processing %s..." % os.path.relpath(path, CLDR_DIR))
			tree = xml.etree.ElementTree.parse(path)

		self.__data["key"] = {
			"Short" : { key.get("type"): key.text for key in tree.findall("./keys/short/key") },
			"Full" : { key.get("type"): key.text for key in tree.findall("./keys/full/key") }
		}

		# Add main CLDR data: Fallback chain for locales
		main = os.path.join(CLDR_DIR, "main")
		files = []
		while True:
			filename = "%s.xml" % os.path.join(main, locale)
			if os.path.isfile(filename):
				files.append(filename)

			if "_" in locale:
				locale = locale[:locale.rindex("_")]
			else:
				break

		# Extend data with root data
		files.append(os.path.join(main, "root.xml"))

		# Finally import all these files in order
		for path in reversed(files):
			Console.info("Processing %s..." % os.path.relpath(path, CLDR_DIR))
			tree = xml.etree.ElementTree.parse(path)

			self.__addDisplayNames(tree)
			#self.__addDelimiters(tree)
			#self.__addCalendars(tree)
			#self.__addNumbers(tree)

		# Add supplemental CLDR data
		#self.__addSupplementals(self.__territory)

		Console.outdent()

	def __addDisplayNames(self, tree):
		""" Adds CLDR display names section """

		display = self.__getStore(self.__data, "display")

		for key in ["languages", "scripts", "territories", "variants", "keys", "types", "measurementSystemNames"]:
			# make it a little bit shorter, there is not really any conflict potential
			if key == "measurementSystemNames":
				store = self.__getStore(display, "Measure")
			elif key == "territories":
				store = self.__getStore(display, "Territory")
			else:
				# remove last character "s" to force singular
				store = self.__getStore(display, key[:-1])

			for element in tree.findall("./localeDisplayNames/%s/*" % key):
				if not element.get("draft"):
					field = element.get("type")
					if not field in store:
						store[camelCaseToUpper(field)] = element.text


	def __getStore(self, parent, name):
		""" Manages data fields """

		if not name in parent:
			store = {}
			parent[name] = store
		else:
			store = parent[name]

		return store


	def getName(self, identifier):
		store = self.__getStore(self.__data, "display")
		store = self.__getStore(store, "language")
		
		return store[identifier.upper()]