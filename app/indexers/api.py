import os, logging

logging_level = getattr(logging, os.getenv("LOGGING_LEVEL"))
if not None is logging_level:
    logging.basicConfig(level = logging_level)

import flask
from flask import request, Response
from urllib.parse import unquote
import json

from Movie_Fetcher import Movie_Fetcher
import searchers
from utils import generate_torrent


app = flask.Flask(__name__)
if logging_level == logging.DEBUG:
    app.config["DEBUG"] = True






@app.route('/', methods=['GET'])
def home():
    return '''<h1>Home of arrt-dl indexers.</h1>'''



@app.route(f"/file_server", methods = ['GET'])
def file_server(filename=None, download_as=None) -> None:
    
    filename = filename or unquote(request.args.get("filename"))
    download_as = download_as or unquote(request.args.get("download_as"))
    return flask.send_file(filename, download_name=download_as, as_attachment=True)


@app.route(f"/get_torrent", methods = ['GET'])
def generate_and_send_fictitious_torrent():
    '''get parameters: url and movie_name

    Returns:
        _type_: torrent file
    '''
    payload = request.args.get("payload")
    payload = json.loads(unquote(payload))
    
    filename = f"/tmp/{payload['output_filename']}"
    torrent_file = generate_torrent(filename, payload)
    download_as = f"{payload['output_filename']}.torrent"

    return file_server(torrent_file, download_as)


@app.route(f"/searcher/<searcher>")
def home_of_searcher(searcher) -> str:
    try:
        searcher : Movie_Fetcher = getattr(searchers, searcher)()
    except:
        logging.error(f"some error in searcher {searcher}")
        return "some error in searcher {searcher}"
    api_url = f"{request.base_url}/api/v1"

    return f'''<h1> Home of the {searcher.__class__.__name__} searcher </h1>
                <h2> The api url is <a href={api_url}>{api_url}</a>  </h2>'''

@app.route(f"/searcher/<searcher>/api/v1", methods=['GET'])
def api_base(searcher) -> Response:
    print(request.args)

    try:
        searcher : Movie_Fetcher = getattr(searchers, searcher)()
        print(type(searcher).__name__)
    except:
        print("some error in searcher {searcher}")

    t = request.args.get("t")
    tmdbid = request.args.get("tmdbid")

    
    if t == "caps": #return our capabilities
        r = searcher.capabilities()

    
    elif not None is tmdbid:  #if queried with tmdbid perform search in our Movie_Fetcher
        r = searcher.fetch(tmdbid = tmdbid)
    
    elif t == "movie":  #otherwise return fictious rss feed. it helps in testing.
        r = searcher.rss()

    else:
        # r = searcher.rss()
        r = searcher.fetch(tmdbid="0")  #empty result
    
    resp = Response(r, status=200, mimetype = "application/x-bittorrent",
                    content_type = "text/xml; charset=utf-8", 
                    headers = {
                        "Cache-Control": "no-cache, no-store, must-revalidate",
                        "Pragma": "no-cache",
                        "Expires": "0",
                    }
        )
    return resp


app.run(host="0.0.0.0", port=os.getenv("FLASK_PORT"))