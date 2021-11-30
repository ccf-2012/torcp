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
    sstr = re.sub(r'(BDMV|BDRemux|\bCCTV\d)\W*', '', sstr, flags=re.I)
    sstr = re.sub(r'Ep?\d+-Ep?\d+\b.*$', '', sstr, flags=re.I)
    sstr = re.sub(r' +', ' ', sstr).strip()
    seasonstr = ''
    sstr = re.sub(r'\S+\w+@\w*', '', sstr)
    m = re.search(r'\bS\d+(-S\d+)?\b', sstr, flags=re.A|re.I)
    if m:
        seasonstr = m.group(0)
        sstr = sstr.replace(seasonstr, '')
    yearstr = ''
    m = re.search(r'\w+.*\b(19\d{2}\b|20\d{2})\b.*$', sstr, flags=re.A|re.I)
    if m:
        yearstr = m.group(1)
        sstr = re.sub(yearstr+'.*$', '', sstr)
        # sstr = sstr.replace(yearstr, '')

    chtitle = sstr
    m = re.search(
        r'^.*[\u4e00-\u9fa5\u3041-\u30fc](S\d+| |\.|\d|-)*(?=[A-Z])', sstr)
    if m:
        chtitle = m.group(0)
        sstr = sstr.replace(chtitle, '')
    sstr = re.sub(r'\((\w+| )\)?(?!.*\(.*\)).*$', '', sstr).strip()
    if sstr.endswith(' JP'):
        sstr = sstr.replace(' JP', '')

    titlestr = sstr if len(sstr) > 6 else chtitle
    return titlestr, yearstr, seasonstr
    # return titlestr


def genTargetDir(cat, filename):
    return os.path.join(cat, filename)


def rcloneCopy(fromLoc, toLoc):
    print('rclone copy ', fromLoc, GD_PATH+toLoc)

    cfg_path = GD_CONFIG

    with open(cfg_path) as f:
        cfg = f.read()

    result = rclone.with_config(cfg).copy(fromLoc, GD_PATH+toLoc)

    return result


def main():
    if len(sys.argv) <= 1:
        cpLocation = '.'
    else:
        cpLocation = sys.argv[1]

    for fileItem in os.listdir(cpLocation):
        cat, group = GuessCategoryUtils.guessByName(fileItem)
        title, year, season = parseMovieName(fileItem)
        folderName = title + ' ('+year+')'
        if cat == 'TV':
            if len(season) > 0:
                targetDirParent = os.path.join(cat, folderName, season)
            else:
                targetDirParent = os.path.join(cat, folderName)
            tvPath = os.path.join(cpLocation, fileItem)
            for tvItem in os.listdir(tvPath):
                tvSource = os.path.join(tvPath, tvItem)
                if os.path.isdir(tvSource):
                    rcloneCopy(tvSource, targetDirParent)
                else:
                    rcloneCopy(tvSource, targetDirParent)
        else:
            pass                    


if __name__ == '__main__':
    main()
