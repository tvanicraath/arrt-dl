import os, sys, time, subprocess
import json
import logging
import aria2p

download_directory = os.getenv("DOWNLOAD_DIRECTORY")

if os.getenv("DEBUG") == "TRUE":
    logging_level = logging.DEBUG
else:
    logging_level = logging.INFO
logging.basicConfig(level=logging_level)


def clear_files(download : aria2p.Download):
    for download_file in download.files:
        logging.debug(f"removing {download_file.path}")
        exitcode = subprocess.run(["rm", download_file.path]).returncode
        if exitcode == 0:
            logging.info(f"Deleted {download_file.path}")
        else:
            logging.error(f"Failed to delete {download_file.path}")



def connect_to_aria2() -> aria2p.API:
    host=os.getenv("ARIA2_HOST")
    port=os.getenv("RPC_PORT")
    secret=os.getenv("RPC_SECRET")

    while True:
        try:
            client = aria2p.Client(host=host, port=port, secret=secret)
            aria2 = aria2p.API(client)
            aria2.get_global_options()  #test if connection is good
            return aria2
        except Exception as e:
            logging.error(f"failed to connect to aria2 rpc at {host}:{port} with secret {secret}, error: {e}")
            logging.info("retring in 1 minute")
            time.sleep(60)
        except:
            logging.info("exiting")
            sys.exit()


aria2 = connect_to_aria2()

gid : int = sys.argv[1]
logging.info(f"processing download with gid: {gid}")

try:
    download = aria2.get_download(gid)
except:
    logging.error(f"no download with gid: {gid}. I am exiting")
    sys.exit()

logging.debug(f"download gid: {gid}, name: {download.name}")


assert(len(download.files) == 1) 
download_file = download.files[0]
logging.debug(f"download gid: {gid}, download_file_path: {download_file.path}")



with open(download_file.path, "r") as f:
    json_data = json.load(f)
    command = json_data.get("command")
    logging.debug(f"download gid: {gid}, command: {command}, json data: {json_data}")



clear_files(download)


logging.info(f"download gid: {gid}, now executing: {command}")
exitcode = subprocess.run(command).returncode
if exitcode == 0:
    logging.info(f"download gid: {gid}, success!")
else:
    logging.error(f"download gid: {gid}, exitcode: {exitcode}")
