#
# Konstrukteur - Static website generator
# Copyright 2013 Sebastian Fastner
#

"""
**Konstrukteur - Static website generator**

Konstrukteur is a website generator that uses a template and content files
to create static website output.
"""

__version__ = "0.1.10"
__author__ = "Sebastian Fastner <mail@sebastianfastner.de>"

def info():
    """
    Prints information about Jasy to the console.
    """

    import jasy.core.Console as Console

    print("Jasy %s is a powerful web tooling framework" % __version__)
    print("Visit %s for details." % Console.colorize("https://github.com/sebastian-software/jasy", "underline"))
    print()


class UserError(Exception):
    """
    Standard Jasy error class raised whenever something happens which the system understands (somehow excepected)
    """
    pass
