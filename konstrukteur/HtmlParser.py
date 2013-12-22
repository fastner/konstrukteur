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
	page["content"] = "".join([str(tag) for tag in parsedContent.find("body").contents]) 
	page["title"] = parsedContent.title.string

	for meta in parsedContent.find_all("meta"):
		page[meta["name"].lower()] = meta["contents"]

	return page