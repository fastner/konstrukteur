#
# Konstrukteur - Static Site Generator
# Copyright 2013-2014 Sebastian Fastner
# Copyright 2014 Sebastian Werner
#

import watchdog.events

class FileChangeEventHandler(watchdog.events.FileSystemEventHandler):

	def __init__(self):
		self.dirty = False

	def on_any_event(self, event):
		super(FileChangeEventHandler, self).on_any_event(event)

		self.dirty = True
