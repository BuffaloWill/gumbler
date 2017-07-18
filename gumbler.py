#! /usr/bin/python

import argparse
import os
import sys
from git import *
import requests
import string 
import json
from webserver import server
import re

parser = argparse.ArgumentParser()
parser.add_argument('-r','--repo', help='Repo to check', default="", required=False)
parser.add_argument('-p','--project', help='Remote project to check', default="", required=False)
parser.add_argument('-s','--store', help='Where to store project, defaults to /tmp IMPLEMENT', default="", required=False)
parser.add_argument('-g','--gitignore', help='Gitignore file', default="", required=False)
parser.add_argument('-b','--branch', help='git branch', default="", required=False)
parser.add_argument('-a','--all', help='iterate all branches', action='store_true', required=False)
parser.add_argument('-j','--json', help='convert json to html', default="", required=False)
parser.add_argument('-x','--server', help='Directory to server content from', default="NULL", required=False)
parser.add_argument('-o','--output', help='By default output is json. Other options: html,server', default="json", required=False)
args = parser.parse_args()

# initialize variables
hits = {}
#no_fly = ["*.a","*.o","*.so","*.arc","*.dylib*","*.out","*.class"]
#no_fly = ["pom.xml","Gemfile","Gemfile.lock","gradle-wrapper.jar"]

# no_fly is a list of files that you might want to avoid viewing due to the high hit rate, e.g. Gemfile
no_fly = []
result = {}

if args.output == "server":
	if args.server == "NULL":
		print "Please provide a directory containing JSON files \n \t\t python gumbler.py -o server -x ./output/"
		sys.exit()
	server.dira = args.server
	server.load_projects()
	server.app.run()
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
		# TODO: this ignores multiple *'s, e.g. /*log*/*
		if ("*" in target) and not (target in no_fly):
			try:
				regex = re.compile(target)
				if regex.search(file):
					add_to_commits(str(commit), file+"_NO_DOWNLOAD")
			except Exception as e:
				"ignore error"
		if file in target:
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

def checks():
	with open("files_to_look_for.txt") as f:
   		extras = f.read().splitlines()
	return extras

# gets the file contents given a commit hash and filename
def get_file_contents(key,val):
	try:
		return Repo(args.repo).git.show(key+":"+val)
	except Exception as e:
		return "|!| Error pulling file, used command 'git show "+key+":"+val+"'"

def create_output():
	results = []
	for key,value in hits.iteritems():
		result = {}

		# open the output file
		result["commit"] = str(key)
		for val in value:
			if not ("NO_DOWNLOAD" in val):
				if "LOCAL_" in args.project:
					result["project"] = args.repo
					result["url"] = "git show "+key+":"+val
					result["file"] = val
					result["results"] = get_file_contents(key,val)
				else:
					result["project"] = args.project
					url = "https://raw.githubusercontent.com/"+args.project+"/"+key+"/"+val
					result["url"] = url
					result["file"] = val
					result["results"] = get_file_contents(key,val)
			else:
				if "LOCAL_" in args.project:
					result["project"] = args.repo
					result["url"] = "git show "+key+":"+string.replace(val,"_NO_DOWNLOAD","")
					result["file"] = string.replace(val,"_NO_DOWNLOAD","")
					result["results"] = "NOT RETRIEVED, LIKELY BINARY CONTENT"
				else:
					result["project"] = args.project
					url = "https://raw.githubusercontent.com/"+args.project+"/"+key+"/"+val.split("_NO_DOWNLOAD")[0]
					result["url"] = url
					result["results"] = "NOT DOWNLOADED, LIKELY BINARY CONTENT"
		results.append(result)

	with open("./output/"+string.replace(args.project,"/","_")+".json", 'w') as the_file:
		the_file.write(json.dumps(results))

	print "|+| Wrote output to "+"./output/"+string.replace(args.project,"/","_")+".json"

def is_ascii(s):
    return all(ord(c) < 128 for c in s)

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
		print "|+| Commit:"+str(key)
		for val in value:
			print "|+| File:"+val

def usage():
	parser.print_help()	


if args.json:
	datas = json.load(open(args.json))
	print "|+| Writing output to "+"./output/"+args.json+".html"
	json_to_html(datas,args.json)
	sys.exit(0)

if args.repo == "":
	print "|!| Supply repo"
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
# git rev-list --all --remotes | wc -l

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

