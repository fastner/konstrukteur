#
# Konstrukteur - Static website generator
# Copyright 2013 Sebastian Fastner
#

import watchdog.events

class FileChangeEventHandler(watchdog.events.FileSystemEventHandler):

	def __init__(self):
		self.dirty = False

	def on_any_event(self, event):
		super(FileChangeEventHandler, self).on_any_event(event)

		self.dirty = True
