#
# Konstrukteur - Static website generator
# Copyright 2013 Sebastian Fastner
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

				parsed = self.__parseContentFile(filename, extension)
				if not parsed:
					Console.error("Error parsing %s" % filename)
					continue

				self.generateFields(parsed, languages)
				collection.append(parsed)

		Console.info("Registered %s files.", len(collection))
		Console.outdent()

		return collection


	def generateFields(self, page, languages):
		for key, value in page.items():
			if type(value) is str:
				page[key] = self.__fixJasyCommands(value)

		if "slug" in page:
			page["slug"] = Util.fixSlug(page["slug"])
		else:
			page["slug"] = Util.fixSlug(page["title"])

		page["content"] = Util.fixCoreTemplating(page["content"])

		if not "status" in page:
			page["status"] = "published"
		if not "pos" in page:
			page["pos"] = 0
		else:
			page["pos"] = int(page["pos"])

		if not "lang" in page:
			page["lang"] = self.__defaultLanguage

		if page["lang"] not in languages:
			languages.append(page["lang"])

		return page


	def __parseContentFile(self, filename, extension):
		""" Parse single content file """

		if not extension in self.__extensionParser:
			raise RuntimeError("No parser for extension %s registered!" % extension)

		# Delegate to main parser
		parsed = self.__extensionParser[extension].parse(filename)

		# Add modification time and short hash
		parsed["mtime"] = os.path.getmtime(filename)
		parsed["hash"] = File.sha1(filename)[0:8]

		# Parse date if available
		if "date" in parsed:
			parsed["date"] = dateutil.parser.parse(parsed["date"]).replace(tzinfo=dateutil.tz.tzlocal())

		# Return result
		return parsed
