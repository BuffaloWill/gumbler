# gumbler

Gumbler is a tool to dig for sensitive files committed in the history of the project. It uses the .gitignore and a starter file (i.e. files_to_look_for.txt) as a seed list. It then checks every branch and commit to see if that file was committed at some point. 

## Usage

### To parse a repo cloned from github and view the results:
```
python gumbler.py -r "./projects/[REPO_NAME]" -a -p "[ORG_NAME]/[REPO_NAME]"
python gumbler.py -o server -x "./output"
```

### To parse a local repo and view the results:
```
python gumbler.py -r "./projects/[REPO_NAME]" -a 
python gumbler.py -o server -x "./output"
```

### To view all files from results containing yml
http://localhost:5000/files?file=yml

## Installation

- [Docker](https://github.com/BuffaloWill/gumbler/wiki/Installation-Instructions#docker)
- [Developer Build](https://github.com/BuffaloWill/gumbler/wiki/Installation-Instructions#dev-build)


## Features:

- Lightweight, portable results (i.e. json, html)
- View and search the results via flask server
- No Github API keys required. It can be used against repo's discovered during OSINT and not tied to Github.


## Future Features:

- (Goal) Support svn and mecurial


## Warning

There are lots of bugs and, quite a few, false negatives. Please create an issue if you find something. The project is being actively maintained.
