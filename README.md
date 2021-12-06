# torcp
A script to rename and copy downloaded files to a target in Emby-happy way:
1. Category TV/Movie.
2. Parse movie name, year, season from filename/dirname.
3. [rclone](https://rclone.org/) copy to your `GD drive`, `OneDrive` or anything [rclone](https://rclone.org/) supports, in [Emby-happy](https://support.emby.media/support/solutions/articles/44001159102-movie-naming) naming.
4. or create `Hard Link` in a seperate dir.

##  Usage:
```sh 
python3 torcp.py -h
```

##  Example:
* copy to a gd path
```sh
python3 torcp.py  /home/ccf2012/Downloads/  --gd_path=gd123:/media/
```

* Hard link to a seperate directory:
```sh 
python3 torcp.py /home/ccf2012/Downloads/  --hd_path=/home/ccf2012/emby/ 
```

* copy a single directory to a gd path
```sh 
python3 torcp.py \
   /home/ccf2012/Downloads/The.Boys.S02.2020.1080p.BluRay.DTS.x264-HDS \
   --gd_path=gd123:/176/ -s
```

## Acknowledgement 
@NishinoKana 


