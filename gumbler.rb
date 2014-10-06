require 'optparse'

options = {}
OptionParser.new do |opts|
  opts.banner = "Usage: gumbler.rb GIT_PROJECT_PATH DIRECTORY_TO_STORE_RESULTS"

  opts.on("-f", "--file FILE", "File to search for, defaults to .gitignore list") do |v|
    options[:file] = v
  end

  opts.on("-l", "--lazy", "Lazy matches on filenames") do |v|
    options[:lazy] = v
  end

  opts.on("-s", "--stream", "Stream based search") do |v|
    options[:stream] = v
  end

  opts.on("-g", "--grep string", "Grep commit log for specific strings (e.g. CVE) and save the modified files to the directory") do |v|
    options[:grep] = v
  end
end.parse!

if ARGV.size < 2
	puts "\n\tgumbler.rb GIT_PROJECT_PATH DIRECTORY_TO_STORE_RESULTS\n\n"
	abort
else
	@directory = ARGV[0]
	@matches = ARGV[1]
end

ignores = []
if options[:file]
	# let the user set the file to look for
	ignores.push(options[:file])
else
	# read in the gitignore
	file = File.new("#{@directory}/.gitignore","rb")
	while(line = file.gets)
		next unless line.chomp
		next if line =~ /#/
		ignores.push(line.chomp)
	end
end

# take in the git @directory, push all revisions into a hash
# TODO: this only uses the master branch
def build_list(directory)
	bz = {}
	puts "|-| Jumping to remote @directory #{@directory}"
	branches = `cd #{@directory} && git rev-list master`

	puts "|-| Storing every revision"
	branches.split("\n").each do |branch|
		flist = []	

		a = `cd #{@directory} && git ls-tree --name-only -r #{branch}`	
		a.split("\n").each do |fname|
			bz["#{branch}"] = flist.push(fname)
		end
	end

	return bz
end

def iterate_ignores(ignores,fz,options)
	ignores.each do |ignore|
		next unless ignore.size > 0
		puts "checking for #{ignore}.." unless options[:quiet]

		fz.each do |key,value|
			if ignore =~ /\*/
				ignore_ext = ignore.split("*").last
				next if ignore_ext.size <= 0
				
				value.each do |fil|
					if fil =~ /#{ignore_ext.gsub(".","[.]")}/
						if fil =~ /\//
							if options[:lazy]
								puts "|+| Lazy matching for #{ignore_ext}, Found it in BRANCH : #{key} #{fil}. Storing it in #{@matches}."
								`cd #{@directory} && git show #{key}:#{fil} > #{@matches}/#{key}_#{fil.gsub("/","_")}`											
							else							
								# ok, now check that all the dir info is there if we aren't lazy matching
								ig_s = ignore.split("\/")
								i = 0
								match = true

								ig_s.each do |ig|
									if i == ig_s.size
										if match
											puts "|+| Looking for #{ignore}, Found it in BRANCH : #{key} #{fil}. Storing it in #{@matches}."
											`cd #{@directory} && git show #{key}:#{fil} > #{@matches}/#{key}_#{fil.gsub("/","_")}`											
										end
									end
									
									unless fil =~ /#{ig.gsub("*","")}/
										match = false
									end
									i = i + 1
								end
							end					
						else
							puts "|+| Looking for #{ignore}, Found it in BRANCH : #{key} #{fil}. Storing it in #{@matches}."
							`cd #{@directory} && git show #{key}:#{fil} > #{@matches}/#{key}_#{fil.gsub("/","_")}`											
						end
											
					end			
				end
			else
				if value.include?(ignore)
					puts "|+| Looking for #{ignore}, Found it in BRANCH : #{key} #{ignore}. Storing it in #{@matches}."
					`cd #{@directory} && git show #{key}:#{ignore} > #{@matches}/#{key}_#{ignore.gsub("/","_")}`				
				end
			end
		end
	end
end

if(options[:grep])
	puts "|!| skipping .gitignore, searching commit log for #{options[:grep]}"
	
	results = `cd #{@directory} && git log --raw -p --pretty=tformat:"gmb_commit:%H-%ci==> %ci %s %B" --grep=#{options[:grep]}`
	results.split("gmb_commit:").each do |log|
		next unless log.size > 0
		fname = log.split("==>").first.gsub(" ","_").gsub("`","_")
		file = File.new("#{@matches}/#{fname}.diff","w")
		file.puts(log)
		file.close
	end

else
	if(options[:stream])
		branches = `cd #{@directory} && git rev-list master`
		
		puts "|!| Stream based parsing, Total Branches: #{branches.split("\n").size}"
		
		total = 0
		branches.split("\n").each do |branch|
			bz = {}
			flist = []	

			a = `cd #{@directory} && git ls-tree --name-only -r #{branch}`	
			a.split("\n").each do |fname|
				bz["#{branch}"] = flist.push(fname)
			end
			options[:quiet] = true
			iterate_ignores(ignores, bz, options)
			
			total = total + 1
			puts "#{total} of #{branches.split("\n").size} complete"
		end		
	else
		fz = build_list(@directory)
		iterate_ignores(ignores,fz,options)
	end
end
