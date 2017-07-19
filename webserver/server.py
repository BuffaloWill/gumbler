from flask import Flask, render_template, request
from flask_pymongo import PyMongo
import argparse
import os
import sys
import requests
import string 
import json
import re
from os import listdir
from os.path import isfile, join
from bson import Binary, Code
from bson.json_util import dumps


dira = ""
json_l = []

app = Flask(__name__)

# initialize the db, allow user specficied later
app.config['MONGO_URI'] = 'mongodb://127.0.0.1:27017/gumbler'
mongo = PyMongo(app, config_prefix='MONGO')

@app.route("/")
def main():
	return render_template('index.html')

# move to library
def is_ascii(s):
    return all(ord(c) < 128 for c in s)

def projects():
	projects = mongo.db.findings.distinct("project")
	return render_template('project.html',projects=projects)

def project():
	proj = request.args.get("project")
	# do we need sanitization considerations?
	projects = mongo.db.findings.find({"project":proj})

	# this should be refactored 
	p = []
	for project in projects:
		if project["results"] == "NOT DOWNLOADED":
				project["not_downloaded"] = True
		if is_ascii(project["results"]):
			project["is_ascii"] = True
			project["results"] = project["results"].replace("<","&lt;").replace(">","&gt;")
		p.append(project)
	return render_template('display.html',projects=p)


def files():
	file = request.args.get("file")
	projects = mongo.db.findings.find({"file":file})

	# this should be refactored 
	p = []
	for project in projects:
		if project["results"] == "NOT DOWNLOADED":
			project["not_downloaded"] = True
		if is_ascii(project["results"]):
			project["is_ascii"] = True
			project["results"] = project["results"].replace("<","&lt;").replace(">","&gt;")
			p.append(project)
	return render_template('file_list.html',projects=p)

def check():
	txt_checks = mongo.db.checks.find()
	return render_template('checks.html', txt_checks=txt_checks)

# run a list of regexes across all loaded projects
def run_regex(regexes,matching_only):
	results = []

	for regex in regexes:
		reg = re.compile(regex)
		findings = mongo.db.findings.find({"results":reg})
		for finding in findings:
			if not ("Error pulling file" in finding["results"]):
				if finding["results"] == "NOT DOWNLOADED":
					finding["not_downloaded"] = True
				if is_ascii(finding["results"]):
					finding["is_ascii"] = True
					finding["results"] = finding["results"].replace("<","&lt;").replace(">","&gt;")

				if matching_only:
					# show only the matching text
					match = reg.search(finding["results"])
					finding["match"] = finding.group(0)
				else:
					finding["match"] = finding["results"]

				finding["regex"] = regex
				results.append(finding)
	return results

# run the check provided
def run_check():
	check = request.args.get("check")
	matching_only = request.args.get("matching_only")

	results = []

	txt_check = mongo.db.checks.find_one({"name":check})
	regexes = txt_check["check_regex"]

	results = run_regex(regexes,matching_only)
	print("|+| Hits found:"+str(len(results)))
	return render_template('check_results.html', results=results)

# list all projects from json e.g. /list
app.add_url_rule('/list', 'index', projects)

# list all files matching name e.g. /files?file=gemfile
app.add_url_rule('/files', 'files', files)

# display a project /project?project=x
app.add_url_rule('/project', 'project', project)

# index
app.add_url_rule('/index', 'main', main)

# checks
app.add_url_rule('/check', 'check', check)

# checks
app.add_url_rule('/run_check', 'run_check', run_check)

if __name__ == "__main__":
	app.run(debug=True)
