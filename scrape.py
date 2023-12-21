import requests
import json

import os
import random as r
import time as t

#utility functions
def random_user_agent(typ="str"):
    agents = open("agents.txt", "r")
    agent = r.choice(agents.readlines())
    agents.close()
    if typ == "dict":
        balls = dict()
        balls["User-Agent"] = str(agent).replace("\n", "")
        return balls
    else:
        return agent

def mkdir_tree(words_of_interest, boards):
	try:
		os.mkdir("./boards/")
	except Exception:
		pass

	for board in boards:
		try:
			os.mkdir("./boards/"+board["board"]+"/")
		except Exception:
			pass

		for keyw in words_of_interest:
			try:
				os.mkdir("./boards/"+board["board"]+"/"+keyw+"/")
			except Exception:
				pass

#4chan request functions, as you descend the search size narrows
def get_boards():
	print("Searching for boards")
	boards = []
	req = requests.get(headers=random_user_agent(typ="dict"),url="https://a.4cdn.org/boards.json")
	j = json.loads(req.text)
	for i in j["boards"]:
		boards.append({"board":i["board"], "pages":i["pages"], "title":i["title"]})

	return boards

def get_threads(board, stop_date):
	threads = []#if stopdate, else pull all
	page = 1
	print("Starting board: " + board["title"])
	base = "https://a.4cdn.org/"+board["board"]+"/"
	req = json.loads(requests.get(url=base+str(page)+".json", headers=random_user_agent("dict")).text)
	brok = False

	req_time = t.time()
	print("total pages: "+str(board["pages"]))
	while page <= int(board["pages"]) and not brok:
		print("page: "+str(page))
		for thread in req["threads"]:
			if stop_date!= 0:
				if thread["time"] > stop_date:
					brok = True
					break
				else:
					threads.append(thread)

			else:
				threads.append(thread)
		
		page+=1
		if page > int(board["pages"]):break
		while t.time() < req_time+1:
			t.sleep(.01)
		req = ""
		retries = 0 
		while req == "":
			try:
				req = json.loads(requests.get(url=base+str(page)+".json", headers=random_user_agent("dict")).text)
			except Exception:
				t.sleep(1.1)
				retries+=1
				
				if retries == 4:
					print("failed to find: "+board["title"])
					return threads
				
				print("retryin:"+str(base+str(page)+".json"))
				

	return threads

def get_comment_text(thread):
	thread_info = []
	url = "https://a.4cdn.org/"+thread["board"]["board"]+"/thread/"+str(thread["posts"][0]["no"])+".json"
	att = ""
	while att == "":
		try:
			t.sleep(1.1)
			att = requests.get(url, headers=random_user_agent("dict")).text
		except Exception:
			pass

	req = json.loads(att)
	
	comments = []
	for comment in range(1, len(thread["posts"])-1):
		comment_post = req["posts"][comment]
		try:
			comments.append({"no":comment_post["no"], "com":comment_post["com"]})
		except Exception:
			pass#means only responded with an image, how are these stored on 4chan?

	return comments


exec_start_time = int(t.time())
old_date = 0
print("Note: 4chan wants no more then 1 req per sec\nThis code follows that request, but tries to minimize waste")

words_of_interest = []#add your desired things here
blacklist_boards = ["Yuri", "Ecchi", "Hentai", "Handsome Men", "Hardcore", "Sexy Beautiful Women", "Flash", "Hentai/Alternative", "Yaoi", "Torrents", "High Resolution", "Adult GIF", "Adult Cartoons", "Adult Requests"]#allows for simple content filtration, I want science info and have no need for NSFW boards

boards = get_boards()

white_boards = []
for board in boards:
	if board["title"] not in blacklist_boards:
		white_boards.append(board)

boards = white_boards
mkdir_tree(words_of_interest, boards)

print("Found this many!  "+str(len(boards)))

resume_json = {}
resume_time = 0
if os.path.exists("./resume.json"):
	f = open("resume.json", "r")
	if f.read() != "":
		resume_json = json.load(f).to_dict()
		f.close()
		resume_time = int(resume_json["resume_time"])

		b = open("resume.json", "w")
	else:
		b = open("resume.json", "w+")
else:
	print("Did not find a resume.json, starting full scrape")
	b = open("resume.json", "w+")


if len(list(resume_json.keys())) == 0:
	resume_json["resume_time"] = str(exec_start_time)

for board in boards:
	threads = get_threads(board, resume_time)
	print("Found this many threads: "+str(len(threads)))
	if len(threads) != 0:
		for thread in threads:
			thing = False
			keyw = ""
			for keyword in words_of_interest:
				if str(thread).find(keyword)!=-1:
					thing=True
					print("Matched: "+keyword)
					keyw = keyword
					break

			if thing == True:
				thread["board"] = board
				thread["keyword"] = keyw

				start_of_deep = int(t.time())
				thread["comments"] = get_comment_text(thread)
				while start_of_deep+1 > int(t.time()):t.sleep(.01)#wait until atleast a second has passed

				with open("./boards/"+board["board"]+"/"+keyw+"/"+str(thread["posts"][0]["no"])+".json", "w+") as f:
					f.write(json.dumps(thread, indent=4))
					f.close()

json.dump(b, resume_json)
b.close()
print("Sucessfully Saved")
