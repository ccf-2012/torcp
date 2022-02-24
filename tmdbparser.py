from tmdbv3api import TMDb, TV, Search
import re
from torcategory import GuessCategoryUtils
from tortitle import parseMovieName
from difflib import SequenceMatcher


def transFromCCFCat(cat):
    if re.match('(movie|MV)', cat, re.I):
        return 'movie'
    elif re.match('TV', cat, re.I):
        return 'tv'
    else:
        return ''


def transToCCFCat(mediatype, originCat):
    if mediatype == 'tv':
        return 'TV'
    elif mediatype == 'movie':
        if not re.match('(movie|BDMVISO|MV)', originCat, re.I):
            return 'Movie'
    return originCat


def similar(a, b):
    return SequenceMatcher(None, a, b).ratio()


class TMDbNameParser():
    def __init__(self, tmdb_api_key, tmdb_lang):
        self.ccfcat = ''
        self.title = ''
        self.year = ''
        self.tmdbid = 0
        self.season = ''
        self.episode = ''
        self.cntitle = ''
        self.resolution = ''
        self.group = ''

        if tmdb_api_key:
            self.tmdb = TMDb()
            self.tmdb.api_key = tmdb_api_key
            self.tmdb.language = tmdb_lang

    def parse(self, torname, TMDb=False):
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

        if TMDb:
            self.searchTMDb(self.title, transFromCCFCat(self.ccfcat), self.year, self.cntitle)

    def fixSeasonName(self, seasonStr):
        if re.match(r'^Ep?\d+(-Ep?\d+)?$', seasonStr,
                    flags=re.I) or not seasonStr:
            return 'S01'
        else:
            return seasonStr.upper()

    def saveTmdbTVResult(self, result):
        if hasattr(result, 'name'):
            self.title = result.name
            # print('name: ' + result.name)
        elif hasattr(result, 'original_name'):
            self.title = result.original_name
            # print('original_name: ' + result.original_name)
        if hasattr(result, 'first_air_date'):
            m = re.match('^(\d+)', result.first_air_date)
            if m:
                resyear = m.group(0)
                if self.year and self.season == 'S01' and self.year != resyear:
                    result.id = 0
                    print('\033[33mNot match in tmdb: [%s]\033[0m ' % (self.title))
                else:
                    self.year = resyear
        elif hasattr(result, 'release_date'):
            m = re.match('^(\d+)', result.release_date)
            if m:
                self.year = m.group(0)
                if self.year and self.season == 'S01' and self.year != resyear:
                    result.id = 0
                    print('\033[33mNot match in tmdb: [%s]\033[0m ' % (self.title))
                else:
                    self.year = resyear

        if hasattr(result, 'media_type'):
            self.ccfcat = transToCCFCat(result.media_type, self.ccfcat)
        self.tmdbid = result.id

        return result.id, self.title, self.year

    def saveTmdbMovieResult(self, result):
        if hasattr(result, 'title'):
            self.title = result.title
            # print('title: ' + result.title)
        elif hasattr(result, 'original_title'):
            self.title = result.original_title
            # print('original_title: ' + result.original_title)
        if hasattr(result, 'release_date'):
            m = re.match('^(\d+)', result.release_date)
            if m:
                resyear = m.group(0)
                if self.year and self.year != resyear:
                    result.id = 0
                    print('\033[33mNot match in tmdb: [%s]\033[0m ' % (self.title))
                else:
                    self.year = resyear
        elif hasattr(result, 'first_air_date'):
            m = re.match('^(\d+)', result.first_air_date)
            if m:
                self.year = m.group(0)
                if self.year and self.year != resyear:
                    print('\033[33mNot match in tmdb: [%s]\033[0m ' % (self.title))
                    result.id = 0
                else:
                    self.year = resyear
        if hasattr(result, 'media_type'):
            self.ccfcat = transToCCFCat(result.media_type, self.ccfcat)
        self.tmdbid = result.id
        return result.id, self.title, self.year

    def imdbMultiQuery(self, title, year=None):
        search = Search()
        return search.multi({"query": title, "year": year, "page": 1})

    def sortByPopularity(resultList):
        newlist = sorted(resultList, key=lambda x: x.popularity, reverse=True)

    def searchTMDb(self, title, cat=None, year=None, cntitle=None):
        # querystr = urllib.parse.quote(title)
        if cat == 'tv':
            tv = TV()
            print('Search TV: ' + title)
            results = tv.search(title)
            if len(results) > 0:
                return self.saveTmdbTVResult(results[0])
            print('Search TV: ' + cntitle)
            results = tv.search(cntitle)
            if len(results) > 0:
                return self.saveTmdbTVResult(results[0])


        elif cat == 'movie':
            print('Search Movie: ' + title)
            search = Search()
            results = search.movies({"query": title, "year": year, "page": 1})
            if len(results) > 0:
                return self.saveTmdbMovieResult(results[0])

            print('Search Movie: ' + cntitle)
            results = search.movies({"query": cntitle, "year": year, "page": 1})
            if len(results) > 0:
                return self.saveTmdbMovieResult(results[0])

            # maxhit = 0.0
            # for result in results:
            #     resid, restitle, resyear = getTmdbResult(result)
            #     ht = similar(restitle, title)
            #     if ht > 0.8:
            #         print("imdbCatQuery %s %f " % (cat, ht))
            #         return resid, restitle, resyear
            #     if ht > maxhit:
            #         maxhit = ht

        print('Search multi: ' + title)
        results = self.imdbMultiQuery(title, year)
        # if not year:
        #     results.sort(key=lambda x: x.popularity, reverse=True)
        if len(results) > 0:
            if results[0].media_type == 'tv':
                return self.saveTmdbTVResult(results[0])
            else:
                return self.saveTmdbMovieResult(results[0])

        if (cntitle != title):
            print('Search multi: ' + cntitle)
            results = self.imdbMultiQuery(cntitle, year)
            if len(results) > 0:
                self.ccfcat = transToCCFCat(results[0].media_type, self.ccfcat)
                if results[0].media_type == 'tv':
                    return self.saveTmdbTVResult(results[0])
                else:
                    return self.saveTmdbMovieResult(results[0])

        print('\033[31mTMDb Not found: [%s] [%s]\033[0m ' % (title, cntitle))
        return 0, title, year


if __name__ == '__main__':
    itemName = '彩虹宝宝第三季.Rainbow.Ruby.S02.2020.WEB-DL.4k.H265.AAC-HDSWEB'
    print(itemName)
    # export TMDB_API_KEY='YOUR_API_KEY'
    p = TMDbNameParser('', 'zh-CN')
    p.parse(itemName, TMDb=True)
    print(p.title, p.year, p.ccfcat, p.tmdbid)
