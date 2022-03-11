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
from tmdbparser import TMDbNameParser
import time

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
    if not ARGS.dryrun:
        ensureDir(destDir)
    if os.path.isfile(fromLoc):
        if toLocFile:
            destFile = os.path.join(destDir, toLocFile)
        else:
            destFile = os.path.join(destDir, os.path.basename(fromLoc))
        if not os.path.exists(destFile):
            if ARGS.dryrun:
                print(fromLoc, ' ==> ', destFile)
            else:
                print('ln ', fromLoc, destFile)
                os.link(fromLoc, destFile)
        else:
            print('\033[32mTarget Exists: [%s]\033[0m ' % destFile)

    elif os.path.isdir(fromLoc):
        destDir = os.path.join(destDir, os.path.basename(fromLoc))
        if not os.path.exists(destDir):
            if ARGS.dryrun:
                print('copytree' + fromLoc + ' ==> ' + destDir)
            else:
                print('copytree ', fromLoc, destDir)
                shutil.copytree(fromLoc, destDir, copy_function=os.link)
        else:
            print('\033[32mTarget Exists: [%s]\033[0m ' % destDir)
    else:
        print('File/Dir %s not found' % (fromLoc))


def pathMove(fromLoc, toLocFolder, toLocFile=''):
    if os.path.islink(fromLoc):
        print('\033[31mSKIP symbolic link: [%s]\033[0m ' % fromLoc)
        return
    destDir = os.path.join(ARGS.hd_path, toLocFolder)
    if not ARGS.dryrun:
        ensureDir(destDir)
        if ARGS.sleep:
            time.sleep(ARGS.sleep)
    if os.path.isfile(fromLoc):
        if toLocFile:
            destFile = os.path.join(destDir, toLocFile)
        else:
            destFile = os.path.join(destDir, os.path.basename(fromLoc))
        if not os.path.exists(destFile):
            if ARGS.dryrun:
                print(fromLoc, ' ==> ', destFile)
            else:
                print('mv ', fromLoc, destFile)
                os.rename(fromLoc, destFile)
        else:
            print('\033[32mTarget Exists: [%s]\033[0m ' % destFile)
    else:
        destDir = os.path.join(destDir, os.path.basename(fromLoc))
        if not os.path.exists(destDir):
            if ARGS.dryrun:
                print(fromLoc, ' ==> ', destDir)
            else:
                print('mvdir ', fromLoc, destDir)
                shutil.move(fromLoc, destDir)
        else:
            print('\033[32mTarget Exists: [%s]\033[0m ' % destDir)


def hdlinkLs(loc):
    destDir = os.path.join(ARGS.hd_path, loc)
    ensureDir(destDir)
    return os.listdir(destDir)


def targetCopy(fromLoc, toLocPath, toLocFile=''):
    if os.path.islink(fromLoc):
        print('\033[31mSKIP symbolic link: [%s]\033[0m ' % fromLoc)
        return

    if ARGS.move_run:
        pathMove(fromLoc, toLocPath, toLocFile)
    else:
        hdlinkCopy(fromLoc, toLocPath, toLocFile)


def getSeasonFromFolderName(folderName, failDir=''):
    m1 = re.search(r'(\bS\d+(-S\d+)?|第(\d+)季)', folderName, flags=re.A | re.I)
    if m1:
        if m1.group(3):
            return 'S' + m1.group(3)
        else:
            return m1.group(1)
    else:
        return folderName
        # return failDir


def genMediaFolderName(cat, title, year, season, tmdbid):
    #[tmdbid=509635]
    tmdbTail = ''
    if tmdbid > 0:
        if ARGS.emby_bracket:
            tmdbTail = ' [tmdbid='+str(tmdbid)+']'
        if ARGS.plex_bracket:
            tmdbTail = ' {tmdb-'+str(tmdbid)+'}'
        mediaFolderName = title + ' (' + year + ')' + tmdbTail
    else:
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
    return file_ext.lower() in KEEPEXTS


def copyTVSeasonItems(tvSourceFullPath, tvFolder, seasonFolder, groupName, resolution):
    if os.path.isdir(os.path.join(tvSourceFullPath, 'BDMV')):
        # break, process BDMV dir for this dir
        bdmvTVFolder = os.path.join(tvFolder, seasonFolder)
        processBDMV(tvSourceFullPath, bdmvTVFolder, 'TV')
        return

    catutil = GuessCategoryUtils()
    for tv2item in os.listdir(tvSourceFullPath):
        tv2itemPath = os.path.join(tvSourceFullPath, tv2item)
        if os.path.isdir(tv2itemPath):
            print('\033[31mSKIP dir in TV: [%s]\033[0m ' % tv2itemPath)
        else:
            filename, file_ext = os.path.splitext(tv2item)
            seasonFolderFullPath = os.path.join('TV', tvFolder, seasonFolder)
            if isMediaFileType(file_ext):
                if ARGS.origin_name:
                    newTVFileName = os.path.basename(tv2item)
                else:
                    if not groupName:
                        cat, groupName = catutil.guessByName(tv2item)
                        if not resolution:
                            resolution = catutil.resolution
                    newTVFileName = genTVSeasonEpisonGroup(tv2item, groupName, resolution)
                targetCopy(tv2itemPath, seasonFolderFullPath, newTVFileName)
            elif file_ext.lower() in ['.iso']:
                # TODO: aruba need iso when extract_bdmv
                if ARGS.full_bdmv or ARGS.extract_bdmv:
                    targetCopy(tv2itemPath, seasonFolderFullPath)


def uselessFile(entryName):
    return entryName in ['@eaDir', '.DS_Store', '.@__thumb']


def selfGenCategoryDir(dirName):
    return dirName in [
        'MovieEncode', 'MovieRemux', 'MovieWebdl', 'MovieBDMV', 'BDMVISO', 'Movie', 'TV'
    ]


def genTVSeasonEpisonGroup(mediaFilename, groupName, resolution):
    tvTitle, tvYear, tvSeason, tvEpisode, cntitle = parseMovieName(
        mediaFilename)

    filename, file_ext = os.path.splitext(mediaFilename)
    ch1 = ' - ' if (resolution or groupName) else ''
    ch2 = '_' if (resolution and groupName) else ''
    return tvTitle + ((' (' + tvYear + ')') if tvYear else '') + (
        ' ' + tvSeason.upper() if tvSeason else
        '') + (tvEpisode.upper() if tvEpisode else '') + ch1 + (
            resolution if resolution else '') + ch2 + (groupName if groupName
                                                       else '') + file_ext


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
        # cat, fileGroup, resolution = getCategory(testFile)
        # parseTitle, parseYear, parseSeason, parseEpisode, cntitle = parseMovieName(
        #     testFile)

        p = TMDbNameParser(ARGS.tmdb_api_key, ARGS.tmdb_lang)
        p.parse(testFile, TMDb=False)
        # if p.ccfcat != 'TV':
        #     print('\033[33mWarn, is this TV? :  %s \033[0m' % testFile)
        #     print('\033[33mProcess anyway ... \033[0m')

        if not folderGroup:
            group = p.group
        if not folderSeason:
            season = p.season
        if not season:
            season = 'S01'
    return season, group


def copyTVFolderItems(tvSourceFolder, genFolder, folderSeason, groupName, resolution):
    if os.path.islink(tvSourceFolder):
        print('\033[31mSKIP symbolic link: [%s]\033[0m ' % tvSourceFolder)
        return
    if os.path.isdir(os.path.join(tvSourceFolder, 'BDMV')):
        # a BDMV dir in a TV folder, treat as Movie
        processBDMV(tvSourceFolder, genFolder, 'MovieM2TS')
        return

    parseSeason, parseGroup = fixSeasonGroupWithFilename(
        tvSourceFolder, folderSeason, groupName)

    if not os.path.isdir(tvSourceFolder):
        return 

    for tvitem in os.listdir(tvSourceFolder):
        if uselessFile(tvitem):
            print('\033[34mSKIP useless file: [%s]\033[0m ' % tvitem)
            continue
        if selfGenCategoryDir(tvitem):
            print('\033[34mSKIP self-generated dir: [%s]\033[0m ' % tvitem)
            continue

        tvitemPath = os.path.join(tvSourceFolder, tvitem)
        if os.path.isdir(tvitemPath):
            seasonFolder = getSeasonFromFolderName(tvitem, failDir=parseSeason)
            copyTVSeasonItems(tvitemPath, genFolder, seasonFolder, parseGroup, resolution)
        else:
            filename, file_ext = os.path.splitext(tvitemPath)
            if isMediaFileType(file_ext):
                if ARGS.origin_name:
                    newTVFileName = os.path.basename(tvitemPath)
                else:
                    newTVFileName = genTVSeasonEpisonGroup(tvitem, parseGroup, resolution)
                seasonFolderFullPath = os.path.join('TV', genFolder,
                                                    parseSeason)
                targetCopy(tvitemPath, seasonFolderFullPath, newTVFileName)


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


# def getCategory(itemName):
#     catutil = GuessCategoryUtils()
#     cat, group = catutil.guessByName(itemName)
#     if ARGS.tv:
#         cat = 'TV'
#     elif ARGS.movie:
#         cat = 'Movie'
#     else:
#         if cat == 'Movie4K':
#             cat = 'MovieEncode'
#         elif cat == 'MovieWeb4K':
#             cat = 'MovieWebdl'
#         elif cat == 'MovieBDMV4K':
#             cat = 'MovieBDMV'
#     return cat, group, catutil.resolution

def setArgsCategory():
    cat = ''
    if ARGS.tv:
        # if parser.ccfcat != 'TV':
        #     print('\033[34mWarn: I don\'t think it is TV  %s \033[0m' % parser.title)
        cat = 'TV'
    elif ARGS.movie:
        # if parser.ccfcat not in ['MovieEncode', 'MovieWebdl', 'MovieRemux', 'MovieBDMV', 'MV']:
        #     print('\033[34mWarn: I don\'t think it is Movie  %s \033[0m' % parser.title)
        cat = 'Movie'
    return cat

def checkTMDbNotFound(parser):
    if  ARGS.tmdb_api_key and parser.tmdbid == 0:
        parser.ccfcat = 'TMDbNotFound'

def isCollections(folderName):
    return re.search(r'\b(Pack$|合集|Collections?|国语配音4K动画电影$)',
                     folderName,
                     flags=re.I)


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

    if not os.path.isdir(mediaSrc):
        return

    for movieItem in os.listdir(mediaSrc):
        if uselessFile(movieItem):
            print('\033[34mSKIP useless file: [%s]\033[0m ' % movieItem)
            continue
        if selfGenCategoryDir(movieItem):
            print('\033[34mSKIP self-generated dir: [%s]\033[0m ' % movieItem)
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

        if not isMediaFileType(file_ext):
            print('\033[34mSkip : %s \033[0m' % movieItem)
            continue

        # cat, group, resolution = getCategory(movieItem)
        # parseTitle, parseYear, parseSeason, parseEpisode, cntitle = parseMovieName( movieItem)
        # if parseSeason and (cat != 'TV'):
        #     print('Category fixed: ' + movieItem)
        #     cat = 'TV'
        cat = setArgsCategory()
        p = TMDbNameParser(ARGS.tmdb_api_key, ARGS.tmdb_lang, ccfcat_hard=cat)
        p.parse(movieItem, TMDb=(ARGS.tmdb_api_key is not None))
        checkTMDbNotFound(p)

        destFolderName = genMediaFolderName(p.ccfcat, p.title, str(p.year),
                                            p.season, p.tmdbid)
        destCatFolderName = os.path.join(p.ccfcat, destFolderName)

        if p.ccfcat == 'TV':
            print('\033[31mMiss Categoried TV: [%s]\033[0m ' % mediaSrc)
            # parseSeason = fixSeasonName(parseSeason)
            if p.ccfcat != folderCat:
                copyTVFolderItems(mediaSrc, destFolderName, p.season, p.group, p.resolution)
            else:
                copyTVFolderItems(mediaSrc, folderGenName, p.season, p.group, p.resolution)
            return

        if ARGS.origin_name:
            newMovieName = os.path.basename(movieItem)
        else:
            newMovieName = genMovieResGroup(movieItem, p.title, p.year,
                                            p.resolution, p.group)
        mediaSrcItem = os.path.join(mediaSrc, movieItem)
        targetCopy(mediaSrcItem, destCatFolderName, newMovieName)


def processOneDirItem(cpLocation, itemName):
    mediaSrc = os.path.join(cpLocation, itemName)
    if os.path.islink(mediaSrc):
        print('\033[31mSKIP symbolic link: [%s]\033[0m ' % mediaSrc)
        return

    # cat, group, resolution = getCategory(itemName)
    # parseTitle, parseYear, parseSeason, parseEpisode, cntitle = parseMovieName(
    #     itemName)
    cat = setArgsCategory()
    p = TMDbNameParser(ARGS.tmdb_api_key, ARGS.tmdb_lang, ccfcat_hard=cat)
    p.parse(itemName, TMDb=(ARGS.tmdb_api_key is not None))
    checkTMDbNotFound(p)   

    destFolderName = genMediaFolderName(p.ccfcat, p.title, str(p.year), p.season, p.tmdbid)
    destCatFolderName = os.path.join(p.ccfcat, destFolderName)

    if os.path.isfile(mediaSrc):
        filename, file_ext = os.path.splitext(itemName)
        if isMediaFileType(file_ext):
            if p.ccfcat == 'TV':
                print('\033[33mSingle Episode file?  %s \033[0m' % mediaSrc)
                if ARGS.origin_name:
                    newTVFileName = itemName
                else:
                    newTVFileName = genTVSeasonEpisonGroup(itemName, p.group, p.resolution)
                seasonFolderFullPath = os.path.join('TV', destFolderName,
                                                    p.season)
                targetCopy(mediaSrc, seasonFolderFullPath, newTVFileName)
            elif p.ccfcat in ['MovieEncode', 'MovieWebdl', 'MovieRemux']:
                if ARGS.origin_name:
                    newMovieName = itemName
                else:
                    newMovieName = genMovieResGroup(mediaSrc, p.title, str(p.year),
                                                    p.resolution, p.group)
                targetCopy(mediaSrc, destCatFolderName, newMovieName)
            elif p.ccfcat in ['MovieBDMV']:
                # since it's a .mkv(mp4) file, no x264/5, not tv and no BDMV dir
                print('\033[33mMaybe remux? : %s \033[0m' % itemName)
                targetCopy(mediaSrc, os.path.join('MovieRemux',
                                                  destFolderName))
            elif p.ccfcat in ['TMDbNotFound']:
                targetCopy(mediaSrc, p.ccfcat)
            else:
                print('\033[33mSingle media file : [ %s ] %s \033[0m' %
                      (p.ccfcat, mediaSrc))
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
        if p.ccfcat == 'TV':
            copyTVFolderItems(mediaSrc, destFolderName, p.season, p.group, p.resolution)
        elif p.ccfcat in ['Movie', 'MovieEncode', 'MovieWebdl', 'MovieBDMV', 'MovieRemux']:
            processMovieDir(mediaSrc, p.ccfcat, destFolderName)
        elif p.ccfcat in ['MV']:
            targetCopy(mediaSrc, p.ccfcat)
        elif p.ccfcat in ['TMDbNotFound']:
            targetCopy(mediaSrc, p.ccfcat)
        elif p.ccfcat in ['eBook', 'Music', 'Audio', 'HDTV']:
            print('\033[33mSkip eBoook, Music, Audio, HDTV: [%s], %s\033[0m ' %
                  (p.ccfcat, mediaSrc))
            # if you don't want to skip these, comment up and uncomment below
            # targetCopy(mediaSrc, p.cat)
        else:
            print('\033[33mDir treat as movie folder: [ %s ], %s\033[0m ' %
                  (p.ccfcat, mediaSrc))
            processMovieDir(mediaSrc, p.ccfcat, destFolderName)


def makeKeepExts():
    global KEEPEXTS
    KEEPEXTS = ['.mkv', '.mp4', '.ts']
    if ARGS.keep_ext:
        argExts = ARGS.keep_ext.split(',')
        for ext in argExts:
            ext = ext.strip()
            if ext:
                if ext[0] == '.':
                    KEEPEXTS.append(ext)
                else:
                    KEEPEXTS.append('.' + ext)


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
                        required=True,
                        help='the dest path to create Hard Link.')
    parser.add_argument('-e',
                        '--keep-ext',
                        help='keep files with these extention(\'srt,ass\').')
    parser.add_argument(
        '--tmdb-api-key',
        help=
        'Search API for the tmdb id, and gen dirname as Name (year)\{tmdbid=xxx\}'
    )
    parser.add_argument('--tmdb-lang',
                        default='zh-CN',
                        help='specify the TMDb language')
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
    parser.add_argument('--sleep',
                        type=int,
                        help='sleep x seconds after operation.')
    parser.add_argument('--move-run',
                        action='store_true',
                        help='WARN: REAL MOVE...with NO REGRET.')
    parser.add_argument('--emby-bracket',
                        action='store_true',
                        help='ex: Alone (2020) [tmdbid=509635]')
    parser.add_argument('--plex-bracket',
                        action='store_true',
                        help='ex: Alone (2020) {tmdb-509635}')

    global ARGS
    ARGS = parser.parse_args()
    ARGS.MEDIA_DIR = os.path.expanduser(ARGS.MEDIA_DIR)
    makeKeepExts()


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
            if isCollections(torFolderItem) and os.path.isdir(
                    os.path.join(cpLocation, torFolderItem)):
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
