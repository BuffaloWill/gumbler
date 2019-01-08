from flask import Flask, render_template, request
from flask_paginate import Pagination, get_page_args
from pymongo import MongoClient
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
mongo = ""
db = ""
json_l = []

# keeps the count in memory for faster re-use
check_cache = {}

app = Flask(__name__, static_url_path="", static_folder="public")


@app.route("/")
def main():
    print('mongodb://'+mongo+':27017/gumbler')
    return render_template('index.html')

# move to library


def is_ascii(s):
    return all(ord(c) < 128 for c in s)

# updates the count value in the projects collection


def update_project_tallies():
    projects = db.findings.distinct("project")
    for project in projects:

        # update the count, one ah ah ah two ah ah ah
        count = db.findings.find({"project": project}).count()
        pr = '{ "project":"'+str(project)+'","count":"'+str(count)+'"}'

        find_project = db.projects.find_one({"project": project})
        if find_project == None:
            # add to the projects collection if not in there
            db.projects.insert_one(json.loads(pr))
        else:
            # set the value otherwise
            db.projects.update({
                'project': project
            }, {
                '$set': {
                    'count': count
                }
            })


def projects():
    if request.args.get("recount") == "y":
        update_project_tallies()

    projects_ = db.projects.find()
    search = request.args.get("search")

    if not (search == None):
        projects = []
        search = request.args.get("search")
        for proj in projects_:
            if str(search) in proj:
                projects.append(proj)
    else:
        projects = projects_

    page, per_page, offset = get_page_args()
    from_ = 20*(page-1)
    to_ = 20*page
    projects_render = projects[from_:to_]
    pagination = Pagination(page=page, offset=offset, per_page=20,
                            total=projects.count(), search=False, record_name='projects')

    return render_template('project.html', projects=projects_render, pagination=pagination)


def in_seed_list(file_):
    with open("files_to_look_for.txt") as f:
        extras = f.read().splitlines()
    for ext in extras:
        if ext in file_:
            return True
    return False


def project():
    proj = request.args.get("project")
    # do we need sanitization considerations?
    projects = db.findings.find({"project": proj})

    # this should be refactored
    p = []
    for project in projects:
        if not in_seed_list(project["file"]):
            project["gitignore"] = False

        if project["results"] == "NOT DOWNLOADED":
            project["not_downloaded"] = True
        if is_ascii(project["results"]):
            project["is_ascii"] = True
            project["results"] = project["results"]
        p.append(project)
    return render_template('display.html', projects=p)


def orgs():
    if request.args.get("recount") == "y":
        update_project_tallies()

    projects_ = db.projects.find()
    search = request.args.get("org")

    if not (search == None):
        projects = []
        for proj in projects_:
            if str(search) in proj["project"].lower():
                projects.append(proj)
    else:
        projects = projects_

    page, per_page, offset = get_page_args()
    from_ = 20*(page-1)
    to_ = 20*page
    projects_render = projects[from_:to_]
    pagination = Pagination(page=page, offset=offset, per_page=20,
                            total=len(projects), search=False, record_name='projects')

    return render_template('project.html', projects=projects_render, pagination=pagination)


def files():
    file_ = request.args.get("file")

    reg = re.compile(file_)
    projects = db.findings.find({"file": reg})

    # this should be refactored
    p = []
    for project in projects:
        if project["results"] == "NOT DOWNLOADED":
            project["not_downloaded"] = True
        if is_ascii(project["results"]):
            project["is_ascii"] = True
            project["results"] = project["results"].replace("<", "&lt;").replace(">", "&gt;")
            p.append(project)
    return render_template('file_list.html', projects=p)


def check():
    txt_checks = db.checks.find()
    return render_template('checks.html', txt_checks=txt_checks)

# run a list of regexes across all loaded projects


def run_regex(regex, matching_only, from_, limit_):
    results = []

    reg = re.compile(regex)

    findings = db.findings.find({"results": reg})
    for finding in findings:
        if not ("Error pulling file" in finding["results"]):
            if finding["results"] == "NOT DOWNLOADED":
                finding["not_downloaded"] = True
            if is_ascii(finding["results"]):
                finding["is_ascii"] = True
                finding["results"] = finding["results"]

            if matching_only:
                # show only the matching text
                match = reg.search(finding["results"])
                finding["match"] = match.group(0)
            else:
                finding["match"] = finding["results"]

            finding["regex"] = regex
            results.append(finding)
    return results

# run the check provided


def run_check():
    check = request.args.get("check")
    matching_only = request.args.get("matching_only")

    ignore = ""
    ignore = request.args.get("ignore")
    ignore = str(ignore)
    filename = ""
    filemame = request.args.get("filename")
    filename = str(filename)
    results = []

    txt_check = db.checks.find_one({"name": check})
    regex = txt_check["check_regex"]
    check_name = str(txt_check["name"])

    page, per_page, offset = get_page_args()
    per_page = 200
    from_ = per_page*(page-1)

    if not (check_name in check_cache):
        reg = re.compile(regex)
        # uncomment when can figure out limit and offset with pymongo
        #findings = db.findings.find({"results":reg})
        #total = 0
        # for finding in findings:
        #	if not ("Error pulling file" in finding["results"]):
        #		total =+ 1
        #check_cache[check_name] = total

        results = run_regex(regex, matching_only, from_, per_page)
        check_cache[check_name] = results
        results = results[from_:from_+per_page]
    else:
        results = check_cache[check_name][from_:from_+per_page]

    pagination = Pagination(page=page, offset=offset, per_page=per_page, total=len(
        check_cache[check_name]), search=False, record_name='results')

    return render_template('check_results.html', results=results, filename_=filename, ignore=ignore, pagination=pagination)


def show_file():
    commit = request.args.get("commit")
    file_ = request.args.get("file")

    result = db.findings.find_one({"commit": commit, "file": file_})

    if result == None:
        return "No such commit,file"

    if result["results"] == "NOT DOWNLOADED":
        result["not_downloaded"] = True
    if is_ascii(result["results"]):
        result["is_ascii"] = True
        result["results"] = result["results"]

    return render_template('display_file.html', result=result)


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

# show file/commit
app.add_url_rule('/show_file', 'show_file', show_file)

# search by org
app.add_url_rule('/orgs', 'org', orgs)

if __name__ == "__main__":
    app.run(debug=True)
