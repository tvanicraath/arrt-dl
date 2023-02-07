import os, sys, json, enum
from urllib.request import urlopen
from urllib.parse import quote
from torrentfile import execute
from dataclasses import dataclass

arrt_dl_root = f"http://{os.getenv('HOSTNAME')}:{os.getenv('FLASK_PORT')}"


@dataclass
class PictureQuality:
    height: str
    name: str
    category_id: int = 2030
    

class Quality(enum.Enum):
    _Unknown = PictureQuality("Unkown", "Unknown", 2000)
    _270p = PictureQuality("270p", "SD", 2030)
    _360p = PictureQuality("360p", "SD", 2030)
    _480p = PictureQuality("720p", "SD", 2030)
    _720p = PictureQuality("720p", "HD", 2040)
    _1080p = PictureQuality("1080p", "HD", 2040)
    _2k = PictureQuality("2k", "UHD", 2045)
    _4k = PictureQuality("4k", "UHD", 2045)


def content_length(url) -> int:
    site = urlopen(url)
    meta = site.info()
    if 'Content-Length' in meta:
        return meta['Content-Length']
    return 1000


def guess_quality(content_length: int, duration : int):

    try:
        bit_rate = (8.0*int(content_length))/(1000*int(duration)*60) #in kbps
        bit_rate = int(bit_rate)
    except:
        return Quality._Unknown

    if bit_rate < 600:
        return Quality._270p
    if bit_rate < 1000:
        return Quality._360p
    if bit_rate < 1500:
        return Quality._480p
    if bit_rate < 4000:
        return Quality._720p
    if bit_rate < 8000:
        return Quality._1080p
    return Quality._4k


def content_type(url):
    site = urlopen(url)
    meta = site.info()
    if 'Content-Type' in meta:
        return meta['Content-Type']
    return 'Unkown'

def read_file(f, mode='r'):
    with open(f, mode=mode) as ff:
        response = ff.read()
        return response

def touch_file(f):
    with open(f, "w") as ff:
        ff.write("hello world!")

def str_to_xml(s):
    '''
    modify string to honor weird xml requirements
    '''
    s = s.replace("&", "&amp;")
    s = s.replace("<", "&lt;")
    s = s.replace(">", "&gt;")
    s = s.replace("\"", "&quot;")
    s = s.replace("'", "&apos;")
    return s


def generate_torrent(filename: str, payload: dict) -> str:
    '''
    Creates new file filename. Dumps payload in it. Should read it as a json file. 
    '''
    relative_filename = os.path.basename(filename)
    torrent_filename = f"{filename}.torrent"

    with open(filename, 'w') as f:
        json.dump(payload, f)

    url = f"{arrt_dl_root}/file_server?filename={quote(filename)}&download_as={quote(relative_filename)}"
    

    args = ["torrentfile", "create", "-w", url, "-o", torrent_filename, filename]
    sys.argv = args
    execute()
    return torrent_filename
