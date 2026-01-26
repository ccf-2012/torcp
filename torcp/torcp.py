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
import logging

from torcp.tmdbparser import TMDbNameParser
from torcp.torcategory import TorCategory
from torcp.tortitle import TorTitle, is0DayName
from torcp.cacheman import CacheManager
from torcp.progress import TorcpProgress
from torcp.tmdbcache import TMDbCache
import xml.etree.ElementTree as ET

def area5dir(arecode):
    AREADICT = {
        'useu' : ['GB', 'FR', 'DE', 'IT', 'RU', 'DK', 'NO', 'IS', 'SE', 'FI', 'IE', 'ES', 'PT', 'NL', 'BE', 'AT', 
            'CH', 'UA', 'BY', 'PL', 'CZ', 'GR', 'TR', 'BG', 'RO', 'LT', 'HU', 'LU', 'MC', 'LI', 'EE', 'LV', 
            'HR', 'RS', 'SK', 'MD', 'SI', 'AL', 'MK', 'AZ', 'GE', 'ME', 'BA', 'CA', 'US', 'MX', 'GT', 'BZ', 
            'SV', 'HN', 'NI', 'CR', 'PA', 'BS', 'CU', 'JM', 'HT', 'DO', 'KN', 'AG', 'DM', 'LC', 'VC', 'BB', 
            'GD', 'TT', 'CO', 'EC', 'VE', 'GF', 'SR', 'PE', 'BO', 'PY', 'BR', 'CL', 'AR', 'UY'],
        # 'jpkr' : ['JP', 'KR', 'KO', 'JA'],
        'jp' : ['JP', 'JA'],
        'kr' : ['KR', 'KO'],
        'cn' : ['CN', 'ZH'],
        'hktw': ['HK', 'TW']
        }
    return next((x for x, k in AREADICT.items() if arecode in AREADICT[x]), 'other')

def area7dir(arecode):
    AREADICT = {
        'us' : ['US'],
        'occident' : ['GB', 'FR', 'DE', 'IT', 'RU', 'DK', 'NO', 'IS', 'SE', 'FI', 'IE', 'ES', 'PT', 'NL', 'BE', 'AT', 
            'CH', 'UA', 'BY', 'PL', 'CZ', 'GR', 'TR', 'BG', 'RO', 'LT', 'HU', 'LU', 'MC', 'LI', 'EE', 'LV', 
            'HR', 'RS', 'SK', 'MD', 'SI', 'AL', 'MK', 'AZ', 'GE', 'ME', 'BA', 'CA', 'MX', 'GT', 'BZ', 
            'SV', 'HN', 'NI', 'CR', 'PA', 'BS', 'CU', 'JM', 'HT', 'DO', 'KN', 'AG', 'DM', 'LC', 'VC', 'BB', 
            'GD', 'TT', 'CO', 'EC', 'VE', 'GF', 'SR', 'PE', 'BO', 'PY', 'BR', 'CL', 'AR', 'UY'],
        # 'jpkr' : ['JP', 'KR', 'KO', 'JA'],
        'jp' : ['JP', 'JA'],
        'kr' : ['KR', 'KO'],
        'cn' : ['CN', 'ZH'],
        'hk' : ['HK'],
        'tw' : ['TW']
        }
    return next((x for x, k in AREADICT.items() if arecode in AREADICT[x]), 'other')


logger = logging.getLogger(__name__)


class Torcp:
    def __init__(self):
        self.CUR_MEDIA_NAME = ''
        self.KEEPEXTALL = False
        self.KEEPEXTS = ['.mkv', '.mp4', '.ts', '.m2ts', '.mov', '.strm']
        self.ARGS = None
        self.EXPORT_OBJ = None
        self.CATNAME_TV = 'TV'
        self.CATNAME_MOVIE = 'Movie'
        self.progress = None  # Will be initialized after args are parsed
        self.tmdb_cache = None  # Will be initialized after args are parsed
        self._item_work_done = False  # Track if actual work was done for current item
        # Processing statistics
        self.stats = {
            'processed': 0,
            'skipped': [],  # List of (item_name, reason)
            'failed': [],   # List of (item_name, reason)
        }

    def record_skip(self, item_name, reason):
        """Record a skipped item with reason."""
        self.stats['skipped'].append((item_name, reason))

    def record_fail(self, item_name, reason):
        """Record a failed item with reason."""
        self.stats['failed'].append((item_name, reason))

    def record_success(self):
        """Record a successfully processed item."""
        self.stats['processed'] += 1

    def ensureDir(self, file_path):
        if os.path.isfile(file_path):
            file_path = os.path.dirname(file_path)
        if not os.path.exists(file_path):
            os.makedirs(file_path)

    def makeLogfile(self, fromLoc, destDir, logDir=None):
        if not self.ARGS.make_log:
            return 
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
            self.ensureDir(destDir)
        with codecs.open(logFilename, "a+", "utf-8") as logfile:
            try:
                logfile.write(fromLoc+'\n')
                logfile.close()
            except:
                logger.warning("Error occur when write log file")
                pass

    def getDestDir(self, toLocPath):
        if self.ARGS.other_dir:
            if not toLocPath.startswith(self.CATNAME_TV) and not toLocPath.startswith(self.CATNAME_MOVIE):
                return os.path.join(self.ARGS.other_dir, toLocPath)
        destDir = os.path.join(self.ARGS.hd_path, toLocPath)
        return destDir

    def hdlinkCopy(self, fromLoc, toLocPath, toLocFile=''):
        if os.path.islink(fromLoc):
            logger.info('SKIP symbolic link: [%s] ' % fromLoc)
            self.record_skip(os.path.basename(fromLoc), "symbolic link")
            return
        destDir = self.getDestDir(toLocPath)

        # Show progress status for hardlink operation
        if self.progress:
            self.progress.set_status(f"Hardlink: {os.path.basename(fromLoc)[:30]}")

        if not self.ARGS.dryrun:
            self.ensureDir(destDir)
            self.makeLogfile(fromLoc, destDir)
        if os.path.isfile(fromLoc):
            if toLocFile:
                destFile = os.path.join(destDir, toLocFile)
            else:
                destFile = os.path.join(destDir, os.path.basename(fromLoc))
            if not os.path.exists(destFile):
                if self.ARGS.dryrun:
                    logger.info('%s ==> %s' %  (fromLoc, destFile))
                else:
                    logger.info('ln %s %s ' % (fromLoc, destFile))
                    os.link(fromLoc, destFile)
                self._item_work_done = True
            else:
                logger.info('Target Exists: [%s] ' % destFile)

        elif os.path.isdir(fromLoc):
            destDir = os.path.join(destDir, os.path.basename(fromLoc))
            if not os.path.exists(destDir):
                if self.ARGS.dryrun:
                    logger.info('copytree' + fromLoc + ' ==> ' + destDir)
                else:
                    logger.info('copytree %s %s ' % (fromLoc, destDir))
                    shutil.copytree(fromLoc, destDir, copy_function=os.link)
                self._item_work_done = True
            else:
                logger.info('Target Exists: [%s] ' % destDir)
        else:
            logger.warning('File/Dir %s not found' % (fromLoc))

    def pathMove(self, fromLoc, toLocFolder, toLocFile=''):
        if not os.path.exists(fromLoc):
            logger.warning('[%s] not exists. ' % fromLoc)
            self.record_fail(os.path.basename(fromLoc), "source not found")
            return

        if os.path.islink(fromLoc):
            logger.info('SKIP symbolic link: [%s] ' % fromLoc)
            self.record_skip(os.path.basename(fromLoc), "symbolic link")
            return
        # destDir = os.path.join(self.ARGS.hd_path, toLocFolder)
        destDir = self.getDestDir(toLocFolder)

        # Show progress status for move operation
        if self.progress:
            self.progress.set_status(f"Moving: {os.path.basename(fromLoc)[:30]}")

        if not self.ARGS.dryrun:
            self.ensureDir(destDir)
            self.makeLogfile(fromLoc, toLocFolder)
            if self.ARGS.sleep:
                time.sleep(self.ARGS.sleep)
        if os.path.isfile(fromLoc):
            if toLocFile:
                destFile = os.path.join(destDir, toLocFile)
            else:
                destFile = os.path.join(destDir, os.path.basename(fromLoc))
            if not os.path.exists(destFile):
                if self.ARGS.dryrun:
                    logger.info('%s ==> %s' % (fromLoc, destFile))
                else:
                    logger.info('mv %s %s' % (fromLoc, destFile))
                    os.rename(fromLoc, destFile)
                self._item_work_done = True
            else:
                logger.info('Target Exists: [%s] ' % destFile)
        else:
            destDir = os.path.join(destDir, os.path.basename(fromLoc))
            if not os.path.exists(destDir):
                if self.ARGS.dryrun:
                    logger.info('%s ==> %s' % (fromLoc, destDir))
                else:
                    logger.info('mvdir %s %s ' % (fromLoc, destDir))
                    shutil.move(fromLoc, destDir)
                self._item_work_done = True
            else:
                logger.info('Target Exists: [%s] ' % destDir)

    def symbolLink(self, fromLoc, toLocPath, toLocFile=''):
        if os.path.islink(fromLoc):
            logger.info('SKIP symbolic link: [%s] ' % fromLoc)
            self.record_skip(os.path.basename(fromLoc), "symbolic link")
            return
        # destDir = os.path.join(self.ARGS.hd_path, toLocPath)
        destDir = self.getDestDir(toLocPath)

        # Show progress status for symlink operation
        if self.progress:
            self.progress.set_status(f"Symlink: {os.path.basename(fromLoc)[:30]}")

        if not self.ARGS.dryrun:
            self.ensureDir(destDir)
            self.makeLogfile(fromLoc, toLocPath)
        if os.path.isfile(fromLoc):
            if toLocFile:
                destFile = os.path.join(destDir, toLocFile)
            else:
                destFile = os.path.join(destDir, os.path.basename(fromLoc))
            if not os.path.exists(destFile):
                if self.ARGS.dryrun:
                    logger.info('%s ==> %s' %  (fromLoc, destFile))
                else:
                    logger.info('ln -s %s %s' % (fromLoc, destFile))
                    os.symlink(fromLoc, destFile)
                self._item_work_done = True
            else:
                logger.info('Target Exists: [%s] ' % destFile)

        elif os.path.isdir(fromLoc):
            destDir = os.path.join(destDir, os.path.basename(fromLoc))
            if not os.path.exists(destDir):
                logger.info('(DIR) ln -s ' + fromLoc + ' ==> ' + destDir)
                if not self.ARGS.dryrun:
                    os.symlink(fromLoc, destDir)
                    # shutil.copytree(fromLoc, destDir, copy_function=os.link)
                self._item_work_done = True
            else:
                logger.info('Target Exists: [%s] ' % destDir)
        else:
            logger.info('File/Dir %s not found' % (fromLoc))

    def hdlinkLs(self, loc):
        destDir = os.path.join(self.ARGS.hd_path, loc)
        self.ensureDir(destDir)
        return os.listdir(destDir)

    def targetCopy(self, fromLoc, toLocPath, toLocFile=''):
        if os.path.islink(fromLoc):
            logger.info('SKIP symbolic link: [%s] ' % fromLoc)
            self.record_skip(os.path.basename(fromLoc), "symbolic link")
            return

        if self.ARGS.move_run:
            self.pathMove(fromLoc, toLocPath, toLocFile)
        else:
            if self.ARGS.symbolink:
                self.symbolLink(fromLoc, toLocPath, toLocFile)
            else:
                self.hdlinkCopy(fromLoc, toLocPath, toLocFile)

    def getSeasonFromFolderName(self, folderName, failDir=''):
        m1 = re.search(r'(\bS\d+(-S\d+)?|第(\d+)季)', folderName, flags=re.A | re.I)
        if m1:
            if m1.group(3):
                return 'S' + m1.group(3)
            else:
                return m1.group(1)
        else:
            return folderName

    def fixNtName(self, file_path):
        # file_path = re.sub(r'(\:|\?|<|>|\*|\\|\")', ' ', file_path)
        if platform.system() == 'Windows':
            file_path = re.sub(r'(\:|\?|<|>|\*|\\|/|\")', ' ', file_path)
        else:
            file_path = re.sub(r'/', ' ', file_path)
        return file_path


    def genMediaFolderName(self, nameParser):
        if nameParser.tmdbid > 0:
            if self.ARGS.emby_bracket:
                tmdbTail = '[tmdbid=' + str(nameParser.tmdbid) + ']'
            elif self.ARGS.plex_bracket:
                tmdbTail = '{tmdb-' + str(nameParser.tmdbid) + '}'
            else:
                tmdbTail = ''

            media_folder_name = nameParser.title
            if self.ARGS.add_year_dir:
                year_dir_name = str(nameParser.year) if nameParser.year > 0 else 'none'
                media_folder_name = os.path.join(year_dir_name, nameParser.title)

            subdir_title = media_folder_name
            area_dir = ''
            if self.ARGS.lang:
                if self.ARGS.lang.lower() == 'all':
                    area_dir = nameParser.original_language
                    # subdir_title = os.path.join(nameParser.original_language,
                    #                             media_folder_name)
                else:
                    ollist = [x.strip() for x in self.ARGS.lang.lower().split(',')]
                    area_dir = nameParser.original_language if nameParser.original_language in ollist else 'other'
                    # if nameParser.original_language in ollist:
                    #     subdir_title = os.path.join(nameParser.original_language,
                    #                                 media_folder_name)
                    # else:
                    #     subdir_title = os.path.join('other', media_folder_name)
            elif self.ARGS.sep_area:
                area_dir = nameParser.getProductionArea()
                # area_dir = os.path.join(area, media_folder_name)
            elif self.ARGS.sep_area5:
                area_dir = area5dir(nameParser.getProductionArea().upper())
            elif self.ARGS.sep_area7:
                area_dir = area7dir(nameParser.getProductionArea().upper())

            genre_dir = area_dir
            if self.ARGS.genre:
                argGenreList = [x.strip() for x in self.ARGS.genre.lower().split(',')]
                mediaGenreList = [d.lower().strip() for d in nameParser.getGenres()]
                matchGenre = next((g for g in argGenreList if g in mediaGenreList), '')
                if matchGenre:
                    # 如果匹配 genre 则放弃前面的 area_dir
                    genre_dir = matchGenre
                matchGenreWithArea = ''
                if self.ARGS.genre_with_area:
                    argGenrewAreaList = [x.strip() for x in self.ARGS.genre_with_area.lower().split(',')]
                    matchGenreWithArea = next((g for g in argGenrewAreaList if g in mediaGenreList), '')
                    if matchGenreWithArea:
                        # 如果匹配 --genre-with-area 则将前面的 area_dir 加进来，使用 --genre-with-area 则要求 --genre 同时有
                        genre_dir = os.path.join(matchGenreWithArea, area_dir)
                # 不分地区时，设置了 --genre， --genre-with-area 都没匹配上，单独放一目录
                genre_dir = genre_dir if genre_dir else 'genres'
            subdir_title = os.path.join(genre_dir, media_folder_name)
                
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
                    mediaFolderName = '%s (%d)' % (nameParser.title, nameParser.year)
                else:
                    mediaFolderName = nameParser.title
            else:
                if nameParser.year > 0:
                    mediaFolderName = '%s (%d)' % (nameParser.title, nameParser.year)
                    # mediaFolderName = nameParser.title + ' (' + str(
                    #     nameParser.year) + ')'
                else:
                    mediaFolderName = nameParser.title
                
        return mediaFolderName.strip()


    def isMediaFileType(self, file_ext):
        return self.KEEPEXTALL or file_ext.lower() in self.KEEPEXTS

    def renameS0d(self, seasonFolderName):
        match = re.match(r'^S(\d+)$', seasonFolderName)
        if match:
            return f"Season {match.group(1)}"
        else:
            return seasonFolderName
        
    def copyTVSeasonItems(self, tvSourceFullPath, tvFolder, seasonFolder, groupName,
                        resolution, folderTmdbParser=None):
        if os.path.isdir(os.path.join(tvSourceFullPath, 'BDMV')):
            # break, process BDMV dir for this dir
            bdmvTVFolder = os.path.join(tvFolder, seasonFolder)
            self.processBDMV(tvSourceFullPath, bdmvTVFolder, self.CATNAME_TV, tmdbParser=folderTmdbParser)
            return

        # catutil = TorCategory()
        for tv2item in os.listdir(tvSourceFullPath):
            tv2itemPath = os.path.join(tvSourceFullPath, tv2item)
            if os.path.isdir(tv2itemPath):
                logger.info('\033[31mSKIP dir in TV: [%s]\033[0m ' % tv2itemPath)
            else:
                filename, file_ext = os.path.splitext(tv2item)
                seasonFolderFullPath = os.path.join(self.CATNAME_TV, tvFolder, seasonFolder)
                if self.isMediaFileType(file_ext):
                    if self.ARGS.origin_name:
                        newTVFileName = os.path.basename(tv2item)
                    else:
                        if not groupName:
                            tc = TorCategory(tv2item)
                            cat, groupName = tc.ccfcat, tc.group
                            if not resolution:
                                resolution = tc.resolution
                        newTVFileName = self.genTVSeasonEpisonGroup(
                            tv2item, groupName, resolution)
                    self.targetCopy(tv2itemPath, seasonFolderFullPath, newTVFileName)
                elif file_ext.lower() in ['.iso']:
                    # TODO: aruba need iso when extract_bdmv
                    if self.ARGS.full_bdmv or self.ARGS.extract_bdmv:
                        self.targetCopy(tv2itemPath, seasonFolderFullPath)


    def uselessFile(self, entryName):
        return entryName in ['@eaDir', '.DS_Store', '.@__thumb']

    def selfGenCategoryDir(self, dirName):
        special_folders = [
            'MovieEncode', 'MovieRemux', 'MovieWebdl', 'MovieBDMV',
            self.CATNAME_MOVIE, self.CATNAME_TV,
            self.ARGS.tmdb_not_found_folder
        ]
        # Include legacy BDMV/ISO folders when not using unified-folders
        if not self.ARGS.unified_folders:
            special_folders.extend(['BDMVISO', 'MovieM2TS'])
        return dirName in special_folders

    def genTVSeasonEpisonGroup(self, mediaFilename, groupName, resolution):
        tt = TorTitle(mediaFilename)
        tvTitle, tvYear, tvSeason, tvEpisode, cntitle = tt.title, tt.yearstr, tt.season, tt.episode, tt.cntitle
        # tvTitle = fixNtName(tvTitle)
        cutName = self.cutOriginName(mediaFilename)

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

    def countMediaFile(self, filePath):
        types = ('*.mkv', '*.mp4', '*.ts', '*.m2ts', '*.mov')
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

    def getFirstMediaFile(self, filePath):
        mediaFiles = self.getMediaFiles(filePath)
        return os.path.basename(mediaFiles[0]) if mediaFiles else None
        
    def getMediaFiles(self, filePath):
        types = ('*.mkv', '*.mp4', '*.ts', '*.m2ts', '*.mov')
        filesFound = []
        curdir = os.getcwd()
        os.chdir(filePath)
        for files in types:
            filesFound.extend(glob.glob(files))
        os.chdir(curdir)
        return filesFound

    def getMusicFile(self, filePath):
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

    def fixSeasonGroupWithFilename(self, folderPath, folderSeason, folderGroup, folderResolution, destFolderName):
        season = folderSeason
        group = folderGroup
        resolution = folderResolution
        foldername = destFolderName
        testFile = self.getFirstMediaFile(folderPath)
        if testFile:
            p = TMDbNameParser(self.ARGS.tmdb_api_key, self.ARGS.tmdb_lang, cache=self.tmdb_cache)
            p.parse(testFile, useTMDb=False)
            if not folderGroup:
                group = p.group
            if not folderSeason:
                season = p.season
            if not season:
                season = 'S01'
        return season, group, foldername, resolution

    def copyTVFolderItems(self, tvSourceFolder, genFolder, folderSeason, groupName,
                        resolution, folderTmdbParser):
        if os.path.islink(tvSourceFolder):
            logger.info('SKIP symbolic link: [%s] ' % tvSourceFolder)
            self.record_skip(os.path.basename(tvSourceFolder), "symbolic link")
            return
        if os.path.isdir(os.path.join(tvSourceFolder, 'BDMV')):
            if self.ARGS.full_bdmv or self.ARGS.extract_bdmv:
                if self.ARGS.unified_folders:
                    # Keep in TV folder structure
                    self.processBDMV(tvSourceFolder, genFolder, self.CATNAME_TV, tmdbParser=folderTmdbParser)
                    self.targetDirHook(os.path.join(self.CATNAME_TV, genFolder), tmdbidstr=str(folderTmdbParser.tmdbid), tmdbcat=folderTmdbParser.tmdbcat, tmdbtitle=folderTmdbParser.title, tmdbobj=folderTmdbParser)
                else:
                    # Legacy behavior: separate MovieM2TS folder
                    self.processBDMV(tvSourceFolder, genFolder, 'MovieM2TS', tmdbParser=folderTmdbParser)
                    self.targetDirHook(os.path.join('MovieM2TS', genFolder), tmdbidstr=str(folderTmdbParser.tmdbid), tmdbcat=folderTmdbParser.tmdbcat, tmdbtitle=folderTmdbParser.title, tmdbobj=folderTmdbParser)
            else:
                logger.info('Skip BDMV/ISO  %s ' % genFolder)
                self.record_skip(os.path.basename(tvSourceFolder), "BDMV (use --full-bdmv)")
            return

        parseSeason, parseGroup, genFolder, resolution = self.fixSeasonGroupWithFilename(
            tvSourceFolder, folderSeason, groupName, resolution, genFolder)
        # for 香香
        parseSeason = self.renameS0d(parseSeason)                       

        if not os.path.isdir(tvSourceFolder):
            return

        for tvitem in sorted(os.listdir(tvSourceFolder)):
            if self.uselessFile(tvitem):
                logger.info('SKIP useless file: [%s] ' % tvitem)
                continue
            if self.selfGenCategoryDir(tvitem):
                logger.info('SKIP self-generated dir: [%s] ' % tvitem)
                continue

            tvitemPath = os.path.join(tvSourceFolder, tvitem)
            if os.path.isdir(tvitemPath):
                seasonFolder = self.getSeasonFromFolderName(tvitem, failDir=parseSeason)
                # for 香香
                seasonFolder = self.renameS0d(seasonFolder)                       
                self.copyTVSeasonItems(tvitemPath, genFolder, seasonFolder, parseGroup,
                                resolution, folderTmdbParser=folderTmdbParser)
            else:
                filename, file_ext = os.path.splitext(tvitemPath)
                if self.isMediaFileType(file_ext):
                    if self.ARGS.origin_name:
                        newTVFileName = os.path.basename(tvitemPath)
                    else:
                        newTVFileName = self.genTVSeasonEpisonGroup(
                            tvitem, parseGroup, resolution)
                    seasonFolderFullPath = os.path.join(self.CATNAME_TV, genFolder,
                                                        parseSeason)
                    self.targetCopy(tvitemPath, seasonFolderFullPath, newTVFileName)
                elif file_ext.lower() == '.iso':
                    if self.ARGS.full_bdmv or self.ARGS.extract_bdmv:
                        if self.ARGS.unified_folders:
                            # Keep ISO in TV folder structure
                            destFolder = os.path.join(self.CATNAME_TV, genFolder, parseSeason)
                            self.targetCopy(tvitemPath, destFolder)
                        else:
                            # Legacy: skip ISO in TV folders
                            logger.info('Skip ISO in TV folder: %s' % tvitem)
                            self.record_skip(tvitem, "ISO in TV folder")

        self.mkPlexMatch(os.path.join(self.CATNAME_TV, genFolder), folderTmdbParser)
        self.mkMediaNfo(os.path.join(self.CATNAME_TV, genFolder), "", folderTmdbParser)
        self.targetDirHook(os.path.join(self.CATNAME_TV, genFolder), tmdbidstr=str(folderTmdbParser.tmdbid), tmdbcat=folderTmdbParser.tmdbcat, tmdbtitle=folderTmdbParser.title, tmdbobj=folderTmdbParser)

    def cutOriginName(self, srcOriginName):
        # return srcOriginName
        # TODO:  full orginal name
        m1 = re.search( r'^.*\b(720p|1080[pi]|2160p|576i)[\. ]*', srcOriginName, flags=re.I)
        sstr = srcOriginName
        if m1:
            sstr = srcOriginName[m1.span(1)[0]:]
        else:
            m2 = re.search( r'([\(\[]?((19\d{2}\b|20\d{2})(-19\d{2}|-20\d{2})?)[\)\]]?)(?!.*\b\d{4}\b.*)', srcOriginName, flags=re.A | re.I)
            if m2:
                sstr = sstr[m2.span(1)[1]:].strip()
        sstr = re.sub(r'^[. ]*', '', sstr)
        sstr = re.sub(r'-', '_', sstr)
        return sstr

    def genTMDbTail(self, nameParser):
        tmdbTail = ''
        if (nameParser and nameParser.tmdbid > 0 and self.ARGS.emby_bracket):
            tmdbTail = ' [tmdbid=' + str(nameParser.tmdbid) + ']'
        return tmdbTail

    def genMovieOriginName(self, mediaSrc, movieName, year, nameParser=None):
        originName = os.path.basename(mediaSrc)
        # filename, file_ext = os.path.splitext(mediaSrc)
        ch1 = ' - '
        tmdbTail = self.genTMDbTail(nameParser)
        medianame = movieName + ((' (' + year + ')' ) if year else '') + tmdbTail + ch1 + originName
        return medianame.strip()

    def genMovieTMDbOriginName(self, mediaSrc, movieName, year, nameParser=None):
        originName = os.path.basename(mediaSrc)
        # filename, file_ext = os.path.splitext(mediaSrc)
        ch1 = ' - '
        tmdbTail = self.genTMDbTail(nameParser)
        medianame = movieName + ((' (' + year + ')' ) if year else '') + tmdbTail + ch1 + originName
        return medianame.strip()


    def genMovieResGroup(self, mediaSrc, movieName, year, resolution, group, nameParser=None):
        filename, file_ext = os.path.splitext(mediaSrc)
        ch1 = ' - ' if (resolution or group) else ''
        ch2 = '_' if (resolution and group) else ''
        tmdbTail = self.genTMDbTail(nameParser)
        medianame = movieName + ((' (' + year + ')' ) if year else '') + tmdbTail + ch1 + (
            resolution if resolution else '') + ch2 + (group
                                                    if group else '') + file_ext
        return medianame.strip()

    def getLargestFiles(self, dirName):
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

    def setArgsCategory(self):
        cat = ''
        if self.ARGS.tv:
            cat = self.CATNAME_TV
        elif self.ARGS.movie:
            cat = self.CATNAME_MOVIE
        return cat

    def genCatFolderName(self, parser):
        # Always treat HDTV as TV
        effective_tmdbcat = 'tv' if parser.tmdbcat == 'HDTV' else parser.tmdbcat

        # Check for TMDb lookup failure
        if self.ARGS.tmdb_api_key and parser.tmdbid <= 0 and effective_tmdbcat in ['tv', 'movie']:
            return self.ARGS.tmdb_not_found_folder

        # When filename parsing (ccfcat) says movie but TMDb says tv,
        # trust the filename - TMDb multi-search may return wrong type
        # ccfcat can be 'Movie', 'MovieBDMV', 'MovieEncode', 'MovieRemux', etc.
        ccfcat_lower = parser.ccfcat.lower() if parser.ccfcat else ''
        if ccfcat_lower.startswith('movie') and effective_tmdbcat == 'tv':
            logger.warning(f'TMDb returned TV but filename suggests Movie: {parser.title}')
            effective_tmdbcat = 'movie'

        if effective_tmdbcat == 'movie':
            self.CATNAME_MOVIE = self.ARGS.movie_folder_name
            return self.ARGS.movie_folder_name
        elif effective_tmdbcat == 'tv':
            self.CATNAME_TV = self.ARGS.tv_folder_name
            return self.ARGS.tv_folder_name
        else:
            return parser.ccfcat

    def isCollections(self, folderName):
        return re.search(r'(\bPack$|合集|Anthology|Trilogy|Quadrilogy|Tetralogy|(?<!Criterion[ .])Collections?|国语配音4K动画电影$)',
                        folderName,
                        flags=re.I)

    def processBDMV(self, mediaSrc, folderGenName, catFolder, tmdbParser=None):
        destCatFolderName = os.path.join(catFolder, folderGenName)
        if self.ARGS.full_bdmv:
            for bdmvItem in os.listdir(mediaSrc):
                fullBdmvItem = os.path.join(mediaSrc, bdmvItem)
                self.targetCopy(fullBdmvItem, destCatFolderName)
            return

        if self.ARGS.extract_bdmv:
            bdmvDir = os.path.join(mediaSrc, 'BDMV', 'STREAM')
            if not os.path.isdir(bdmvDir):
                logger.info('BDMV/STREAM/ dir not found in   %s ' % mediaSrc)
                return

            largestStreams = sorted(self.getLargestFiles(bdmvDir))
            folderGenList = re.split(r'\/|\\', folderGenName)
            folderName = folderGenList[0]
            diskName = "" if len(folderGenList) <= 1 else folderGenList[1]

            if catFolder == self.CATNAME_TV:
                m = re.search(r"(S|Season)(\d+)", diskName, re.I)
                if m:
                    ssName = "S%02d" % int(m[2])
                else:
                    ssName = "S01"
                destCatFolderName = os.path.join(catFolder, folderName, ssName)
                time.sleep(1)
                epCount = self.countMediaFile(os.path.join(self.ARGS.hd_path, destCatFolderName))
                for epidx, stream in enumerate(largestStreams):
                    tsname = "%s %sE%02d %s_%s" % (folderName, ssName, epCount+epidx+1, diskName, os.path.basename(stream))
                    # tsname = '%s %s_%s' % (folderName, diskName, os.path.basename(stream))
                    self.targetCopy(stream, destCatFolderName, tsname)
            else:
                for stream in largestStreams:
                    # tsname = folderGenName + ' - ' + os.path.basename(mediaSrc) + '_' + os.path.basename( stream)
                    tsname = folderName + ' - ' + os.path.basename( stream)
                    self.targetCopy(stream, destCatFolderName, tsname)

        else:
            logger.info('Skip BDMV/ISO  %s ' % mediaSrc)
            self.record_skip(os.path.basename(mediaSrc), "BDMV (use --full-bdmv)")

    def processMusic(self, mediaSrc, folderCat, folderGenName):
        # destCatFolderName = os.path.join(folderCat, folderGenName)
        self.targetCopy(mediaSrc, folderCat)
        # TODO: new item add to Music folder cause full update
        self.targetDirHook('Music', tmdbidstr='', tmdbcat='music', tmdbtitle=os.path.basename(mediaSrc), tmdbobj=None)

    def processMovieDir(self, mediaSrc, folderCat, folderGenName, folderTmdbParser):
        if os.path.isdir(os.path.join(mediaSrc, 'BDMV')):
            # break, process BDMV dir for this dir
            if self.ARGS.full_bdmv or self.ARGS.extract_bdmv:
                if self.ARGS.unified_folders:
                    # Keep in Movie folder structure
                    self.processBDMV(mediaSrc, folderGenName, self.CATNAME_MOVIE, tmdbParser=folderTmdbParser)
                    self.targetDirHook(os.path.join(self.CATNAME_MOVIE, folderGenName), tmdbidstr=str(folderTmdbParser.tmdbid), tmdbcat=folderTmdbParser.tmdbcat, tmdbtitle=folderTmdbParser.title, tmdbobj=folderTmdbParser)
                else:
                    # Legacy behavior: separate MovieM2TS folder
                    self.processBDMV(mediaSrc, folderGenName, 'MovieM2TS', tmdbParser=folderTmdbParser)
                    self.targetDirHook(os.path.join('MovieM2TS', folderGenName), tmdbidstr=str(folderTmdbParser.tmdbid), tmdbcat=folderTmdbParser.tmdbcat, tmdbtitle=folderTmdbParser.title, tmdbobj=folderTmdbParser)
            else:
                logger.info('Skip BDMV/ISO  %s ' % mediaSrc)
                self.record_skip(os.path.basename(mediaSrc), "BDMV (use --full-bdmv)")
            return

        if not os.path.isdir(mediaSrc):
            return

        testFile = self.getMusicFile(mediaSrc)
        if testFile:
            self.processMusic(mediaSrc, 'Music', folderGenName)
            return

        countMediaFiles = self.countMediaFile(mediaSrc)
        for movieItem in os.listdir(mediaSrc):
            if self.uselessFile(movieItem):
                logger.info('SKIP useless file: [%s] ' % movieItem)
                continue
            if self.selfGenCategoryDir(movieItem):
                logger.info('SKIP self-generated dir: [%s] ' % movieItem)
                continue

            if (os.path.isdir(os.path.join(mediaSrc, movieItem))):
                # Dir in movie folder
                if os.path.isdir(os.path.join(mediaSrc, movieItem, 'BDMV')):
                    logger.info(" Alert: MovieBDMV in a Movie dir.....?")
                    if self.ARGS.unified_folders:
                        self.processBDMV(os.path.join(mediaSrc, movieItem),
                                    os.path.join(folderGenName, movieItem),
                                    self.CATNAME_MOVIE)
                    else:
                        self.processBDMV(os.path.join(mediaSrc, movieItem),
                                    os.path.join(folderGenName, movieItem),
                                    'MovieM2TS')
                else:
                    logger.info('SKip dir in movie folder: [%s] ' % movieItem)
                continue

            filename, file_ext = os.path.splitext(movieItem)
            if file_ext.lower() in ['.iso']:
                # TODO: aruba need iso when extract_bdmv
                if self.ARGS.full_bdmv or self.ARGS.extract_bdmv:
                    if self.ARGS.unified_folders:
                        destCatFolderName = os.path.join(self.CATNAME_MOVIE, folderGenName)
                    else:
                        destCatFolderName = os.path.join('BDMVISO', folderGenName)
                    self.targetCopy(os.path.join(mediaSrc, movieItem), destCatFolderName)
                    self.targetDirHook(destCatFolderName, tmdbidstr='', tmdbcat='iso', tmdbtitle=movieItem, tmdbobj=None)
                else:
                    logger.info('SKip iso file: [%s] ' % movieItem)
                continue

            if not self.isMediaFileType(file_ext):
                logger.info('Skip : %s ' % movieItem)
                continue

            p = folderTmdbParser
            if not (self.ARGS.tmdbid and self.ARGS.single):
                if not folderTmdbParser.tmdbhard and (folderTmdbParser.tmdbid <= 0) or countMediaFiles > 1:
                    fnok = is0DayName(movieItem)
                    if fnok:
                        pf = TMDbNameParser(self.ARGS.tmdb_api_key, self.ARGS.tmdb_lang,
                                            ccfcat_hard=self.setArgsCategory(), cache=self.tmdb_cache)
                        pf.parse(movieItem, useTMDb=(self.ARGS.tmdb_api_key is not None))
                        pf.title = self.fixNtName(pf.title)
                        if pf.tmdbid > 0 or fnok:
                            p = pf

            cat = self.genCatFolderName(p)
            destFolderName = self.genMediaFolderName(p)
            destCatFolderName = os.path.join(cat, destFolderName)
            mediaSrcItem = os.path.join(mediaSrc, movieItem)

            if cat == self.CATNAME_TV:
                logger.info('Miss Categoried TV: [%s] ' % mediaSrc)
                self.copyTVFolderItems(mediaSrc, destFolderName, p.season, p.group,
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
                # catItemFolder = os.path.join(cat, movieItem)
                self.targetCopy(mediaSrcItem, destCatFolderName)
                self.targetDirHook(destCatFolderName, tmdbidstr=str(p.tmdbid), tmdbcat=p.tmdbcat, tmdbtitle=p.title, tmdbobj=p)
                continue
            else:
                if self.ARGS.origin_name:
                    # newMovieName = os.path.basename(movieItem)
                    yearstr = str(p.year) if p.year > 0 else ''
                    newMovieName = self.genMovieOriginName(movieItem, p.title, yearstr,
                                                    nameParser=p)
                elif self.ARGS.tmdb_origin_name:
                    yearstr = str(p.year) if p.year > 0 else ''
                    newMovieName = self.genMovieTMDbOriginName(movieItem, p.title, yearstr,
                                                    nameParser=p)
                else:
                    yearstr = str(p.year) if p.year > 0 else ''
                    newMovieName = self.genMovieResGroup(movieItem, p.title, yearstr,
                                                    p.resolution, p.group, nameParser=p)
                self.targetCopy(mediaSrcItem, destCatFolderName, newMovieName)
                self.mkMediaNfo(destCatFolderName, newMovieName, p)
                self.targetDirHook(destCatFolderName, tmdbidstr=str(p.tmdbid), tmdbcat=p.tmdbcat, tmdbtitle=p.title, tmdbobj=p)

    def mkPlexMatch(self, targetDir, tmdbParser):
        if not self.ARGS.make_plex_match:
            return

        if not tmdbParser:
            return

        pmfilepath = os.path.join(self.ARGS.hd_path, targetDir, '.plexmatch')
        with open(pmfilepath, "w", encoding='utf-8') as pmfile:
            pmfile.write("Title: %s\ntmdbid: %d\n" %
                        (tmdbParser.title, tmdbParser.tmdbid))
            if tmdbParser.year > 1990:
                pmfile.write("Year: %d\n" % (tmdbParser.year))

    def writeNfoFile(self, nfoFilename, etroot):
        # ET.indent(etroot, '  ')
        # etroot.write(nfoFilename, encoding="utf-8", xml_declaration=True)
        with open(nfoFilename, "w", encoding='utf-8') as nfo_file:
            nfo_file.write(ET.tostring(etroot, encoding="unicode"))

    def mkMediaNfo(self, targetDir, mediaFilename, tmdbParser):
        if not self.ARGS.make_nfo:
            return
        if not tmdbParser:
            return
        if tmdbParser.tmdbid < 0:
            return
        
        if tmdbParser.tmdbcat == 'tv':
            root = ET.Element("tvshow")
            nfoFilename = 'tvshow.nfo'
        elif tmdbParser.tmdbcat == 'movie':
            root = ET.Element("movie")
            fn, ext = os.path.splitext(mediaFilename)
            nfoFilename = fn + ".nfo"
        else:
            return
        
        title = ET.SubElement(root, "title")
        title.text = tmdbParser.title

        year = ET.SubElement(root, "year")
        year.text = str(tmdbParser.year)

        tmdbid = ET.SubElement(root, "tmdbid")
        tmdbid.text = str(tmdbParser.tmdbid)

        if not tmdbParser.tmdbDetails:
            tmdbParser.getDetails()
        if hasattr(tmdbParser.tmdbDetails, 'original_title'):
            originaltitle = ET.SubElement(root, "originaltitle")
            originaltitle.text = tmdbParser.tmdbDetails.original_title

        # if hasattr(tmdbParser.tmdbDetails, 'original_language'):
        #     originaltitle = ET.SubElement(root, "original_language")
        #     originaltitle.text = tmdbParser.tmdbDetails.original_title

        if hasattr(tmdbParser.tmdbDetails, 'overview'):
            plot = ET.SubElement(root, "plot")
            plot.text = tmdbParser.tmdbDetails.overview

        if hasattr(tmdbParser.tmdbDetails, 'vote_average'):
            rating = ET.SubElement(root, "rating")
            rating.text = str(tmdbParser.tmdbDetails.vote_average)

        if hasattr(tmdbParser.tmdbDetails, "genres"):
            genre = ET.SubElement(root, "genre")
            for genre_detail in tmdbParser.tmdbDetails.genres:
                genre_item = ET.SubElement(genre, "item")
                genre_item.text = genre_detail["name"]

        mediaDir = self.getDestDir(targetDir)
        if not os.path.exists(mediaDir):
            logger.warning('media dir not created: ' + mediaDir)
            # self.ensureDir(mediaDir)
            return
        nfoFilepath = os.path.join(mediaDir, nfoFilename)
        self.writeNfoFile(nfoFilepath, root)

    def targetDirHook(self, targetDir, tmdbidstr='', tmdbcat='', tmdbtitle='', tmdbobj=None):
        # exportTargetDir = os.path.join(ARGS.hd_path, targetDir)
        exportTargetDir = targetDir
        logger.info('Target Dir: ' + exportTargetDir)
        if self._item_work_done:
            self.record_success()
        else:
            self.record_skip(self.CUR_MEDIA_NAME, "target exists")
        if self.EXPORT_OBJ:
            self.EXPORT_OBJ.onOneItemTorcped(exportTargetDir, self.CUR_MEDIA_NAME, tmdbidstr, tmdbcat, tmdbtitle, tmdbobj)
        if self.ARGS.after_copy_script:
            import subprocess        
            cmd = [self.ARGS.after_copy_script, exportTargetDir, self.CUR_MEDIA_NAME, tmdbidstr, tmdbcat, tmdbtitle]
            subprocess.Popen(cmd).wait()
            # os.system("%s %s" % (ARGS.next_script, targetDir))
        return

    def processOneDirItem(self, cpLocation, itemName, imdbidstr='', tmdbidstr=''):
        self.CUR_MEDIA_NAME = itemName
        self._item_work_done = False  # Reset for each new item
        mediaSrc = os.path.join(cpLocation, itemName)
        if os.path.islink(mediaSrc):
            logger.info('SKIP symbolic link: [%s] ' % mediaSrc)
            self.record_skip(itemName, "symbolic link")
            return

        logger.info(" >> [%s] %s %s" % (itemName, imdbidstr, tmdbidstr))
        cat = self.setArgsCategory()

        # Show TMDB search status
        if self.progress and self.ARGS.tmdb_api_key:
            displayName = itemName[:35] + "..." if len(itemName) > 35 else itemName
            self.progress.set_status(f"TMDB: {displayName}")

        p = TMDbNameParser(self.ARGS.tmdb_api_key, self.ARGS.tmdb_lang, ccfcat_hard=cat, cache=self.tmdb_cache)
        p.parse(itemName, useTMDb=(self.ARGS.tmdb_api_key is not None), hasIMDbId=imdbidstr, hasTMDbId=tmdbidstr, exTitle=self.ARGS.extitle)
        p.title = self.fixNtName(p.title)
        cat = self.genCatFolderName(p)

        destFolderName = self.genMediaFolderName(p)
        destCatFolderName = os.path.join(cat, destFolderName)

        if os.path.isfile(mediaSrc):
            filename, file_ext = os.path.splitext(itemName)
            if self.isMediaFileType(file_ext):
                if cat == self.CATNAME_TV:
                    logger.info('Single Episode file?  %s ' % mediaSrc)
                    if self.ARGS.origin_name:
                        newTVFileName = itemName
                    else:
                        newTVFileName = self.genTVSeasonEpisonGroup(
                            itemName, p.group, p.resolution)
                    # for 香香
                    seasonFolder = self.renameS0d(p.season)                       
                    seasonFolderFullPath = os.path.join(self.ARGS.tv_folder_name, destFolderName,
                                                        seasonFolder)
                    self.targetCopy(mediaSrc, seasonFolderFullPath, newTVFileName)
                    self.mkPlexMatch(os.path.join(self.ARGS.tv_folder_name, destFolderName), p)
                    self.mkMediaNfo(os.path.join(self.ARGS.tv_folder_name, destFolderName), "", p)
                    self.targetDirHook(os.path.join(self.ARGS.tv_folder_name, destFolderName), tmdbidstr=str(p.tmdbid), tmdbcat=p.tmdbcat, tmdbtitle=p.title, tmdbobj=p)
                elif cat == self.CATNAME_MOVIE:
                    if self.ARGS.origin_name:
                        # newMovieName = itemName
                        yearstr = str(p.year) if p.year > 0 else ''
                        newMovieName = self.genMovieOriginName(mediaSrc, p.title,
                                                        yearstr, nameParser=p)
                    elif self.ARGS.tmdb_origin_name:
                        yearstr = str(p.year) if p.year > 0 else ''
                        newMovieName = self.genMovieTMDbOriginName(mediaSrc, p.title,
                                                        yearstr, nameParser=p)
                    else:
                        yearstr = str(p.year) if p.year > 0 else ''
                        newMovieName = self.genMovieResGroup(mediaSrc, p.title,
                                                        yearstr, p.resolution,
                                                        p.group, nameParser=p)
                    self.targetCopy(mediaSrc, destCatFolderName, newMovieName)
                    self.mkMediaNfo(destCatFolderName, newMovieName, p)
                    self.targetDirHook(destCatFolderName, tmdbidstr=str(p.tmdbid), tmdbcat=p.tmdbcat, tmdbtitle=p.title, tmdbobj=p)
                elif cat == 'TMDbNotFound':
                    self.targetCopy(mediaSrc, cat)
                    self.targetDirHook(os.path.join(cat, itemName), tmdbidstr=str(p.tmdbid), tmdbcat=p.tmdbcat, tmdbtitle=p.title, tmdbobj=p)
                else:
                    logger.info('Single media file : [ %s ] %s ' % (cat, mediaSrc))
                    self.targetCopy(mediaSrc, destCatFolderName)
                    self.targetDirHook(destCatFolderName, tmdbidstr=str(p.tmdbid), tmdbcat=p.tmdbcat, tmdbtitle=p.title, tmdbobj=p)
            elif file_ext.lower() in ['.iso']:
                #  TODO: aruba need iso when extract_bdmv
                if self.ARGS.full_bdmv or self.ARGS.extract_bdmv:
                    if self.ARGS.unified_folders:
                        # Use the actual category (Movie or TV)
                        bdmvFolder = os.path.join(cat, destFolderName)
                    else:
                        bdmvFolder = os.path.join('BDMVISO', destFolderName)
                    self.targetCopy(mediaSrc, bdmvFolder)
                    self.targetDirHook(bdmvFolder, tmdbidstr='', tmdbcat='iso', tmdbtitle=itemName, tmdbobj=None)
                else:
                    logger.info('Skip .iso file:  %s ' % mediaSrc)
                    self.record_skip(itemName, "ISO file (use --full-bdmv)")
            else:
                logger.info('Skip file:  %s ' % mediaSrc)
        else:
            if cat == self.CATNAME_TV:
                self.copyTVFolderItems(mediaSrc, destFolderName, p.season, p.group,
                                p.resolution, p)
            elif cat == self.CATNAME_MOVIE:
                self.processMovieDir(mediaSrc, p.ccfcat,
                                destFolderName, folderTmdbParser=p)
            elif cat in ['MV']:
                self.targetCopy(mediaSrc, cat)
                self.targetDirHook(os.path.join(cat, itemName), tmdbidstr='', tmdbcat='mv', tmdbtitle=itemName, tmdbobj=None)
            elif cat in ['Music']:
                self.processMusic(mediaSrc, cat, destFolderName)
            elif cat in ['TMDbNotFound']:
                if p.tmdbcat == 'movie':
                    logger.info('Search media in dir: [ %s ], %s ' % (cat, mediaSrc))
                    self.processMovieDir(mediaSrc, cat, destFolderName, folderTmdbParser=p)
                else:
                    self.targetCopy(mediaSrc, cat)
                    self.targetDirHook(os.path.join(cat, itemName), tmdbidstr='', tmdbcat='notfound', tmdbtitle=itemName, tmdbobj=None)

            elif cat in ['Audio']:
                self.targetCopy(mediaSrc, cat)
                self.targetDirHook(os.path.join(cat, itemName), tmdbidstr='', tmdbcat='audio', tmdbtitle=itemName, tmdbobj=None)
            elif cat in ['eBook']:
                logger.info('Skip eBoook: [%s], %s ' % (cat, mediaSrc))
                self.record_skip(itemName, "eBook")
                # if you don't want to skip these, comment up and uncomment below
                # targetCopy(mediaSrc, p.cat)
            else:
                logger.info('Dir treat as movie folder: [ %s ], %s ' % (cat, mediaSrc))
                self.processMovieDir(mediaSrc, cat, destFolderName, folderTmdbParser=p)

    def makeKeepExts(self):
        if self.ARGS.keep_ext == 'all':
            self.KEEPEXTALL = True
            return
        if self.ARGS.keep_ext:
            argExts = self.ARGS.keep_ext.split(',')
            for ext in argExts:
                ext = ext.strip()
                if ext:
                    if ext[0] == '.':
                        self.KEEPEXTS.append(ext)
                    else:
                        self.KEEPEXTS.append('.' + ext)

    def ensureIMDb(self):
        if self.ARGS.imdbid:
            m1 = re.search(r'(tt\d+)', self.ARGS.imdbid, re.A)
            if m1:
                self.ARGS.imdbid = m1[1]
            else:
                self.ARGS.imdbid = ''

    def loadArgs(self, argv=None):
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
                            help='seperate dir by language(\'cn,en\').')
        parser.add_argument('--genre',
                            help='seperate dir by genre(\'anime,document\').')
        parser.add_argument('--other-dir',
                            help='for any dir Other than Movie/TV.')
        parser.add_argument('--sep-area',
                            action='store_true',
                            help='seperate dir by all production area.')
        parser.add_argument('--sep-area5',
                            action='store_true',
                            help='seperate 5 dirs(cn,hktw,jp,kr,useu,other) by production area.')
        parser.add_argument('--sep-area7',
                            action='store_true',
                            help='seperate 7 dirs(us,cn,hk,tw,jp,kr,occident,other) by production area.')
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
        parser.add_argument('--plex-bracket',
                            action='store_true',
                            help='ex: Alone (2020) {tmdb-509635}')
        parser.add_argument('--make-plex-match',
                            action='store_true',
                            help='Create a .plexmatch file at the top level of a series')
        parser.add_argument('--make-nfo',
                            action='store_true',
                            help='Create a .nfo file in the media dir')
        parser.add_argument('--after-copy-script',
                            default='',
                            help='call this script with destination folder path after link/move')
        parser.add_argument('--imdbid',
                            default='',
                            help='specify the IMDb id, -s single mode only')
        parser.add_argument('--tmdbid',
                            default='',
                            help='specify the TMDb id, -s single mode only')
        parser.add_argument('--extitle',
                            default='',
                            help='specify the extra title to search')
        parser.add_argument('--site-str',
                            help='site-id(ex. hds-12345) folder name, set site strs like (\'chd,hds,ade,ttg\').')
        parser.add_argument('--add-year-dir',
                            action='store_true',
                            help='Add a year dir above the media folder')
        parser.add_argument('--genre-with-area',
                            default='',
                            help='specify genres with area subdir, seperated with comma')
        parser.add_argument('--progress',
                            action='store_true',
                            help='enable progress bar display')
        parser.add_argument('--no-tmdb-cache',
                            action='store_true',
                            help='disable TMDB query cache')
        parser.add_argument('--clear-tmdb-cache',
                            action='store_true',
                            help='clear TMDB cache before running')
        parser.add_argument('--save-skipped',
                            type=str,
                            help='save skipped items list to specified file')
        parser.add_argument('--save-failed',
                            type=str,
                            help='save failed items list to specified file')
        parser.add_argument('--unified-folders',
                            action='store_true',
                            help='merge BDMV/ISO into Movie/TV folders based on content category')
        parser.add_argument('--tmdb-not-found-folder',
                            type=str,
                            default='TMDbNotFound',
                            help='folder name for items that fail TMDb lookup (default: TMDbNotFound)')

        self.ARGS = parser.parse_args(argv)
        self.ensureIMDb()
        self.ARGS.MEDIA_DIR = os.path.expanduser(self.ARGS.MEDIA_DIR)
        self.ARGS.hd_path = os.path.expanduser(self.ARGS.hd_path)
        if self.ARGS.other_dir:
            self.ARGS.other_dir = os.path.expanduser(self.ARGS.other_dir)
        self.makeKeepExts()

    def hasTMDbId(self, str):
        m1 = re.search(r'tmdb(id)?[=-]((m|tv)?-?(\d+))', str.strip(), flags=re.A | re.I)
        if m1:
            return m1[4]
        else:
            return None

    def hasIMDbId(self, str):
        m1 = re.search(r'imdb(id)?\=(tt\d+)', str.strip(), flags=re.A | re.I)
        m2 = re.search(r'(tt\d+)\s*$', str, flags=re.A | re.I)
        if m1:
            return m1[2]
        elif m2:
            return m2[1]
        else:
            return None

    def matchSiteId(self, str):
        if self.ARGS.site_str:
            # argSites = ARGS.site_str.split(',')
            # siteStr = '|'.joint(argSites)
            siteStr = self.ARGS.site_str.replace(',', '|')
        else:
            siteStr = 'chd|hds|ourbits|hdc|ttg|ade|cmct|frds|pter|u2|mteam|hdh|lemon'
        # m1 = re.search(r'(chd|hds|ourbits|hdc|ttg|ade|cmct|frds|pter|u2|mteam|hdh|lemon)-(\d+)$', str.strip(), flags=re.A | re.I)
        m1 = re.search(r'('+siteStr+')-(\d+)$', str.strip(), flags=re.A | re.I)
        if m1:
            return m1[2]
        else:
            return None

    def underSiteIdFolder(self, cpLocation, foldername):
        siteid = self.matchSiteId(foldername)
        if siteid:
            # dirlist = [name for name in os.listdir(os.path.join(cpLocation, foldername)) if os.path.isdir(os.path.join(cpLocation, foldername, name))]
            dirlist = os.listdir(os.path.join(cpLocation, foldername))
            if len(dirlist) >= 1:
                return siteid, dirlist[0]
        return '', ''

    def underIMDbFolder(self, cpLocation, foldername):
        imdbstr = self.hasIMDbId(foldername)
        if imdbstr:
            dirlist = os.listdir(os.path.join(cpLocation, foldername))
            if len(dirlist) >= 1:
                return imdbstr, dirlist[0]
            # dirlist = [name for name in os.listdir(os.path.join(cpLocation, foldername)) if os.path.isdir(os.path.join(cpLocation, foldername, name))]
            # if len(dirlist) == 1:
                # return imdbstr, dirlist[0]
        return '', ''

    def underTMDbFolder(self, cpLocation, foldername):
        tmdbstr = self.hasTMDbId(foldername)
        if tmdbstr:
            dirlist = os.listdir(os.path.join(cpLocation, foldername))
            if len(dirlist) >= 1:
                return tmdbstr, dirlist[0]
        return '', ''

    def parseFolderIMDbId(self, locIn, itemIn):
        siteid, insideSiteFolderName = self.underSiteIdFolder(locIn, itemIn)
        folderIMDb, insideIMDbFolderName = self.underIMDbFolder(locIn, itemIn)
        folderTMDb, insideTMDbFolderName = self.underTMDbFolder(locIn, itemIn)
        if folderIMDb:
            parentLocation = os.path.join(locIn, itemIn)
            itemName = insideIMDbFolderName
        elif folderTMDb:
            parentLocation = os.path.join(locIn, itemIn)
            itemName = insideTMDbFolderName
        elif siteid:
            parentLocation = os.path.join(locIn, itemIn)
            itemName = insideSiteFolderName
        else:
            parentLocation = locIn
            itemName = itemIn
        return parentLocation, itemName, folderIMDb, folderTMDb

    def processWithSameTIMDb(self, parentFolder, folderImdb, folderTmdb):
        for item in os.listdir(parentFolder):
            self.processOneDirItem(parentFolder, item, imdbidstr=folderImdb, tmdbidstr=folderTmdb)

    def print_summary(self):
        """Print processing summary at end of run."""
        total = self.stats['processed'] + len(self.stats['skipped']) + len(self.stats['failed'])
        if total == 0:
            return

        print(f"\n{'='*50}")
        print(f"Processing Summary")
        print(f"{'='*50}")
        print(f"Total items:     {total}")
        print(f"Processed:       {self.stats['processed']}")
        print(f"Skipped:         {len(self.stats['skipped'])}")
        print(f"Failed:          {len(self.stats['failed'])}")

        if self.stats['skipped']:
            print(f"\nSkipped items:")
            # Group by reason
            by_reason = {}
            for item, reason in self.stats['skipped']:
                by_reason.setdefault(reason, []).append(item)
            for reason, items in by_reason.items():
                print(f"  [{reason}] ({len(items)} items)")
                for item in items[:5]:  # Show first 5
                    print(f"    - {item}")
                if len(items) > 5:
                    print(f"    ... and {len(items) - 5} more")

        if self.stats['failed']:
            print(f"\nFailed items:")
            for item, reason in self.stats['failed']:
                print(f"  - {item}: {reason}")

    def save_report_to_file(self, filepath, items, header):
        """Save items list to file."""
        from datetime import datetime
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(f"# {header}\n")
                f.write(f"# Generated: {datetime.now().isoformat()}\n\n")
                for item, reason in items:
                    f.write(f"{item}\t{reason}\n")
            logger.info(f"Saved {header} to {filepath}")
        except IOError as e:
            logger.warning(f"Failed to save {header}: {e}")

    def main(self, argv=None, exportObject=None):
        self.EXPORT_OBJ = exportObject
        self.loadArgs(argv)
        cpLocation = self.ARGS.MEDIA_DIR
        cpLocation = os.path.abspath(cpLocation)

        # Initialize progress bar
        self.progress = TorcpProgress(disable=not self.ARGS.progress)

        # Initialize TMDB cache
        if self.ARGS.tmdb_api_key and not self.ARGS.no_tmdb_cache:
            self.tmdb_cache = TMDbCache()
            if self.ARGS.clear_tmdb_cache:
                self.tmdb_cache.clear()
                logger.info("TMDB cache cleared")

        logger.info("=========>>> " +
            datetime.datetime.now().astimezone().strftime("%Y-%m-%dT%H:%M:%S %z"))

        if self.ARGS.cache:
            searchCache = CacheManager(cpLocation)
            searchCache.openCache()

        argIMDb = self.ARGS.imdbid if (self.ARGS.single and self.ARGS.imdbid) else ''
        argTMDb = self.ARGS.tmdbid if (self.ARGS.single and self.ARGS.tmdbid) else ''

        if os.path.isfile(cpLocation):
            self.progress.start(1, "Processing file")
            self.progress.set_status(os.path.basename(cpLocation)[:50])
            self.processOneDirItem(os.path.dirname(cpLocation),
                            os.path.basename(os.path.normpath(cpLocation)), imdbidstr=argIMDb, tmdbidstr=argTMDb)
            self.progress.update(advance=1)
            self.progress.stop()
        else:
            if self.ARGS.single and not self.isCollections(cpLocation):
                # processOneDirItem(os.path.dirname(cpLocation),
                #                   os.path.basename(os.path.normpath(cpLocation)), imdbidstr)

                parentLocation, itemName, folderimdb, folderTmdb = self.parseFolderIMDbId(os.path.dirname(cpLocation),
                                os.path.basename(os.path.normpath(cpLocation)))
                self.progress.start(1, "Processing")
                self.progress.set_status(itemName[:50])
                if argIMDb or argTMDb:
                    self.processOneDirItem(parentLocation, itemName, imdbidstr=argIMDb, tmdbidstr=argTMDb)
                elif folderimdb or folderTmdb:
                    self.processWithSameTIMDb(parentLocation, folderImdb=folderimdb, folderTmdb=folderTmdb)
                else:
                    self.processOneDirItem(parentLocation, itemName, imdbidstr=folderimdb, tmdbidstr=folderTmdb)
                self.progress.update(advance=1)
                self.progress.stop()

            else:
                # Get list of items and filter useless files for accurate count
                allItems = [item for item in os.listdir(cpLocation) if not self.uselessFile(item)]
                self.progress.start(len(allItems), "Processing media")

                for idx, torFolderItem in enumerate(allItems):
                    parentLocation, itemName, folderimdb, folderTmdb = self.parseFolderIMDbId(cpLocation, torFolderItem)

                    # Update progress with current item name
                    displayName = itemName[:40] + "..." if len(itemName) > 40 else itemName
                    self.progress.update(description=f"[{idx+1}/{len(allItems)}] Processing", status=displayName)

                    if self.isCollections(itemName) and os.path.isdir(
                            os.path.join(parentLocation, itemName)):
                        logger.info('Process collections: %s ' % itemName)
                        packDir = os.path.join(parentLocation, itemName)
                        for fn in os.listdir(packDir):
                            if self.ARGS.cache:
                                if searchCache.isCached(fn):
                                    logger.info('Skipping. File previously linked: %s ' % (fn))
                                    continue
                                else:
                                    searchCache.append(fn)
                            self.processOneDirItem(packDir, fn, imdbidstr='')
                    else:
                        if self.ARGS.cache:
                            if searchCache.isCached(itemName):
                                logger.info('Skipping. File previously linked: %s ' % (itemName))
                                self.progress.update(advance=1)
                                continue
                            else:
                                searchCache.append(itemName)
                    if (folderimdb or folderTmdb) and (parentLocation != cpLocation):
                        self.processWithSameTIMDb(parentLocation, folderImdb=folderimdb, folderTmdb=folderTmdb)
                    else:
                        self.processOneDirItem(parentLocation, itemName, imdbidstr=folderimdb, tmdbidstr=folderTmdb)

                    self.progress.update(advance=1)

                self.progress.stop()

        if self.ARGS.cache:
            searchCache.closeCache()

        # Save TMDB cache
        if self.tmdb_cache:
            self.tmdb_cache.close()

        # Print summary and save reports
        self.print_summary()
        if self.ARGS.save_skipped and self.stats['skipped']:
            self.save_report_to_file(self.ARGS.save_skipped, self.stats['skipped'], "Skipped Items")
        if self.ARGS.save_failed and self.stats['failed']:
            self.save_report_to_file(self.ARGS.save_failed, self.stats['failed'], "Failed Items")


def main():
    logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(funcName)s %(message)s')
    o = Torcp()
    o.main()


if __name__ == '__main__':
    main()
