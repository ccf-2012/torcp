"""
A script hardlink media files and directories in Emby-happy naming and structs.
"""
#  Usage:
#   python3 torcp.py -h
#
#  Example: hard link to a seperate dir
#    python3 torcp.py /home/ccf2012/Downloads/  -d=/home/ccf2012/emby/
#
#
import re
import os
import argparse
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
        if not season:
            season = 'S01'
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

def uselessFile(entryName):
    return entryName in ['@eaDir', '.DS_Store']

def copyTVFolderItems(tvSourceFolder, genFolder, parseSeason):
    if os.path.islink(tvSourceFolder):
        print('\033[31mSKIP symbolic link: [%s]\033[0m ' % tvSourceFolder)
        return
    # breakpoint()
    if not parseSeason:
        parseSeason = 'S01'
    for tvitem in os.listdir(tvSourceFolder):
        if uselessFile(tvitem):
            print('\033[31mSKIP useless file: [%s]\033[0m ' % tvitem)
            continue
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


def genMovieResGroup(mediaSrc, movieName, year, resolution, group):
    filename, file_ext = os.path.splitext(mediaSrc)
    return movieName + ((' (' + year +')') if year else '') + ' - ' + ((resolution + '_') if resolution else '') + (group if group else '') + file_ext


# def copyMovieFolderItems(movieSourceFolder, movieTargeDir):
#     copyFiles(movieSourceFolder, movieTargeDir)

# def isTVFilename(filename):
#     cat, group, resolution = getCategory(filename)
#     return cat == 'TV'


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

def isCollections(folderName):
    return re.search(r'\b(Pack$|Collection$|国语配音4K动画电影$|movies? collections?)', folderName, flags=re.I)

def fixSeasonName(seasonStr):
    if re.match(r'^Ep?\d+(-Ep?\d+)?$', seasonStr, flags=re.I) or not seasonStr:
        return 'S01'
    else:
        return seasonStr

    
def processMovieDir(mediaSrc, folderCat, folderGenName):
    for movieItem in os.listdir(mediaSrc):
        if uselessFile(movieItem):
            continue
        # destCatFolderName = os.path.join('MovieBDMV', os.path.basename(os.path.normpath(mediaSrc)))
        if (os.path.isdir(os.path.join(mediaSrc, movieItem))):
            if movieItem == 'BDMV':
                targetCopy(mediaSrc, 'MovieBDMV')
                return
            continue

        filename, file_ext = os.path.splitext(movieItem)
        if file_ext.lower() in ['.iso']:
            print('\033[34miso file: [%s]\033[0m ' % movieItem)
            targetCopy(mediaSrc, 'MovieBDMV')
            continue

        if file_ext.lower() not in ['.mkv', '.mp4']:
            continue

        # mediaFilePath = getLargestFile(mediaSrc)
        cat, group, resolution = getCategory(movieItem)
        parseTitle, parseYear, parseSeason, cntitle = parseMovieName(movieItem)
        if parseSeason and cat != 'TV':
            print('Category fixed: '+movieItem)
            cat = 'TV'

        destFolderName = genMediaFolderName(cat, parseTitle, parseYear,
                                            parseSeason)
        destCatFolderName = os.path.join(cat, destFolderName)


        if cat == 'TV':
            print('\033[31mMiss Categoried TV: [%s]\033[0m ' % mediaSrc)
            parseSeason = fixSeasonName(parseSeason)
            copyTVFolderItems(mediaSrc, folderGenName, parseSeason)
            return

        cat = folderCat
        newMovieName = genMovieResGroup(
            movieItem, parseTitle, parseYear, resolution, group)
        mediaSrcItem = os.path.join(mediaSrc, movieItem)
        targetCopy(mediaSrcItem, destCatFolderName, newMovieName)


def processOneDirItem(cpLocation, itemName):
    mediaSrc = os.path.join(cpLocation, itemName)
    if os.path.islink(mediaSrc):
        print('\033[31mSKIP symbolic link: [%s]\033[0m ' % mediaSrc)
        return

    cat, group, resolution = getCategory(itemName)
    parseTitle, parseYear, parseSeason, cntitle = parseMovieName(itemName)
    if parseSeason and cat != 'TV':
        print('Category fixed: '+itemName)
        cat = 'TV'
    if cat == 'TV':
        parseSeason = fixSeasonName(parseSeason)
    destFolderName = genMediaFolderName(cat, parseTitle, parseYear,
                                        parseSeason)
    destCatFolderName = os.path.join(cat, destFolderName)
        
    if os.path.isfile(mediaSrc):
        filename, file_ext = os.path.splitext(itemName)
        if file_ext in ['.mkv', '.mp4']:
            if cat == 'TV':
                print('\033[33mSingle Episode file?  %s \033[0m' % mediaSrc)
                targetCopy(mediaSrc, destCatFolderName)
            elif cat in ['MovieEncode', 'MovieWebdl']:
                newMovieName = genMovieResGroup(
                    mediaSrc, parseTitle, parseYear, resolution, group)
                targetCopy(mediaSrc, destCatFolderName, newMovieName)
            else:
                print('\033[31mWhat\'s this?  %s \033[0m' % mediaSrc)
                targetCopy(mediaSrc, destCatFolderName)
        else:
            print('\033[33mCopy *.mkv & *.mp4 only: %s \033[0m' % mediaSrc)
    else:
        if cat == 'TV':
            copyTVFolderItems(mediaSrc, destFolderName, parseSeason)
        elif cat in ['MovieEncode', 'MovieWebdl']:
            processMovieDir(mediaSrc, cat, destFolderName)
        elif cat in ['MovieBDMV', 'MV']:
            targetCopy(mediaSrc, cat)
        else:
            print('\033[33mWARN, treat as movie folder: [%s], %s\033[0m ' % (cat, mediaSrc))
            processMovieDir(mediaSrc, cat, destFolderName)




def loadArgs():
    parser = argparse.ArgumentParser(
        description='torcp: a script hardlink media files and directories in Emby-happy naming and structs.'
    )
    parser.add_argument(
        'MEDIA_DIR',
        help='The directory contains TVs and Movies to be copied.')
    parser.add_argument('-d', '--hd_path',
                        help='the dest path to create Hard Link.')
    parser.add_argument('--tv',
                        action='store_true',
                        help='specify the src directory is TV.')
    parser.add_argument('--movie',
                        action='store_true',
                        help='specify the src directory is Movie.')
    parser.add_argument('--dryrun',
                        action='store_true',
                        help='print message instead of real copy.')
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
            if uselessFile(torFolderItem):
                continue
            if isCollections(torFolderItem):
                print('\033[35mProcess collections: %s \033[0m' % torFolderItem)
                packDir = os.path.join(cpLocation, torFolderItem)
                for fn in os.listdir(packDir):
                    processOneDirItem(packDir, fn)
            else:
                processOneDirItem(cpLocation, torFolderItem)


if __name__ == '__main__':
    # # uncomment this to show rclone messages
    # logging.basicConfig(level=logging.DEBUG)
    main()
