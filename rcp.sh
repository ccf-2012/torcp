#!/bin/bash
#
# qBittorrent 'Run after completion':
# /home/ccf2012/torcp/rcp.sh "%F"  "%N"

python3 /home/ccf2012/torcp/torcp.py "$1" -d "/home/ccf2012/emby/$2/" -s --tmdb-api-key <tmdb api key> --lang cn,jp
rclone copy "/home/ccf2012/emby/$2/"  gd:/media/148/emby/
rm -rf "/home/ccf2012/emby/$2/"