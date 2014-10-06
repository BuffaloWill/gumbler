# gumbler

gumbler was a one-off script to search through Git project history. In it's default case it will use the .gitignore file as a seed list and look through every revision looking for a commit where a file from the seedlist may have been commited to the repository. 

For example, say the .gitignore file for the project has an entry for "./conf/config.yml". gumbler will look through every revision of the project looking for any commit that includes the file "./conf/config.yml". The idea would be that a developer might have committed something secret or sensitive in this file at some point. Any matches are stored in the directory specified.

## Warning

* gumbler uses OS execution and git commands to parse revisions. That is always a dangerous thing. Be confident in the github project you are searching. 
* There are still plenty of bugs. Your mileage may vary. Turns out wildcards are hard. 

## Examples

First you will want to clone a project. For example:

```
git clone [GITHUB_URL_TO_PROJECT]
```
Use this directory below as the {PATH_TO_GIT_PROJECT}

### Using the .gitignore as a seed list

ruby gumbler.rb {PATH_TO_GIT_PROJECT} {DIRECTORY_TO_STORE_RESULTS} 

```
ruby gumbler.rb ./my_github_project/ /tmp/storage/
```

### Using the .gitignore as a seed list in a very large project (i.e. stream parse)

ruby gumbler.rb --stream {PATH_TO_GIT_PROJECT} {DIRECTORY_TO_STORE_RESULTS} 

```
ruby gumbler.rb --stream ./my_big_github_project/ /tmp/storage/
```

### Search for any file in any revision with passwords in the title 

ruby gumbler.rb -l -f passwords {PATH_TO_GIT_PROJECT} {DIRECTORY_TO_STORE_RESULTS} 

```
ruby gumbler.rb -l -f passwords ./my_github_project/ /tmp/storage/
```

### Looking for all commits with CVE in a commit log entry

ruby gumbler.rb --grep CVE {PATH_TO_PROJECT} {DIRECTORY_TO_STORE_DIFFS} 

```
uby gumbler.rb --grep CVE ./my_github_project/ /tmp/storage/
```

## TODO
- Currently only searches master branch
