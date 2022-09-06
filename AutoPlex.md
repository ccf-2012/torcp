# 配合 PTPP 完成 Emby/Plex 自动入库流程

## 0 概述
1. 安装 [修改的PT Plugin Plus](https://github.com/ccf-2012/PT-Plugin-Plus/tree/dev)，在各PT站的种子详情页，点击“一键下载”，解析详情页中的 **IMDb id**，并在添加种子时以此 **IMDb id** 作为标签，当前仅支持qBittorrent
2. 设置qBittorrent在下载完成时，对完成的种子存储目录执行脚本，输出种子的**存储路径**，和上述 **IMDb id**，作为参数
3. 在脚本中，调用 torcp 相关命令完成目录的改名和重新组织，torcp 对于传进来的**IMDb id** 会直接在TMDb中查找
4. 对于Plex, 可以调用 [Plex Notify](https://github.com/ccf-2012/plex_notify) 通知Plex更新指定的目录

## 1 修改版PTPP
> 此处致敬致谢 [ronggang](https://github.com/ronggang/PT-Plugin-Plus)等创作者。当前本修改代码和功能太过不完善，希望后续比较成型后提交pr给原PTPP库
1. 下载并切dev库
```sh
git clone https://github.com/ccf-2012/PT-Plugin-Plus
cd PT-Plugin-Plus
git check dev
```

2. 编译
```sh
yarn install 
yarn build
```
* 详情参考 https://github.com/ronggang/PT-Plugin-Plus/wiki/developer

3. 安装后，PTPP中设置一个默认下载器，需要是qBittorrent，然后在各pt站的种子详情页中，会显示“一键下载”
![一键下载](https://ptpimg.me/y7dw6b.png)

* 当前修改版仅作测试体验，仅在这种情况下的 “一键下载” 才会解析添加 IMDb 标签

![添加标签的种子](https://ptpimg.me/k509vo.png)

## 2 设置 qBittorrent
* 设置 qBittorrent 使种子在完成下载后，自动运行脚本：
![qb-set](https://ptpimg.me/rb09o2.png)

* 其中脚本中，可以使用传进来的3个参数，例如上述所设的 rcp.sh 中写如下语句：
```sh
python3 /home/ccf2013/torcp/tp.py "$1" -d "/home/ccf2013/emby/$2/" -s --imdbid "$3" --tmdb-api-key xxxxxx  --tmdb-lang en-US --lang cn,ja,ko 
```
* 以上代码表示：以 torcp 处理新完成的种子的存储目录（$1)，生成在 /home/ccf2013/emby/<种子名称($2)> 目录下，指定此媒体IMDb为 qBit传来的参数($3)
* 完成 torcp 改名和目录重组后，可以将此目录 rclone 到目标存储(如gd)中，更多的示例，参考 [qb自动入库](qb自动入库.md)

## 3 通知 Plex 更新
* 对于Plex，有单独更新指定媒体文件夹的功能，为此写了一个 [Plex Notify](https://github.com/ccf-2012/plex_notify)
* torcp 2022.7.21 版本加入 --after-copy-script 参数，可在完成一个媒体项目的 link/move 之后，对目标文件夹执行一个脚本。
torcp传出的是一个在 Plex/Emby 根目录下面的相对目录
* 具体参考[相关说明](https://github.com/ccf-2012/plex_notify#%E9%85%8D%E5%90%88torcp%E4%BD%BF%E7%94%A8)

