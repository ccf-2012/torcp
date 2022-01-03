# torcp
A script to rename and copy media files to a target in Emby-happy way:
1. Category TV/Movie.
2. Parse movie name, year, season from filename/dirname.
3. Rename and organize your media files  in [Emby-happy](https://support.emby.media/support/solutions/articles/44001159102-movie-naming) ways, supports:
   1. create `Hard Link` ( ln ) to a seperate dir,  or:
   2. [rclone](https://rclone.org/) copy to your `GD drive`, `OneDrive` or anything [rclone](https://rclone.org/) supports,.
 

##  Usage:
```sh 
python3 torcp.py -h
```

##  Examples:
* rclone copy whole dir to a gd path, with guessed category:
```sh
python3 torcp.py  /home/ccf2012/Downloads/  --gd_path=gd123:/media/
```

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

* rclone copy a single dir to a gd path
```sh 
python3 torcp.py \
   /home/ccf2012/Downloads/The.Boys.S02.2020.1080p.BluRay.DTS.x264-HDS \
   --gd_path=gd123:/176/ -s
```

## Acknowledgement 
@NishinoKana @Esc @Hangsijing

