from tmdbv3api import TMDb, TV, Search
import re
from torcategory import GuessCategoryUtils
from tortitle import parseMovieName
from difflib import SequenceMatcher


def transFromCCFCat(cat):
    if re.match('(Movie|BDMV)', cat, re.I):
        return 'movie'
    elif re.match('(TV|HDTV)', cat, re.I):
        return 'tv'
    else:
        return cat


def transToCCFCat(mediatype, originCat):
    if mediatype == 'tv':
        return 'TV'
    elif mediatype == 'movie':
        if not re.match('(movie|BDMV|MV)', originCat, re.I):
            return 'Movie'
    return originCat


def similar(a, b):
    return SequenceMatcher(None, a, b).ratio()


class TMDbNameParser():
    def __init__(self, tmdb_api_key, tmdb_lang, ccfcat_hard=None):
        self.ccfcatHard = ccfcat_hard
        self.ccfcat = ''
        self.title = ''
        self.year = ''
        self.tmdbid = 0
        self.season = ''
        self.episode = ''
        self.cntitle = ''
        self.resolution = ''
        self.group = ''
        self.tmdbcat = ''

        if tmdb_api_key:
            self.tmdb = TMDb()
            self.tmdb.api_key = tmdb_api_key
            self.tmdb.language = tmdb_lang
        else:
            self.tmdb = None
            # self.tmdb.api_key = None

    def clearData(self):
        self.ccfcat = ''
        self.title = ''
        self.year = ''
        self.tmdbid = 0
        self.season = ''
        self.episode = ''
        self.cntitle = ''
        self.resolution = ''
        self.group = ''
        self.tmdbcat = ''

    def parse(self, torname, TMDb=False):
        self.clearData()
        catutil = GuessCategoryUtils()
        self.ccfcat, self.group = catutil.guessByName(torname)
        self.resolution = catutil.resolution
        self.title, self.year, self.season, self.episode, self.cntitle = parseMovieName(
            torname)
        if self.season and (self.ccfcat != 'TV'):
            # print('Category fixed: ' + movieItem)
            self.ccfcat = 'TV'
        if self.ccfcat == 'TV':
            self.season = self.fixSeasonName(self.season)

        if self.ccfcatHard:
            self.ccfcat = self.ccfcatHard

        if TMDb:
            self.tmdbcat = transFromCCFCat(self.ccfcat)
            if self.tmdbcat in ['tv', 'movie']:
                self.searchTMDb(self.title, self.tmdbcat,
                                self.year, self.cntitle)
            self.ccfcat = transToCCFCat(self.tmdbcat, self.ccfcat)

    def fixSeasonName(self, seasonStr):
        if re.match(r'^Ep?\d+(-Ep?\d+)?$', seasonStr,
                    flags=re.I) or not seasonStr:
            return 'S01'
        else:
            return seasonStr.upper()

    def verifyYear(self, resultDate, cat):
        match = False
        resyear = self.year
        m = re.match(r'^(\d+)\b', resultDate)
        if m:
            resyear = m.group(0)
            intyear = int(resyear)
            if cat == 'tv':
                match = not (self.season == 'S01' and self.year and self.year not in [str(intyear-1), str(intyear), str(intyear+1)])
            else:
                match = not self.year or (self.year in [str(intyear-1), str(intyear), str(intyear+1)])
        if match:
            self.year = resyear
        return match

    def saveTmdbTVResultMatch(self, result):
        if result:
            if hasattr(result, 'name'):
                self.title = result.name
                # print('name: ' + result.name)
            elif hasattr(result, 'original_name'):
                self.title = result.original_name
                # print('original_name: ' + result.original_name)
            self.tmdbid = result.id
            self.tmdbcat = 'tv'
            print('Found [%d]: %s' % (self.tmdbid, self.title))
        else:
            print('\033[33mNot match in tmdb: [%s]\033[0m ' % (self.title))

        return result is not None

    def saveTmdbMovieResult(self, result):
        if hasattr(result, 'title'):
            self.title = result.title
        elif hasattr(result, 'original_title'):
            self.title = result.original_title
        # if hasattr(result, 'media_type'):
        #     self.ccfcat = transToCCFCat(result.media_type, self.ccfcat)
        self.tmdbid = result.id
        self.tmdbcat = 'movie'
        print('Found [%d]: %s' % (self.tmdbid, self.title))
        return True

    # def imdbMultiQuery(self, title, year=None):
    #     search = Search()
    #     return search.multi({"query": title, "year": year, "page": 1})

    # def sortByPopularity(resultList):
    #     newlist = sorted(resultList, key=lambda x: x.popularity, reverse=True)

    def getYear(self, datestr):
        intyear = 0
        m2 = re.search(
            r'\b((19\d{2}\b|20\d{2})(-19\d{2}|-20\d{2})?)',
            datestr,
            flags=re.A | re.I)
        if m2:
            yearstr = m2.group(2)
            intyear = int(yearstr)
        # m = re.match(r'^(\d+)\b', datestr)
        # if m:
        #     yearstr = m.group(0)
        #     intyear = int(yearstr)
        return intyear

    def findYearMatch(self, results, year, strict=True):
        for result in results:
            datestr = ''
            if hasattr(result, 'first_air_date'):
                datestr = result.first_air_date
            elif hasattr(result, 'release_date'):
                datestr = result.release_date

            resyear = self.getYear(datestr)
            if year == 0:
                return result

            if strict:
                if resyear == year:
                    return result
            else:
                if resyear in [year-2, year-1, year, year+1, year+2]:
                    self.year = resyear
                    return result
        return None

    def searchTMDb(self, title, cat=None, year=None, cntitle=None):
        searchList = []
        if title == cntitle:
            cntitle = ''
        cuttitle = re.sub(r'\b(Extended|HD|Anthology|Trilogy|Quadrilogy|Tetralogy|Collections?|S\d+|V\d+|4K)\s*$', '', title, flags=re.I)
        cuttitle = re.sub(r'(\d+部曲|全\d+集.*|原盘|系列)\s*$', '', cuttitle, flags=re.I)
        cuttitle = re.sub(r'^\s*(剧集|BBC：?|TLOTR|Documentary|【.*】)', '', cuttitle, flags=re.I)

        m2 = re.search(
            r'\b((19\d{2}\b|20\d{2})(-19\d{2}|-20\d{2})?)\b(?!.*\b\d{4}\b.*)',
            cuttitle,
            flags=re.A | re.I)
        if m2 and m2.span(1)[0] > 0:
            cuttitle = cuttitle[:m2.span(1)[0]].strip()
            cuttitle2 = cuttitle[m2.span(1)[1]:].strip()

        intyear = self.getYear(year)

        if self.ccfcatHard:
            if cat.lower() == 'tv':
                searchList = [('tv', cntitle), ('tv', cuttitle)]
            elif cat.lower() == 'movie':
                searchList = [('movie', cntitle), ('movie', cuttitle)]
        else:
            if cat.lower() == 'tv':
                searchList = [('tv', cntitle), ('tv', cuttitle), ('movie', cntitle), ('movie', cuttitle)]
            elif cat.lower() == 'movie':
                searchList = [('movie', cntitle), ('movie', cuttitle), ('tv', cntitle), ('tv', cuttitle)]

        for s in searchList:
            if s[0] == 'tv' and s[1]:
                print('Search TV: ' + s[1])
                # tv = TV()
                # results = tv.search(s[1])
                search = Search()
                results = search.tv_shows({"query": s[1], "year": str(intyear), "page": 1})
                if len(results) > 0:
                    if intyear > 0 and self.season != 'S01':
                        intyear = 0
                    result = self.findYearMatch(results, intyear, strict=True)
                    if result:
                        self.saveTmdbTVResultMatch(result)
                        return self.tmdbid, self.title, self.year
                    else:
                        result = self.findYearMatch(results, intyear, strict=False)
                        if result:
                            self.saveTmdbTVResultMatch(result)
                            return self.tmdbid, self.title, self.year

            elif s[0] == 'movie' and s[1]:
                print('Search Movie:  %s (%d)' % (s[1], intyear))
                search = Search()
                if intyear == 0:
                    results = search.movies({"query": s[1], "page": 1})
                else:
                    results = search.movies({"query": s[1], "year": str(intyear), "page": 1})

                if len(results) > 0:
                    result = self.findYearMatch(results, intyear, strict=True)
                    if result:
                        self.saveTmdbMovieResult(result)
                        return self.tmdbid, self.title, self.year
                    else:
                        result = self.findYearMatch(results, intyear, strict=False)
                        if result:
                            self.saveTmdbMovieResult(result)
                            return self.tmdbid, self.title, self.year
                elif intyear > 0:
                    results = search.movies({"query": s[1], "page": 1})
                    if len(results) > 0:
                        result = self.findYearMatch(results, intyear, strict=False)
                        if result:
                            self.saveTmdbMovieResult(result)
                            return self.tmdbid, self.title, self.year

        print('\033[31mTMDb Not found: [%s] [%s]\033[0m ' % (title, cntitle))
        return 0, title, year

