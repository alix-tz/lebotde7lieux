import requests
import json
import tweepy


# REPORTS ###########################################################################################

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


def report_uploading_image():
    """display a message"""
    print("Uploading image.")


def report_posting_tweet():
    """display a message"""
    print("Posting tweet.")


def report_statuscode(sc: str):
    """display a colored message"""
    from termcolor import colored

    if int(sc) == 200:
        print(colored("Request successfully sent: {}".format(sc), 'green'))
    elif str(sc).startswith("5"):
        print(colored("Oops, something went wrong with the server: {}".format(sc), 'red'))
    else:
        print(colored("Seems like something wen wrong with the request: {}".format(sc), 'yellow'))


# LOADING DATA ######################################################################################

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


# MAP GENERATION ####################################################################################

def generate_map(places):
    """Create an image of a map containing markers"""
    def make_a_marker(coords, label):
        """Add a marker for a given location"""
        color = "f71c01"
        lon, lat = coords.replace("Point(", "").replace(")", "").split(" ")
        return "pin-s-{label}+{color}({lon},{lat})".format(color = color, label = label, lon = lon, lat = lat)


    def build_overlay(places):
        """Build the overlay on the map, aka the markers"""
        overlay = ""
        label = 1
        for place in places:
            overlay = overlay + ",{}".format(make_a_marker(place["coords"], label))
            label += 1
        if overlay[0] == ",":
            overlay = overlay[1:]
        return overlay


    #from secrets import mapbox_pkey
    from os import environ
    MAPBOX_PKEY = environ['MAPBOX_PKEY']

    report_map_generation()
    username = "botde7lieux"
    style_id = "ck3czdwk33eyf1cp75mrdryex"
    overlay = build_overlay(places)
    url = "https://api.mapbox.com/styles/v1/{username}/{style_id}/static/{overlay}/{lon},{lat},{zoom}/{width}x{height}@2x?access_token={pk}".format(username=username, style_id=style_id, lon=0, lat=0, zoom=0, width=900, height=900, overlay=overlay, pk=MAPBOX_PKEY)
    r = requests.get(url = url)
    report_statuscode(r.status_code)
    return r.content # this is a png file


def save_image_file(img):
    """save the image in a temporary file"""
    with open("temp.png", "wb") as fh:
        fh.write(img)


# BUILDING CONTENT ##################################################################################

def build_text_for_tweet(category, places):
    """Create the textual  content of the future tweet"""
    def make_short_label(label, limit_len_line):
        """Follow a scenario in orfer to shorten a label"""
        if len(label) < limit_len_line:
            return label
        else:
            limit_len_line = limit_len_line -3
            label = label[:limit_len_line] + "..."
            return label


    def shorten_message(message):
        """Follow a scenario in order to shorten the whole tweet"""
        print("We need to remove {} characters".format(len(message)-280))
        lines = message.split("\n")
        new_message = "{firstline}\n{hashtags}\n".format(firstline=lines[0], hashtags=lines[1])
        top = len(new_message)
        limit_len_line = (280-top-7) // 7
        for label in lines[2:]:
            new_message = new_message + "{label}".format(label=make_short_label(label, limit_len_line)) + "\n"
        print("{} characters were removed".format(len(message)-len(new_message)))
        return new_message

    
    message = "Now discover 7 instances of '{}'!\n#wikidata #B7L\n".format(category)
    label = 1
    for place in places :
        message = "{message}{label}: {name}\n".format(message=message, label=label, name=place["name"])
        label += 1
    if message[-1] == "\n":
        message = message[:-1]

    while len(message) > 280:
        report_msg_too_long()
        message = shorten_message(message)
    report_message(message)
    return message


def create_tweet(source):
    """Retrieve 7 locations from Wikidata and generate a map and a message to post on Twwiter"""
    entities = load_file(source)
    status = 0
    while int(status) != 200:
        qid = choose_key(entities)
        report_qid(qid, entities)
        status, response = send_wd_request(qid)
    places = list_items(json.loads(response))
    
    message = build_text_for_tweet(entities[qid]["name"], places)
    image = generate_map(places)
    return image, message


# TWEETING ##########################################################################################

def tweet(message):
    """Post a tweet"""
    from os import environ
    CONSUMER_KEY = environ['CONSUMER_KEY']
    CONSUMER_SECRET = environ['CONSUMER_SECRET']
    ACCESS_TOKEN = environ['ACCESS_TOKEN']
    ACCESS_TOKEN_SECRET = environ['ACCESS_TOKEN_SECRET']
    #from secrets import CONSUMER_KEY, CONSUMER_SECRET, ACCESS_TOKEN, ACCESS_TOKEN_SECRET

    # Twitter authentication
    auth = tweepy.OAuthHandler(CONSUMER_KEY, CONSUMER_SECRET)
    auth.set_access_token(ACCESS_TOKEN, ACCESS_TOKEN_SECRET)
    api = tweepy.API(auth)

    # posting
    report_uploading_image()
    try:
        uploaded = api.media_upload(filename = "temp.png")
    except tweepy.error.TweepError as e:
        print(e)
        uploaded = None

    report_posting_tweet()
    try:
        api.update_status(status = message, media_ids = [uploaded.media_id])
    except tweepy.error.TweepError as e:
        print(e.message)


if __name__ == "__main__":
    source = "./data/classes_of_entity.json"
    image, message = create_tweet(source)
    save_image_file(image)
    tweet(message)
    
    
