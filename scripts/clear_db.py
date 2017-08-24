from pymongo import MongoClient

client = MongoClient('mongodb://127.0.0.1:27017/gumbler')
db = client.gumbler

db.findings.remove({})
db.projects.remove({})