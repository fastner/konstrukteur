#
# Konstrukteur - Static Site Generator
# Copyright 2013-2014 Sebastian Fastner
# Copyright 2014 Sebastian Werner
#

__all__ = ["beautify"]

import re
import bs4

# Allow custom indenting for BS4
# Via: http://stackoverflow.com/questions/15509397/custom-indent-width-for-beautifulsoup-prettify
orig_prettify = bs4.BeautifulSoup.prettify
r = re.compile(r'^(\s*)', re.MULTILINE)
def prettify(self, encoding=None, formatter="minimal", indent_width=2):
	return r.sub(r'\1' * indent_width, orig_prettify(self, encoding, formatter))
bs4.BeautifulSoup.prettify = prettify

def beautify(html):
	return BeautifulSoup(html).prettify(indent_width=2)
