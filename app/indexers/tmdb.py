import os
import requests

class TMDB:
    def __init__(self) -> None:
        self.api_key = os.getenv("TMDB_API_KEY")
        self.api_root = "https://api.themoviedb.org/3/"

    def query_by_tmdbid(self, tmdbid: str):
            tmdb_url = f"{self.api_root}movie/{str(tmdbid)}?api_key={self.api_key}"
            return requests.get(tmdb_url).json()

if __name__ == "__main__":
    tmdb = TMDB()
    tmdb_response = tmdb.query_by_tmdbid("141603")
    title = tmdb_response["original_title"]
    assert(title == "Gunda")
    print("success!")