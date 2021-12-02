"""
A script copies movie and TV files to your GD drive, in a Emby-happy struct.
"""
#  python3 torcp.py \
#   /home/ccf2012/Downloads/The.Boys.S02.2020.1080p.BluRay.DTS.x264-HDS \
#   --gd_path=gd123:/176/ -s  --dryrun
#
#  python3 torcp.py \
#   /home/ccf2012/Downloads/ \
#   --gd_path=gd123:/176/   --dryrun
#
import re
import os
import glob
import sys
import argparse
import rclone
from torguess import GuessCategoryUtils

GD_CONFIG = r'/root/.config/rclone/rclone.conf'
GD_PATH = r''


def parseMovieName(torName):
    sstr = GuessCategoryUtils.cutExt(torName)

    sstr = re.sub(
        r'((UHD)?\s+BluRay|Blu-?ray|720p|1080[pi]|2160p|576i|WEB-DL|\.DVD\.|WEBRip|HDTV|REMASTERED|LIMITED|Complete|SUBBED|TV Series).*$',
        '',
        sstr,
        flags=re.I)

    dilimers = {
        '[': ' ',
        ']': ' ',
        '.': ' ',
        '{': ' ',
        '}': ' ',
        '_': ' ',
    }
    for original, replacement in dilimers.items():
        sstr = sstr.replace(original, replacement)

    sstr = re.sub(r'^\W?(BDMV|\BDRemux|\bCCTV\d|[A-Z]{1,5}TV)\W*', '', sstr, flags=re.I)
    seasonstr = ''
    yearstr = ''
    titlestr = sstr
    mep = re.search(r'(\bEp?\d+-Ep?\d+)\b', sstr, flags=re.A | re.I)
    if mep:
        seasonstr = mep.group(1)
        sstr = sstr.replace(seasonstr, '')
    m1 = None
    for m1 in re.finditer(r'(\bS\d+(-S\d+)?)\b', sstr, flags=re.A | re.I):
        pass
    # m1 = re.search(r'(\bS\d+(-S\d+)?)\b', sstr, flags=re.A | re.I)
    if m1:
        seasonstr = m1.group(1)
        seasonsapn = m1.span(1)
        sstr = sstr.replace(seasonstr, '')

    m2 = re.search(r'\b((19\d{2}\b|20\d{2})-?(19\d{2}|20\d{2})?)\b',
                   sstr,
                   flags=re.I)
    if m2:
        yearstr = m2.group(1)
        yearspan = m2.span(1)
        if re.search(r'\w.*' + yearstr, sstr):
            sstr = sstr[:yearspan[0] - 1]
    else:
        if m1:
            ss2 = sstr[:seasonsapn[0] - 1]
            if not re.search(r'[\u4e00-\u9fa5\u3041-\u30fc]$', ss2):
                sstr = ss2

    titlestr = re.sub(r' +', ' ', sstr).strip()

    chtitle = titlestr
    m = re.search(r'^.*[\u4e00-\u9fa5\u3041-\u30fc](S\d+| |\.|\d|-)*(?=[A-Z])',
                  titlestr)
    if m:
        chtitle = m.group(0)
        titlestr = titlestr.replace(chtitle, '')
    # if titlestr.endswith(' JP'):
    #     titlestr = titlestr.replace(' JP', '')

    return titlestr, yearstr, seasonstr, chtitle


def rcloneCopy(fromLoc, toLoc):
    print('rclone copy ', fromLoc, GD_PATH + toLoc)

    result = ''
    if not args.dryrun:
        cfg_path = GD_CONFIG
        with open(cfg_path) as f:
            cfg = f.read()
        result = rclone.with_config(cfg).copy(fromLoc, GD_PATH + toLoc)
    return result


def rcloneLs(loc):
    cfg_path = GD_CONFIG
    with open(cfg_path) as f:
        cfg = f.read()

    dirStr = rclone.with_config(cfg).lsd(GD_PATH + loc)['out'].decode("utf-8")
    dirlist = re.sub(r' +-1\s\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\s+-1\s', '',
                     dirStr).split('\n')
    return dirlist


def getSeasonFromFolderName(folderName, failDir=''):
    m1 = re.search(r'(\bS\d+(-S\d+)?)\b', folderName, flags=re.A | re.I)
    if m1:
        return m1.group(1)
    else:
        return failDir


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
        rcloneCopy(tv2FullPath, seasonFolderFullPath)


def copyTVFolderItems(tvSourceFolder, genFolder, parseSeason):
    for tvitem in os.listdir(tvSourceFolder):
        tvitemPath = os.path.join(tvSourceFolder, tvitem)
        if os.path.isdir(tvitemPath):
            seasonFolder = getSeasonFromFolderName(tvitem, failDir=parseSeason)
            copyTVSeasonItems(tvitemPath, genFolder, seasonFolder)
        else:
            seasonFolderFullPath = os.path.join('TV', genFolder, parseSeason)
            rcloneCopy(tvitemPath, seasonFolderFullPath)


def copyMovieFolderItems(movieSourceFolder, movieTargeDir):
    if args.full:
        for movieItem in os.listdir(movieSourceFolder):
            movieFullPath = os.path.join(movieSourceFolder, movieItem)
            rcloneCopy(movieFullPath, movieTargeDir)
    else:
        mediaFilePath = getLargestFile(movieSourceFolder)
        rcloneCopy(mediaFilePath, movieTargeDir)


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


def processOneDir(cpLocation, folderName):
    cat, group = GuessCategoryUtils.guessByName(folderName)
    parseTitle, parseYear, parseSeason, cntitle = parseMovieName(folderName)
    mediaFolderName = genMediaFolderName(cat, parseTitle, parseYear,
                                         parseSeason)
    if cat == 'TV':
        if args.single or (mediaFolderName not in gdTVList):
            copyTVFolderItems(os.path.join(cpLocation, folderName),
                              mediaFolderName, parseSeason)
    elif cat == 'MovieEncode':
        if args.single or (mediaFolderName not in gdMovieList):
            copyMovieFolderItems(os.path.join(cpLocation, folderName),
                                 os.path.join(cat, mediaFolderName))


def loadArgs():
    parser = argparse.ArgumentParser(
        description=
        'A script copies Movies and TVs to your GD drive, in Emby-happy struct.'
    )
    parser.add_argument(
        'MEDIA_DIR',
        help='The directory contains TVs and Movies to be copied.')
    parser.add_argument('--gd_conf',
                        help='the full path to the GD config file.')
    parser.add_argument('--gd_path', required=True, help='the dest GD path.')
    parser.add_argument('--dryrun',
                        action='store_true',
                        help='print msg instead of real copy.')
    parser.add_argument('--single',
                        '-s',
                        action='store_true',
                        help='parse and copy one single folder.')
    parser.add_argument(
        '--full',
        action='store_true',
        help='Movie only: copy all files, otherwise only the largest file')

    global args
    global GD_CONFIG
    global GD_PATH
    args = parser.parse_args()
    if args.gd_conf:
        GD_CONFIG = args.gd_conf
    if args.gd_path:
        GD_PATH = args.gd_path


def main():
    loadArgs()
    cpLocation = args.MEDIA_DIR
    cpLocation = os.path.abspath(cpLocation)

    global gdTVList
    global gdMovieList
    gdTVList = rcloneLs('TV')
    gdMovieList = rcloneLs('MovieEncode')
    if args.single:
        processOneDir(os.path.dirname(cpLocation),
                      os.path.basename(os.path.normpath(cpLocation)))
    else:
        for torFolderItem in os.listdir(cpLocation):
            processOneDir(cpLocation, torFolderItem)


if __name__ == '__main__':
    main()
