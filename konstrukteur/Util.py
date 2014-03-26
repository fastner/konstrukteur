#
# Konstrukteur - Static Site Generator
# Copyright 2013-2014 Sebastian Fastner
# Copyright 2014 Sebastian Werner
#

import re
import unidecode

def fixCoreTemplating(content):
	""" This fixes differences between Core's templating and standard Mustache templating """

	# Replace {{=tagname}} with {{&tagname}}
	content = re.sub(r"{{=(?P<tag>.+?)}}", "{{&\g<tag>}}", content)

	# Replace {{?tagname}} with {{#tagname}}
	content = re.sub(r"{{\?(?P<tag>.+?)}}", "{{#\g<tag>}}", content)

	return content


def fixSlug(slug):
	""" Replaces unicode character with something equal from ascii ( e.g. ü -> u ) """

	pattern = r'[.\s]+'
	return re.sub(pattern, "-", unidecode.unidecode(slug).lower())
