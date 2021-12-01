import re
import os
import sys
import rclone
from torguess import GuessCategoryUtils

GD_CONFIG = r'/root/.config/rclone/rclone.conf'
GD_PATH = r'gd123:/176/'


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

    sstr = re.sub(r'^\W?(BDMV|\BDRemux|\bCCTV\d)\W*', '', sstr, flags=re.I)
    # sstr = re.sub(r'\S+\w+@\w*', '', sstr)
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

    # titlestr = re.sub(r'\((\w+| )\)?(?!.*\(.*\)).*$', '', sstr).strip()
    # if titlestr.endswith(' JP'):
    #     titlestr = titlestr.replace(' JP', '')

    return titlestr, yearstr, seasonstr, chtitle


def genTargetDir(cat, filename):
    return os.path.join(cat, filename)


def rcloneCopy(fromLoc, toLoc):
    print('rclone copy ', fromLoc, GD_PATH + toLoc)

    cfg_path = GD_CONFIG

    with open(cfg_path) as f:
        cfg = f.read()

    result = rclone.with_config(cfg).copy(fromLoc, GD_PATH + toLoc)

    return result

def getSeasonFromFolderName(folderName, failDir=''):
    m1 = re.search(r'(\bS\d+(-S\d+)?)\b', folderName, flags=re.A | re.I)
    if m1:
        return m1.group(1)
    else:
        return failDir

def main():
    if len(sys.argv) <= 1:
        cpLocation = '.'
    else:
        cpLocation = sys.argv[1]

    for torFolderItem in os.listdir(cpLocation):
        cat, group = GuessCategoryUtils.guessByName(torFolderItem)
        title, year, season, chtitle = parseMovieName(torFolderItem)
        mediaFolderName = title + ' (' + year + ')'
        if cat == 'TV':
            tv0Path = os.path.join(cpLocation, torFolderItem)
            for tv1item in os.listdir(tv0Path):
                tv1FullPath = os.path.join(tv0Path, tv1item)
                if os.path.isdir(tv1FullPath):
                    seasonFolder = getSeasonFromFolderName(tv1item, failDir=season)
                    seasonFolderFullPath = os.path.join(cat, mediaFolderName, seasonFolder)
                    for tv2item in os.listdir(tv1FullPath):
                        tv2FullPath = os.path.join(tv1FullPath, tv2item)
                        rcloneCopy(tv2FullPath, seasonFolderFullPath)
                else:
                    seasonFolderFullPath = os.path.join(cat, mediaFolderName, season)
                    rcloneCopy(tv1FullPath, seasonFolderFullPath )
        elif cat == 'MovieEncode':
            movieParentDir = os.path.join(cat, mediaFolderName)
            movieSource = os.path.join(cpLocation, torFolderItem)
            for movieItem in os.listdir(movieSource):
                movieFullPath = os.path.join(movieSource, movieItem)
                rcloneCopy(movieFullPath, movieParentDir)


if __name__ == '__main__':
    main()
