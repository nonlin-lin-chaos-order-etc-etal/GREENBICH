import json

# read file
with open('local.json', 'r') as myfile:
    data=myfile.read()
config = json.loads(data)

def settings(key):
    return config[key]

def getconfig():
	return config
