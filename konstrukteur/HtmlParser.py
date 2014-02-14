#
# Konstrukteur - Static website generator
# Copyright 2013 Sebastian Fastner
#

__all__ = ["parse"]

from jasy.env.State import session
from jasy.core import Console
from bs4 import BeautifulSoup


def parse(filename):
	""" HTML parser class for Konstrukteur """
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