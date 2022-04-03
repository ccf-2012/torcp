# Auto link/copy to the emby media folder with QB 'Run after completion'

## Set 'Run after completion' in qBittorrent
the qBittorrent client has a funtion to run some script after a torrent complete.
* suppose torcp source file locate at  `/home/ccf2012/torcp`
* set 'Run after completion' of qBittorrent as：
```sh
/home/ccf2012/torcp/rcp.sh  "%F" "%N"
```
> means when a torrent finished downloading, run `/home/ccf2012/torcp/rcp.sh`, with parameter  `%F` refer to full path of the torrent download location, and `%N` refer to the torrent file/dir name, both need be quote with `"`

## link to a location after download completed
* suppose torcp has been setted up, try  `python3 torcp.py -h`  to confirm everything ok。
* modify the script `/home/ccf2012/torcp/rcp.sh`, note:
1. the location of torcp.py: `/home/ccf2012/torcp/torcp.py` 
2. the location of emby/plex media folder: `/home/ccf2012/emby/`
3. your TMDb api key： `your_tmdb_api_key`
4. the log file path： `/home/ccf2012/rcp.log` and `/home/ccf2012/rcp_error.log`

```sh 
#!/bin/bash
python3 /home/ccf2012/torcp/torcp.py "$1" -d "/home/ccf2012/emby/" -s --tmdb-api-key your_tmdb_api_key --lang cn,jp  >>/home/ccf2012/rcp.log 2>>/home/ccf2012/rcp_error.log
```

## rclone copy to a rclone target (ex. google drive, onedrive)

if you want to copy the files(s) to a rclone target (ex. google drive, onedrive), the script `rcp.sh` should be like this:
1. location of torcp `/home/ccf2012/torcp/`
2. cache location `/home/ccf2012/emby/` (total 3 occurs), keep the trailing `/$2/`
3. rclone target `gd:/media/emby/`
4. your TMDb api key: `your_tmdb_api_key`
5. the log file path： `/home/ccf2012/rcp.log` and `/home/ccf2012/rcp_error.log`

```sh 
#!/bin/bash
python3 /home/ccf2012/torcp/torcp.py "$1" -d "/home/ccf2012/emby/$2/" -s --tmdb-api-key your_tmdb_api_key --lang cn,jp  >>/home/ccf2012/rcp.log 2>>/home/ccf2012/rcp_error.log

rclone copy "/home/ccf2012/emby/$2/"  gd:/media/emby/
rm -rf "/home/ccf2012/emby/$2/"
```


## if you run qbittorrent in a docker
* the location and execute permittion should set properly at the docker's view.

### the script and the target folder
*  the script and the target folder, should locate at some mounted volume of the docker，for example, there should be 2 dirs in the mounted volume `/downloads` :
```
/
├── downloads/
│   ├── emby/
│   ├── torcp/
│   └── ....
....
```

* the script path set in the qBittorrent, should also be the path in the docker. for example the 'Run after completion' should be：
```sh
/downloads/torcp/rcp.sh "%F" "%N"
```

* the qBittorrent will call the script to run torcp, so the docker should install the dependencies. for qbittorrent docker build with Alphine linux:
1. `docker exec -it dockername /bin/bash` to enter the docker shell
2. `apk add py3-pip`  to install `pip3`
3. `cd /downloads/torcp/` and run `pip3 install -r requirements.txt` to install dependencies
