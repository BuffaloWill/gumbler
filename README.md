# Project no longer maintained. 

Hi! This project is no longer maintained as better options now exist. I would recommend:

- https://github.com/dxa4481/truffleHog
- https://github.com/awslabs/git-secrets

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
python gumbler.py -o server 
```

### To clone a remote repo, store the results in the project directory, and analyze:
```
python gumbler.py -s projects -p https://github.com/BuffaloWill/NaughtyGitProject.git
python gumbler.py -o server 
```


### To import a previously generated json file into the database
```
python gumbler.py -j output/myfile.json

# import the entire directory containing json files

python gumbler.py -j output
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
