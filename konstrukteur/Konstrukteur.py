#
# Konstrukteur - Static website generator
# Copyright 2013 Sebastian Fastner
#

# requires pystache, beautifulsoup4, watchdog

# Little helper to allow python modules in libs path
import sys, os.path, inspect
filename = inspect.getframeinfo(inspect.currentframe()).filename
path = os.path.join(os.path.dirname(os.path.abspath(filename)), "..", "libs", "watchdog", "src")
sys.path.insert(0,path)


__all__ = ["build"]

from jasy.env.State import session
from jasy.core import Console
import konstrukteur.FileManager
import pystache
import os.path
import glob
import re
import operator
import konstrukteur.HtmlParser
import konstrukteur.Language
import konstrukteur.FileWatcher

import time
from watchdog.observers import Observer
from watchdog.events import LoggingEventHandler

def build(regenerate):
	""" Build static website """

	if regenerate:
		session.pause()

	app = Konstrukteur()
	config = session.getMain().getConfigValue("konstrukteur")

	app.sitename = session.getMain().getConfigValue("konstrukteur.site.name", "Test website")
	app.siteurl = session.getMain().getConfigValue("konstrukteur.site.url", "//localhost")
	app.articleurl = session.getMain().getConfigValue("konstrukteur.articleurl", "{{current.lang}}/blog/{{current.slug}}")
	app.pageurl = session.getMain().getConfigValue("konstrukteur.pageurl", "{{current.lang}}/{{current.slug}}")
	app.extensions = session.getMain().getConfigValue("konstrukteur.extensions", ["md", "html"])
	app.theme = session.getMain().getConfigValue("konstrukteur.theme", "testtheme")
	app.mainPath = session.getMain().getPath()

	app.regenerate = not regenerate == False

	app.build()

	if regenerate:
		session.resume()

class Konstrukteur:
	""" Core application class for Konstrukteur """

	sitename = None
	siteurl = None
	articleurl = None
	pageurl = None
	extensions = None
	theme = None
	mainPath = None
	regenerate = None

	__templates = None
	__pages = None
	__languages = None
	__extensionParser = None
	__articleUrl = None
	__pageUrl = None

	__renderer = None
	__safeRenderer = None
	__fileManager = None
	__locale = None

	def __init__(self):
		self.__extensionParser = {}
		self.__extensionParser["html"] = konstrukteur.HtmlParser

		self.__fileManager = konstrukteur.FileManager.FileManager(session)
		self.__locale = {}


	def build(self):
		""" Build static website """
		Console.header("Konstrukteur - static website generator")
		Console.indent()

		self.__themePath = os.path.join(self.mainPath, "theme", self.theme)
		self.__staticPath = os.path.join(self.mainPath, "static");
		self.__contentPath = os.path.join(self.mainPath, "content")
		
		if not os.path.exists(self.__themePath):
			raise RuntimeError("Path to theme not found : %s" % self.__themePath)
		if not os.path.exists(self.__staticPath):
			raise RuntimeError("Path to static files not found : %s" % self.__staticPath)
		if not os.path.exists(self.__contentPath):
			raise RuntimeError("Path to content not found : %s" % self.__contentPath)

		self.__articleUrl = pystache.parse(self.articleurl)
		self.__pageUrl = pystache.parse(self.pageurl)

		self.__parseTemplate()
		self.__build()

		if self.regenerate:
			fileChangeEventHandler = konstrukteur.FileWatcher.FileChangeEventHandler()
			observer = Observer()
			observer.schedule(fileChangeEventHandler, self.__contentPath, recursive=True)
			observer.start()
			try:
				Console.info("Waiting for file changes (abort with CTRL-C)")
				while True:
					time.sleep(1)
					if fileChangeEventHandler.dirty:
						fileChangeEventHandler.dirty = False
						self.__build()
			except KeyboardInterrupt:
				observer.stop()
			observer.join()

		Console.outdent()


	def __build(self):
		""" Build static website """
		self.__parseContent()
		self.__copyStaticFiles()
		self.__outputContent()

		Console.info("Done processing website")


	def __fixCoreTemplating(self, content):
		""" This fixes differences between core JS templating and standard mustache templating """

		# Replace {{=tagname}} with {{&tagname}}
		content = re.sub(r"{{=(?P<tag>.+?)}}", "{{&\g<tag>}}", content)

		# Replace {{?tagname}} with {{#tagname}}
		content = re.sub(r"{{\?(?P<tag>.+?)}}", "{{#\g<tag>}}", content)

		return content


	def __parseTemplate(self):
		""" Parse all templates in theme's template directory """
		self.__templates = {}

		templatePath = os.path.join(self.__themePath, "template")
		Console.info("Parse templates at %s" % templatePath)
		Console.indent()

		for filename in glob.iglob(os.path.join(templatePath, "*.html")):
			basename = os.path.basename(filename)
			name = basename[:basename.rindex(".")]
			Console.debug("Parsing %s as %s" % (basename, name))

			self.__templates[name] = self.__fixCoreTemplating(open(filename, "rt").read())

		self.__renderer = pystache.Renderer(partials=self.__templates, escape=lambda u: u)

		Console.info("Found and parsed %d templates" % len(self.__templates))

		Console.outdent()


	def __parseContent(self):
		""" Parse all content files in users content directory """
		self.__pages = []
		self.__languages = []

		pagesPath = os.path.join(self.__contentPath, "pages")
		Console.info("Parse content files at %s" % pagesPath)
		Console.indent()

		for extension in self.extensions:
			for filename in glob.iglob(os.path.join(pagesPath, "*.%s" % extension)):
				basename = os.path.basename(filename)
				Console.debug("Parsing %s" % basename)

				page = self.__parseContentFile(filename, extension)

				if page:
					page["content"] = self.__fixCoreTemplating(page["content"])

					if not "status" in page:
						page["status"] = "published"
					if not "pos" in page:
						page["pos"] = 0
					else:
						page["pos"] = int(page["pos"])

					self.__pages.append(page)

					if page["lang"] not in self.__languages:
						self.__locale[page["lang"]] = konstrukteur.Language.LocaleParser(page["lang"])
						self.__languages.append(page["lang"])
				else:
					Console.error("Error parsing %s" % filename)

		Console.outdent()


	def __parseContentFile(self, filename, extension):
		""" Parse single content file """
		if not extension in self.__extensionParser:
			raise RuntimeError("No content parser for extension %s registered" % extension)

		return self.__extensionParser[extension].parse(filename)


	def __copyStaticFiles(self):
		""" Copy static files to output directory """
		staticTemplatePath = os.path.join(self.__themePath, "static")
		staticContentPath = self.__staticPath
		destinationPath = os.path.join(self.mainPath, "output");

		Console.info("Copy static content")
		Console.indent()

		self.__fileManager.removeDir(destinationPath)

		Console.info("Copy from template at path %s" % staticTemplatePath)
		self.__fileManager.copyDir(staticTemplatePath, destinationPath)

		Console.info("Copy from content at path %s" % staticContentPath)
		self.__fileManager.copyDir(staticContentPath, destinationPath)

		Console.outdent()



	def __mapLanguages(self, languages, currentPage):
		""" Annotate languges list with information about current language """

		def languageMap(value):
			currentLanguage = value == currentPage["lang"]
			currentName = self.__locale[value].getName(value)
			
			if currentLanguage:
				translatedName = currentName
				relativeUrl = "."
			else:
				translatedName = self.__locale[currentPage["lang"]].getName(value)
				relativeUrl = currentPage["translations"][value]

			return {
				"code" : value,
				"current" : currentLanguage,
				"name" : currentName,
				"translatedName" : translatedName,
				"relativeUrl" : relativeUrl,
				"page" : currentPage
			}


		return list(map(languageMap, languages))



	def __refreshUrls(self, pages, currentPage):
		""" Refresh urls of every page relative to current active page """
		siteUrl = self.siteurl
		pageUrlTemplate = self.__pageUrl

		for page in pages:
			url = page["url"] if "url" in page else self.__renderer.render(pageUrlTemplate, { "current" : page })
			page["absoluteUrl"] = os.path.join(siteUrl, url)
			page["rootUrl"] = url
			page["baseUrl"] = os.path.relpath("/", os.path.dirname("/%s" % url))

		for page in pages:
			if page == currentPage:
				page["active"] = True
				page["relativeUrl"] = ""
			else:
				page["active"] = False
				page["relativeUrl"] = os.path.relpath(page["rootUrl"], os.path.dirname(currentPage["rootUrl"]))

		for page in pages:
			if page["slug"] == currentPage["slug"]:
				if not page["lang"] == currentPage["lang"]:
					if not "translations" in currentPage:
						currentPage["translations"] = {}
					currentPage["translations"][page["lang"]] = page["relativeUrl"]



	def __filterAndSortPages(self, pages, currentPage):
		""" Return sorted list of only pages of same language and not hidden """
		pageList = []

		for page in pages:
			if page["lang"] == currentPage["lang"] and not page["status"] == "hidden":
				pageList.append(page)

		return sorted(pageList, key=lambda page: page["pos"])



	def __outputContent(self):
		""" Output processed content to html files """

		Console.info("Generate content files")
		Console.indent()

		for currentPage in self.__pages:
			self.__refreshUrls(self.__pages, currentPage);

			renderModel = {
				'current' : currentPage,
				'content' : currentPage["content"],
				'pages' : self.__filterAndSortPages(self.__pages, currentPage),
				'config' : {
					'sitename' : self.sitename,
					'siteurl' : self.siteurl
				},
				'languages' : self.__mapLanguages(self.__languages, currentPage)
			}

			processedFilename = currentPage["url"] if "url" in currentPage else self.__renderer.render(self.__pageUrl, renderModel)
			outputFilename = os.path.join(self.mainPath, "output", processedFilename)
			Console.info("Writing %s" % outputFilename)

			renderModel["current"]["content"] = renderModel["content"] = self.__renderer.render(self.__templates["page"], renderModel)
			content = self.__renderer.render(self.__templates["layout"], renderModel)
			self.__fileManager.writeFile(outputFilename, content)

		Console.outdent()
