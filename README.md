# torcp

for english version [CLICK ME](README_en.md)

将下载的影视文件，通过 `硬链` 在另一个文件夹中重组目录、改名以便 `Emby` 这样的程序便于刮削识别。本脚本：
1. 对你的影视文件夹中的文件进行分类，主要处理 TV/Movie.
2. 解析影视文件夹中的 `影视名称`，`年份`，`季`，`集`，以及 `制作组`
3. 依照 [Emby-happy](https://support.emby.media/support/solutions/articles/44001159102-movie-naming) 的风格进行重组目录与改名，在目标目录中生成硬链.
> 所谓硬链，就是不占磁盘空间对同一文件的引用，而在使用时就像两个分别的文件一样，可以改名和移动
4. Since 2022.2.26: 支持搜索TMDb，以获得准确的、选定语言的影视名字，然后以此名字进行更名和组织目录
5. Since 2022.3.13: 对于查出了TMDb id的媒体，支持按语言分类
6. Last updated 2022.3.23: 支持软链 `--symbolink`

## Last Update
* 2022.4.3: `--make-log` 在目标目录中建立一个log文件，以便追溯原文件名
* 2022.3.23: `--symbolink` support symbol link
* 2022.3.13: `--lang` dispatch to different folders base on TMDb language
* 2022.2.26: `--tmdb-api-key` Support TMDb search 

## 准备
> 本程序需要在 `python3` 运行环境，以命令行方式运行

* 下载源码
```sh
git clone https://github.com/ccf-2012/torcp.git
```

* 安装依赖（终于）
```sh
pip3 install -r requirements.txt
```

### 群晖中使用 git
* 群晖中在套件中心，搜索git server，安装
* github 连接默认会有困难，请设法解决

### 群晖中使用python3 和 pip3
* DSM 6.x 默认没有安装Python 3，需要要在套件中心中搜索安装 `Python 3` 
* 群晖安装pip
```sh
python3 -m ensurepip
```

* 群晖中安装依赖库，命令这样打：
```sh
python3 -m pip install -r requirements.txt
```

#  使用方法:
* 完整的命令参数，可以通过这样查看：
```sh 
python3 torcp.py -h
```

```
usage: torcp.py [-h] -d HD_PATH [-e KEEP_EXT] [-l LANG] [--tmdb-api-key TMDB_API_KEY] [--tmdb-lang TMDB_LANG] [--tv] [--movie] [--dryrun] [--single] [--extract-bdmv]
                [--full-bdmv] [--origin-name] [--sleep SLEEP] [--move-run] [--make-log] [--symbolink] [--emby-bracket] [--plex-bracket]
                MEDIA_DIR

torcp: a script hardlink media files and directories in Emby-happy naming and structs.

positional arguments:
  MEDIA_DIR             The directory contains TVs and Movies to be copied.

optional arguments:
  -h, --help            show this help message and exit
  -d HD_PATH, --hd_path HD_PATH
                        the dest path to create Hard Link.
  -e KEEP_EXT, --keep-ext KEEP_EXT
                        keep files with these extention('srt,ass').
  -l LANG, --lang LANG  seperate move by language('cn,en').
  --tmdb-api-key TMDB_API_KEY
                        Search API for the tmdb id, and gen dirname as Name (year)\{tmdbid=xxx\}
  --tmdb-lang TMDB_LANG
                        specify the TMDb language
  --tv                  specify the src directory is TV.
  --movie               specify the src directory is Movie.
  --dryrun              print message instead of real copy.
  --single, -s          parse and copy one single folder.
  --extract-bdmv        extract largest file in BDMV dir.
  --full-bdmv           copy full BDMV dir and iso files.
  --origin-name         keep origin file name.
  --sleep SLEEP         sleep x seconds after operation.
  --move-run            WARN: REAL MOVE...with NO REGRET.
  --make-log            Make a log file.
  --symbolink           symbolink instead of hard link
  --emby-bracket        ex: Alone (2020) [tmdbid=509635]
  --plex-bracket        ex: Alone (2020) {tmdb-509635}
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

## `--extract-bdmv` 和 `--full-bdmv`，BDMV的处理
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

#### `--extract-bdmv` 的例子
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

## `--tmdb-api-key` TMDb 查询
* 通过The Movie Database (TMDb) API 查询，得到确切的tmdbid, 确保生成的文件夹可被刮削
* 可选 `--tmdb-lang` 参数，默认是 `zh-CN`
* 查询不到的文件，将会被 `链` 或 `移` 到目标目录下 `TMDbNotFound` 目录中

```sh
python3 torcp.py /home/test/ -d /home/test/result3/ --tmdb-api-key='your TMDb api key'
```

* 组合 `--move-run` 的例子
```sh
python3 torcp.py /home/test/ -d /home/test/result2/ --tmdb-api-key='your TMDb api key' --plex-bracket --move-run  --dryrun
```

### `--lang` 按语言分类
* 如果查出了TMDb id，那么可以将媒体按语言分类
* `--lang` 后面以逗号分隔写所需要分出来的语言，其它的归到 `others` 
* 如果写 `--lang all` 则所有语言都被分类
* 在TMDb 中，中文语言会是 `zh` 和 `cn`
  
```sh
python3 torcp.py /home/test/ -d /home/test/result3/ --tmdb-api-key='your TMDb api key' --lang zh,cn,en
```


### 利用 qBittorrent 的完成后自动执行脚本功能实现入库

[另开文解说](qb自动入库.md)


----

## `--move-run` 直接改名和移动 
* 不作硬链，直接进行move和改名操作，用于对已经放在gd中的文件进行整理
* `-d` 指定要搬移的目标位置，请自己把握不跨区 
* 加了一个`--sleep`参数，可以每次操作搬移一个文件后暂停 `SLEEP` 秒，此参数仅在 `--move-run` 时有效
* 由于这样的操作不可逆，请一定先作 `--dry-run` 确认后才执行

### 例子
```sh
python3 torcp.py /home/test/ -d /home/test/result5/ --move-run --dryrun
```


## DeleteEmptyFolders.py 清除空目录
* 在作了上面 `--move-run` 操作后，原目录将会剩留大量 空的，或仅包含 `.jpg`, `.nfo` 这类小文件的目录
* 除了默认的 `.mkv`, `.mp4`, `.ts`, `.iso` 之外，使用与 `torcp.py` 相同的 `--keep-ext` 来表示那些已经 **不再包含这些扩展名文件** 的目录，将被删除
* 使用 `--dryrun` 先看下将会发生什么

### 例子
```sh
python3 DeleteEmptyFolders.py /home/test/  -e srt,ass --dryrun
```

## Acknowledgement 
 * @Aruba  @ozz
 * @NishinoKana @Esc @Hangsijing @Inu 
