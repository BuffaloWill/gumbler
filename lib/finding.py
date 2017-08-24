
# The finding object

#	file: 				name of the file
#	commit: 			commit hash key
#	project:			project name 
#	project_url:		project_url
#	results:			contents of the file
#	commit_date:		date of the commit hash/file
#	cmd:				command to run on the project to get the data (git show HASH:FILE)
#	is_local:			is the project local
#	is_gitignore:		is the file from the gitignore file
#	is_string_search:	was the file found in a string search
#	is_common:			was the file found from the common file list
#	source:				what was the source of the findings (to be implemented)
#	date:				date of the finding

class Finding(object):
    def __init__(self):
		self.file 				= ""
		self.commit 			= ""
		self.project 			= ""
		self.project_url 		= ""
		self.results 			= ""
		self.commit_date 		= ""
		self.cmd 				= ""
		self.is_local 			= ""
		self.is_gitignore 		= False
		self.is_string_search 	= False
		self.is_common 			= False
		self.date 				= ""
