import requests

#SERVICE wikibase:label { bd:serviceParam wikibase:language "fr,ar,be,bg,bn,ca,cs,da,de,el,en,es,et,fa,fi,he,hi,hu,hy,id,it,ja,jv,ko,nb,nl,eo,pa,pl,pt,ro,ru,sh,sk,sr,sv,sw,te,th,tr,uk,yue,vec,vi,zh"}

def get_these_locations():
	url = "https://query.wikidata.org/sparql"
	query = """
	SELECT ?place ?placeLabel ?coords (MD5(CONCAT(str(?place),str(RAND()))) as ?random)  WHERE {
	?place wdt:P131 ?adminLoc.
	?place wdt:P625 ?coords.
	SERVICE wikibase:label { bd:serviceParam wikibase:language "fr,en,es,fi,it,pt,sw"}
	} ORDER BY ?random
	LIMIT 7
	"""
	r = requests.get(url, params={"format":"json", "query": query})

	if str(r.status_code) == "500":
		print("no tweet today because wikidata server failed to respond")
	else:
		print(r.text)
	return

get_these_locations()