# torcp
A script to rename and copy downloaded files to a target in Emby-happy way:
1. Category TV/Movie.
2. Extract movie name from filename.
3. Copy to your `GD drive`.
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


