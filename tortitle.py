import re
from torcategory import GuessCategoryUtils


def isFullAscii(str):
    return re.fullmatch(r'[\w\d ]*', str, re.A)


def containsCJK(str):
    return re.search(r'[\u4e00-\u9fa5\u3041-\u30fc]', str)


def getIndexItem(items, index):
    if index >= 0 and index < len(items):
        return items[index]
    else:
        return ''


def parseJpAniName(torName):
    items = re.findall(r'\[([^]]*)\]', torName)
    if items[0] in [
            'BDMV',
    ]:
        items.pop(0)
    titleIndex = -1
    if isFullAscii(items[0]):
        titleIndex = 0
    elif isFullAscii(items[1]):
        titleIndex = 1

    prevstr = getIndexItem(items, titleIndex - 1)
    if prevstr and containsCJK(prevstr):
        cntitle = prevstr
    else:
        cntitle = ''

    titlestr = getIndexItem(items, titleIndex)

    nextstr = getIndexItem(items, titleIndex + 1)
    if nextstr and containsCJK(nextstr):
        jptitle = nextstr
        jptitleIndex = titleIndex + 1
    else:
        jptitle = ''
        jptitleIndex = titleIndex

    nextstr2 = getIndexItem(items, jptitleIndex + 1)
    if re.search(r'\b\d{4}\b', nextstr2):
        yearstr = nextstr2
        # seasonstr = getIndexItem(items, jptitleIndex+2)
    else:
        yearstr = ''
        # seasonstr = getIndexItem(items, jptitleIndex+1)
    seasonstr = ''

    return titlestr, yearstr, seasonstr, cntitle
    # return None


def parseMovieName(torName):
    if torName.startswith('['):
        return parseJpAniName(torName)

    sstr = GuessCategoryUtils.cutExt(torName)

    sstr = re.sub(
        r'\b((UHD)?\s+BluRay|Blu-?ray|720p|1080[pi]|2160p|576i|WEB-DL|\.DVD\.|WEBRip|HDTV|REMASTERED|LIMITED|Complete|SUBBED|TV Series).*$',
        '',
        sstr,
        flags=re.I)
    sstr = re.sub(r'\[Vol.*\]$', '', sstr, flags=re.I)

    sstr = re.sub(r'\W?(IMAX|Extended Cut)\s*$', '', sstr, flags=re.I)

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

    sstr = re.sub(r'^\W?(BDMV|\BDRemux|\bCCTV\d|[A-Z]{1,5}TV)\W*',
                  '',
                  sstr,
                  flags=re.I)
    seasonstr = ''
    yearstr = ''
    titlestr = sstr
    mcns = re.search(r'(第(\d+)(-\d+)?季)\b', sstr, flags=re.I)
    if mcns:
        seasonstr = 'S' + mcns.group(2)
        sstr = sstr.replace(mcns.group(1), '')
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
            if not re.search(r'[^a-zA-Z_\- 0-9]$', ss2):
                # if not re.search(r'[\u4e00-\u9fa5\u3041-\u30fc]$', ss2):
                sstr = ss2

    titlestr = re.sub(r' +', ' ', sstr).strip()

    cntitle = titlestr
    m = re.search(r'^.*[^a-zA-Z_\- 0-9](S\d+|\s|\.|\d|-)*\b(?=[A-Z])',
                  titlestr,
                  flags=re.A)
    # m = re.search(r'^.*[\u4e00-\u9fa5\u3041-\u30fc](S\d+| |\.|\d|-)*(?=[A-Z])',
    #               titlestr)
    if m:
        cntitle = m.group(0)
        titlestr = titlestr.replace(cntitle, '')
    # if titlestr.endswith(' JP'):
    #     titlestr = titlestr.replace(' JP', '')
    if re.search(r'\bAKA\b', titlestr):
        titlestr = titlestr.split('AKA')[0].strip()

    return titlestr, yearstr, seasonstr, cntitle
