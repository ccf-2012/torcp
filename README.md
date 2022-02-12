# torcp
将下载的影视文件，通过 `硬链` 在另一个文件夹中重组目录、改名以便 `Emby` 这样的程序便于刮削识别。本脚本：
1. 对你的影视文件夹中的文件进行分类，主要处理 TV/Movie.
2. 解析影视文件夹中的 `影视名称`，`年份`，`季`，`集`，以及 `制作组`
3. 依照 [Emby-happy](https://support.emby.media/support/solutions/articles/44001159102-movie-naming) 的风格进行重组目录与改名，在目标目录中生成硬链.
> 所谓硬链，就是不占磁盘空间对同一文件的引用，而在使用时就像两个分别的文件一样，可以改名和移动

##  使用方法:
* 本程序需要在 `python3` 运行环境，以命令行方式运行
* 完整的命令参数，可以通过这样查看：
```sh 
python3 torcp.py -h
```

```
usage: torcp.py [-h] [-d HD_PATH] [--tv] [--movie] [--dryrun] [--single] [--extract-bdmv] [--full-bdmv]
                [--origin-name]
                MEDIA_DIR

torcp: a script hardlink media files and directories in Emby-happy naming and structs.

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
  --extract-bdmv        extract largest file in BDMV dir.
  --full-bdmv           copy full BDMV dir and iso files.
  --origin-name         keep origin file name.
```

## 例子

* 将一个目录中所有影视文件和目录，硬链到另一个目录，其间会按目录名/文件名猜测分类，并挑出 `.mkv` 和 `.mp4`:
```sh 
python3 torcp.py /home/ccf2012/Downloads/  -d /home/ccf2012/emby/ 
```

* 电影和剧集的处理，是不一样的，如果你确认一个目录是电影或剧集，可以使用`--movie` 和 `--tv` 指定:
```sh
python3 torcp.py /home/ccf2012/Downloads/RSSMovie/ -d /home/ccf2012/emby/ --movie
```

* 如果想单独处理单个目录，可使用 `-s` 指定，例如:
```sh
python3 torcp.py /home/ccf2012/Downloads/权力的游戏.第1-8季.Game.Of.Thrones.S01-S08.1080p.Blu-Ray.AC3.x265.10bit-Yumi -d /home/ccf2012/emby/ -s --tv
```

### BDMV的处理
* 特别说一下对BDMV的处理：
1. 如果什么参数都不加，在碰到含有 `BDMV` 目录和 `.iso` 文件时，将会跳过。
```sh
python3 torcp.py /volume1/video/emby/test -d /volume1/video/emby/testdir
```
2. `--extract-bdmv` 参数，可能最适合 Emby 或 Kodi 的用家，它将会从 `BDMV` 目录中挑出最大的几个 `.m2ts` 文件硬链出来，对于 movie/tv 都行。见[下面的例子](#--extract-bdmv-%E7%9A%84%E4%BE%8B%E5%AD%90)
> with `iso` files copy to sepereate dir
```sh
python3 torcp.py /volume1/video/emby/test -d /volume1/video/emby/testdir --extract-bdmv
```
3. `--full-bdmv` 参数。使用这个参数会将整个 BDMV 文件夹和  `.iso` 文件都硬链出来，对于使用碟机播放的用家，就会有用。
```sh
python3 torcp.py /volume1/video/emby/test -d /volume1/video/emby/testdir --full-bdmv
```

#### --extract-bdmv 的例子
* 命令:
```sh
python torcp.py  /share/CACHEDEV1_DATA/Video/QB/TV  -d /share/CACHEDEV1_DATA/Video/emby/  --extract-bdmv 
```
* 原目录:
```
[/share/CACHEDEV1_DATA/Video/QB/TV/Civilisations.S01.COMPLETE.BLURAY-VEXHD] # tree . -h -A -P *.m2ts
.
├── [4.0K]  CIVILISATIONS_D1
│   └── [4.0K]  BDMV
│       ├── [4.0K]  BACKUP
│       │   ├── [4.0K]  CLIPINF
│       │   └── [4.0K]  PLAYLIST
│       ├── [4.0K]  CLIPINF
│       ├── [4.0K]  META
│       │   └── [4.0K]  DL
│       ├── [4.0K]  PLAYLIST
│       └── [4.0K]  STREAM
│           ├── [ 14G]  00002.m2ts
│           ├── [ 14G]  00003.m2ts
│           ├── [ 14G]  00004.m2ts
│           ├── [1.1M]  00005.m2ts
│           ├── [ 12M]  00006.m2ts
│           ├── [ 94M]  00007.m2ts
│           ├── [ 94M]  00008.m2ts
│           ├── [1.9M]  00009.m2ts
│           ├── [1.5M]  00010.m2ts
│           └── [126K]  00011.m2ts
├── [4.0K]  CIVILISATIONS_D2
│   └── [4.0K]  BDMV
│       ├── [4.0K]  BACKUP
│       │   ├── [4.0K]  CLIPINF
│       │   └── [4.0K]  PLAYLIST
│       ├── [4.0K]  CLIPINF
│       ├── [4.0K]  META
│       │   └── [4.0K]  DL
│       ├── [4.0K]  PLAYLIST
│       └── [4.0K]  STREAM
│           ├── [ 14G]  00002.m2ts
│           ├── [ 14G]  00003.m2ts
│           ├── [ 14G]  00004.m2ts
│           ├── [1.1M]  00005.m2ts
│           ├── [ 12M]  00006.m2ts
│           ├── [ 94M]  00007.m2ts
│           ├── [ 94M]  00008.m2ts
│           ├── [1.9M]  00009.m2ts
│           ├── [1.5M]  00010.m2ts
│           └── [126K]  00011.m2ts
└── [4.0K]  CIVILISATIONS_D3
    └── [4.0K]  BDMV
        ├── [4.0K]  BACKUP
        │   ├── [4.0K]  CLIPINF
        │   └── [4.0K]  PLAYLIST
        ├── [4.0K]  CLIPINF
        ├── [4.0K]  META
        │   └── [4.0K]  DL
        ├── [4.0K]  PLAYLIST
        └── [4.0K]  STREAM
            ├── [ 14G]  00002.m2ts
            ├── [ 14G]  00003.m2ts
            ├── [ 14G]  00004.m2ts
            ├── [1.1M]  00005.m2ts
            ├── [ 12M]  00006.m2ts
            ├── [ 94M]  00007.m2ts
            ├── [ 94M]  00008.m2ts
            ├── [1.9M]  00009.m2ts
            ├── [1.5M]  00010.m2ts
            └── [126K]  00011.m2ts

```
* 执行后:
```
[/share/CACHEDEV1_DATA/Video/emby/BDMV_TV/Civilisations] # tree . -h -A
.
├── [4.0K]  CIVILISATIONS_D1
│   ├── [ 14G]  CIVILISATIONS_D1\ -\ 00002.m2ts
│   ├── [ 14G]  CIVILISATIONS_D1\ -\ 00003.m2ts
│   └── [ 14G]  CIVILISATIONS_D1\ -\ 00004.m2ts
├── [4.0K]  CIVILISATIONS_D2
│   ├── [ 14G]  CIVILISATIONS_D2\ -\ 00002.m2ts
│   ├── [ 14G]  CIVILISATIONS_D2\ -\ 00003.m2ts
│   └── [ 14G]  CIVILISATIONS_D2\ -\ 00004.m2ts
└── [4.0K]  CIVILISATIONS_D3
    ├── [ 14G]  CIVILISATIONS_D3\ -\ 00002.m2ts
    ├── [ 14G]  CIVILISATIONS_D3\ -\ 00003.m2ts
    └── [ 14G]  CIVILISATIONS_D3\ -\ 00004.m2ts

```



## Acknowledgement 
 * @Aruba  
 * @NishinoKana @Esc @Hangsijing 
