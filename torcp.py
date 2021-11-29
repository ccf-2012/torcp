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
        '((UHD)?\s+BluRay|Blu-ray|720p|1080[pi]|2160p|576i|WEB-DL|\.DVD\.|WEBRip|HDTV|REMASTERED|LIMITED|Complete|SUBBED|TV Series).*$',
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
    sstr = re.sub('(BDMV|BDRemux|\bCCTV\d)', '', sstr, flags=re.I)
    sstr = re.sub('\bEp?\d+-Ep?\d+\b.*$', '', sstr, flags=re.I)
    sstr = re.sub(' +', ' ', sstr).strip()

    sstr = re.sub('\S+\w+@\w*', '', sstr)
    # m = re.search('^[\w .]+ \d{4}', sstr)
    # if m:
    #     sstr = m.group(0)

    chtitle = sstr

    m = re.search(
        '^.*[\u4e00-\u9fa5\u3041-\u30fc](S\d+| |\.|\d|-)*(?=[A-Z])', sstr)
    if m:
        chtitle = m.group(0)
        sstr = sstr.replace(chtitle, '')
    sstr = re.sub('\((\w+| )\)?(?!.*\(.*\)).*$', '', sstr).strip()
    if sstr.endswith(' JP'):
        sstr = sstr.replace(' JP', '')

    return sstr if len(sstr) > 6 else chtitle


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
        fullPath = os.path.join(cpLocation, fileItem)
        if os.path.isdir(fullPath):
            parseName = parseMovieName(fileItem)
        else:
            ext = os.path.splitext(fileItem)
            parseName = parseMovieName(ext[0]) + ext[1]
        targetDir = genTargetDir(cat, parseName)
        rcloneCopy(fullPath, targetDir)


if __name__ == '__main__':
    main()
