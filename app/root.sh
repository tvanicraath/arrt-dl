##run as root to set up this container


function installPackages { 
    apt update
    apt -y upgrade
    apt install -y vim sudo wget tar
    apt install -y python3-pip
    apt install -y aria2    #download client
    apt install -y ffmpeg fontconfig #yt-dlp dependencies

    #phantomjs
    apt install -y chrpath libssl-dev libxft-dev libfreetype6-dev libfontconfig1-dev
    cd /tmp
    export PHANTOM_JS="phantomjs-1.9.8-linux-x86_64"
    wget https://bitbucket.org/ariya/phantomjs/downloads/$PHANTOM_JS.tar.bz2
    tar xvjf $PHANTOM_JS.tar.bz2
    mv $PHANTOM_JS /usr/local/share
    ln -sf /usr/local/share/$PHANTOM_JS/bin/phantomjs /usr/local/bin
    rm $PHANTOM_JS.tar.bz2
 } 

function setupUser { 
    adduser --gecos --quiet --disabled-password abc -u 1000
    usermod -aG sudo abc
    echo abc:abc | chpasswd
    echo 'export PATH="/home/abc/.local/bin:$PATH"' >> /etc/bash.bashrc
    export PATH="/home/abc/.local/bin:$PATH"
    
 } 

function installPythonPackages { 
    ##run as abc to set up abc's development env
    su abc -c "python3 -m pip install --upgrade pip"
    su abc -c "python3 -m pip install -r /app/requirements.txt"
 } 



installPackages
setupUser
installPythonPackages

# su abc -c "/app/startup.sh"
