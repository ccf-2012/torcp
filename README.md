# torcp
A script copies movie and TV files to your `GD drive`, or create `Hard Link` in a seperate dir, in Emby-happy struct.


##  Usage:
```sh 
python3 torcp.py -h
```

##  Example:
* copy to a gd path
```sh
python3 torcp.py  /home/ccf2012/Downloads/  --gd_path=gd123:/media/
```
* copy a single directory to a gd path
```sh 
python3 torcp.py \
   /home/ccf2012/Downloads/The.Boys.S02.2020.1080p.BluRay.DTS.x264-HDS \
   --gd_path=gd123:/176/ -s
```

* Hard link to a seperate directory:
```sh 
python3 torcp.py /home/ccf2012/Downloads/  --hd_path=/home/ccf2012/emby/ 
```

## Acknowledgement 
@NishinoKana 


