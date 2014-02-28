#
# Konstrukteur - Static website generator
# Copyright 2013 Sebastian Fastner
#

import glob, os, sys
from jasy.core import Console
import konstrukteur.Language
import konstrukteur.Util
import konstrukteur.MarkdownParser

class ContentParser:
	""" Content parser class for Konstrukteur """


	def __init__(self, extensions, fixJasyCommands, defaultLanguage):
		self.__extensions = extensions

		self.__extensionParser = {}
		self.__extensionParser["html"] = konstrukteur.HtmlParser
		self.__extensionParser["markdown"] = konstrukteur.MarkdownParser

		self.__id = 1
		self.__commandReplacer = []
		self.__fixJasyCommands = fixJasyCommands

		self.__languages = {}

		self.__defaultLanguage = defaultLanguage


	def parse(self, pagesPath, pages, languages):
		#pagesPath = os.path.join(self.__contentPath, sourcePath)
		Console.info("Parse content files at %s" % pagesPath)
		Console.indent()

		for extension in self.__extensions:
			for filename in glob.iglob(os.path.join(pagesPath, "*.%s" % extension)):
				basename = os.path.basename(filename)
				Console.debug("Parsing %s" % basename)

				page = self.__parseContentFile(filename, extension)

				if page:
					self.generateFields(page, languages)
					pages.append(page)
				else:
					Console.error("Error parsing %s" % filename)

		Console.outdent()


	def generateFields(self, page, languages):
		for key, value in page.items():
			page[key] = self.__fixJasyCommands(value)

		if "slug" in page:
			page["slug"] =konstrukteur.Util.fixSlug(page["slug"])
		else:
			page["slug"] = konstrukteur.Util.fixSlug(page["title"])

		page["content"] = konstrukteur.Util.fixCoreTemplating(page["content"])

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
			raise RuntimeError("No content parser for extension %s registered" % extension)

		return self.__extensionParser[extension].parse(filename)



