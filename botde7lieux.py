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
	


if __name__ == '__main__':
	file_path = "./data/classes_of_entity.json"
	classes_of_entities = load_file(file_path)
	status = 0
	while int(status) != 200:
		qid = choose_key(classes_of_entities)
		report_qid(qid, classes_of_entities)
		status, response = send_wd_request(qid)
	places = list_items(json.loads(response)["results"])

