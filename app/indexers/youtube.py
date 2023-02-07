import os, logging
from typing import Tuple
from yt_dlp import YoutubeDL as YTDL
import googleapiclient.discovery

from interfaces import Movie_Details, Movie_Download_Info, Quality
from Movie_Fetcher import Movie_Fetcher



class YoutubeAPI():
    def __init__(self) -> None:
        self.api_key = os.getenv("YOUTUBE_API_KEY")
        self.youtube = googleapiclient.discovery.build('youtube','v3',developerKey = self.api_key)
        logging.debug("successfully initalized youtube api")

    def search(self, query = "gunda"):
        request = self.youtube.search().list(
                    part="snippet",
                    order="relevance",
                    q=query,
                    type="video",
                    videoDefinition="high",
                    videoDuration="long"
            )
        response = request.execute()
        return response

class Youtube(Movie_Fetcher):

    def __init__(self) -> None:
        super().__init__()
        self.youtube_api = YoutubeAPI()
        self.ytdl = YTDL()

    def merge(self, responses_list):
        #weave through returned video ids
        processed = set([])
        final_responses = []

        max_responses_in_list = max([len(response_stream) for response_stream in responses_list])

        for i in range(max_responses_in_list):
            for response_stream in responses_list:
                if i < len(response_stream):
                    if type(response_stream).__name__ == "list":
                        response = response_stream[i]
                    else:
                        response = response_stream
                        #if returning single result, youtube api doesn't wrap it in array
                    
                    videoid = response["id"]["videoId"]
                    if not videoid in processed:
                        processed.add(videoid)
                        final_responses.append(videoid)
                        logging.debug(f"merged {videoid}")
                    else:
                        logging.debug(f"{videoid} was already present, skipping!")

        return final_responses


    def get_video_ids(self, movie_details : Movie_Details):
        #returns the list of matching video ids
        #order is youtube's returned order

        movie_name = movie_details.tmdb_response['title']
        release_year = movie_details.tmdb_response.get("release_date").split("-")[0]
        logging.info(f"searching youtube for {movie_name}")
        
        responses_list = []
        responses_list += [self.youtube_api.search(movie_name)["items"]]
        responses_list += [self.youtube_api.search(f"{movie_name} {release_year}")["items"]]
        responses_list += self.youtube_api.search(f"{movie_name} full movie")["items"]

        video_ids = self.merge(responses_list)
        logging.debug(f"found {len(video_ids)} videos: {','.join(video_ids)}")
        return video_ids


    def parse(self, movie_details: Movie_Details, run_from_cache: bool = False) -> Tuple[Movie_Download_Info]:

        video_ids = self.get_video_ids(movie_details)
        yt_dlp_infos = {}
        movie_download_infos = []


        filtered_video_ids = []
        for video_id in video_ids:
            info = self.ytdl.extract_info(url=f"https://www.youtube.com/watch?v={video_id}", download=False, process=False)
            yt_dlp_infos[video_id] = info
            title = info["title"]

            expected_duration = int(movie_details.tmdb_response["runtime"])
            duration = int(info["duration"]) // 60
            if abs(duration - expected_duration) > 15:
                logging.info(f"--> skpiping movie {video_id} -- {title} -- because of difference in duration. Expected: {expected_duration} got: {duration}")
                continue

            formats = set([f["format_note"] for f in info["formats"]])
            if not ("1080p" in formats or "720p" in formats):
                logging.info(f"--> skpiping movie {video_id} -- {title} -- because it doesn't seem to have hd video")
                continue

            like_count =  int(info["like_count"])
            view_count = int(info["view_count"])
            if like_count < 0.001 * view_count:
                logging.info(f"--> skpiping movie {video_id} -- {title} -- because of low likes. Views: {view_count} likes: {like_count}")
                continue

            filtered_video_ids.append(video_id)

        logging.debug(f"filtered videos: {','.join(filtered_video_ids)}")

        for video_id in filtered_video_ids:
            info = yt_dlp_infos[video_id]
            info_url = info["original_url"]
            title = info["title"]
            upload_date = str(info["upload_date"])


            quality = Quality._Unknown
            size = 1000
            for format in info["formats"]:
                if "1080p" in format["format_note"]:
                    quality = Quality._1080p
                elif quality == Quality._Unknown and "720p" in format["format_note"]:
                    quality = Quality._720p
                if not None is format.get("filesize"):
                    size = max(size, format["filesize"])   


            mdi = Movie_Download_Info(
                movie_details = movie_details,
                info_url = info_url,
                extension = "mkv",
                quality = quality,
                size = size,
                title_override = f"{title} [WEBDL] [{quality.value.height}]",
                upload_date = upload_date)
            
            mdi.command = ("/home/abc/.local/bin/yt-dlp",
                "-f", "bestvideo[height<=1080]+bestaudio/best[height<=1080]",
                "--merge-output-format", "mkv",
                info_url, "-o", mdi.get_output_filepath())

            
            logging.info(f"--> *adding* movie {video_id} -- {title}")
            movie_download_infos.append(mdi)

            

        return movie_download_infos



if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)

    youtube = Youtube()
    
    md = Movie_Details(tmdbid=141603)    #gunda
    mdis = youtube.parse(md, run_from_cache = False)

    print(f"got {len(mdis)} movie download infos as follows -----")
    for mdi in mdis:
        print(mdi.title, " ---> ", mdi.get_output_filename())
    print("success!")