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

ARGS = None


def ensureDir(file_path):
    if os.path.isfile(file_path):
        file_path = os.path.dirname(file_path)
    if not os.path.exists(file_path):
        os.makedirs(file_path)


def hdlinkCopy(fromLoc, toLocPath, toLocFile=''):
    if os.path.islink(fromLoc):
        print('\033[31mSKIP symbolic link: [%s]\033[0m ' % fromLoc)
        return
    destDir = os.path.join(ARGS.hd_path, toLocPath)
    ensureDir(destDir)
    if os.path.isfile(fromLoc):
        if toLocFile:
            destFile = os.path.join(destDir, toLocFile)
        else:
            destFile = os.path.join(destDir, os.path.basename(fromLoc))
        if not os.path.exists(destFile):
            print('ln ', fromLoc, destFile)
            os.link(fromLoc, destFile)
    else:
        destDir = os.path.join(destDir, os.path.basename(fromLoc))
        if not os.path.exists(destDir):
            print('copytree ', fromLoc, destDir)
            shutil.copytree(fromLoc, destDir, copy_function=os.link)


def hdlinkLs(loc):
    destDir = os.path.join(ARGS.hd_path, loc)
    ensureDir(destDir)
    return os.listdir(destDir)


def targetCopy(fromLoc, toLocPath, toLocFile=''):
    if os.path.islink(fromLoc):
        print('\033[31mSKIP symbolic link: [%s]\033[0m ' % fromLoc)
        return

    if ARGS.dryrun:
        print(fromLoc, ' ==> ', toLocPath)
        return

    if ARGS.hd_path:
        hdlinkCopy(fromLoc, toLocPath, toLocFile)



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
    if os.path.islink(tvSourceFolder):
        print('\033[31mSKIP symbolic link: [%s]\033[0m ' % tvSourceFolder)
        return
    for tvitem in os.listdir(tvSourceFolder):
        tvitemPath = os.path.join(tvSourceFolder, tvitem)
        if os.path.isdir(tvitemPath):
            seasonFolder = getSeasonFromFolderName(tvitem, failDir=parseSeason)
            copyTVSeasonItems(tvitemPath, genFolder, seasonFolder)
        else:
            seasonFolderFullPath = os.path.join('TV', genFolder, parseSeason)
            targetCopy(tvitemPath, seasonFolderFullPath)


def copyFiles(fromDir, toDir):
    if os.path.islink(fromDir):
        print('\033[31mSKIP symbolic link: [%s]\033[0m ' % fromDir)
        return
    for movieItem in os.listdir(fromDir):
        movieFullPath = os.path.join(fromDir, movieItem)
        targetCopy(movieFullPath, toDir)

def genMovieResGroup(mediaSrc, movieName, resolution, group):
    filename, file_ext = os.path.splitext(mediaSrc)
    return movieName + ' - ' + ((resolution+ '_') if resolution else '')  + (group if group else '') + file_ext

def copyMovieFolderItems(movieSourceFolder, movieTargeDir):
    copyFiles(movieSourceFolder, movieTargeDir)


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


def getCategory(itemName):
    catutil = GuessCategoryUtils()
    if ARGS.tv or ARGS.movie:
        if ARGS.tv:
            cat = 'TV'
        elif ARGS.movie:
            cat = 'Movie'
    else:
        cat, group = catutil.guessByName(itemName)
        if cat == 'Movie4K':
            cat = 'MovieEncode'
        elif cat == 'MovieWeb4K':
            cat = 'MovieWebdl'
        elif cat == 'MovieBDMV4K':
            cat = 'MovieBDMV'
    return cat, catutil.group, catutil.resolution


def fixSeasonName(seasonStr):
    return re.sub(r'^Ep?\d+-Ep?\d+$', 'S01', seasonStr, re.I)


def processOneDirItem(cpLocation, itemName):
    cat, group, resolution = getCategory(itemName)
    parseTitle, parseYear, parseSeason, cntitle = parseMovieName(itemName)
    if parseSeason and cat != 'TV':
        print('Category fixed: '+itemName)
        cat = 'TV'
    parseSeason = fixSeasonName(parseSeason)

    mediaFolderName = genMediaFolderName(cat, parseTitle, parseYear,
                                         parseSeason)
    mediaSrc = os.path.join(cpLocation, itemName)
    mediaTargeDir = os.path.join(cat, mediaFolderName)
    if cat == 'TV':
        if os.path.isfile(mediaSrc):
            targetCopy(mediaSrc, mediaTargeDir)
        else:
            copyTVFolderItems(os.path.join(cpLocation, itemName),
                              mediaFolderName, parseSeason)
    elif cat in ['MovieEncode', 'MovieWebdl']:
        # mediaTargetFile = os.path.join(mediaTargeDir, newMovieName)
        if os.path.isfile(mediaSrc):
            newMovieName = genMovieResGroup(mediaSrc, parseTitle, resolution, group)
            targetCopy(mediaSrc, mediaTargeDir, newMovieName)
        elif os.path.isdir(mediaSrc):
            mediaFilePath = getLargestFile(mediaSrc)
            if mediaFilePath:
                filename, file_ext = os.path.splitext(mediaFilePath)
                if file_ext in ['.mkv', '.mp4']:
                    newMovieName = genMovieResGroup(mediaFilePath, parseTitle, resolution, group)
                    targetCopy(mediaFilePath, mediaTargeDir, newMovieName)
                else:
                    print('\033[31mOnly copy *.mkv & *.mp4 : %s \033[0m' % mediaFilePath)
            else:
                print('\033[31mNo file found in: %s \033[0m' % mediaSrc)
        else:
            print('\033[31mWhat\'s it?  %s \033[0m' % mediaSrc)


    elif cat in [ 'MovieBDMV', 'MovieBDMV4K', 'MV' ]:
        if os.path.isfile(mediaSrc):
            targetCopy(mediaSrc, mediaTargeDir)
        else:
            copyMovieFolderItems(mediaSrc, mediaTargeDir)
    else:
        print('\033[33mSKIP: [%s], %s\033[0m ' % (cat, mediaSrc))


def loadArgs():
    parser = argparse.ArgumentParser(
        description=
        'torcp: a script to organize media files in Emby-happy way, support hardlink and rclone.'
    )
    parser.add_argument(
        'MEDIA_DIR',
        help='The directory contains TVs and Movies to be copied.')
    parser.add_argument('--hd_path', help='the dest path to create Hard Link.')
    parser.add_argument('--tv',
                        action='store_true',
                        help='specify the src directory is TV.')
    parser.add_argument('--movie',
                        action='store_true',
                        help='specify the src directory is Movie.')
    parser.add_argument('--dryrun',
                        action='store_true',
                        help='print msg instead of real copy.')
    parser.add_argument('--single',
                        '-s',
                        action='store_true',
                        help='parse and copy one single folder.')

    global ARGS
    ARGS = parser.parse_args()


def main():
    loadArgs()
    cpLocation = ARGS.MEDIA_DIR
    cpLocation = os.path.abspath(cpLocation)

    if ARGS.single:
        processOneDirItem(os.path.dirname(cpLocation),
                          os.path.basename(os.path.normpath(cpLocation)))
    else:
        for torFolderItem in os.listdir(cpLocation):
            processOneDirItem(cpLocation, torFolderItem)


if __name__ == '__main__':
    # # uncomment this to show rclone messages
    # logging.basicConfig(level=logging.DEBUG)
    main()
