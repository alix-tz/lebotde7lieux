import requests
import json


def incorrect_loading_mode(m: str):
	"""display a message"""
	print("'{}' is not a correct loading mode, switching to default : 'json'".format(m))


def failed_loading_data(m: str):
	"""display a message"""
	print("Failed to load with mode '{}'' or 'json'".format(m))


def report_qid(idk: str, dictionnary: dict):
	"""display a message"""
	print("Going for '{}':'{}'".format(idk, dictionnary[idk]["name"]))


def report_map_generation():
	"""display a message"""
	print("Generating the map.")


def report_message(message):
	"""display a message"""
	print('This message was generated :\n"{}"'.format(message))


def report_msg_too_long():
	"""display a message"""
	print("The generated message exceeds 280 characters.")


def report_statuscode(sc: str):
	"""display a colored message"""
	from termcolor import colored

	if int(sc) == 200:
		print(colored("Request successfully sent: {}".format(sc), 'green'))
	elif str(sc).startswith("5"):
		print(colored("Oops, something went wrong with the server: {}".format(sc), 'red'))
	else:
		print(colored("Seems like something wen wrong with the request: {}".format(sc), 'yellow'))


def choose_key(dictionnary: dict):
	"""return one random key from a dictionnary."""
	import random
	
	keys = [k for k in dictionnary.keys()]
	return random.choice(keys)


def load_file(filepath: str, mode="json"):
	"""load a file according to indicated mode of loading (default is JSON)"""
	with open(filepath, "r", encoding="utf-8") as fh:
		if mode.lower() == "json":
			fcontent = json.load(fh)
		else:
			incorrect_loading_mode(mode)
			try:
				fcontent = json.load(fh)
			except Exception as e:
				failed_loading_data(mode)
	return fcontent


def send_wd_request(idk: str):
	"""send a request to Wikidata sparqlendpoint, return query status and content"""
	url = "https://query.wikidata.org/sparql"
	query = """SELECT DISTINCT ?item ?itemLabel ?coords (MD5(CONCAT(str(?item),str(RAND()))) as ?random) WHERE {{ 
	?item wdt:P31*/wdt:P279* wd:{} ; 
		wdt:P625 ?coords. 
	SERVICE wikibase:label {{ bd:serviceParam wikibase:language "en, fr"}} }} ORDER BY ?random LIMIT 7""".format(idk)
	r = requests.get(url, params={"format":"json", "query": query})
	report_statuscode(r.status_code)
	return r.status_code, r.text


def list_items(response: dict):
	"""extract the essential elements from the response"""
	seven_places = []
	for item in response["results"]["bindings"]:
		seven_places.append({"url":item["item"]["value"], "name": item["itemLabel"]["value"], "coords": item["coords"]["value"]})
	return seven_places


def generate_map(places):
	def make_a_marker(coords, label):
		color = "f71c01"
		lon, lat = coords.replace("Point(", "").replace(")", "").split(" ")
		return "pin-s-{label}+{color}({lon},{lat})".format(color = color, label = label, lon = lon, lat = lat)


	def build_overlay(places):
		overlay = ""
		label = 1
		for place in places:
			overlay = overlay + ",{}".format(make_a_marker(place["coords"], label))
			label += 1
		if overlay[0] == ",":
			overlay = overlay[1:]
		return overlay


	from secrets import mapbox_pkey

	report_map_generation()
	username = "botde7lieux"
	style_id = "ck3czdwk33eyf1cp75mrdryex"
	overlay = build_overlay(places)
	url = "https://api.mapbox.com/styles/v1/{username}/{style_id}/static/{overlay}/{lon},{lat},{zoom}/{width}x{height}@2x?access_token={pk}".format(username=username, style_id=style_id, lon=0, lat=0, zoom=0, width=900, height=900, overlay=overlay, pk=mapbox_pkey)
	r = requests.get(url = url)
	report_statuscode(r.status_code)
	return r.content # this is a png file


def build_text_for_tweet(category, places):
    def make_short_line(line):
        words = line.split(" ")
        if len(words) > 3:
            while len(line) > 30 :
                words = words[:-1]
                line = " ".join(words)
                line = line + "..."
        return line


    def shorten_message(message):
        print("We need to remove {} characters".format(len(message)-280))
        lines = message.split("\n")
        new_message = lines[0]
        for line in lines[1:]:
        	new_message = new_message + "\n{}".format(make_short_line(line))
        print("{} characters were removed".format(len(message)-len(new_message)))
        return new_message


    message = "7 instances of '{}':".format(category)
    label = 1
    for place in places :
    	message = "{message}\n{label}: {name}".format(message=message, label=label, name=place["name"])
    	label += 1
    while len(message) > 280:
    	report_msg_too_long()
    	message = shorten_message(message)
    report_message(message)
    return message

if __name__ == '__main__':
    file_path = "./data/classes_of_entity.json"
    classes_of_entities = load_file(file_path)
    status = 0
    while int(status) != 200:
        qid = choose_key(classes_of_entities)
        report_qid(qid, classes_of_entities)
        status, response = send_wd_request(qid)
    places = list_items(json.loads(response))
    text = build_text_for_tweet(classes_of_entities[qid]["name"], places)
    generate_map(places)
