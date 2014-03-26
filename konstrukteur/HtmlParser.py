#
# Konstrukteur - Static Site Generator
# Copyright 2013-2014 Sebastian Fastner
# Copyright 2014 Sebastian Werner
#

__all__ = ["parse"]

from bs4 import BeautifulSoup

def parse(filename):
	""" HTML Parser class for Konstrukteur """

	page = {}

	parsedContent = BeautifulSoup(open(filename, "rt").read())

	body = parsedContent.find("body")

	page["content"] = "".join([str(tag) for tag in body.contents])
	page["title"] = parsedContent.title.string

	firstP = body.p
	if firstP:
		page["summary"] = body.p.get_text()
	else:
		page["summary"] = ""

	for meta in parsedContent.find_all("meta"):
		if not hasattr(meta, "name") or not hasattr(meta, "content"):
			raise RuntimeError("Meta elements must have attributes name and content : %s" % filename)

		page[meta["name"].lower()] = meta["content"]

	return page
