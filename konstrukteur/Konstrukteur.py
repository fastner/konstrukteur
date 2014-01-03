#
# Konstrukteur - Static website generator
# Copyright 2013 Sebastian Fastner
#

# requires pystache, beautifulsoup4, watchdog

# Little helper to allow python modules in libs path
import sys, os.path, inspect
filename = inspect.getframeinfo(inspect.currentframe()).filename
path = os.path.join(os.path.dirname(os.path.abspath(filename)), "..", "konstrukteurlibs", "watchdog", "src")
sys.path.insert(0,path)


__all__ = ["build"]

from jasy.env.State import session
from jasy.core import Console
from jasy.core import FileManager
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

COMMAND_REGEX = re.compile(r"{{@(?P<cmd>\S+?)(?:\s+?(?P<params>.+?))}}")

def build(regenerate, profile):
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
	app.theme = session.getMain().getConfigValue("konstrukteur.theme", None)

	app.regenerate = not regenerate == False

	app.build(profile)

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

		self.__locale = {}
		self.__commandReplacer = []
		self.__id = 0
		self.__templates = {}


	def build(self, profile):
		""" Build static website """
		Console.header("Konstrukteur - static website generator")
		Console.indent()

		self.__templatePath = os.path.join(session.getMain().getPath(), "source", "template") #, self.theme)
		self.__contentPath = os.path.join(session.getMain().getPath(), "source", "content")
		self.__sourcePath = os.path.join(session.getMain().getPath(), "source")

		self.__profile = profile
		self.__fileManager = FileManager.FileManager(profile)
		
		if not os.path.exists(self.__templatePath):
			raise RuntimeError("Path to theme not found : %s" % self.__templatePath)
		if not os.path.exists(self.__contentPath):
			raise RuntimeError("Path to content not found : %s" % self.__contentPath)

		if self.theme:
			theme = session.getProjectByName(self.theme)
			if not theme:
				raise RuntimeError("Theme '%s' not found" % self.theme)

		self.__articleUrl = pystache.parse(self.articleurl)
		self.__pageUrl = pystache.parse(self.pageurl)

		self.__parseTemplate()
		self.__build()

		if self.regenerate:
			fileChangeEventHandler = konstrukteur.FileWatcher.FileChangeEventHandler()
			observer = Observer()
			observer.schedule(fileChangeEventHandler, self.__sourcePath, recursive=True)
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
		self.__outputContent()

		Console.info("Done processing website")


	def __fixCoreTemplating(self, content):
		""" This fixes differences between core JS templating and standard mustache templating """

		# Replace {{=tagname}} with {{&tagname}}
		content = re.sub(r"{{=(?P<tag>.+?)}}", "{{&\g<tag>}}", content)

		# Replace {{?tagname}} with {{#tagname}}
		content = re.sub(r"{{\?(?P<tag>.+?)}}", "{{#\g<tag>}}", content)

		return content


	def __fixJasyCommands(self, content):
		def commandReplacer(command):
			cmd = command.group("cmd")
			params = command.group("params").split()
			id = "jasy_command_%s" % self.__id
			
			self.__id += 1
			self.__commandReplacer.append((id, cmd, params))
		
			return "{{%s}}" % id


		return re.sub(COMMAND_REGEX, commandReplacer, content)


	def __parseTemplate(self):
		""" Parse all templates in theme's template directory """

		mainProject = session.getMain()

		for project in session.getProjects():
			projectId = project.getName()

			templatePath = os.path.join(project.getPath(), "source", "template")

			Console.info("Parse templates at %s" % templatePath)
			Console.indent()

			for filename in glob.iglob(os.path.join(templatePath, "*.html")):
				basename = os.path.basename(filename)
				name = basename[:basename.rindex(".")]
				Console.debug("Parsing %s as %s" % (basename, name))

				template = self.__fixCoreTemplating(self.__fixJasyCommands(open(filename, "rt").read()))

				if mainProject == project:
					self.__templates[name] = template
					
				self.__templates["%s.%s" % (projectId, name[0].upper()+name[1:])] = template

			self.__renderer = pystache.Renderer(partials=self.__templates, escape=lambda u: u)

			Console.outdent()

		Console.indent()
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
					for key, value in page.items():
						page[key] = self.__fixJasyCommands(value)

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


	def __mapLanguages(self, languages, currentPage):
		""" Annotate languges list with information about current language """

		def languageMap(value):
			currentLanguage = value == currentPage["lang"]
			currentName = self.__locale[value].getName(value)
			
			if "translations" not in currentPage:
				return None

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



	def __jasyCommandsHandling(self, renderModel, filename):
		oldWorkingPath = self.__profile.getWorkingPath()
		self.__profile.setWorkingPath(os.path.dirname(filename))

		for id, cmd, params in self.__commandReplacer:
			result, type = self.__profile.executeCommand(cmd, params)
			renderModel[id] = result

		self.__profile.setWorkingPath(oldWorkingPath)



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
			outputFilename = self.__profile.expandFileName(os.path.join(self.__profile.getDestinationPath(), processedFilename))
			Console.info("Writing %s" % outputFilename)

			self.__jasyCommandsHandling(renderModel, outputFilename)

			if self.theme:
				pageName = "%s.page" % self.theme
				layoutName = "%s.layout" % self.theme
			else:
				pageName = "page"
				layoutName = "layout"

			renderModel["current"]["content"] = renderModel["content"] = self.__renderer.render(renderModel["content"], renderModel)
			renderModel["current"]["content"] = renderModel["content"] = self.__renderer.render(self.__templates[pageName], renderModel)
			renderModel["current"]["content"] = renderModel["content"] = self.__renderer.render(self.__templates[layoutName], renderModel)
			self.__fileManager.writeFile(outputFilename, self.__renderer.render(renderModel["content"], renderModel))

		Console.outdent()
