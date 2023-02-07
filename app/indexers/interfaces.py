import os, json, logging, uuid
from urllib.parse import quote
from datetime import datetime

from tmdb import TMDB
from utils import Quality, guess_quality, str_to_xml, arrt_dl_root


class Movie_Details:
    def __init__(self, tmdbid: str, uid: str = str(uuid.uuid4()), version : str = "1"):
        self.version = version
        self.uid = uid
        self.tmdbid = tmdbid
        self.tmdb_response = TMDB().query_by_tmdbid(tmdbid)


class Movie_Download_Info:
    def __init__(self,
                movie_details: Movie_Details, info_url: str = "", uid : str = str(uuid.uuid4()),
                version : str = "1",
                quality: Quality = Quality._Unknown, size : int = 1000, upload_date : str = None,
                title_override : str = "",
                command : tuple = (), extension: str = ""
    ):

        self.movie_details = movie_details
        self.info_url = info_url
        self.size = size
        self.command = command
        self.extension = extension
        self.upload_date = upload_date
        self.quality = quality
        self.version = version
        
        if title_override == "":
            self.title = self.movie_details.tmdb_response["title"]
        else:
            self.title = title_override

        if self.quality == Quality._Unknown:
            try:
                self.quality = guess_quality(self.size, self.movie_details.tmdb_response.get("runtime"))
            except:
                logging.info("failed to guess quality")
                
        self.uid = str(uuid.uuid5(
            uuid.NAMESPACE_URL,
            f"{info_url}#{quality.value.name}")
        )   #set it from info url and quality
        
        
        
        
        self.categories = { #each key(i.e category) should be a dictionary of tuple(i.e subcategories). empty typle if no subcategory
            "2000": (       #Movies
                    str(self.quality.value.category_id)
                ),
            str(self.quality.value.category_id): ()
        }


    def get_title(self):
        return self.title

    def get_output_filename(self):
        official_title = self.movie_details.tmdb_response["title"]
        tmdbid = self.movie_details.tmdbid
        release_year = self.movie_details.tmdb_response.get("release_date").split("-")[0]

        ouput_filename = f'{official_title} ({release_year}) [tmdb-{tmdbid}] [{self.quality.value.height}].{self.extension}'
        return ouput_filename

    def get_output_filepath(self):
        download_directory = os.getenv("DOWNLOAD_DIRECTORY")
        return f'{download_directory}/{self.get_output_filename()}'


class TornzabXML():
    def __init__(self, title = "generic title") -> None:
        self.header = '''<?xml version="1.0" encoding="UTF-8"?>
                    <rss version="1.0" xmlns:atom="http://www.w3.org/2005/Atom" xmlns:torznab="http://torznab.com/schemas/2015/feed">
                        <channel>'''
        self.footer = '''</channel>
                    </rss>'''

        self.title = title
        self.movie_download_infos = []



    def add_movie_download_info(self, movie_download_info : Movie_Download_Info) -> None:
        self.movie_download_infos.append(movie_download_info)
        logging.debug(f"added {movie_download_info.uid}")

    def get_payload(self, movie_download_info: Movie_Download_Info) -> str:
        payload = {
            "version": movie_download_info.version,
            "command": movie_download_info.command,
            "output_filepath": movie_download_info.get_output_filepath(),
            "output_filename": movie_download_info.get_output_filename()
        }
        payload_json = json.dumps(payload)
        payload_quoted = quote(payload_json)
        return payload_quoted

    def get_xml_item(self, movie_download_info : Movie_Download_Info) -> str:
        payload = self.get_payload(movie_download_info)
        movie_details = movie_download_info.movie_details

        movie_title = movie_download_info.get_title()
        movie_title = str_to_xml(movie_title)

        if movie_details.tmdb_response.get("status") == "Released":
            logging.info(f"upload date is {movie_download_info.upload_date}")
            release_date = movie_details.tmdb_response.get("release_date")
            if not None is movie_download_info.upload_date:
                upload_date = movie_download_info.upload_date
                upload_date = datetime.strptime(upload_date, '%Y%m%d').date()
                upload_date = upload_date.isoformat()
            else:
                upload_date = release_date
        else:
            release_date = "Unreleased"
        
        if movie_download_info.info_url == "" or release_date == "Unreleased":
            ###There should not be any relase
            return ""

        download_quality = movie_download_info.quality.value.height

        torrent_url = f"{arrt_dl_root}/get_torrent?payload={payload}"

        content = f'''
                    <item>
                        <title>{" ".join([movie_title])}</title>
                        <description />
                        <guid isPermaLink="true">{movie_download_info.uid}</guid>
                        <comments>{quote(movie_download_info.info_url, safe=":/?=")}</comments>
                        <pubDate>{upload_date}</pubDate>
                        <size>{movie_download_info.size}</size>
                        <link>{quote(movie_download_info.info_url, safe=":?/=")}</link>
                        <category>2040</category>
                        <category>100042</category>
                        <enclosure url="{torrent_url}" length="{str(movie_download_info.size)}" type="application/x-bittorrent" />
                        {self.get_category_xml(movie_download_info.quality)}
                        <torznab:attr name="size" value="{movie_download_info.size}"/>
                        <torznab:attr name="tag" value="freeleech" />
                        <torznab:attr name="seeders" value="100" />
                        <torznab:attr name="peers" value="200" />
                        <torznab:attr name="downloadvolumefactor" value="0" />
                        <torznab:attr name="uploadvolumefactor" value="1" />
                    </item>
                '''
        return content


    def get_category_xml(self, quality : Quality):
        category_xml = f'''<torznab:attr name="category" value="2000" /> 
        <torznab:attr name="category" value="{quality.value.category_id}" />
        '''
        return category_xml

    
    def get_xml(self) -> str:
        xml =   f'''{self.header}
                    <title>{self.title}</title>'''
        for movie_download_info in self.movie_download_infos:
            xml += self.get_xml_item(movie_download_info)
        
        xml += self.footer
        return xml


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)

    md = Movie_Details(tmdbid=141603)
    assert(md.tmdb_response['title'] == "Gunda")

    tornzab = TornzabXML()
    xml1 = tornzab.get_xml()

    mdi = Movie_Download_Info(md)
    tornzab.add_movie_download_info(mdi)
    xml2 = tornzab.get_xml()
    assert(xml1 == xml2)

    from youtube import Youtube
    youtube = Youtube()
    mdis = youtube.parse(md, run_from_cache = False)
    for mdi in mdis:
        logging.info(f"adding {mdi.get_title()}")
        tornzab.add_movie_download_info(mdi)
    xml3 = tornzab.get_xml()

    print("success!")