import os, logging, json
from typing import Tuple

from urllib.request import urlopen
from bs4 import BeautifulSoup

from utils import content_length
from interfaces import Movie_Details, Movie_Download_Info, Quality
from Movie_Fetcher import Movie_Fetcher



class Publicdomainmoviedotnet(Movie_Fetcher):
    
    def __init__(self):
        super().__init__()
        self.my_name = self.__class__.__name__

    def search_data_url_in_info_url(self, info_url) -> str:
        fp = urlopen(info_url)
        soup = BeautifulSoup(fp, 'html.parser')
        video_div = soup.find_all("div", {"class": "field-name-download"})[0]
        video_url = video_div.find("a").get('href')
        return f"http://publicdomainmovie.net{video_url}"

    def search_urls(self, r) -> Tuple[str, str]:
        imdbid = r['imdb_id']
        key = f"http://www.imdb.com/title/{imdbid}/"
        with open("/app/indexers/files/free-movies-publicdomainmovies-net.json") as f:
            response = json.load(f)
        
        if key in response:
            info_url = response.get(key).get("freenessurl")
            data_url = self.search_data_url_in_info_url(info_url)
            return (info_url, data_url)
        return ("", "")

    def parse(self, movie_details: Movie_Details) -> Tuple[Movie_Download_Info]:
        '''get all details from tmdbid
            then search for url on your site
            return all details inculding url
        '''

        info_url, data_url = self.search_urls(movie_details.tmdb_response)

        if info_url == "" or data_url == "":
            logging.info(f"{self.my_name} did not find any match for {movie_details.tmdbid}")
            return []   #failed to find match

        movie_size = content_length(data_url)

        mdi = Movie_Download_Info(
            movie_details=movie_details, info_url=info_url, size = movie_size, extension="mp4")
        mdi.command = ("/home/abc/.local/bin/yt-dlp", data_url, "-o", mdi.get_output_filepath())

        logging.info(f"{self.my_name} found a match for tmdb-{movie_details.tmdbid} at {info_url}")
        return [mdi]

if __name__ == "__main__":
    import xmltodict
    logging.basicConfig(level=logging.DEBUG)

    publicdomainmoviedotnet = Publicdomainmoviedotnet()

    # #Gunda
    md = Movie_Details(tmdbid=141603)
    mdis = publicdomainmoviedotnet.parse(md)
    assert(len(mdis) == 0)

    #The Great St. Louis Bank Robbery
    md = Movie_Details(tmdbid=5926)
    assert(md.tmdb_response.get("title") == "The Great St. Louis Bank Robbery")
    
    mdis = publicdomainmoviedotnet.parse(md)
    assert(len(mdis) == 1)
    mdi = mdis[0]
    assert(mdi.quality == Quality._360p)
    assert(str(mdi.size) == "384284457")
    assert("2030" in mdi.categories)

    xml1 = publicdomainmoviedotnet.fetch(movie_details = md)
    d1 = xmltodict.parse(xml1)


    xml2 = publicdomainmoviedotnet.fetch(tmdbid = "5926")
    d2 = xmltodict.parse(xml2)

    assert(d1 == d2)
    assert(d1['rss']['channel']['item']['link'] == 'http://publicdomainmovie.net/movie/the-saint-louis-bank-robbery')

    print("success!")