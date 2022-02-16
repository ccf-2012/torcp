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
import glob

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


def isMediaFileType(file_ext):
    return file_ext.lower() in ['.mkv', '.mp4']


def copyTVSeasonItems(tvSourceFullPath, tvFolder, seasonFolder, groupName):
    if os.path.isdir(os.path.join(tvSourceFullPath, 'BDMV')):
        # break, process BDMV dir for this dir
        bdmvTVFolder = os.path.join(tvFolder, seasonFolder)
        processBDMV(tvSourceFullPath, bdmvTVFolder, 'TV')
        return

    for tv2item in os.listdir(tvSourceFullPath):
        tv2itemPath = os.path.join(tvSourceFullPath, tv2item)
        if os.path.isdir(tv2itemPath):
            print('\033[31mSKIP dir in TV: [%s]\033[0m ' % tv2itemPath)
        else:
            filename, file_ext = os.path.splitext(tv2item)
            if isMediaFileType(file_ext):
                seasonFolderFullPath = os.path.join('TV', tvFolder,
                                                    seasonFolder)
                if ARGS.origin_name:
                    newTVFileName = os.path.basename(tv2item)
                else:
                    newTVFileName = genTVSeasonEpisonGroup(tv2item, groupName)
                targetCopy(tv2itemPath, seasonFolderFullPath, newTVFileName)
            elif file_ext.lower() in ['.iso']:
                # TODO: aruba need iso when extract_bdmv
                if ARGS.full_bdmv or ARGS.extract_bdmv:
                    targetCopy(tv2itemPath, seasonFolderFullPath)


def uselessFile(entryName):
    return entryName in ['@eaDir', '.DS_Store', '.@__thumb']


def genTVSeasonEpisonGroup(mediaFilename, groupName):
    tvTitle, tvYear, tvSeason, tvEpisode, cntitle = parseMovieName(
        mediaFilename)

    filename, file_ext = os.path.splitext(mediaFilename)
    return tvTitle + ' ' + (tvSeason.upper() if tvSeason else '') + (
        tvEpisode.upper() if tvEpisode else '') + (
            (' - ' + groupName) if groupName else '') + file_ext


def getMediaFile(filePath):
    types = ('*.mkv', '*.mp4')
    files_grabbed = []
    curdir = os.getcwd()
    os.chdir(filePath)
    for files in types:
        files_grabbed.extend(glob.glob(files))
    os.chdir(curdir)
    if files_grabbed:
        return os.path.basename(files_grabbed[0])
    else:
        return None


def fixSeasonGroupWithFilename(folderPath, folderSeason, folderGroup):
    season = folderSeason
    group = folderGroup
    testFile = getMediaFile(folderPath)
    if testFile:
        cat, fileGroup, resolution = getCategory(testFile)
        parseTitle, parseYear, parseSeason, parseEpisode, cntitle = parseMovieName(
            testFile)

        if cat != 'TV':
            print('\033[33mWarn, is this TV? :  %s \033[0m' % testFile)
            print('\033[33Process anyway ... \033[0m')
        if not folderGroup:
            group = fileGroup
        if not folderSeason:
            season = parseSeason
        if not season:
            season = 'S01'
    return season, group


def copyTVFolderItems(tvSourceFolder, genFolder, folderSeason, groupName):
    if os.path.islink(tvSourceFolder):
        print('\033[31mSKIP symbolic link: [%s]\033[0m ' % tvSourceFolder)
        return
    if os.path.isdir(os.path.join(tvSourceFolder, 'BDMV')):
        # a BDMV dir in a TV folder, treat as Movie
        processBDMV(tvSourceFolder, genFolder, 'MovieM2TS')
        return

    parseSeason, parseGroup = fixSeasonGroupWithFilename(
        tvSourceFolder, folderSeason, groupName)

    for tvitem in os.listdir(tvSourceFolder):
        if uselessFile(tvitem):
            print('\033[34mSKIP useless file: [%s]\033[0m ' % tvitem)
            continue

        tvitemPath = os.path.join(tvSourceFolder, tvitem)
        if os.path.isdir(tvitemPath):
            seasonFolder = getSeasonFromFolderName(tvitem, failDir=parseSeason)
            copyTVSeasonItems(tvitemPath, genFolder, seasonFolder, parseGroup)
        else:
            filename, file_ext = os.path.splitext(tvitemPath)
            if isMediaFileType(tvitemPath):
                if ARGS.origin_name:
                    newTVFileName = os.path.basename(tvitemPath)
                else:
                    newTVFileName = genTVSeasonEpisonGroup(tvitem, parseGroup)
                seasonFolderFullPath = os.path.join('TV', genFolder,
                                                    parseSeason)
                targetCopy(tvitemPath, seasonFolderFullPath, newTVFileName)


def copyFiles(fromDir, toDir):
    if os.path.islink(fromDir):
        print('\033[31mSKIP symbolic link: [%s]\033[0m ' % fromDir)
        return
    for movieItem in os.listdir(fromDir):
        movieFullPath = os.path.join(fromDir, movieItem)
        targetCopy(movieFullPath, toDir)


def genMovieResGroup(mediaSrc, movieName, year, resolution, group):
    filename, file_ext = os.path.splitext(mediaSrc)
    ch1 = ' - ' if (resolution or group) else ''
    ch2 = '_' if (resolution and group) else ''
    return movieName + ((' (' + year + ')') if year else '') + ch1 + (
        resolution if resolution else '') + ch2 + (group
                                                   if group else '') + file_ext


def getLargestFiles(dirName):
    fileSizeTupleList = []
    largestSize = 0
    largestFiles = []

    for i in os.listdir(dirName):
        p = os.path.join(dirName, i)
        if os.path.isfile(p):
            fileSizeTupleList.append((p, os.path.getsize(p)))

    if len(fileSizeTupleList) > 0:
        fileSizeTupleList.sort(key=lambda x: x[1], reverse=True)

        a, largestSize = fileSizeTupleList[0]
        for fileName, fileSize in fileSizeTupleList:
            if fileSize > (largestSize * 0.6):
                largestFiles.append(fileName)
        return largestFiles
    else:
        return []


def getCategory(itemName):
    catutil = GuessCategoryUtils()
    cat, group = catutil.guessByName(itemName)
    if ARGS.tv:
        cat = 'TV'
    elif ARGS.movie:
        cat = 'Movie'
    else:
        if cat == 'Movie4K':
            cat = 'MovieEncode'
        elif cat == 'MovieWeb4K':
            cat = 'MovieWebdl'
        elif cat == 'MovieBDMV4K':
            cat = 'MovieBDMV'
    return cat, group, catutil.resolution


def isCollections(folderName):
    return re.search(r'\b(Pack$|合集|Collections?|国语配音4K动画电影$)',
                     folderName,
                     flags=re.I)


def fixSeasonName(seasonStr):
    if re.match(r'^Ep?\d+(-Ep?\d+)?$', seasonStr, flags=re.I) or not seasonStr:
        return 'S01'
    else:
        return seasonStr.upper()


def processBDMV(mediaSrc, folderGenName, catFolder):
    if ARGS.full_bdmv:
        destCatFolderName = os.path.join(catFolder, folderGenName)
        for bdmvItem in os.listdir(mediaSrc):
            fullBdmvItem = os.path.join(mediaSrc, bdmvItem)
            targetCopy(fullBdmvItem, destCatFolderName)
        return

    if ARGS.extract_bdmv:
        bdmvDir = os.path.join(mediaSrc, 'BDMV', 'STREAM')
        if not os.path.isdir(bdmvDir):
            print('\033[31m BDMV/STREAM/ dir not found in   %s \033[0m' %
                  mediaSrc)
            return

        largestStreams = getLargestFiles(bdmvDir)
        for stream in largestStreams:
            # fn, ext = os.path.splitext(stream)
            tsname = os.path.basename(mediaSrc) + ' - ' + os.path.basename(
                stream)
            targetCopy(stream, os.path.join(catFolder, folderGenName), tsname)
    else:
        print('\033[31mSkip BDMV/ISO  %s \033[0m' % mediaSrc)


def processMovieDir(mediaSrc, folderCat, folderGenName):
    if os.path.isdir(os.path.join(mediaSrc, 'BDMV')):
        # break, process BDMV dir for this dir
        processBDMV(mediaSrc, folderGenName, 'MovieM2TS')
        return

    for movieItem in os.listdir(mediaSrc):
        if uselessFile(movieItem):
            print('\033[34mSKIP useless file: [%s]\033[0m ' % movieItem)
            continue
        if (os.path.isdir(os.path.join(mediaSrc, movieItem))):
            # Dir in movie folder
            if os.path.isdir(os.path.join(mediaSrc, movieItem, 'BDMV')):
                processBDMV(os.path.join(mediaSrc, movieItem),
                            os.path.join(folderGenName, movieItem),
                            'MovieM2TS')
            else:
                print('\033[34mSKip dir in movie folder: [%s]\033[0m ' %
                      movieItem)
            continue

        filename, file_ext = os.path.splitext(movieItem)
        if file_ext.lower() in ['.iso']:
            # TODO: aruba need iso when extract_bdmv
            if ARGS.full_bdmv or ARGS.extract_bdmv:
                destCatFolderName = os.path.join('BDMVISO', folderGenName)
                targetCopy(os.path.join(mediaSrc, movieItem),
                           destCatFolderName)
            else:
                print('\033[31mSKip iso file: [%s]\033[0m ' % movieItem)
            continue

        if not isMediaFileType(movieItem):
            print('\033[34mSkip : %s \033[0m' % movieItem)
            continue

        cat, group, resolution = getCategory(movieItem)
        parseTitle, parseYear, parseSeason, parseEpisode, cntitle = parseMovieName(
            movieItem)
        if parseSeason and (cat != 'TV'):
            print('Category fixed: ' + movieItem)
            cat = 'TV'

        # movieCatList = ['MovieEncode', 'MovieWebdl', 'MovieRemux', 'Movie', 'TV']
        # if (cat not in movieCatList) and (folderCat not in movieCatList):
        #     # since it's a .mkv(mp4) file, no x264/5, not tv and no BDMV dir
        #     print('\033[33mMaybe remux? : %s \033[0m' % movieItem)
        #     cat = 'MovieRemux'

        destFolderName = genMediaFolderName(cat, parseTitle, parseYear,
                                            parseSeason)
        destCatFolderName = os.path.join(cat, destFolderName)

        if cat == 'TV':
            print('\033[31mMiss Categoried TV: [%s]\033[0m ' % mediaSrc)
            parseSeason = fixSeasonName(parseSeason)
            if cat != folderCat:
                copyTVFolderItems(mediaSrc, destFolderName, parseSeason, group)
            else:
                copyTVFolderItems(mediaSrc, folderGenName, parseSeason, group)
            return

        if ARGS.origin_name:
            newMovieName = os.path.basename(movieItem)
        else:
            newMovieName = genMovieResGroup(movieItem, parseTitle, parseYear,
                                            resolution, group)
        mediaSrcItem = os.path.join(mediaSrc, movieItem)
        targetCopy(mediaSrcItem, destCatFolderName, newMovieName)


def processOneDirItem(cpLocation, itemName):
    mediaSrc = os.path.join(cpLocation, itemName)
    if os.path.islink(mediaSrc):
        print('\033[31mSKIP symbolic link: [%s]\033[0m ' % mediaSrc)
        return

    cat, group, resolution = getCategory(itemName)
    parseTitle, parseYear, parseSeason, parseEpisode, cntitle = parseMovieName(
        itemName)
    if parseSeason and cat != 'TV':
        print('Category fixed: ' + itemName)
        cat = 'TV'
    if cat == 'TV':
        parseSeason = fixSeasonName(parseSeason)
    destFolderName = genMediaFolderName(cat, parseTitle, parseYear,
                                        parseSeason)
    destCatFolderName = os.path.join(cat, destFolderName)

    if os.path.isfile(mediaSrc):
        filename, file_ext = os.path.splitext(itemName)
        if isMediaFileType(itemName):
            if cat == 'TV':
                print('\033[33mSingle Episode file?  %s \033[0m' % mediaSrc)
                if ARGS.origin_name:
                    newTVFileName = itemName
                else:
                    newTVFileName = genTVSeasonEpisonGroup(itemName, group)
                seasonFolderFullPath = os.path.join('TV', destFolderName,
                                                    parseSeason)
                targetCopy(mediaSrc, seasonFolderFullPath, newTVFileName)
            elif cat in ['MovieEncode', 'MovieWebdl', 'MovieRemux']:
                if ARGS.origin_name:
                    newMovieName = itemName
                else:
                    newMovieName = genMovieResGroup(mediaSrc, parseTitle,
                                                    parseYear, resolution,
                                                    group)
                targetCopy(mediaSrc, destCatFolderName, newMovieName)
            elif cat in ['MovieBDMV']:
                # since it's a .mkv(mp4) file, no x264/5, not tv and no BDMV dir
                print('\033[33mMaybe remux? : %s \033[0m' % itemName)
                targetCopy(mediaSrc, os.path.join('MovieRemux',
                                                  destFolderName))
            else:
                print('\033[33mSingle media file : [ %s ] %s \033[0m' %
                      (cat, mediaSrc))
                targetCopy(mediaSrc, destCatFolderName)
        elif file_ext.lower() in ['.iso']:
            #  TODO: aruba need iso when extract_bdmv
            if ARGS.full_bdmv or ARGS.extract_bdmv:
                bdmvFolder = os.path.join('BDMVISO', destFolderName)
                targetCopy(mediaSrc, bdmvFolder)
            else:
                print('\033[33mSkip .iso file:  %s \033[0m' % mediaSrc)
        else:
            print('\033[34mSkip file:  %s \033[0m' % mediaSrc)
    else:
        if cat == 'TV':
            copyTVFolderItems(mediaSrc, destFolderName, parseSeason, group)
        elif cat in ['MovieEncode', 'MovieWebdl']:
            processMovieDir(mediaSrc, cat, destFolderName)
        # TODO: merge
        elif cat in ['MovieBDMV', 'MovieRemux']:
            processMovieDir(mediaSrc, cat, destFolderName)
        elif cat in ['MV']:
            targetCopy(mediaSrc, cat)
        elif cat in ['eBook', 'Music', 'Audio', 'HDTV']:
            print('\033[33mSkip eBoook, Music, Audio, HDTV: [%s], %s\033[0m ' %
                  (cat, mediaSrc))
            # if you don't want to skip these, comment up and uncomment below
            # targetCopy(mediaSrc, cat)
        else:
            print('\033[33mDir treat as movie folder: [ %s ], %s\033[0m ' %
                  (cat, mediaSrc))
            processMovieDir(mediaSrc, cat, destFolderName)


def loadArgs():
    parser = argparse.ArgumentParser(
        description=
        'torcp: a script hardlink media files and directories in Emby-happy naming and structs.'
    )
    parser.add_argument(
        'MEDIA_DIR',
        help='The directory contains TVs and Movies to be copied.')
    parser.add_argument('-d',
                        '--hd_path',
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
    parser.add_argument('--extract-bdmv',
                        action='store_true',
                        help='extract largest file in BDMV dir.')
    parser.add_argument('--full-bdmv',
                        action='store_true',
                        help='copy full BDMV dir and iso files.')
    parser.add_argument('--origin-name',
                        action='store_true',
                        help='keep origin file name.')

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
                print('\033[35mProcess collections: %s \033[0m' %
                      torFolderItem)
                packDir = os.path.join(cpLocation, torFolderItem)
                for fn in os.listdir(packDir):
                    processOneDirItem(packDir, fn)
            else:
                processOneDirItem(cpLocation, torFolderItem)


if __name__ == '__main__':
    # # uncomment this to show rclone messages
    # logging.basicConfig(level=logging.DEBUG)
    main()
