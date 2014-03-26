#
# Konstrukteur - Static Site Generator
# Copyright 2013-2014 Sebastian Fastner
# Copyright 2014 Sebastian Werner
#

"""
**Konstrukteur - Static Site Generator**

Konstrukteur is a website generator that uses a template and content files
to create static website output.
"""

__version__ = "0.1.15"
__author__ = "Sebastian Fastner <mail@sebastianfastner.de>"

def info():
    """
    Prints information about Jasy to the console.
    """

    import jasy.core.Console as Console

    print("Konstrukteur %s is a static site generator" % __version__)
    print("Visit %s for details." % Console.colorize("https://github.com/fastner/konstrukteur", "underline"))
    print()


class UserError(Exception):
    """
    Standard Konstrukteur error class raised whenever something happens which the system understands (somehow excepected)
    """
    pass
