from tmdbv3api import TMDb, TV, Search
import re
from torcategory import GuessCategoryUtils
from tortitle import parseMovieName
from difflib import SequenceMatcher


def transformCCFCat(cat):
    if re.match('(movie|MV)', cat, re.I):
        return 'movie'
    elif re.match('TV', cat, re.I):
        return 'tv'
    else:
        return ''


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
            tmdb = TMDb()
            tmdb.api_key = tmdb_api_key
            tmdb.language = tmdb_lang

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
            self.tmdbid, self.title, self.year = self.searchTMDb(
                self.title, transformCCFCat(self.ccfcat), self.year,
                self.cntitle)

    def fixSeasonName(self, seasonStr):
        if re.match(r'^Ep?\d+(-Ep?\d+)?$', seasonStr,
                    flags=re.I) or not seasonStr:
            return 'S01'
        else:
            return seasonStr.upper()

    def getTmdbResult(self, result):
        restitle = ''
        resyear = ''
        if hasattr(result, 'original_name'):
            restitle = result.original_name
            print('original_name: ' + result.original_name)
        # elif hasattr(result, 'name'):
        #     restitle = result.name
        #     print('name: ' + result.name)
        elif hasattr(result, 'title'):
            restitle = result.title
            print('title: ' + result.title)
        elif hasattr(result, 'original_title'):
            restitle = result.original_title
            print('original_title: ' + result.original_title)
        if hasattr(result, 'first_air_date'):
            resyear = re.match('^(\d+)', result.first_air_date).group(0)
        elif hasattr(result, 'release_date'):
            resyear = re.match('^(\d+)', result.release_date).group(0)
        return result.id, restitle, resyear

    def imdbCatQuery(self, title, cat, year=None):
        results = []
        if cat == 'tv':
            tv = TV()
            results = tv.search(title)
        elif cat == 'movie':
            search = Search()
            results = search.movies({"query": title, "year": year, "page": 1})
        return results

    def imdbMultiQuery(self, title, year=None):
        search = Search()
        return search.multi({"query": title, "year": year, "page": 1})

    def searchTMDb(self, title, cat=None, year=None, cntitle=None):
        # querystr = urllib.parse.quote(title)
        results = self.imdbCatQuery(title, cat, year)
        if len(results) > 0:
            return self.getTmdbResult(results[0])
        # maxhit = 0.0
        # for result in results:
        #     resid, restitle, resyear = getTmdbResult(result)
        #     ht = similar(restitle, title)
        #     if ht > 0.8:
        #         print("imdbCatQuery %s %f " % (cat, ht))
        #         return resid, restitle, resyear
        #     if ht > maxhit:
        #         maxhit = ht

        results = self.imdbCatQuery(cntitle, cat, year)
        if len(results) > 0:
            return self.getTmdbResult(results[0])

        results = self.imdbMultiQuery(title, year)
        if len(results) > 0:
            self.ccfcat = results[0].media_type
            return self.getTmdbResult(results[0])

        results = self.imdbMultiQuery(cntitle, year)
        if len(results) > 0:
            self.ccfcat = results[0].media_type
            return self.getTmdbResult(results[0])

        print('\033[31mTMDb Not found: [%s] [%s]\033[0m ' % (title, cntitle))
        return 0, title, year


if __name__ == '__main__':
    itemName = 'The.Walking.Dead.S11E10.720p.WEB.h264-GOSSIP.mkv'
    print(itemName)
    # export TMDB_API_KEY='YOUR_API_KEY'
    p = TMDbNameParser('', 'zh-CN')
    p.parse(itemName, TMDb=True)
    print(p.title, p.year, p.tmdbid)
