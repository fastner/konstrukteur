#
# Konstrukteur - Static website generator
# Copyright 2013 Sebastian Fastner
#

__all__ = ["parse"]

from jasy.env.State import session
from jasy.core import Console
from bs4 import BeautifulSoup
import misaka
import re
import urllib

jasyCommands = "%7B%7B@.*?%7D%7D"

def replaceJasyCommand(matchobj):
	cmd = urllib.parse.unquote(matchobj.group(0))
	return cmd

def parse(filename):
	""" HTML parser class for Konstrukteur """
	page = {}

	rndr = misaka.HtmlRenderer()
	md = misaka.Markdown(rndr)

	content = open(filename, "rt").read().split("\n---\n", 1)
	parsedContent = md.render(content[1])
	parsedContent = re.sub(jasyCommands, replaceJasyCommand, parsedContent)

	page["content"] = parsedContent

	body = BeautifulSoup(parsedContent)
	firstP = body.p
	if firstP:
		page["summary"] = body.p.get_text()
	else:
		page["summary"] = ""

	for line in content[0].split("\n"):
		if ":" in line:
			meta = line.split(":")
			page[meta[0].strip().lower()] = meta[1].strip()

	return page