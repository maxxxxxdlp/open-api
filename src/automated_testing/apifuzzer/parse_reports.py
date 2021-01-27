import glob
import json

urls = []

for file_name in glob.glob('./reports/*'):
	with open(file_name) as file:
		urls.append(json.loads(file.read())['request_url'])

with open('parsed.txt','w') as file:
	file.write('\n'.join(urls))