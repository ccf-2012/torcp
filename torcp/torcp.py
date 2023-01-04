# -*- coding: utf-8 -*-
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
import time
import datetime
import argparse
import shutil
import glob
import platform
import codecs

from torcp.tmdbparser import TMDbNameParser
from torcp.torcategory import TorCategory
from torcp.tortitle import TorTitle, is0DayName
from torcp.cacheman import CacheManager

ARGS = None

CATNAME_TV = 'TV'
CATNAME_MOVIE = 'Movie'


def ensureDir(file_path):
    if os.path.isfile(file_path):
        file_path = os.path.dirname(file_path)
    if not os.path.exists(file_path):
        os.makedirs(file_path)


def makeLogfile(fromLoc, toLocPath, logDir=None):
    if not ARGS.make_log:
        return 
    destDir = os.path.join(ARGS.hd_path, toLocPath)
    if not logDir:
        fromLocDir = fromLoc
        if os.path.isfile(fromLoc):
            fromLocDir = os.path.dirname(fromLoc)
            if re.search(r'\bS\d+$', fromLocDir):
                fromLocDir = os.path.dirname(fromLocDir)
        originName, ext = os.path.splitext(os.path.basename(fromLocDir))
    else:
        originName = os.path.basename(logDir)
    if not originName:
        originName = '_'
    logFilename = os.path.join(destDir, originName + '.log')
    
    if not os.path.exists(destDir):
        ensureDir(destDir)
    with codecs.open(logFilename, "a+", "utf-8") as logfile:
        logfile.write(fromLoc+'\n')
        logfile.close()


def hdlinkCopy(fromLoc, toLocPath, toLocFile=''):
    if os.path.islink(fromLoc):
        print('\033[31mSKIP symbolic link: [%s]\033[0m ' % fromLoc)
        return
    destDir = os.path.join(ARGS.hd_path, toLocPath)
    if not ARGS.dryrun:
        ensureDir(destDir)
        makeLogfile(fromLoc, toLocPath)
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
        makeLogfile(fromLoc, toLocFolder)
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


def symbolLink(fromLoc, toLocPath, toLocFile=''):
    if os.path.islink(fromLoc):
        print('\033[31mSKIP symbolic link: [%s]\033[0m ' % fromLoc)
        return
    destDir = os.path.join(ARGS.hd_path, toLocPath)
    if not ARGS.dryrun:
        ensureDir(destDir)
        makeLogfile(fromLoc, toLocPath)
    if os.path.isfile(fromLoc):
        if toLocFile:
            destFile = os.path.join(destDir, toLocFile)
        else:
            destFile = os.path.join(destDir, os.path.basename(fromLoc))
        if not os.path.exists(destFile):
            if ARGS.dryrun:
                print(fromLoc, ' ==> ', destFile)
            else:
                print('ln -s', fromLoc, destFile)
                os.symlink(fromLoc, destFile)
        else:
            print('\033[32mTarget Exists: [%s]\033[0m ' % destFile)

    elif os.path.isdir(fromLoc):
        destDir = os.path.join(destDir, os.path.basename(fromLoc))
        if not os.path.exists(destDir):
            if ARGS.dryrun:
                print('(DIR) ln -s ' + fromLoc + ' ==> ' + destDir)
            else:
                print('(DIR) ln -s ', fromLoc, destDir)
                os.symlink(fromLoc, destDir)
                # shutil.copytree(fromLoc, destDir, copy_function=os.link)
        else:
            print('\033[32mTarget Exists: [%s]\033[0m ' % destDir)
    else:
        print('File/Dir %s not found' % (fromLoc))


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
        if ARGS.symbolink:
            symbolLink(fromLoc, toLocPath, toLocFile)
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


def fixNtName(file_path):
    # file_path = re.sub(r'(\:|\?|<|>|\*|\\|\")', ' ', file_path)
    if platform.system() == 'Windows':
        file_path = re.sub(r'(\:|\?|<|>|\*|\\|/|\")', ' ', file_path)
    else:
        file_path = re.sub(r'/', ' ', file_path)
    return file_path


def genMediaFolderName(nameParser):
    if nameParser.tmdbid > 0:
        if ARGS.emby_bracket:
            tmdbTail = '[tmdbid=' + str(nameParser.tmdbid) + ']'
        elif ARGS.plex_bracket:
            tmdbTail = '{tmdb-' + str(nameParser.tmdbid) + '}'
        else:
            tmdbTail = ''

        subdir_title = nameParser.title

        if ARGS.lang:
            if ARGS.lang.lower() == 'all':
                subdir_title = os.path.join(nameParser.original_language,
                                            nameParser.title)
            else:
                ollist = ARGS.lang.lower().split(',')
                if nameParser.original_language in ollist:
                    subdir_title = os.path.join(nameParser.original_language,
                                                nameParser.title)
                else:
                    subdir_title = os.path.join('other', nameParser.title)

        if nameParser.year > 0:
            mediaFolderName = '%s (%d) %s' % (
                subdir_title, nameParser.year, tmdbTail)
        else:
            mediaFolderName = '%s %s' % (subdir_title, tmdbTail)

    else:
        if nameParser.ccfcat == 'tv':
            # if not nameParser.season:
            #     tempseason = 'S01'
            if nameParser.year > 0 and nameParser.season == 'S01':
                mediaFolderName = '%s (%d)' % (nameParser.title,
                                               nameParser.year)
            else:
                mediaFolderName = nameParser.title
        else:
            if nameParser.year > 0:
                mediaFolderName = '%s (%d)' % (nameParser.title,
                                               nameParser.year)
                # mediaFolderName = nameParser.title + ' (' + str(
                #     nameParser.year) + ')'
            else:
                mediaFolderName = nameParser.title
            
    return mediaFolderName.strip()


def isMediaFileType(file_ext):
    return KEEPEXTALL or file_ext.lower() in KEEPEXTS


def copyTVSeasonItems(tvSourceFullPath, tvFolder, seasonFolder, groupName,
                      resolution, folderTmdbParser=None):
    if os.path.isdir(os.path.join(tvSourceFullPath, 'BDMV')):
        # break, process BDMV dir for this dir
        bdmvTVFolder = os.path.join(tvFolder, seasonFolder)
        processBDMV(tvSourceFullPath, bdmvTVFolder, CATNAME_TV, tmdbParser=folderTmdbParser)
        return

    # catutil = TorCategory()
    for tv2item in os.listdir(tvSourceFullPath):
        tv2itemPath = os.path.join(tvSourceFullPath, tv2item)
        if os.path.isdir(tv2itemPath):
            print('\033[31mSKIP dir in TV: [%s]\033[0m ' % tv2itemPath)
        else:
            filename, file_ext = os.path.splitext(tv2item)
            seasonFolderFullPath = os.path.join(CATNAME_TV, tvFolder, seasonFolder)
            if isMediaFileType(file_ext):
                if ARGS.origin_name:
                    newTVFileName = os.path.basename(tv2item)
                else:
                    if not groupName:
                        tc = TorCategory(tv2item)
                        cat, groupName = tc.ccfcat, tc.group
                        if not resolution:
                            resolution = tc.resolution
                    newTVFileName = genTVSeasonEpisonGroup(
                        tv2item, groupName, resolution)
                # makeLogfile(tv2itemPath, seasonFolderFullPath, tvSourceFullPath)
                targetCopy(tv2itemPath, seasonFolderFullPath, newTVFileName)
            elif file_ext.lower() in ['.iso']:
                # TODO: aruba need iso when extract_bdmv
                if ARGS.full_bdmv or ARGS.extract_bdmv:
                    targetCopy(tv2itemPath, seasonFolderFullPath)


def uselessFile(entryName):
    return entryName in ['@eaDir', '.DS_Store', '.@__thumb']


def selfGenCategoryDir(dirName):
    return dirName in [
        'MovieEncode', 'MovieRemux', 'MovieWebdl', 'MovieBDMV', 'BDMVISO',
        CATNAME_MOVIE, CATNAME_TV, 'TMDbNotFound'
    ]


def genTVSeasonEpisonGroup(mediaFilename, groupName, resolution):
    tt = TorTitle(mediaFilename)
    tvTitle, tvYear, tvSeason, tvEpisode, cntitle = tt.title, tt.yearstr, tt.season, tt.episode, tt.cntitle
    # tvTitle = fixNtName(tvTitle)
    cutName = cutOriginName(mediaFilename)

    tvEpisode = re.sub(r'^Ep\s*', 'E', tvEpisode, flags=re.I)
    # filename, file_ext = os.path.splitext(mediaFilename)
    # ch1 = '- ' if (resolution or groupName) else ''
    # ch2 = '_' if (resolution and groupName) else ''
    # tvname = '%s %s %s%s %s%s%s' % (tvTitle,
    #                                 ('(' + tvYear + ')') if tvYear else '',
    #                                 tvSeason.upper() if tvSeason else '',
    #                                 tvEpisode.upper() if tvEpisode else '',
    #                                 (tt.subEpisode+' ') if tt.subEpisode else '',
    #                                 ch1+resolution if resolution else '',
    #                                 ch2+groupName if groupName else '')
    tvname = '%s %s %s%s %s - %s' % (tvTitle,
                                    ('(' + tvYear + ')') if tvYear else '',
                                    tvSeason.upper() if tvSeason else '',
                                    tvEpisode.upper() if tvEpisode else '',
                                    (tt.subEpisode+' ') if tt.subEpisode else '',
                                    cutName)

    tvname = tvname.strip()

    # filename, file_ext = os.path.splitext(mediaFilename)
    # ch1 = ' - ' if (resolution or groupName) else ''
    # ch2 = '_' if (resolution and groupName) else ''
    # tvname = tvTitle + ((' (' + tvYear + ')') if tvYear else '') + (
    #     ' ' + tvSeason.upper() if tvSeason else
    #     '') + (tvEpisode.upper() if tvEpisode else '') + ch1 + (
    #         resolution if resolution else '') + ch2 + (groupName if groupName
    #                                                    else '') + file_ext
    return tvname.strip()


def countMediaFile(filePath):
    types = ('*.mkv', '*.mp4', '*.ts', '*.m2ts')
    curdir = os.getcwd()
    mediaCount = 0
    try:
        os.chdir(filePath)
        for files in types:
            mediaCount += len(glob.glob(files))
        os.chdir(curdir)
    except:
        pass
    return mediaCount


def getFirstMediaFile(filePath):
    mediaFiles = getMediaFiles(filePath)
    return os.path.basename(mediaFiles[0]) if mediaFiles else None
    

def getMediaFiles(filePath):
    types = ('*.mkv', '*.mp4', '*.ts')
    filesFound = []
    curdir = os.getcwd()
    os.chdir(filePath)
    for files in types:
        filesFound.extend(glob.glob(files))
    os.chdir(curdir)
    return filesFound


def getMusicFile(filePath):
    types = ('*.flac', '*.ape', '*.wav')
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


def fixSeasonGroupWithFilename(folderPath, folderSeason, folderGroup, folderResolution, destFolderName):
    season = folderSeason
    group = folderGroup
    resolution = folderResolution
    foldername = destFolderName
    testFile = getFirstMediaFile(folderPath)
    if testFile:
        p = TMDbNameParser(ARGS.tmdb_api_key, ARGS.tmdb_lang)
        p.parse(testFile, useTMDb=False)
        if not folderGroup:
            group = p.group
        if not folderSeason:
            season = p.season
        if not season:
            season = 'S01'
    return season, group, foldername, resolution


def copyTVFolderItems(tvSourceFolder, genFolder, folderSeason, groupName,
                      resolution, folderTmdbParser):
    if os.path.islink(tvSourceFolder):
        print('\033[31mSKIP symbolic link: [%s]\033[0m ' % tvSourceFolder)
        return
    if os.path.isdir(os.path.join(tvSourceFolder, 'BDMV')):
        if ARGS.full_bdmv or ARGS.extract_bdmv:
            # a BDMV dir in a TV folder, treat as Movie
            processBDMV(tvSourceFolder, genFolder, 'MovieM2TS', tmdbParser=folderTmdbParser)
            targetDirHook(os.path.join('MovieM2TS', genFolder), tmdbidstr=str(folderTmdbParser.tmdbid))
        else:
            print('\033[31mSkip BDMV/ISO  %s \033[0m' % genFolder)
        return

    parseSeason, parseGroup, genFolder, resolution = fixSeasonGroupWithFilename(
        tvSourceFolder, folderSeason, groupName, resolution, genFolder)

    if not os.path.isdir(tvSourceFolder):
        return

    for tvitem in sorted(os.listdir(tvSourceFolder)):
        if uselessFile(tvitem):
            print('\033[34mSKIP useless file: [%s]\033[0m ' % tvitem)
            continue
        if selfGenCategoryDir(tvitem):
            print('\033[34mSKIP self-generated dir: [%s]\033[0m ' % tvitem)
            continue

        tvitemPath = os.path.join(tvSourceFolder, tvitem)
        if os.path.isdir(tvitemPath):
            seasonFolder = getSeasonFromFolderName(tvitem, failDir=parseSeason)
            copyTVSeasonItems(tvitemPath, genFolder, seasonFolder, parseGroup,
                              resolution, folderTmdbParser=folderTmdbParser)
        else:
            filename, file_ext = os.path.splitext(tvitemPath)
            if isMediaFileType(file_ext):
                if ARGS.origin_name:
                    newTVFileName = os.path.basename(tvitemPath)
                else:
                    newTVFileName = genTVSeasonEpisonGroup(
                        tvitem, parseGroup, resolution)
                seasonFolderFullPath = os.path.join(CATNAME_TV, genFolder,
                                                    parseSeason)
                # makeLogfile(tvitemPath, seasonFolderFullPath, tvSourceFolder)
                targetCopy(tvitemPath, seasonFolderFullPath, newTVFileName)

    mkPlexMatch(os.path.join(CATNAME_TV, genFolder), folderTmdbParser)
    targetDirHook(os.path.join(CATNAME_TV, genFolder), tmdbidstr=str(folderTmdbParser.tmdbid))


def cutOriginName(srcOriginName):
    m1 = re.search( r'^.*\b(720p|1080[pi]|2160p|576i)[\. ]*', srcOriginName, flags=re.I)
    sstr = srcOriginName
    if m1:
        sstr = srcOriginName[m1.span(1)[0]:]
    else:
        m2 = re.search( r'\b((19\d{2}\b|20\d{2})(-19\d{2}|-20\d{2})?)\b(?!.*\b\d{4}\b.*)', srcOriginName, flags=re.A | re.I)
        if m2:
            sstr = sstr[m2.span(1)[1]:]
    sstr = re.sub(r'^[. ]*', '', sstr)
    sstr = re.sub(r'-', '_', sstr)
    return sstr


def genMovieTMDbOriginName(mediaSrc, movieName, year, nameParser=None):
    originName = cutOriginName(os.path.basename(mediaSrc))
    # filename, file_ext = os.path.splitext(mediaSrc)
    ch1 = ' - '
    tmdbTail = ''
    if (nameParser and nameParser.tmdbid > 0 and ARGS.filename_emby_bracket and ARGS.emby_bracket):
        tmdbTail = ' [tmdbid=' + str(nameParser.tmdbid) + ']'
    medianame = movieName + ((' (' + year + ')' ) if year else '') + tmdbTail + ch1 + originName
    return medianame.strip()


def genMovieResGroup(mediaSrc, movieName, year, resolution, group, nameParser=None):
    filename, file_ext = os.path.splitext(mediaSrc)
    ch1 = ' - ' if (resolution or group) else ''
    ch2 = '_' if (resolution and group) else ''
    tmdbTail = ''
    if (nameParser and nameParser.tmdbid > 0 and ARGS.filename_emby_bracket and ARGS.emby_bracket):
        tmdbTail = ' [tmdbid=' + str(nameParser.tmdbid) + ']'
    medianame = movieName + ((' (' + year + ')' ) if year else '') + tmdbTail + ch1 + (
        resolution if resolution else '') + ch2 + (group
                                                   if group else '') + file_ext
    return medianame.strip()


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


def setArgsCategory():
    cat = ''
    if ARGS.tv:
        # if parser.ccfcat != 'TV':
        #     print('\033[34mWarn: I don\'t think it is TV  %s \033[0m' % parser.title)
        cat = CATNAME_TV
    elif ARGS.movie:
        # if parser.ccfcat not in ['MovieEncode', 'MovieWebdl', 'MovieRemux', 'MovieBDMV', 'MV']:
        #     print('\033[34mWarn: I don\'t think it is Movie  %s \033[0m' % parser.title)
        cat = CATNAME_MOVIE
    return cat


def genCatFolderName(parser):
    global CATNAME_MOVIE, CATNAME_TV
    if ARGS.tmdb_api_key and parser.tmdbid <= 0 and parser.tmdbcat in ['tv', 'movie']:
        return 'TMDbNotFound'
    else:
        if parser.tmdbcat == 'movie':
            CATNAME_MOVIE = ARGS.movie_folder_name
            return ARGS.movie_folder_name
        elif parser.tmdbcat == 'tv':
            CATNAME_TV = ARGS.tv_folder_name
            return ARGS.tv_folder_name
        else:
            return parser.ccfcat


def isCollections(folderName):
    return re.search(r'(\bPack$|合集|Anthology|Trilogy|Quadrilogy|Tetralogy|(?<!Criterion[ .])Collections?|国语配音4K动画电影$)',
                     folderName,
                     flags=re.I)


def processBDMV(mediaSrc, folderGenName, catFolder, tmdbParser=None):
    destCatFolderName = os.path.join(catFolder, folderGenName)
    if ARGS.full_bdmv:
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

        largestStreams = sorted(getLargestFiles(bdmvDir))
        folderGenList = re.split(r'\/|\\', folderGenName)
        folderName = folderGenList[0]
        diskName = "" if len(folderGenList) <= 1 else folderGenList[1]

        if tmdbParser and tmdbParser.tmdbcat == 'tv':
            m = re.search(r"(S|Season)(\d+)", diskName, re.I)
            if m:
                ssName = "S%02d" % int(m[2])
            else:
                ssName = "S01"
            destCatFolderName = os.path.join(catFolder, folderName, ssName)
            time.sleep(1)
            epCount = countMediaFile(os.path.join(ARGS.hd_path, destCatFolderName))
            for epidx, stream in enumerate(largestStreams):
                tsname = "%s %sE%02d %s_%s" % (folderName, ssName, epCount+epidx+1, diskName, os.path.basename(stream))
                # tsname = '%s %s_%s' % (folderName, diskName, os.path.basename(stream))
                targetCopy(stream, destCatFolderName, tsname)
        else:
            for stream in largestStreams:
                # tsname = folderGenName + ' - ' + os.path.basename(mediaSrc) + '_' + os.path.basename( stream)
                tsname = folderName + ' - ' + os.path.basename( stream)
                targetCopy(stream, destCatFolderName, tsname)

    else:
        print('\033[31mSkip BDMV/ISO  %s \033[0m' % mediaSrc)


def processMusic(mediaSrc, folderCat, folderGenName):
    # destCatFolderName = os.path.join(folderCat, folderGenName)
    targetCopy(mediaSrc, folderCat)
    # TODO: new item add to Music folder cause full update
    targetDirHook('Music', tmdbidstr='music')


def processMovieDir(mediaSrc, folderCat, folderGenName, folderTmdbParser):
    if os.path.isdir(os.path.join(mediaSrc, 'BDMV')):
        # break, process BDMV dir for this dir
        if ARGS.full_bdmv or ARGS.extract_bdmv:
            processBDMV(mediaSrc, folderGenName, 'MovieM2TS', tmdbParser=folderTmdbParser)
            targetDirHook(os.path.join('MovieM2TS', folderGenName), tmdbidstr=str(folderTmdbParser.tmdbid))
        else:
            print('\033[31mSkip BDMV/ISO  %s \033[0m' % mediaSrc)
        return

    if not os.path.isdir(mediaSrc):
        return

    testFile = getMusicFile(mediaSrc)
    if testFile:
        processMusic(mediaSrc, 'Music', folderGenName)
        return

    countMediaFiles = countMediaFile(mediaSrc)
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
                print(" Alert: MovieBDMV in a Movie dir.....?")
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
                targetDirHook(destCatFolderName, tmdbidstr='iso') 
            else:
                print('\033[31mSKip iso file: [%s]\033[0m ' % movieItem)
            continue

        if not isMediaFileType(file_ext):
            print('\033[34mSkip : %s \033[0m' % movieItem)
            continue

        p = folderTmdbParser
        if (folderTmdbParser.tmdbid <= 0) or countMediaFiles > 1:
            fnok = is0DayName(movieItem)
            if fnok:
                pf = TMDbNameParser(ARGS.tmdb_api_key, ARGS.tmdb_lang,
                                    ccfcat_hard=setArgsCategory())
                pf.parse(movieItem, useTMDb=(ARGS.tmdb_api_key is not None))
                pf.title = fixNtName(pf.title)
                if pf.tmdbid > 0 or fnok:
                    p = pf

        cat = genCatFolderName(p)
        destFolderName = genMediaFolderName(p)
        destCatFolderName = os.path.join(cat, destFolderName)

        if cat == CATNAME_TV:
            print('\033[31mMiss Categoried TV: [%s]\033[0m ' % mediaSrc)
            copyTVFolderItems(mediaSrc, destFolderName, p.season, p.group,
                              p.resolution, p)
            # parseSeason = fixSeasonName(parseSeason)
            # if cat != folderCat:
            #     copyTVFolderItems(mediaSrc, destFolderName, p.season, p.group,
            #                       p.resolution)
            # else:
            #     copyTVFolderItems(mediaSrc, folderGenName, p.season, p.group,
            #                       p.resolution)
            return
        elif cat in ['TMDbNotFound', 'HDTV', 'Audio', 'eBook']:
            targetCopy(mediaSrc, cat)
            targetDirHook(cat, tmdbidstr=str(p.tmdbid))
            continue
        else:
            if ARGS.origin_name:
                newMovieName = os.path.basename(movieItem)
            elif ARGS.tmdb_origin_name:
                yearstr = str(p.year) if p.year > 0 else ''
                newMovieName = genMovieTMDbOriginName(movieItem, p.title, yearstr,
                                                nameParser=p)
            else:
                yearstr = str(p.year) if p.year > 0 else ''
                newMovieName = genMovieResGroup(movieItem, p.title, yearstr,
                                                p.resolution, p.group, nameParser=p)
            mediaSrcItem = os.path.join(mediaSrc, movieItem)
            # makeLogfile(mediaSrcItem, destCatFolderName)
            targetCopy(mediaSrcItem, destCatFolderName, newMovieName)
            targetDirHook(destCatFolderName, tmdbidstr=str(p.tmdbid))


def mkPlexMatch(targetDir, tmdbParser):
    if not ARGS.make_plex_match:
        return

    if not tmdbParser:
        return

    pmfilepath = os.path.join(ARGS.hd_path, targetDir, '.plexmatch')
    with open(pmfilepath, "w") as pmfile:
        pmfile.write("Title: %s\ntmdbid: %d\n" %
                     (tmdbParser.title, tmdbParser.tmdbid))
        if tmdbParser.year > 1990:
            pmfile.write("Year: %d\n" % (tmdbParser.year))


def targetDirHook(targetDir, tmdbidstr=''):
    # exportTargetDir = os.path.join(ARGS.hd_path, targetDir)
    exportTargetDir = targetDir
    print('Target Dir: ' + exportTargetDir)
    if ARGS.after_copy_script:
        import subprocess        
        cmd = [ARGS.after_copy_script, exportTargetDir, CUR_MEDIA_NAME, str(tmdbidstr)]
        subprocess.Popen(cmd).wait()
        # os.system("%s %s" % (ARGS.next_script, targetDir))
    return


def processOneDirItem(cpLocation, itemName, imdbidstr='', tmdbidstr=''):
    global CUR_MEDIA_NAME 
    CUR_MEDIA_NAME = itemName
    mediaSrc = os.path.join(cpLocation, itemName)
    if os.path.islink(mediaSrc):
        print('\033[31mSKIP symbolic link: [%s]\033[0m ' % mediaSrc)
        return

    print(" >> [%s] %s %s" % (itemName, imdbidstr, tmdbidstr))
    cat = setArgsCategory()
    p = TMDbNameParser(ARGS.tmdb_api_key, ARGS.tmdb_lang, ccfcat_hard=cat)
    p.parse(itemName, useTMDb=(ARGS.tmdb_api_key is not None), hasIMDbId=imdbidstr, hasTMDbId=tmdbidstr)
    p.title = fixNtName(p.title)
    cat = genCatFolderName(p)

    destFolderName = genMediaFolderName(p)
    destCatFolderName = os.path.join(cat, destFolderName)

    if os.path.isfile(mediaSrc):
        filename, file_ext = os.path.splitext(itemName)
        if isMediaFileType(file_ext):
            if cat == CATNAME_TV:
                print('\033[33mSingle Episode file?  %s \033[0m' % mediaSrc)
                if ARGS.origin_name:
                    newTVFileName = itemName
                else:
                    newTVFileName = genTVSeasonEpisonGroup(
                        itemName, p.group, p.resolution)
                seasonFolderFullPath = os.path.join(ARGS.tv_folder_name, destFolderName,
                                                    p.season)
                targetCopy(mediaSrc, seasonFolderFullPath, newTVFileName)
                mkPlexMatch(os.path.join(ARGS.tv_folder_name, destFolderName), p)
                targetDirHook(os.path.join(ARGS.tv_folder_name, destFolderName), tmdbidstr=str(p.tmdbid))
            elif cat == CATNAME_MOVIE:
                if ARGS.origin_name:
                    newMovieName = itemName
                elif ARGS.tmdb_origin_name:
                    yearstr = str(p.year) if p.year > 0 else ''
                    newMovieName = genMovieTMDbOriginName(mediaSrc, p.title,
                                                    yearstr, nameParser=p)
                else:
                    yearstr = str(p.year) if p.year > 0 else ''
                    newMovieName = genMovieResGroup(mediaSrc, p.title,
                                                    yearstr, p.resolution,
                                                    p.group, nameParser=p)
                targetCopy(mediaSrc, destCatFolderName, newMovieName)
                targetDirHook(destCatFolderName, tmdbidstr=str(p.tmdbid))
            elif cat == 'TMDbNotFound':
                targetCopy(mediaSrc, cat)
                targetDirHook(os.path.join(cat, itemName), tmdbidstr=str(p.tmdbid))
            else:
                print('\033[33mSingle media file : [ %s ] %s \033[0m' %
                      (cat, mediaSrc))
                targetCopy(mediaSrc, destCatFolderName)
                targetDirHook(destCatFolderName, tmdbidstr=str(p.tmdbid))
        elif file_ext.lower() in ['.iso']:
            #  TODO: aruba need iso when extract_bdmv
            if ARGS.full_bdmv or ARGS.extract_bdmv:
                bdmvFolder = os.path.join('BDMVISO', destFolderName)
                targetCopy(mediaSrc, bdmvFolder)
                targetDirHook(bdmvFolder, tmdbidstr='iso')
            else:
                print('\033[33mSkip .iso file:  %s \033[0m' % mediaSrc)
        else:
            print('\033[34mSkip file:  %s \033[0m' % mediaSrc)
    else:
        if cat == CATNAME_TV:
            copyTVFolderItems(mediaSrc, destFolderName, p.season, p.group,
                              p.resolution, p)
        elif cat == CATNAME_MOVIE:
            processMovieDir(mediaSrc, p.ccfcat,
                            destFolderName, folderTmdbParser=p)
        elif cat in ['MV']:
            targetCopy(mediaSrc, cat)
            targetDirHook(os.path.join(cat, itemName), tmdbidstr='mv')
        elif cat in ['Music']:
            processMusic(mediaSrc, cat, destFolderName)
        elif cat in ['TMDbNotFound']:
            if p.tmdbcat == 'movie':
                print('\033[33mSearch media in dir: [ %s ], %s\033[0m ' %
                    (cat, mediaSrc))
                processMovieDir(mediaSrc, cat, destFolderName, folderTmdbParser=p)
            else:
                targetCopy(mediaSrc, cat)
                targetDirHook(os.path.join(cat, itemName), tmdbidstr='notfound')

        elif cat in ['Audio']:
            targetCopy(mediaSrc, cat)
            targetDirHook(os.path.join(cat, itemName), tmdbidstr='audio')
        elif cat in ['eBook']:
            print('\033[33mSkip eBoook: [%s], %s\033[0m ' %
                  (cat, mediaSrc))
            # if you don't want to skip these, comment up and uncomment below
            # targetCopy(mediaSrc, p.cat)
        else:
            print('\033[33mDir treat as movie folder: [ %s ], %s\033[0m ' %
                  (cat, mediaSrc))
            processMovieDir(mediaSrc, cat, destFolderName, folderTmdbParser=p)


def makeKeepExts():
    global KEEPEXTS, KEEPEXTALL
    KEEPEXTALL = False
    KEEPEXTS = ['.mkv', '.mp4', '.ts', '.m2ts']
    if ARGS.keep_ext == 'all':
        KEEPEXTALL = True
        return
    if ARGS.keep_ext:
        argExts = ARGS.keep_ext.split(',')
        for ext in argExts:
            ext = ext.strip()
            if ext:
                if ext[0] == '.':
                    KEEPEXTS.append(ext)
                else:
                    KEEPEXTS.append('.' + ext)


def ensureIMDb():
    if ARGS.imdbid:
        m1 = re.search(r'(tt\d+)', ARGS.imdbid, re.A)
        if m1:
            ARGS.imdbid = m1[1]
        else:
            ARGS.imdbid = ''


def loadArgs():
    parser = argparse.ArgumentParser(
        description='torcp: a script hardlink media files and directories in Emby-happy naming and structs.'
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
    parser.add_argument('-l',
                        '--lang',
                        help='seperate move by language(\'cn,en\').')
    parser.add_argument(
        '--tmdb-api-key',
        help='Search API for the tmdb id, and gen dirname as Name (year)\{tmdbid=xxx\}'
    )
    parser.add_argument('--tmdb-lang',
                        default='zh-CN',
                        help='specify the TMDb language')
    parser.add_argument('--tv-folder-name',
                        default='TV',
                        help='specify the name of TV directory, default TV.')
    parser.add_argument('--movie-folder-name',
                        default='Movie',
                        help='specify the name of Movie directory, default Movie.')
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
    parser.add_argument('--tmdb-origin-name',
                        action='store_true',
                        help='filename emby bracket - origin file name.')
    parser.add_argument('--sleep',
                        type=int,
                        help='sleep x seconds after operation.')
    parser.add_argument('--move-run',
                        action='store_true',
                        help='WARN: REAL MOVE...with NO REGRET.')
    parser.add_argument('--make-log',
                        action='store_true',
                        help='Make a log file.')
    parser.add_argument('--symbolink',
                        action='store_true',
                        help='symbolink instead of hard link')
    parser.add_argument('--cache',
                        action='store_true',
                        help='cache searched dir entries')
    parser.add_argument('--emby-bracket',
                        action='store_true',
                        help='ex: Alone (2020) [tmdbid=509635]')
    parser.add_argument('--filename-emby-bracket',
                        action='store_true',
                        help='filename with emby bracket')
    parser.add_argument('--plex-bracket',
                        action='store_true',
                        help='ex: Alone (2020) {tmdb-509635}')
    parser.add_argument('--make-plex-match',
                        action='store_true',
                        help='Create a .plexmatch file at the top level of a series')
    parser.add_argument('--after-copy-script',
                        default='',
                        help='call this script with destination folder path after link/move')
    parser.add_argument('--imdbid',
                        default='',
                        help='specify the IMDb id, -s single mode only')
    parser.add_argument('--tmdbid',
                        default='',
                        help='specify the TMDb id, -s single mode only')
    parser.add_argument('--site-str',
                        help='site-id(ex. hds-12345) folder name, set site strs like (\'chd,hds,ade,ttg\').')

    global ARGS
    ARGS = parser.parse_args()
    ensureIMDb()
    ARGS.MEDIA_DIR = os.path.expanduser(ARGS.MEDIA_DIR)
    makeKeepExts()


def hasIMDbId(str):
    m1 = re.search(r'\[imdb(id)?\=(tt\d+)\]', str.strip(), flags=re.A | re.I)
    m2 = re.search(r'(tt\d+)\s*$', str, flags=re.A | re.I)
    if m1:
        return m1[2]
    elif m2:
        return m2[1]
    else:
        return None


def matchSiteId(str):
    if ARGS.site_str:
        # argSites = ARGS.site_str.split(',')
        # siteStr = '|'.joint(argSites)
        siteStr = ARGS.site_str.replace(',', '|')
    else:
        siteStr = 'chd|hds|ourbits|hdc|ttg|ade|cmct|frds|pter|u2|mteam|hdh|lemon'
    # m1 = re.search(r'(chd|hds|ourbits|hdc|ttg|ade|cmct|frds|pter|u2|mteam|hdh|lemon)-(\d+)$', str.strip(), flags=re.A | re.I)
    m1 = re.search(r'('+siteStr+')-(\d+)$', str.strip(), flags=re.A | re.I)
    if m1:
        return m1[2]
    else:
        return None


def onlyOneDirInSiteIdFolder(cpLocation, foldername):
    siteid = matchSiteId(foldername)
    if siteid:
        # dirlist = [name for name in os.listdir(os.path.join(cpLocation, foldername)) if os.path.isdir(os.path.join(cpLocation, foldername, name))]
        dirlist = os.listdir(os.path.join(cpLocation, foldername))
        if len(dirlist) >= 1:
            return siteid, dirlist[0]
    return '', ''


def onlyOneDirInIMDbFolder(cpLocation, foldername):
    imdbstr = hasIMDbId(foldername)
    if imdbstr:
        dirlist = os.listdir(os.path.join(cpLocation, foldername))
        if len(dirlist) >= 1:
            return imdbstr, dirlist[0]
        # dirlist = [name for name in os.listdir(os.path.join(cpLocation, foldername)) if os.path.isdir(os.path.join(cpLocation, foldername, name))]
        # if len(dirlist) == 1:
            # return imdbstr, dirlist[0]
    return '', ''


def parseFolderIMDbId(locIn, itemIn):
    siteid, insideSiteFolderName = onlyOneDirInSiteIdFolder(locIn, itemIn)
    folderIMDb, insideIMDbFolderName = onlyOneDirInIMDbFolder(locIn, itemIn)
    if folderIMDb:
        parentLocation = os.path.join(locIn, itemIn)
        itemName = insideIMDbFolderName
    elif siteid:
        parentLocation = os.path.join(locIn, itemIn)
        itemName = insideSiteFolderName
    else:
        parentLocation = locIn
        itemName = itemIn
    return parentLocation, itemName, folderIMDb


def main():
    loadArgs()
    cpLocation = ARGS.MEDIA_DIR
    cpLocation = os.path.abspath(cpLocation)

    print("=========>>> " +
          datetime.datetime.now().astimezone().strftime("%Y-%m-%dT%H:%M:%S %z"))

    if ARGS.cache:
        searchCache = CacheManager(cpLocation)
        searchCache.openCache()

    argIMDb = ARGS.imdbid if (ARGS.single and ARGS.imdbid) else ''
    argTMDb = ARGS.tmdbid if (ARGS.single and ARGS.tmdbid) else ''

    if os.path.isfile(cpLocation):
        processOneDirItem(os.path.dirname(cpLocation),
                          os.path.basename(os.path.normpath(cpLocation)), imdbidstr=argIMDb, tmdbidstr=argTMDb)
    else:
        if ARGS.single and not isCollections(cpLocation):
            # processOneDirItem(os.path.dirname(cpLocation),
            #                   os.path.basename(os.path.normpath(cpLocation)), imdbidstr)
            
            parentLocation, itemName, folderimdb = parseFolderIMDbId(os.path.dirname(cpLocation),
                              os.path.basename(os.path.normpath(cpLocation)))
            if argIMDb or argTMDb:
                processOneDirItem(parentLocation, itemName, imdbidstr=argIMDb, tmdbidstr=argTMDb)
            else:
                processOneDirItem(parentLocation, itemName, folderimdb)

        else:
            for torFolderItem in os.listdir(cpLocation):
                if uselessFile(torFolderItem):
                    continue
                
                parentLocation, itemName, folderimdb = parseFolderIMDbId(cpLocation, torFolderItem)

                if isCollections(itemName) and os.path.isdir(
                        os.path.join(parentLocation, itemName)):
                    print('\033[35mProcess collections: %s \033[0m' %
                          itemName)
                    packDir = os.path.join(parentLocation, itemName)
                    for fn in os.listdir(packDir):
                        if ARGS.cache:
                            if searchCache.isCached(fn):
                                print('\033[32mSkipping. File previously linked: %s \033[0m' % (fn))
                                continue
                            else:
                                searchCache.append(fn)
                        processOneDirItem(packDir, fn, imdbidstr='')
                else:
                    if ARGS.cache:
                        if searchCache.isCached(itemName):
                            print('\033[32mSkipping. File previously linked: %s \033[0m' % (itemName))
                            continue
                        else:
                            searchCache.append(itemName)
                    processOneDirItem(parentLocation, itemName, folderimdb)

    if ARGS.cache:
        searchCache.closeCache()


if __name__ == '__main__':
    # logging.basicConfig(level=logging.DEBUG)
    main()
