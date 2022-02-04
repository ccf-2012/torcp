# torcp
A script to organize media files in Emby-happy way, create hardlink in a seperate dir:
1. Category TV/Movie.
2. Parse movie name, year, season from filename/dirname.
3. Rename and organize your media files  in [Emby-happy](https://support.emby.media/support/solutions/articles/44001159102-movie-naming) ways:
4. create `Hard Link` ( ln ) to a seperate dir
 

##  Usage:
```sh 
python3 torcp.py -h
```

```
usage: torcp.py [-h] [-d HD_PATH] [--tv] [--movie] [--dryrun] [--single]
                MEDIA_DIR

torcp: a script hardlink media files and directories in Emby-happy naming and
structs.

positional arguments:
  MEDIA_DIR             The directory contains TVs and Movies to be copied.

optional arguments:
  -h, --help            show this help message and exit
  -d HD_PATH, --hd_path HD_PATH
                        the dest path to create Hard Link.
  --tv                  specify the src directory is TV.
  --movie               specify the src directory is Movie.
  --dryrun              print message instead of real copy.
  --single, -s          parse and copy one single folder.
```
##  Examples:

* hardlink whole dir to a seperate dir, with guessed category:
```sh 
python3 torcp.py /home/ccf2012/Downloads/  --hd_path=/home/ccf2012/emby/ 
```

* hardlink, specify ALL subdirs are Movie:
```sh
python3 torcp.py /home/ccf2012/Downloads/RSSMovie/ --hd_path=/home/ccf2012/emby/ --movie
```

* hardlink, specify one SINGLE dir is TV:
```sh
python3 torcp.py /home/ccf2012/Downloads/权力的游戏.第1-8季.Game.Of.Thrones.S01-S08.1080p.Blu-Ray.AC3.x265.10bit-Yumi --hd_path=/home/ccf2012/emby/ -s --tv
```


## Acknowledgement 
@NishinoKana @Esc @Hangsijing

