#!/usr/bin/env python
from flask_script import Manager
from flask_script import Command
import os
from service.app import app

class ListFS(Command):
	"""prints file system file names"""

	def run(self):
		for path, dirs, files in os.walk(path):
			print path
				for f in files:
					print f

class ListFS(Command):
	"""prints file system file names"""

	def run(self):
		for path, dirs, files in os.walk(path):
			print path
				for f in files:
					print f



app = Flask(__name__)
# configure your app

manager = Manager(app)

if __name__ == "__main__":
	manager.run()