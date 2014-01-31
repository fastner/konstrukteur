#
# Konstrukteur - Static website generator
# Copyright 2013 Sebastian Fastner
#

import re
import unidecode

def fixCoreTemplating(content):
	""" This fixes differences between core JS templating and standard mustache templating """

	# Replace {{=tagname}} with {{&tagname}}
	content = re.sub(r"{{=(?P<tag>.+?)}}", "{{&\g<tag>}}", content)

	# Replace {{?tagname}} with {{#tagname}}
	content = re.sub(r"{{\?(?P<tag>.+?)}}", "{{#\g<tag>}}", content)

	return content


def fixSlug(slug):
	""" Replaces unicode character with something equal from ascii ( e.g. ü -> u ) """
	
	pattern = r'[.\s]+'
	return re.sub(pattern, "-", unidecode.unidecode(slug).lower())