# gumbler


~~gumbler was a one-off script to search through Git project history.~~
gumbler is going through a re-write with a move over to python, still running against projects IRL before commiting (05/15/17). 

In it's default case it will use the .gitignore file as a seed list and look through every revision and branch looking for a commit where a file from the seedlist may have been commited to the repository. 

For example, say the .gitignore file for the project has an entry for "./conf/config.yml". gumbler will look through every revision of the project looking for any commit that includes the file "./conf/config.yml". The idea would be that a developer might have committed something secret or sensitive in this file at some point. Any matches are stored in the directory specified.

