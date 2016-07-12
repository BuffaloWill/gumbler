
if [ -n "$1" ] ; then
    ORG="$1"
else
    echo -n "Enter ORGINZATION NAME:"
    read ORG
fi

curl -o $ORG.json "https://api.github.com/orgs/$ORG/repos?page=1&per_page=10000" 
sleep 1 
curl -o $ORG-1.json "https://api.github.com/orgs/$ORG/repos?page=2&per_page=10000" 
sleep 2
curl -o $ORG-2.json "https://api.github.com/orgs/$ORG/repos?page=3&per_page=10000"
