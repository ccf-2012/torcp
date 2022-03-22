# 利用 qBittorrent 的完成后自动执行脚本功能实现入库
* qBittorrent提供一种下载完成自动运行脚本的功能，可以利用这个功能运行torcp 自动入库
  
## 在Linux机器，QB非docker安装
* 假设 torcp 在 `/home/ccf2012/torcp` 位置
* qBittorrent的 'Torrent完成时运行外部程序' / 'Run after completion' 中填写命令：
```sh
/home/ccf2012/torcp/rcp.sh  "%F" "%N"
```

### 硬链到同分区目录入媒体库
假设 torcp已经安装好依赖，可以独立运行

* `rcp.sh` 内容如下，注意修改其中的:
1. torcp.py 的位置，下面示例中的： `/home/ccf2012/torcp/`
2. 媒体库目录，下面示例中的： `/home/ccf2012/emby/`
3. TMDb的api key： `your_tmdb_api_key`
4. log输出的位置： `/home/ccf2012/rcp.log` 和 `/home/ccf2012/rcp_error.log`

```sh 
#!/bin/bash
python3 /home/ccf2012/torcp/torcp.py "$1" -d "/home/ccf2012/emby/" -s --tmdb-api-key your_tmdb_api_key --lang cn,jp  >>/home/ccf2012/rcp.log 2>>/home/ccf2012/rcp_error.log
```

* 下载一个种子，完成后，查看 `rcp_error.log` 和 `rcp.log`



### 拷到 rclone 目标(如gd, od)
`rcp.sh` 内容如下，注意修改其中的:
1. torcp位置 `/home/ccf2012/torcp/`
2. 暂存路径 `/home/ccf2012/emby` (3处) 
3. `tmdb-api-key`
```sh 
#!/bin/bash
python3 /home/ccf2012/torcp/torcp.py "$1" -d "/home/ccf2012/emby/$2/" -s --tmdb-api-key your_tmdb_api_key --lang cn,jp  >>/home/ccf2012/rcp.log 2>>/home/ccf2012/rcp_error.log

rclone copy "/home/ccf2012/emby/$2/"  gd:/media/148/emby/
rm -rf "/home/ccf2012/emby/$2/"
```


## 在Linux机器，QB以docker安装
* 要硬链的目录文件夹，应当放在docker所mount的存储位置(volume)内，torcp也可以在此，比如 `/downloads` 所对应的目录下内容类似如下：
```
/
├── downloads/
│   ├── emby/
│   ├── torcp/
│   └── ....
```

* 假设安装的docker名为 `linuxserver-qbittorrent1` , 需要进入docker shell中进行操作:
```sh
docker exec -it linuxserver-qbittorrent1 /bin/bash
```

QB的docker，一般是Alphine Linux，已经安装有 python3, 这样可以在docker shell内作以下：
1. `apk add py3-pip`  安装 `pip3`
2. `cd /downloads/torcp/` 转到torcp目录下，`pip3 install -m requirements.txt` 安装依赖
3. 确定QB的读写权限，保证QB可以读写 `/downloads/emby/` 目录。如QB在Docker中的用户名是`abc`，则：
```sh
chown -R abc /downloads/emby/
```
4. 修改 `rcp.sh` 内容如下：
```sh 
#!/bin/bashs
python3 /downloads/torcp/torcp.py "$1" -d "/downloads/emby/" -s --tmdb-api-key your_tmdb_api_key --lang cn,jp  >>/downloads/torcp/rcp.log 2>>/downloads/torcp/rcp_error.log
```
5. 下载一个种子，完成后，查看 `rcp_error.log` 和 `rcp.log`
