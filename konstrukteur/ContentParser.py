#
# Konstrukteur - Static website generator
# Copyright 2013-2014 Sebastian Fastner
# Copyright 2014 Sebastian Werner
#

import glob, os, sys, dateutil

import jasy.core.Console as Console
import jasy.core.File as File

import konstrukteur.Language
import konstrukteur.Util as Util
import konstrukteur.MarkdownParser

class ContentParser:
	""" Content parser class for Konstrukteur """

	def __init__(self, extensions, fixJasyCommands, defaultLanguage):
		self.__extensions = extensions
		self.__extensionParser = {
			"html" : konstrukteur.HtmlParser,
			"markdown" : konstrukteur.MarkdownParser,
			"md" : konstrukteur.MarkdownParser,
			"txt" : konstrukteur.MarkdownParser
		}

		self.__id = 1
		self.__commandReplacer = []
		self.__fixJasyCommands = fixJasyCommands
		self.__languages = {}
		self.__defaultLanguage = defaultLanguage


	def parse(self, path, languages):
		Console.info("Processing %s..." % path)
		Console.indent()

		collection = []
		for extension in self.__extensions:
			for filename in glob.iglob(os.path.join(path, "*.%s" % extension)):
				basename = os.path.basename(filename)
				Console.debug("Parsing %s" % basename)

				parsed = self.__parseWithSpecificParser(filename, extension)
				if not parsed:
					Console.error("Error parsing file %s" % filename)
					continue

				self.postProcess(parsed, languages)
				collection.append(parsed)

		Console.info("Registered %s files.", len(collection))
		Console.outdent()

		return collection


	def postProcess(self, parsed, languages):
		for key, value in parsed.items():
			if type(value) is str:
				parsed[key] = self.__fixJasyCommands(value)

		if "slug" in parsed:
			parsed["slug"] = Util.fixSlug(parsed["slug"])
		else:
			parsed["slug"] = Util.fixSlug(parsed["title"])

		parsed["content"] = Util.fixCoreTemplating(parsed["content"])

		if not "status" in parsed:
			parsed["status"] = "published"
		if not "pos" in parsed:
			parsed["pos"] = 0
		else:
			parsed["pos"] = int(parsed["pos"])

		if not "lang" in parsed:
			parsed["lang"] = self.__defaultLanguage

		if parsed["lang"] not in languages:
			languages.append(parsed["lang"])

		# Add modification time and short hash
		parsed["mtime"] = os.path.getmtime(filename)
		parsed["hash"] = File.sha1(filename)[0:8]

		# Parse date if available
		if "date" in parsed:
			parsed["date"] = dateutil.parser.parse(parsed["date"]).replace(tzinfo=dateutil.tz.tzlocal())

		return parsed


	def __parseWithSpecificParser(self, filename, extension):
		""" Parse single content file """

		if not extension in self.__extensionParser:
			raise RuntimeError("No parser for extension %s registered!" % extension)

		# Delegate to main parser
		return self.__extensionParser[extension].parse(filename)

