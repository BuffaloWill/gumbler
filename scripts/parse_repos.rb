require 'json'

# specify repos.json as an argument
if ARGV.size < 1
	puts "Usage:\n\t\tparse_repos.rb FILE_WITH_REPO_LIST"
	exit
end

file = File.read(ARGV[0])

# parse the json
data_hash = JSON.parse(file)

# iterate each hash
data_hash.each do |hash|
  # ignore forked repos
  if !(hash["fork"]) 
      puts "|+| Cloning #{hash["name"]}"
      
      if hash["size"] > 50000
      	puts "|!| Size of project greater than 50mb, skipping"
      end
      next if hash["size"] > 50000

      # clone the project
      `git clone #{hash["clone_url"]}`
      
      # Gumbler requires full directory paths
      #`ruby ~/gumbler/gumbler.rb -s -p #{hash["name"]} ~/[ORG]/results/`

      sleep(3)
  end
end