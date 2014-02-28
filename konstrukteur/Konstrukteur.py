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
import konstrukteur.ContentParser
import konstrukteur.Util

import dateutil.parser
import dateutil.tz

import datetime
import time
from watchdog.observers import Observer
from watchdog.events import LoggingEventHandler
import itertools

from unidecode import unidecode

from bs4 import BeautifulSoup

COMMAND_REGEX = re.compile(r"{{@(?P<cmd>\S+?)(?:\s+?(?P<params>.+?))}}")

def build(regenerate, profile):
	""" Build static website """

	if regenerate:
		session.pause()

	app = Konstrukteur()
	app.config = session.getMain().getConfigValue("konstrukteur")

	app.sitename = session.getMain().getConfigValue("konstrukteur.site.name", "Test website")
	app.siteurl = session.getMain().getConfigValue("konstrukteur.site.url", "//localhost")
	app.articleurl = session.getMain().getConfigValue("konstrukteur.blog.articleurl", "{{current.lang}}/blog/{{current.slug}}")
	app.pageurl = session.getMain().getConfigValue("konstrukteur.pageurl", "{{current.lang}}/{{current.slug}}")
	app.feedurl = session.getMain().getConfigValue("konstrukteur.blog.feedurl", "feed.{{current.lang}}.xml")
	app.extensions = session.getMain().getConfigValue("konstrukteur.extensions", ["markdown", "html"])
	app.theme = session.getMain().getConfigValue("konstrukteur.theme", session.getMain().getName())
	app.defaultLanguage = session.getMain().getConfigValue("konstrukteur.defaultLanguage", "en")

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
	feedurl = None
	extensions = None
	theme = None
	regenerate = None
	defaultLanguage = None
	config = None

	__templates = None
	__pages = None
	__languages = None
	__articleUrl = None
	__pageUrl = None
	__feedUrl = None

	__renderer = None
	__safeRenderer = None
	__fileManager = None
	__locale = None

	def __init__(self):
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
		self.__feedUrl = pystache.parse(self.feedurl)

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


	def __fixJasyCommands(self, content):
		def commandReplacer(command):
			cmd = command.group("cmd")
			params = command.group("params").split()
			id = "jasy_command_%s" % self.__id
			
			self.__id += 1
			self.__commandReplacer.append((id, cmd, params))
		
			return "{{%s}}" % id


		return re.sub(COMMAND_REGEX, commandReplacer, content)


	def __fixName(self, name):
		s = name.split(".")
		sname = s[-1]
		sname = sname[0].upper() + sname[1:]
		return ".".join(s[:-1] + [sname])


	def __parseTemplate(self):
		""" Process all templates to support jasy commands """

		for project in session.getProjects():
			templates = project.getItems("jasy.Template")
			if templates:
				for template, content in templates.items():
					template = self.__fixName(template)
					self.__templates[template] = konstrukteur.Util.fixCoreTemplating(self.__fixJasyCommands(content.getText()))

		self.__renderer = pystache.Renderer(partials=self.__templates, escape=lambda u: u)
		self.__safeRenderer = pystache.Renderer(partials=self.__templates)


	def __parseContent(self):
		""" Parse all content files in users content directory """

		contentParser = konstrukteur.ContentParser.ContentParser(self.extensions, self.__fixJasyCommands, self.defaultLanguage)
		self.__pages = []
		self.__article = []
		self.__languages = []

		contentParser.parse(os.path.join(self.__contentPath, "pages"), self.__pages, self.__languages)
		contentParser.parse(os.path.join(self.__contentPath, "article"), self.__article, self.__languages)

		for article in self.__article:
			if not "date" in article:
				raise RuntimeError("No date metadata in article : " + article["title"])
			else:
				article["date"] = dateutil.parser.parse(article["date"]).replace(tzinfo=dateutil.tz.tzlocal())

		for language in self.__languages:
			if not language in self.__locale:
				self.__locale[language] = konstrukteur.Language.LocaleParser(language)


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



	def __refreshUrls(self, pages, currentPage, pageUrlTemplate):
		""" Refresh urls of every page relative to current active page """
		siteUrl = self.siteurl

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


	def __createPage(self, slug, title, content):
		contentParser = konstrukteur.ContentParser.ContentParser(self.extensions, self.__fixJasyCommands, self.defaultLanguage)
		return contentParser.generateFields({
			"slug": slug,
			"title": title,
			"content": content
		}, self.__languages)


	def __generateArticleIndex(self):
		indexPages = []
		itemsInIndex = self.config["blog"]["itemsInIndex"]

		if not type(self.config["blog"]["indexTitle"]) == dict:
			indexTitleLang = {}
			for language in self.__languages:
				indexTitleLang[language] = self.config["blog"]["indexTitle"]
			self.config["blog"]["indexTitle"] = indexTitleLang

		for language in self.__languages:

			indexTitle = self.config["blog"]["indexTitle"][language] if "indexTitle" in self.config["blog"] else "Index %d"
			sortedArticles = sorted([article for article in self.__article if article["lang"] == language], key=self.__articleSorter)

			pos = 0
			page = 1
			while pos < len(sortedArticles):
				self.__renderer.render(indexTitle, {
					"current" : {
						"pageno" : page,
						"lang" : language
					}
				})
				indexPage = self.__createPage("index-%d" % page, indexTitle, "")
				indexPages.append(indexPage)

				indexPage["article"] = sortedArticles[pos:itemsInIndex+pos]
				indexPage["pageno"] = page

				pos += itemsInIndex
				page += 1

		return indexPages
		


	def __outputContent(self):
		""" Output processed content to html files """

		Console.info("Generate content files")
		Console.indent()

		if self.__article:
			for article in self.__article:
				article["publish"] = article["status"] == "published"
				article["date"] = article["date"].isoformat()

		for type in ["article", "articleIndex", "page"]:
			# Articles must be generated before articleIndex
			if type == "articleIndex":
				urlGenerator = self.config["blog"]["indexurl"]
				pages = self.__generateArticleIndex()
			elif type == "page":
				urlGenerator = self.__pageUrl
				pages = self.__pages
			else:
				urlGenerator = self.__articleUrl
				pages = self.__article

			for currentPage in pages:
				self.__refreshUrls(pages, currentPage, urlGenerator)
				if type == "articleIndex":
					for cp in pages:
						self.__refreshUrls(currentPage["article"], cp, self.__articleUrl)
				renderModel = self.__generateRenderModel(pages, currentPage, type)

				processedFilename = currentPage["url"] if "url" in currentPage else self.__renderer.render(urlGenerator, renderModel)
				outputFilename = self.__profile.expandFileName(os.path.join(self.__profile.getDestinationPath(), processedFilename))
				Console.info("Writing %s" % outputFilename)

				self.__jasyCommandsHandling(renderModel, outputFilename)

				outputContent = self.__processOutputContent(renderModel, type)
				self.__fileManager.writeFile(outputFilename, self.__cleanHtml(outputContent))

		Console.outdent()
		
		if self.__article:
			Console.info("Generate feed")
			Console.indent()

			for language in self.__languages:
				sortedArticles = sorted([article for article in self.__article if article["lang"] == language], key=self.__articleSorter)

				renderModel = {
					'config' : self.config,
					'site' : {
						'name' : self.sitename,
						'url' : self.siteurl
					},
					"current" : {
						"lang" : language
					},
					"now" : datetime.datetime.now(tz=dateutil.tz.tzlocal()).replace(microsecond=0).isoformat(),
					"article" : sortedArticles[:self.config["blog"]["itemsInFeed"]]
				}
				

				feedUrl = self.__renderer.render(self.__feedUrl, renderModel)
				renderModel["feedurl"] = feedUrl

				outputContent = self.__safeRenderer.render(self.__templates["%s.Feed" % self.theme], renderModel)
				outputFilename = self.__profile.expandFileName(os.path.join(self.__profile.getDestinationPath(), feedUrl))
				self.__fileManager.writeFile(outputFilename, outputContent)

			Console.outdent()
		


	def __cleanHtml(self, content):
		return content


	def __articleSorter(self, item):
		return item["date"]


	def __generateRenderModel(self, pages, currentPage, pageType):
		res = {}
		for key in currentPage:
			res[key] = currentPage[key]

		res["type"] = pageType
		res["current"] = currentPage
		res["pages"] = self.__filterAndSortPages(pages, currentPage)
		res["config"] = dict(itertools.chain(self.config.items(), {
				"sitename" : self.sitename,
				"siteurl" : self.siteurl
			}.items()))
		res["languages"] = self.__mapLanguages(self.__languages, currentPage)

		return res



	def __processOutputContent(self, renderModel, type):
		pageName = "%(theme)s.%(type)s" % {
			"theme": self.theme,
			"type": type[0].upper() + type[1:]
		}
		layoutName = "%s.Layout" % self.theme

		if not layoutName in self.__templates:
			raise RuntimeError("Template %s not found" % layoutName)
		if not pageName in self.__templates:
			raise RuntimeError("Template %s not found" % pageName)

		renderModel["current"]["content"] = renderModel["content"] = self.__renderer.render(renderModel["content"], renderModel)
		renderModel["current"]["content"] = renderModel["content"] = self.__renderer.render(self.__templates[pageName], renderModel)
		renderModel["current"]["content"] = renderModel["content"] = self.__renderer.render(self.__templates[layoutName], renderModel)

		return self.__renderer.render(renderModel["content"], renderModel)
