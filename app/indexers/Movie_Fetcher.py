from typing import Tuple
import logging

import utils
from tmdb import TMDB
from interfaces import Movie_Details, Movie_Download_Info, TornzabXML


class Movie_Fetcher:
    def __init__(self) -> None:
        self.tmdb = TMDB()


    def parse(self, movie_details : Movie_Details) -> Tuple[Movie_Download_Info]:  #implement this!
        return []

    def rss(self):
        logging.info(f"{self.__class__.__name__} sending sample rss")
        response = utils.read_file("/app/indexers/files/rss.xml")
        return response
    
    def capabilities(self):
        logging.info(f"{self.__class__.__name__} sending generic capabilities")
        response = utils.read_file("/app/indexers/files/my_capabilities.xml")
        return response


    def fetch(self, tmdbid : int = None, movie_details : Movie_Details = None):
        #will always return valid xml no matter what
        my_name = self.__class__.__name__
        tornzabXML = TornzabXML(title = my_name)
        xml_with_zero_results = tornzabXML.get_xml()

        if (not None is tmdbid) and int(tmdbid) < 1:
            logging.info("sending empty xml")
            return xml_with_zero_results


        try:
            if not None is movie_details:
                #already have valied movie details
                tmdbid = str(movie_details.tmdb_response['id'])
            else:
                #need to call tmdb api to get movie details
                movie_details = Movie_Details(tmdbid = str(tmdbid))
                assert(str(tmdbid) == str(movie_details.tmdb_response['id']))

            logging.info(f"{my_name} will search movie {movie_details.tmdb_response['title']} with tmdbid {tmdbid}")
            movie_download_infos = self.parse(movie_details = movie_details)
        
            for movie_download_info in movie_download_infos:
                logging.debug(f"adding {movie_download_info.uid} to xml")
                tornzabXML.add_movie_download_info(movie_download_info)
            logging.info(f"{my_name} added {len(movie_download_infos)} movie download infos")


        except Exception as e:
            #something went wrong
            #we don't want to crash, so returning valid XML with zero items
            logging.error("something went wrong in generating xml", e)
            return xml_with_zero_results
                
        return tornzabXML.get_xml()







if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    
    mf = Movie_Fetcher()
    caps = mf.capabilities()
    rss = mf.rss()

    empty_xml = TornzabXML(title = "Movie_Fetcher").get_xml()
    xml = mf.fetch(tmdbid=141603)    #gunda
    assert(xml == empty_xml)
    
    print("success!")