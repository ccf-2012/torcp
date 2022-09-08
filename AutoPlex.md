# 配合 PTPP 与torcc 实现 Emby/Plex 自动入库流程

## 0 概述
torcp原本设计仅依靠种子文件夹名，结合TMDb进行猜测来建立适合刮削的目录，然而如果能在下载时就从种子的详情信息页获取（通常都有的）IMDb信息，则可以准确地确定媒体。

因此，一方面torcp支持了在`--single`模式对媒体指定IMDb的功能；另一方面，需要在下载种子时，就通过种子的信息页面解析出媒体的IMDb，进而在qBittorrent中添加种子时同时添加tag（标签)以记录此IMDb，在种子完成时，这个标签可以输出给torcp。

在PT站下载种子并添加标签，现在有两类形式：
1. 手工单次下载，在PT站上，在单个种子的详情页点PTPP的一键下载：
   *  安装 [修改版 PT Plugin Plus](https://github.com/ccf-2012/PT-Plugin-Plus/tree/dev)，在各PT站的种子详情页，点击“一键下载”。此修改版PTPP在添加种子到qBittorrent时会添加IMDb标签。
2. rss自动批量下载：
   * 使用[torcc](https://github.com/ccf-2012/torcc) 在获取rss条目时，对各条目的信息页进行解析，在添加到qBittorrent时添加标签。
   * 此rss脚本为命令行模式运行，可使用crontab 定时启动运行
   

## 1 修改版PTPP
> 此处致敬致谢 [ronggang](https://github.com/ronggang/PT-Plugin-Plus)等创作者。当前本修改代码和功能太过不完善，希望后续比较成型后提交pr给原PTPP库
1. 下载并切dev库
```sh
git clone https://github.com/ccf-2012/PT-Plugin-Plus
cd PT-Plugin-Plus
git checkout dev
```

2. 编译
```sh
yarn install 
yarn build
```
* 详情参考 https://github.com/ronggang/PT-Plugin-Plus/wiki/developer

3. 安装后，PTPP“常规设置”中设置一个默认下载器，需要是qBittorrent，然后在各pt站的种子详情页中，会显示“一键下载”
![一键下载](https://ptpimg.me/y7dw6b.png)

* 当前修改版仅作测试体验，仅在这种情况下的 “一键下载” 才会解析添加 IMDb 标签。下载器中添加了IMDb标签的种子如下图：

![添加标签的种子](https://ptpimg.me/k509vo.png)


## 2 设置 qBittorrent 完成后执行脚本
* 设置 qBittorrent 当种子在完成下载后，自动运行脚本。命令中的 `$G` 参数，即是将IMDb标签输出给脚本，另外两个参数 `$F` 和 `$N` 分别是种子完整路径和文件名称：
![qb-set](https://ptpimg.me/rb09o2.png)

* 所调用脚本中，可以使用传进来的3个参数，例如上述所设的 rcp.sh 中写如下语句：
```sh
python3 /home/ccf2013/torcp/tp.py "$1" -d "/home/ccf2013/emby/$2/" -s --imdbid "$3" --tmdb-api-key xxxxxx  --tmdb-lang en-US --lang cn,ja,ko 
```
* 以上代码表示：以 torcp 处理新完成的种子的存储目录（$1)，生成在 /home/ccf2013/emby/<种子名称($2)> 目录下，指定此媒体IMDb为qBit传来的 Tag参数($3)
* 完成 torcp 改名和目录重组后，可以将此目录 rclone copy 到目标存储(如gd)中，更多的示例和完整的说明，参考 [qb自动入库](qb自动入库.md)


## 3 RSS下载
使用[torcc](https://github.com/ccf-2012/torcc) 可以批量下载站点最新的种子，同时解析并添加标签，可以放在crontab中定时后台运行。需要参数包括：
1. 站点的rss链接
2. 站点的cookie
3. qBittorrent的信息，包括Host, Port, User, Pass

* 使用示例：
```sh
python torcc.py -R "https://some.pt.site/torrentrss.php?rows=10&..." -c "c_secure_uid=ABCDE; ....c_secure_tracker_ssl=bm9wZQ=="  -H qb.server.ip -P 8088 -u qb_user -p qb_pass
```

* 如果希望对rss来的条目进一步作正则(regex)过滤，可加 `--title-regex` 参数 和 `info-regex` 以及 `info-not-regex` 进行筛选。
* 更多的示例和完整的说明，参考：[torcc 主页](https://github.com/ccf-2012/torcc)

## 4 通知 Plex 更新
* 对于Plex，有单独更新指定媒体文件夹的功能，为此写了一个 [Plex Notify](https://github.com/ccf-2012/plex_notify)
* torcp 2022.7.21 版本加入 --after-copy-script 参数，可在完成一个媒体项目的 link/move 之后，对目标文件夹执行一个脚本。
torcp传出的是一个在 Plex/Emby 根目录下面的相对目录
* 具体参考[相关说明](https://github.com/ccf-2012/plex_notify#%E9%85%8D%E5%90%88torcp%E4%BD%BF%E7%94%A8)

