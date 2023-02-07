##run this to start container's services
whoami


aria2c  --rpc-save-upload-metadata=false --enable-rpc=true --rpc-listen-all --rpc-allow-origin-all --rpc-listen-port=$RPC_PORT --rpc-secret=$RPC_SECRET --enable-dht=false --disable-ipv6 --seed-time=0 --on-bt-download-complete=/app/downloader/on-bt-download-complete.sh -d $DOWNLOAD_DIRECTORY &

python3 /app/indexers/api.py
