"""
A script hardlink/rclone copy media files and directories in Emby-happy naming and structs.
"""
#  Usage:
#   python3 torcp.py -h
#
#  Example 1, rclone copy to a gd drive
#   python3 torcp.py  /home/ccf2012/Downloads/  --gd_path=gd123:/176/
#
#  Example 2, hard link to a seperate dir
#    python3 torcp.py /home/ccf2012/Downloads/  --hd_path=/home/ccf2012/emby/
#
#
import re
import os
import argparse
import rclone
import shutil
from torcategory import GuessCategoryUtils
from tortitle import parseMovieName
import logging

g_args = None


def ensureDir(file_path):
    if os.path.isfile(file_path):
        file_path = os.path.dirname(file_path)
    if not os.path.exists(file_path):
        os.makedirs(file_path)


def hdlinkCopy(fromLoc, toLoc):
    destDir = os.path.join(g_args.hd_path, toLoc)
    ensureDir(destDir)
    if os.path.isfile(fromLoc):
        destFile = os.path.join(destDir, os.path.basename(fromLoc))
        print('ln ', fromLoc, destFile)
        if not os.path.exists(destFile):
            os.link(fromLoc, destFile)
    else:
        destDir = os.path.join(destDir, os.path.basename(fromLoc))
        print('copytree ', fromLoc, destDir)
        if not os.path.exists(destDir):
            shutil.copytree(fromLoc, destDir, copy_function=os.link)


def hdlinkLs(loc):
    destDir = os.path.join(g_args.hd_path, loc)
    ensureDir(destDir)
    return os.listdir(destDir)


def targetCopy(fromLoc, toLoc):
    if g_args.hd_path:
        hdlinkCopy(fromLoc, toLoc)
    elif g_args.gd_path:
        rcloneCopy(fromLoc, toLoc)


def rcloneCopy(fromLoc, toLoc):
    print('rclone copy ', fromLoc, g_args.gd_path + toLoc)

    if g_args.gd_flags:
        flagList = g_args.gd_flags.split(' ')
    result = ''
    if not g_args.dryrun:
        with open(g_args.gd_conf) as f:
            cfg = f.read()
        result = rclone.with_config(cfg).copy(fromLoc,
                                              g_args.gd_path + toLoc,
                                              flags=flagList)
    return result


def rcloneLs(loc):
    if not g_args.gd_path:
        print('forgot --gd_path?')
        return ''

    with open(g_args.gd_conf) as f:
        cfg = f.read()

    try:
        dirStr = rclone.with_config(cfg).lsd(g_args.gd_path +
                                             loc)['out'].decode("utf-8")
        dirlist = re.sub(r' +-1\s\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\s+-1\s',
                         '', dirStr).split('\n')
    except:
        dirlist = ''
    return dirlist


def getSeasonFromFolderName(folderName, failDir=''):
    m1 = re.search(r'(\bS\d+(-S\d+)?)\b', folderName, flags=re.A | re.I)
    if m1:
        return m1.group(1)
    else:
        return folderName
        # return failDir


def genMediaFolderName(cat, title, year, season):
    if cat == 'TV':
        if len(year) == 4 and season == 'S01':
            mediaFolderName = title + ' (' + year + ')'
        else:
            mediaFolderName = title
    else:
        if len(year) == 4:
            mediaFolderName = title + ' (' + year + ')'
        else:
            mediaFolderName = title
    return mediaFolderName


def copyTVSeasonItems(tvSourceFullPath, tvFolder, seasonFolder):
    seasonFolderFullPath = os.path.join('TV', tvFolder, seasonFolder)
    for tv2item in os.listdir(tvSourceFullPath):
        tv2FullPath = os.path.join(tvSourceFullPath, tv2item)
        targetCopy(tv2FullPath, seasonFolderFullPath)


def copyTVFolderItems(tvSourceFolder, genFolder, parseSeason):
    for tvitem in os.listdir(tvSourceFolder):
        tvitemPath = os.path.join(tvSourceFolder, tvitem)
        if os.path.isdir(tvitemPath):
            seasonFolder = getSeasonFromFolderName(tvitem, failDir=parseSeason)
            copyTVSeasonItems(tvitemPath, genFolder, seasonFolder)
        else:
            seasonFolderFullPath = os.path.join('TV', genFolder, parseSeason)
            targetCopy(tvitemPath, seasonFolderFullPath)


def copyMovieFolderItems(movieSourceFolder, movieTargeDir):
    if g_args.largest:
        mediaFilePath = getLargestFile(movieSourceFolder)
        targetCopy(mediaFilePath, movieTargeDir)
    else:
        for movieItem in os.listdir(movieSourceFolder):
            movieFullPath = os.path.join(movieSourceFolder, movieItem)
            targetCopy(movieFullPath, movieTargeDir)


def getLargestFile(dirName):
    fileSizeTupleList = []
    largestSize = 0
    largestFile = None

    for i in os.listdir(dirName):
        p = os.path.join(dirName, i)
        if os.path.isfile(p):
            fileSizeTupleList.append((p, os.path.getsize(p)))

    for fileName, fileSize in fileSizeTupleList:
        if fileSize > largestSize:
            largestSize = fileSize
            largestFile = fileName
    return largestFile


def processOneDirItem(cpLocation, itemName):
    cat, group = GuessCategoryUtils.guessByName(itemName)
    parseTitle, parseYear, parseSeason, cntitle = parseMovieName(itemName)
    parseSeason = re.sub(r'^Ep?\d+-Ep?\d+$', 'S01', parseSeason, re.I)

    mediaFolderName = genMediaFolderName(cat, parseTitle, parseYear,
                                         parseSeason)
    mediaSrc = os.path.join(cpLocation, itemName)
    mediaTargeDir = os.path.join(cat, mediaFolderName)
    if cat == 'TV':
        if g_args.append or g_args.single or (mediaFolderName
                                              not in g_gd_tv_list):
            if os.path.isfile(mediaSrc):
                targetCopy(mediaSrc, mediaTargeDir)
            else:
                copyTVFolderItems(os.path.join(cpLocation, itemName),
                                  mediaFolderName, parseSeason)
    elif cat == 'MovieEncode':
        if g_args.single or (mediaFolderName not in g_gd_movie_list):
            if os.path.isfile(mediaSrc):
                targetCopy(mediaSrc, mediaTargeDir)
            else:
                copyMovieFolderItems(mediaSrc, mediaTargeDir)
    # elif cat == 'MV':
    #     elseSrc = os.path.join(cpLocation, itemName)
    #     rcloneCopy(elseSrc, cat)


def loadArgs():
    parser = argparse.ArgumentParser(
        description=
        'A script copies Movies and TVs to your rclone target, in Emby-happy struct.'
    )
    parser.add_argument(
        'MEDIA_DIR',
        help='The directory contains TVs and Movies to be copied.')
    parser.add_argument('--gd_conf',
                        help='the full path to the rclone config file.',
                        default=r'/root/.config/rclone/rclone.conf')
    parser.add_argument('--gd_path', help='the rclone target path.')
    parser.add_argument('--gd_flags', help='extra rclone flags.')
    parser.add_argument('--hd_path', help='the dest path to create Hard Link.')
    parser.add_argument('--append',
                        action='store_true',
                        help='try copy when dir exists.')
    parser.add_argument('--dryrun',
                        action='store_true',
                        help='print msg instead of real copy.')
    parser.add_argument('--single',
                        '-s',
                        action='store_true',
                        help='parse and copy one single folder.')
    parser.add_argument(
        '--largest',
        action='store_true',
        help='Movie only: copy the largest file, instead all files')

    global g_args
    g_args = parser.parse_args()


def main():
    loadArgs()
    cpLocation = g_args.MEDIA_DIR
    cpLocation = os.path.abspath(cpLocation)

    global g_gd_tv_list
    global g_gd_movie_list
    # global g_gd_mv_list
    if g_args.gd_path:
        g_gd_tv_list = rcloneLs('TV')
        g_gd_movie_list = rcloneLs('MovieEncode')
    elif g_args.hd_path:
        g_gd_tv_list = hdlinkLs('TV')
        g_gd_movie_list = hdlinkLs('MovieEncode')

    # g_gd_mv_list = rcloneLs('MV')
    if g_args.single:
        processOneDirItem(os.path.dirname(cpLocation),
                          os.path.basename(os.path.normpath(cpLocation)))
    else:
        for torFolderItem in os.listdir(cpLocation):
            processOneDirItem(cpLocation, torFolderItem)


if __name__ == '__main__':
    # uncomment this to show rclone messages
    # logging.basicConfig(level=logging.DEBUG)
    main()
