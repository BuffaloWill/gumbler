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


# read in the list of common files
def checks():
	with open("files_to_look_for.txt") as f:
   		extras = f.read().splitlines()
	return extras

def temp_print():
	for key,value in hits.iteritems():
		# open the output file
		print("|+| Commit:"+str(key))
		for val in value:
			print "|+| File:"+val

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

# check if the file contains non-ascii chars, if so don't present in the server
def is_ascii(s):
    return all(ord(c) < 128 for c in s)

def clean(branch):
	if branch[0] == "*":
		return branch.split(" ")[1]
	else:
		return branch.split(" ")[2]

# get the remote origin project url from the configuration
def get_project_url(project):
	try:
		return Repo(project).config_reader().get_value("remote \"origin\"","url")
	except Exception as e:
		return "Could not find a project URL"
