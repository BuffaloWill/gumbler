#!/usr/bin/python

import argparse
import os
import sys
import requests
import string 
import json
import re
import fnmatch
import glob
from pymongo import MongoClient
from webserver import server
from git import *
from datetime import datetime
from bson import Binary, Code
from bson.json_util import dumps

parser = argparse.ArgumentParser()
parser.add_argument('-r','--repo', help='Repo to check', default="", required=False)
parser.add_argument('-p','--project', help='Remote project to check', default="", required=False)
parser.add_argument('-s','--store', help='Where to store project, defaults to /tmp IMPLEMENT', default="", required=False)
parser.add_argument('-g','--gitignore', help='Gitignore file', default="", required=False)
parser.add_argument('-b','--branch', help='git branch', default="", required=False)
parser.add_argument('-a','--all', help='iterate all branches', action='store_true', required=False)
parser.add_argument('-j','--json', help='import json file into mongo', default="", required=False)
parser.add_argument('-x','--server', help='Directory to server content from', default="NULL", required=False)
parser.add_argument('-l','--listen', help='Address to bind server to', default="127.0.0.1", required=False)
parser.add_argument('-o','--output', help='By default output is json. Other options: html,server', default="json", required=False)
parser.add_argument('-m','--mongo', help='Mongodb host IP server', default="127.0.0.1", required=False)
parser.add_argument('-d','--dir', help='Directory containing checks', default="", required=False)

args = parser.parse_args()

# initialize variables
hits = {}
#no_fly = ["*.a","*.o","*.so","*.arc","*.dylib*","*.out","*.class"]
#no_fly = ["pom.xml","Gemfile","Gemfile.lock","gradle-wrapper.jar"]

# no_fly is a list of files that you might want to avoid viewing due to the high hit rate, e.g. Gemfile
no_fly = []
result = {}

# initialize mongodb
client = MongoClient('mongodb://'+args.mongo+':27017/gumbler')
db = client.gumbler

# these are common checks to look for in input
def load_checks():

	if args.dir:
		ws_dir = os.path.join(args.dir+"/webserver/checks/")
	else:
		ws_dir = os.path.join(os.getcwd()+"/webserver/checks/")

	for filename in os.listdir(ws_dir):
		data = json.load(open(ws_dir+filename))
		data["filename"] = filename

		# load the check, must be unique by name
		if db.checks.find_one({"name":data["name"]}) == None:
			db.checks.insert_one(json.loads(dumps(data)))

if args.output == "server":
	server.dira = args.server
	if args.mongo:
		server.mongo = args.mongo
	else:
		server.mongo = "localhost"
	load_checks()
	print("|+| Using db, "+'mongodb://'+server.mongo+':27017/gumbler')
	server.db = db
	server.app.run(host=args.listen)
	sys.exit()


def add_to_commits(commit, file):
	if commit in hits:
		if not file in hits[commit]:
			hits[commit].append(file)
	else:
		hits[commit] = [file]

# Iterate each file in target list against commits
def compare_target_list(target_list, file, commit):
	for target in target_list:
		if ("*" in target) and not (target in no_fly):
			try:
				regex = re.compile(fnmatch.translate(target))
				if regex.search(file):
					add_to_commits(str(commit), file+"_NO_DOWNLOAD")
			except Exception as e:
				"ignore error"
		if target in file:
			add_to_commits(str(commit), file)

# Alternative way to iterate commits, not used right now
def iterate_commits(commits):
	for commit in commits:
		diff_files = []
		for parent in commit.parents:
			for x in commit.diff(parent):
				compare_target_list(ignores,x.b_path,commit)


# Take in a list of commits for a branch and check for target files
def iterate_commits_ba(commits):
	for commit in commits:
		files =  commit.stats.files
		for path,value in files.items():
			compare_target_list(ignores,path,commit)

def clean(branch):
	if branch[0] == "*":
		return branch.split(" ")[1]
	else:
		return branch.split(" ")[2]

# read in the list of common files
def checks():
	with open("files_to_look_for.txt") as f:
   		extras = f.read().splitlines()
	return extras

# get the remote origin project url from the configuration
def get_project_url(project):
	try:
		return Repo(project).config_reader().get_value("remote \"origin\"","url")
	except Exception as e:
		return "Could not find a project URL"

# Save the project into a collection called projects
def save_project_db(project):
	if db.projects.find_one({"name":str(project)}) == None:
		# insert the project into database	
		pr = '{ "project":"'+str(project)+'","count":0}'
		db.projects.insert_one(json.loads(pr))

# gets the file contents given a commit hash and filename
def get_file_contents(key,val):
	try:
		return Repo(args.repo).git.show(key+":"+val)
	except Exception as e:
		return "|!| Error pulling file, used command 'git show "+key+":"+val+"'"

# create the json file from the results
def create_output():
	results = []
	for key,value in hits.iteritems():
		result = {}
		
		result["commit"] = str(key)
		for val in value:
			if not ("NO_DOWNLOAD" in val):
				result["date"] = str(datetime.now())				
				if "LOCAL_" in args.project:
					result["project"] = args.repo
					result["project_url"] = get_project_url(args.repo)
					result["cmd"] = "git show "+key+":"+val
					result["file"] = val
					result["results"] = get_file_contents(key,val)
				else:
					result["project"] = args.project
					result["project_url"] = get_project_url(args.repo)					
					url = "https://raw.githubusercontent.com/"+args.project+"/"+key+"/"+val
					result["url"] = url
					result["file"] = val
					result["results"] = get_file_contents(key,val)
			else:
				if "LOCAL_" in args.project:
					result["project"] = args.repo
					result["project_url"] = get_project_url(args.repo)
					result["cmd"] = "git show "+key+":"+string.replace(val,"_NO_DOWNLOAD","")
					result["file"] = string.replace(val,"_NO_DOWNLOAD","")
					result["results"] = "NOT RETRIEVED, LIKELY BINARY CONTENT"
				else:
					result["project"] = args.project
					result["project_url"] = get_project_url(args.repo)					
					url = "https://raw.githubusercontent.com/"+args.project+"/"+key+"/"+val.split("_NO_DOWNLOAD")[0]
					result["url"] = url
					result["results"] = "NOT DOWNLOADED, LIKELY BINARY CONTENT"
		# insert the finding into an array to return a json file		
		results.append(result)

		# check existing values in the database to make sure we don't duplicate
		#   commit and filename together are unique		
		if db.findings.find_one({"commit":str(key),"file":val}) == None:
			# insert the finding into database	
			db.findings.insert_one(json.loads(dumps(result)))
		else:
			print("|+| Finding not unique, not adding to the database "+str(key)+":"+val)
	
	with open("./output/"+string.replace(args.project,"/","_")+".json", 'w') as the_file:
		the_file.write(json.dumps(results))
	
	save_project_db(args.repo)
	
	print("|+| Updated MongoDB")
	print("|+| Wrote output to "+"./output/"+string.replace(args.project,"/","_")+".json")


# check if the file contains non-ascii chars, if so don't present in the server
def is_ascii(s):
    return all(ord(c) < 128 for c in s)

# convert the json file to html output, kind of ugly
def json_to_html(datas,name):
	with open(name+".html", 'w') as the_file:
		myfile = open("./output/template.html","r")
		lines = myfile.read()
		the_file.write(lines)
		for data in datas:
			if len(data) > 0:
				data["project"] = "UNKNOWN PROJECT"
				the_file.write("<h2>Project:"+data["project"]+"</h2><br>")

				if data["results"] == "NOT DOWNLOADED":
					the_file.write("<h3>Commit:"+data["commit"]+"</h3><br>")
					the_file.write("Not downloaded: <a href=\""+data["url"]+"\">"+data["url"]+"</a><br>")
				else:
					the_file.write("<h3>Commit:"+data["commit"]+"</h3><br>")
					the_file.write("<a href=\""+data["url"]+"\">"+data["url"]+"</a><br><br>")

					if is_ascii(data["results"]):
						the_file.write("<pre><code>"+data["results"].replace("<","&lt;").replace(">","&gt;")+"</code></pre>")
					else:
						the_file.write("<pre><code>BINARY IN FILE, DOWNLOAD RAW</code></pre>")						
		the_file.write("</html>")

def temp_print():
	for key,value in hits.iteritems():
		# open the output file
		print("|+| Commit:"+str(key))
		for val in value:
			print "|+| File:"+val

def load_json(json_data):	
	for finding in json_data:
		# check existing values in the database to make sure we don't duplicate
		#   commit and filename together are unique		
		if db.findings.find_one({"commit":finding["commit"],"file":finding["file"]}) == None:
			print "|+| Inserting finding with commit:"+finding["commit"]+" file:"+finding["file"]
			# insert the finding into database	
			db.findings.insert_one(finding)
		else:
			print "|-| Duplicate finding with commit:"+finding["commit"]+" file:"+finding["file"]

# print usage info
def usage():
	parser.print_help()	

if args.json:
	if os.path.isdir(args.json):
		# process the entire directory
		for f in glob.glob(args.json+"/*.json"):
			print "|+| Importing "+f
			load_json(json.load(open(f)))
	else:		
		findings = json.load(open(args.json))
	sys.exit(0)

if args.repo == "":
	print("|!| No repository given")
	usage()
	sys.exit(0)

if args.project == "":
	args.project = "LOCAL_"+args.repo

try:
    repo = Repo(args.repo)
except Exception as e: 
	print(e)
	sys.exit("no such repo")

if (len(args.gitignore) == 0):
	gi = args.repo+"/.gitignore"
else:
	gi = args.gitignore

ignores = []

# check if gitignore exists
if (os.path.isfile(gi) == False):
	print "|!| Could not find gitignore; "+str(args.repo)+"/.gitignore"
	#sys.exit()
else:
	lines = [line.rstrip('\n') for line in open(gi)]
	i = 0

	for line in lines:
		if (len(line) > 0) and (line[0] != "#"):
			ignores.append(line)

ignores = ignores + checks()

try:
	br = ""
	if(args.branch):
		commits = list(repo.iter_commits(str(args.branch)))
		print "|+| Iterating "+str(args.branch)+"   total commits:"+str(len(commits))
		iterate_commits_ba(commits)
		print ""
	elif(args.all):
		git = repo.git
		branches = git.branch("-a").split("\n")
		print "|+| Total branches: "+str(len(branches))
		for branch in branches:
			br = clean(branch)
			commits = list(repo.iter_commits(str(br)))
			print "|+| Iterating "+str(br)+"   total commits:"+str(len(commits))
			iterate_commits_ba(commits)
	else:
		x = repo.active_branch
		commits = list(repo.iter_commits(str(x)))
		print "|+| Iterating "+str(x)+"   total commits:"+str(len(commits))
		iterate_commits_ba(commits)
		print ""

except Exception,e: 
	print str(e)
	sys.exit("no such branch")

create_output()

if args.output == "html":
	file = "./output/"+string.replace(args.project,"/","_")+".json"	
	datas = json.load(open(file))
	print "|+| Writing output to "+file+".html"
	json_to_html(datas,string.replace(args.project,"/","_")+".json")

