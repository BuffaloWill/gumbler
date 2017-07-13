from flask import Flask, render_template, request
import argparse
import os
import sys
from git import *
import requests
import string 
import json
from os import listdir
from os.path import isfile, join

dira = ""
json_l = []

# this loads all json files into memory, /me ducks
def load_projects():
	only = [f for f in listdir(dira) if isfile(join(dira, f))]
	for file in only:
		if "json" in file:
			x = json.load(open(dira+file))
			for q in x:
				json_l.append(json.dumps(q))
	print len(json_l)

app = Flask(__name__)
@app.route("/")
def main():
	return render_template('index.html')

# move to library
def is_ascii(s):
    return all(ord(c) < 128 for c in s)

def projects():
	projects = set()
	for datax in json_l:
		data = json.loads(datax)
		if len(data) > 0:
			projects.add(data["project"])
	return render_template('project.html',projects=projects)

def project():
	projects = []
	project = request.args.get("project")
	for datax in json_l:
		data = json.loads(datax)
		if len(data) > 0:
			if data["project"] == project:
				if data["results"] == "NOT DOWNLOADED":
					data["not_downloaded"] = True
				if is_ascii(data["results"]):
					data["is_ascii"] = True
					data["results"] = data["results"].replace("<","&lt;").replace(">","&gt;")
				projects.append(data)
	return render_template('display.html',projects=projects)

def files():
	projects = set()
	file = request.args.get("file")

	for datax in json_l:
		data = json.loads(datax)
		if len(data) > 0:
			if 'file' in data and file == data["file"]:
				projects.add(data)
	return render_template('display.html',projects=projects)

def display():
	projects = []
	fname = request.args.get("filename")
	for datax in json_l:
		data = json.loads(datax)
		if len(data) > 0:
			if 'file' in data and fname == data["file"]:
				if data["results"] == "NOT DOWNLOADED":
					data["not_downloaded"] = True
				if is_ascii(data["results"]):
					data["is_ascii"] = True
					data["results"] = data["results"].replace("<","&lt;").replace(">","&gt;")
				projects.append(data)
	return render_template('display.html',projects=projects)

# list all projects from json e.g. /list
app.add_url_rule('/list', 'index', projects)

# list all files matching name e.g. /files?file=gemfile
app.add_url_rule('/files', 'files', files)

# display a filename /display?filename=[filename]
app.add_url_rule('/display', 'display', display)

# display a project /project?project=x
app.add_url_rule('/project', 'project', project)

# index
app.add_url_rule('/index', 'main', main)


if __name__ == "__main__":
	app.run(debug=True)
