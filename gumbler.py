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
# import gumbler helpers
from lib import helper, finding

parser = argparse.ArgumentParser()
parser.add_argument('-r', '--repo', help='Repo to check', default="", required=False)
parser.add_argument('-p', '--project', help='Remote project to check', default="", required=False)
parser.add_argument('-s', '--store', help='URL of a remote project', default="", required=False)
parser.add_argument('-g', '--gitignore', help='Gitignore file', default="", required=False)
parser.add_argument('-b', '--branch', help='git branch', default="", required=False)
parser.add_argument('-a', '--all', help='iterate all branches', action='store_true', required=False)
parser.add_argument('-j', '--json', help='import json file into mongo', default="", required=False)
parser.add_argument('-x', '--server', help='Directory to server content from', default="NULL", required=False)
parser.add_argument('-l', '--listen', help='Address to bind server to', default="127.0.0.1", required=False)
parser.add_argument('-o', '--output', help='By default output is json. Other options: html,server',
                    default="json", required=False)
parser.add_argument('-m', '--mongo', help='Mongodb host IP server', default="127.0.0.1", required=False)
parser.add_argument('-d', '--dir', help='Directory containing checks', default="", required=False)
parser.add_argument('-z', '--delete', help='Recursively delete directory containing cloned project  when done*BE CAREFUL*',
                    action="store_true", required=False)
parser.add_argument('-c', '--comments', help='Search comments from a project', default="", required=False)

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

# load the webserver checks into the db


def load_checks():
    if args.dir:
        ws_dir = os.path.join(args.dir+"/webserver/checks/")
    else:
        ws_dir = os.path.join(os.getcwd()+"/webserver/checks/")

    for filename in os.listdir(ws_dir):
        data = json.load(open(ws_dir+filename))
        data["filename"] = filename

        # load the check, must be unique by name
        if db.checks.find_one({"name": data["name"]}) == None:
            db.checks.insert_one(json.loads(dumps(data)))


# if the user wants to load the webserver, start it up
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


def add_to_commits(commit, f):
    if commit in hits:
        if not file in hits[commit]:
            f.commit = commit
            hits[commit].append(f)
    else:
        f.commit = commit

        hits[commit] = [f]

# Iterate each file in target list against commits


def compare_target_list(target_list, file, commit):
    # iterate files_to_look_for.txt
    for target in helper.checks():
        if ("*" in target) and not (target in no_fly):
            try:
                regex = re.compile(fnmatch.translate(target))
                if regex.search(file):
                    f = finding.Finding()
                    f.file = file+"_NO_DOWNLOAD"
                    add_to_commits(str(commit), f)
            except Exception as e:
                "ignore error"
        if target in file:
            f = finding.Finding()
            f.file = file
            add_to_commits(str(commit), f)

    # iterate the gitignore file
    for target in target_list:
        if ("*" in target) and not (target in no_fly):
            try:
                regex = re.compile(fnmatch.translate(target))
                if regex.search(file):
                    f = finding.Finding()
                    f.is_gitignore = True
                    f.file = file+"_NO_DOWNLOAD"
                    add_to_commits(str(commit), f)
            except Exception as e:
                "ignore error"
        if target in file:
            f = finding.Finding()
            f.file = file
            f.is_gitignore = True
            add_to_commits(str(commit), f)

# Alternative way to iterate commits, not used right now


def iterate_commits(commits):
    for commit in commits:
        diff_files = []
        for parent in commit.parents:
            for x in commit.diff(parent):
                compare_target_list(ignores, x.b_path, commit)


# Take in a list of commits for a branch and check for target files
def iterate_commits_ba(commits):
    for commit in commits:
        files = commit.stats.files
        for path, value in files.items():
            compare_target_list(ignores, path, commit)

# Save the project into a collection called projects


def save_project_db(project, count):
    if db.projects.find_one({"name": str(project)}) == None:
        # insert the project into database
        pr = '{ "project":"'+str(project)+'","count":"'+str(count)+'"}'
        db.projects.insert_one(json.loads(pr))
    else:
        count = db.findings.find({"project": project}).count()
        # set the value otherwise
        db.projects.update({
            'project': project
        }, {
            '$set': {
                'count': count
            }
        })

# gets the commit data


def get_committed_date(key):
    try:
        return Repo(args.repo).commit(key).committed_date
    except Exception as e:
        return "|!| Error pulling committed date"

# gets the file contents given a commit hash and filename


def get_file_contents(key, val):
    try:
        return Repo(args.repo).git.show(key+":"+val)
    except Exception as e:
        return "|!| Error pulling file, used command 'git show "+key+":"+val+"'"


# create the json file from the results
def create_output():
    results = []
    for key, value in hits.iteritems():
        # key => commit hash
        # value => a finding

        # iterate each finding at this commit
        for val in value:
            # initialize the finding
            result = val

            if not ("NO_DOWNLOAD" in val.file):
                result.date = str(datetime.now())
                if "LOCAL_" in args.project:
                    result.project = args.repo
                    result.project_url = helper.get_project_url(args.repo)
                    result.cmd = "git show "+key+":"+val.file
                    result.file = val.file
                    result.results = get_file_contents(key, val.file)
                    result.commit_date = get_committed_date(key)
                else:
                    result.project = args.project
                    result.project_url = helper.get_project_url(args.repo)
                    url = "https://raw.githubusercontent.com/"+args.project+"/"+key+"/"+val.file
                    result.url = url
                    result.file = val.file
                    result.results = get_file_contents(key, val.file)
                    result.commit_date = get_committed_date(key)
            else:
                if "LOCAL_" in args.project:
                    result.project = args.repo
                    result.project_url = helper.get_project_url(args.repo)
                    result.cmd = "git show "+key+":"+string.replace(val.file, "_NO_DOWNLOAD", "")
                    result.file = string.replace(val.file, "_NO_DOWNLOAD", "")
                    result.results = "NOT RETRIEVED, LIKELY BINARY CONTENT"
                    result.commit_date = get_committed_date(key)
                else:
                    result.project = args.project
                    result.project_url = helper.get_project_url(args.repo)
                    url = "https://raw.githubusercontent.com/"+args.project + \
                        "/"+key+"/"+val.file.split("_NO_DOWNLOAD")[0]
                    result.url = url
                    result.results = "NOT DOWNLOADED, LIKELY BINARY CONTENT"
                    result.commit_date = get_committed_date(key)

        # insert the finding into an array to return a json file
        results.append(result.__dict__)

        # check existing values in the database to make sure we don't duplicate
        #   commit and filename together are unique
        if db.findings.find_one({"commit": str(key), "file": val.file}) == None:
            # insert the finding into database
            db.findings.insert_one(json.loads(dumps(result.__dict__)))
        else:
            print("|+| Finding not unique, not adding to the database "+str(key)+":"+val.file)

    with open("./output/"+string.replace(args.project, "/", "_")+".json", 'w') as the_file:
        the_file.write(json.dumps(results))

    save_project_db(args.repo, 0)

    print("|+| Updated MongoDB")
    print("|+| Wrote output to "+"./output/"+string.replace(args.project, "/", "_")+".json")


def load_json(json_data):
    for finding in json_data:
        # check existing values in the database to make sure we don't duplicate
        #   commit and filename together are unique
        if db.findings.find_one({"commit": finding["commit"], "file": finding["file"]}) == None:
            print("|+| Inserting finding with commit:"+finding["commit"]+" file:"+finding["file"])
            # insert the finding into database
            db.findings.insert_one(finding)
        else:
            print("|-| Duplicate finding with commit:"+finding["commit"]+" file:"+finding["file"])

# print usage info


def usage():
    parser.print_help()


# import json files into the DB
if args.json:
    if os.path.isdir(args.json):
        # process the entire directory
        for f in glob.glob(args.json+"/*.json"):
            print("|+| Importing "+f)
            load_json(json.load(open(f)))
    else:
        findings = json.load(open(args.json))
    sys.exit(0)

if args.repo == "" and args.store == "":
    print("|!| No repository given")
    usage()
    sys.exit(0)

if args.store != "":
    if args.project == "":
        print("|!| No repository given, store requires -p also")
        usage()
        sys.exit(0)
    spl = args.project.split("/")
    name = spl[-2]+"/"+spl[-1]
    # if not os.path.isdir(args.store):
    args.store = args.store + "/"+name

    print("|+| Cloning remote project "+args.project+" into "+args.store)
    Repo.clone_from(args.project, args.store)
    args.repo = args.store
    args.project = name

if args.project == "":
    args.project = "LOCAL_"+args.repo

try:
    repo = Repo(args.repo)
except Exception as e:
    print(e)
    sys.exit("no such repo")

if(args.comments != ""):
    findings = helper.search_comments(repo, args.comments)

    for finding in findings:
        finding["project"] = args.repo
        if db.findings.find_one({"commit": finding["commit"]}) == None:
            db.findings.insert_one(json.loads(dumps(finding)))

    sys.exit()

if (len(args.gitignore) == 0):
    gi = args.repo+"/.gitignore"
else:
    gi = args.gitignore

ignores = []

# check if gitignore exists
if (os.path.isfile(gi) == False):
    print("|!| Could not find gitignore; "+str(args.repo)+"/.gitignore")
    # sys.exit()
else:
    lines = [line.rstrip('\n') for line in open(gi)]
    i = 0

    for line in lines:
        if (len(line) > 0) and (line[0] != "#"):
            ignores.append(line)

try:
    br = ""
    if(args.branch):
        commits = list(repo.iter_commits(str(args.branch)))
        print("|+| Iterating "+str(args.branch)+"   total commits:"+str(len(commits)))
        iterate_commits_ba(commits)
        print("")
    elif(args.all):
        git = repo.git
        branches = git.branch("-a").split("\n")
        print("|+| Total branches: "+str(len(branches)))
        for branch in branches:
            br = helper.clean(branch)
            commits = list(repo.iter_commits(str(br)))
            print("|+| Iterating "+str(br)+"   total commits:"+str(len(commits)))
            iterate_commits_ba(commits)
    else:
        x = repo.active_branch
        commits = list(repo.iter_commits(str(x)))
        print("|+| Iterating "+str(x)+"   total commits:"+str(len(commits)))
        iterate_commits_ba(commits)
        print("")

except Exception as e:
    print(str(e))
    sys.exit("no such branch")

create_output()

# convert the json file to html
#	This is not valuable, the server should just include an export function
if args.output == "html":
    file = "./output/"+string.replace(args.project, "/", "_")+".json"
    datas = json.load(open(file))
    print("|+| Writing output to "+file+".html")
    helper.json_to_html(datas, string.replace(args.project, "/", "_")+".json")


# the user has to uncomment this code and understand what it does before using it
if args.delete:
    print("|!| You will need to uncomment this code in order to use recursive delete. ")
# if args.delete:
#	if not args.store == "":
#		from shutil import rmtree
#		print("|!| Deleting recursively "+args.store)
#		rmtree(args.store)
