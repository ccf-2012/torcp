# -*- coding: utf-8 -*-
import re
import time
from tmdbv3api import TMDb, Movie, TV, Search, Find

from torcp import tortitle
from torcp.torcategory import TorCategory

GENRE_LIST_en = [{'id': 28, 'name': 'Action'}, {'id': 12, 'name': 'Adventure'}, {'id': 16, 'name': 'Animation'}, {'id': 35, 'name': 'Comedy'}, {'id': 80, 'name': 'Crime'}, {'id': 99, 'name': 'Documentary'}, {'id': 18, 'name': 'Drama'}, {'id': 10751, 'name': 'Family'}, {'id': 14, 'name': 'Fantasy'}, {
    'id': 36, 'name': 'History'}, {'id': 27, 'name': 'Horror'}, {'id': 10402, 'name': 'Music'}, {'id': 9648, 'name': 'Mystery'}, {'id': 10749, 'name': 'Romance'}, {'id': 878, 'name': 'Science Fiction'}, {'id': 10770, 'name': 'TV Movie'}, {'id': 53, 'name': 'Thriller'}, {'id': 10752, 'name': 'War'}, {'id': 37, 'name': 'Western'}]
GENRE_LIST_cn = [{'id': 28, 'name': '动作'}, {'id': 12, 'name': '冒险'}, {'id': 16, 'name': '动画'}, {'id': 35, 'name': '喜剧'}, {'id': 80, 'name': '犯罪'}, {'id': 99, 'name': '纪录'}, {'id': 18, 'name': '剧情'}, {'id': 10751, 'name': '家庭'}, {'id': 14, 'name': '奇幻'}, {
    'id': 36, 'name': '历史'}, {'id': 27, 'name': '恐怖'}, {'id': 10402, 'name': '音乐'}, {'id': 9648, 'name': '悬疑'}, {'id': 10749, 'name': '爱情'}, {'id': 878, 'name': '科幻'}, {'id': 10770, 'name': '电视电影'}, {'id': 53, 'name': '惊悚'}, {'id': 10752, 'name': '战争'}, {'id': 37, 'name': '西部'}]

def transFromCCFCat(cat):
    if re.match(r'(Movie)', cat, re.I):
        return 'movie'
    elif re.match(r'(TV)', cat, re.I):
        return 'tv'
    else:
        return cat


def transToCCFCat(mediatype, originCat):
    if mediatype == 'tv':
        return 'TV'
    elif mediatype == 'movie':
        if not re.match(r'(movie)', originCat, re.I):
            return 'Movie'
    return originCat


def tryint(instr):
    try:
        string_int = int(instr)
    except ValueError:    
        string_int = 0
    return string_int

def parseTMDbStr(tmdbstr):
    if tmdbstr.isnumeric():
        return '', tmdbstr
    m = re.search(r'(m(ovie)?|t(v)?)[-_]?(\d+)', tmdbstr.strip(), flags=re.A | re.I)
    if m:
        catstr = 'movie' if m[1].startswith('m') else 'tv'
        return catstr, m[4]
    else:
        return '', ''

class TMDbNameParser():
    def __init__(self, tmdb_api_key, tmdb_lang, ccfcat_hard=None):
        self.ccfcatHard = ccfcat_hard
        self.ccfcat = ''
        self.title = ''
        self.year = 0
        self.tmdbid = 0
        self.season = ''
        self.episode = ''
        self.cntitle = ''
        self.resolution = ''
        self.group = ''
        self.tmdbcat = ''
        self.original_language = ''
        self.popularity = 0
        self.poster_path = ''
        self.genre_ids =[]

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
        self.year = 0
        self.tmdbid = -1
        self.season = ''
        self.episode = ''
        self.cntitle = ''
        self.resolution = ''
        self.group = ''
        self.tmdbcat = ''
        self.original_language = ''
        self.popularity = 0
        self.poster_path = ''
        self.genre_ids =[]
        self.tmdbDetails = None

    def parse(self, torname, useTMDb=False, hasIMDbId=None, hasTMDbId=None):
        self.clearData()
        tc = TorCategory(torname)
        self.ccfcat, self.group = tc.ccfcat, tc.group
        self.resolution = tc.resolution
        tt = tortitle.TorTitle(torname)
        self.title, parseYear, self.season, self.episode, self.cntitle = tt.title, tt.yearstr, tt.season, tt.episode, tt.cntitle 
        self.year = tryint(parseYear)

        if self.season and (self.ccfcat != 'TV'):
            # print('Category fixed: ' + movieItem)
            self.ccfcat = 'TV'
        if self.ccfcat == 'TV':
            self.season = self.fixSeasonName(self.season)

        if self.ccfcatHard:
            self.ccfcat = self.ccfcatHard

        self.tmdbcat = transFromCCFCat(self.ccfcat)

        if useTMDb:
            attempts = 0
            while attempts < 3:
                try:
                    if hasTMDbId:
                        cat, tmdbstr = parseTMDbStr(hasTMDbId)
                        if tmdbstr:
                            tmdbid, title, year = self.searchTMDbByTMDbId(cat, tmdbstr)
                            if tmdbid > 0:
                                print(tmdbid, title, self.ccfcat, self.year)
                                return True
                    if hasIMDbId:
                        tmdbid, title, year = self.searchTMDbByIMDbId(hasIMDbId)
                        if tmdbid > 0:
                            print(tmdbid, title, self.ccfcat, self.year)
                            return
                    if not self.checkNameContainsId(torname):
                        if self.tmdbcat in ['tv', 'movie', 'Other', 'HDTV']:
                            self.searchTMDb(self.title, self.tmdbcat,
                                            parseYear, self.cntitle)
                    self.ccfcat = transToCCFCat(self.tmdbcat, self.ccfcat)
                    
                    break
                except:
                    attempts += 1
                    print("TMDb connection failed. Trying %d " % attempts)
                    time.sleep(3)


    def getDetails(self):
        attempts = 0
        while attempts < 3:
            try:
                if self.tmdbid > 0:
                    if self.tmdbcat == 'movie':
                        movie = Movie()
                        self.tmdbDetails = movie.details(self.tmdbid)
                    elif self.tmdbcat == 'tv':
                        tv = TV()
                        self.tmdbDetails = tv.details(self.tmdbid)
                break
            except:
                attempts += 1
                print("TMDb connection failed. Trying %d " % attempts)
                time.sleep(3)


    def getGenres(self):
        ll = []
        if self.genre_ids:
            for x in self.genre_ids:
                s = next((y for y in GENRE_LIST_cn if y['id']==x), None)
                if s:
                    ll.append(s['name'])
        return ll

    def getProductionArea(self):
        if not self.tmdbDetails:
            self.getDetails()
        if self.tmdbcat == 'tv':
            # print(self.tmdbDetails.origin_country)
            if self.tmdbDetails and self.tmdbDetails.origin_country:
                return self.tmdbDetails.origin_country[0]
            elif 'original_language' in self.tmdbDetails:
                return self.tmdbDetails['original_language']
        else:            
            if self.tmdbDetails and self.tmdbDetails.production_countries:
                if 'iso_3166_1' in self.tmdbDetails.production_countries[0]:
                    return self.tmdbDetails.production_countries[0]['iso_3166_1']
            elif 'original_language' in self.tmdbDetails:
                return self.tmdbDetails['original_language']

        return ''
        # if self.tmdbDetails and self.tmdbDetails.production_companies:
        #     r = self.tmdbDetails.production_companies[0].origin_country
        # return r

    def fixSeasonName(self, seasonStr):
        if re.match(r'^Ep?\d+(-Ep?\d+)?$', seasonStr,
                    flags=re.I) or not seasonStr:
            return 'S01'
        else:
            return seasonStr.upper()

    # def verifyYear(self, resultDate, checkYear, cat):
    #     match = False
    #     resyear = checkYear
    #     m = re.match(r'^(\d+)\b', resultDate)
    #     if m:
    #         resyear = m.group(0)
    #         intyear = int(resyear)
    #         if cat == 'tv':
    #             match = not (self.season == 'S01' and self.year and self.year not in [str(intyear-1), str(intyear), str(intyear+1)])
    #         else:
    #             match = not self.year or (self.year in [str(intyear-1), str(intyear), str(intyear+1)])
    #     if match:
    #         self.year = resyear
    #     return match

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
            if hasattr(result, 'original_language'):
                if result.original_language == 'zh':
                    self.original_language = 'cn'
                else:
                    self.original_language = result.original_language
            if hasattr(result, 'popularity'):
                self.popularity = result.popularity
            if hasattr(result, 'poster_path'):
                self.poster_path = result.poster_path
            if hasattr(result, 'first_air_date'):
                self.year = self.getYear(result.first_air_date)
            elif hasattr(result, 'release_date'):
                self.year = self.getYear(result.release_date)
            else:
                self.year = 0
            if hasattr(result, 'genre_ids'):
                self.genre_ids = result.genre_ids
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
        if hasattr(result, 'original_language'):
            if result.original_language == 'zh':
                self.original_language = 'cn'
            else:
                self.original_language = result.original_language
        if hasattr(result, 'popularity'):
            self.popularity = result.popularity
        if hasattr(result, 'poster_path'):
            self.poster_path = result.poster_path
        if hasattr(result, 'release_date'):
            self.year = self.getYear(result.release_date)
        elif hasattr(result, 'first_air_date'):
            self.year = self.getYear(result.first_air_date)
        else:
            self.year = 0
        if hasattr(result, 'genre_ids'):
            self.genre_ids = result.genre_ids
        
        print('Found [%d]: %s' % (self.tmdbid, self.title))
        return True

    def saveTmdbMultiResult(self, result):
        if hasattr(result, 'media_type'):
            self.imdbcat = result.media_type
            if result.media_type == 'tv':
                self.saveTmdbTVResultMatch(result)
            elif result.media_type == 'movie':
                self.saveTmdbMovieResult(result)
            else:
                print('Unknow media_type %s ' % result.media_type)
        return

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
            intyear = tryint(yearstr)
        return intyear

    def getTitle(self, result):
        tt = ''
        if hasattr(result, 'name'):
            tt = result.name
        elif hasattr(result, 'title'):
            tt = result.title
        elif hasattr(result, 'original_name'):
            tt = result.original_name
        elif hasattr(result, 'original_title'):
            tt = result.original_title
        return tt


    def containsCJK(self, str):
        return re.search(r'[\u4e00-\u9fa5]', str)

    def findYearMatch(self, results, year, strict=True):
        matchList = []
        for result in results:
            if year == 0:
                matchList.append(result)
                continue

            datestr = ''
            if hasattr(result, 'first_air_date'):
                datestr = result.first_air_date
            elif hasattr(result, 'release_date'):
                datestr = result.release_date

            resyear = self.getYear(datestr)
                # return result

            if strict:
                if resyear == year:
                    matchList.append(result)
                    continue
            else:
                if resyear in [year-3, year-2, year-1, year, year+1]:
                    self.year = resyear
                    matchList.append(result)
                    continue

        if len(matchList) > 0:
            # prefer item with CJK
            if self.tmdb.language == 'zh-CN':
                for item in matchList[:3]:
                    tt = self.getTitle(item)
                    if not tt:
                        continue
                    if self.containsCJK(tt):
                        return item
            return matchList[0]
        return None

    def selectOrder(self, cntitle, cuttitle, list):
        if len(cntitle) < 3 and len(cuttitle)> 5:
            list[0], list[1] = list[1], list[0]
            return list
        else:
            return list
    
    def fixTmdbParam(self, tparam):
        if "year" in tparam and len(tparam["year"]) != 4:
            del tparam["year"]
        return tparam

    def replaceRomanNum(self, titlestr):
        # no I and X
        romanNum = [ (r'\bII\b', '2'), (r'\bIII\b', '3'), (r'\bIV\b', '4'), (r'\bV\b', '5'), (r'\bVI\b', '6'), (r'\bVII\b', '7'), (r'\bVIII\b', '8'),
                    (r'\bIX\b', '9'), (r'\bXI\b', '11'), (r'\bXII\b', '12'), (r'\bXIII\b', '13'), (r'\bXIV\b', '14'), (r'\bXV\b', '15'), (r'\bXVI\b', '16')]
        for s in romanNum:
            titlestr = re.sub(s[0], s[1], titlestr, flags=re.A)
        return titlestr

    def searchTMDb(self, title, cat=None, parseYearStr=None, cntitle=None):
        searchList = []
        if title == cntitle:
            cntitle = ''
        cuttitle = re.sub(r'\b(Extended|Anthology|Trilogy|Quadrilogy|Tetralogy|Collections?)\s*$', '', title, flags=re.I)
        cuttitle = re.sub(r'\b(Extended|HD|S\d+|E\d+|V\d+|4K|DVD|CORRECTED|UnCut|SP)\s*$', '', cuttitle, flags=re.I)
        cuttitle = re.sub(r'^\s*(剧集|BBC：?|TLOTR|Jade|Documentary|【[^】]*】)', '', cuttitle, flags=re.I)
        cuttitle = re.sub(r'(\d+部曲|全\d+集.*|原盘|系列|\s[^\s]*压制.*)\s*$', '', cuttitle, flags=re.I)
        cuttitle = re.sub(r'(\b国粤双语|[\b\(]?\w+版|\b\d+集全).*$', '', cuttitle, flags=re.I)
        cuttitle = re.sub(r'(The[\s\.]*(Complete\w*|Drama\w*|Animate\w*)?[\s\.]*Series|The\s*Movie)\s*$', '', cuttitle, flags=re.I)
        cuttitle = re.sub(r'\b(Season\s?\d+)\b', '', cuttitle, flags=re.I)
        if cntitle:
            cntitle = re.sub(r'(\d+部曲|全\d+集.*|原盘|系列|\s[^\s]*压制.*)\s*$', '', cntitle, flags=re.I)
            cntitle = re.sub(r'(\b国粤双语|[\b\(]?\w+版|\b\d+集全).*$', '', cntitle, flags=re.I)

        cuttitle = self.replaceRomanNum(cuttitle)

        m1 = re.search(r'the movie\s*$', cuttitle, flags=re.A | re.I)        
        if m1 and m1.span(0)[0] > 0:
            cuttitle = cuttitle[:m1.span(0)[0]].strip()
            cat = 'movie'

        m2 = re.search(
            r'\b((19\d{2}\b|20\d{2})(-19\d{2}|-20\d{2})?)\b(?!.*\b\d{4}\b.*)',
            cuttitle,
            flags=re.A | re.I)
        if m2 and m2.span(1)[0] > 0:
            cuttitle = cuttitle[:m2.span(1)[0]].strip()
            cuttitle2 = cuttitle[m2.span(1)[1]:].strip()

        intyear = self.getYear(parseYearStr)

        if self.ccfcatHard:
            if cat.lower() == 'tv':
                searchList = [('tv', cntitle), ('tv', cuttitle)]
            elif cat.lower() == 'movie':
                searchList = [('movie', cntitle), ('movie', cuttitle)]
        else:
            if self.season:
                searchList = self.selectOrder(cntitle, cuttitle, [('tv', cntitle), ('tv', cuttitle), ('multi', cntitle)])
            elif cat.lower() == 'tv':
                searchList = self.selectOrder(cntitle, cuttitle, [('multi', cntitle), ('tv', cuttitle), ('multi', cuttitle)])
            elif cat.lower() == 'hdtv':
                searchList = [('multi', cntitle), ('multi', cuttitle)]
            elif cat.lower() == 'movie':
                searchList = self.selectOrder(cntitle, cuttitle, [('movie', cntitle), ('multi', cntitle), ('movie', cuttitle), ('multi', cuttitle)])
            else:
                searchList = [('multi', cntitle), ('multi', cuttitle)]

        for s in searchList:
            if s[0] == 'tv' and s[1]:
                print('Search TV: ' + s[1])
                # tv = TV()
                # results = tv.search(s[1])
                search = Search()

                results = search.tv_shows(self.fixTmdbParam({"query": s[1], "year": str(intyear), "page": 1}))
                if len(results) > 0:
                    if intyear > 0:
                        if self.season and 'S01' not in self.season:
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
                    results = search.movies(self.fixTmdbParam({"query": s[1], "year": str(intyear), "page": 1}))

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
            elif s[0] == 'multi' and s[1]:
                print('Search Multi:  %s (%d)' % (s[1], intyear))
                search = Search()
                if intyear == 0:
                    results = search.multi({"query": s[1], "page": 1})
                else:
                    results = search.multi(self.fixTmdbParam({"query": s[1], "year": str(intyear), "page": 1}))

                if len(results) > 0:
                    result = self.findYearMatch(results, intyear, strict=True)
                    if result:
                        self.saveTmdbMultiResult(result)
                        return self.tmdbid, self.title, self.year
                    else:
                        result = self.findYearMatch(results, intyear, strict=False)
                        if result:
                            self.saveTmdbMultiResult(result)
                            return self.tmdbid, self.title, self.year
                elif intyear > 0:
                    results = search.multi({"query": s[1], "page": 1})
                    if len(results) > 0:
                        result = self.findYearMatch(results, intyear, strict=True)
                        if result:
                            self.saveTmdbMultiResult(result)
                            return self.tmdbid, self.title, self.year
                        else:
                            result = self.findYearMatch(results, intyear, strict=False)
                            if result:
                                self.saveTmdbMultiResult(result)
                                return self.tmdbid, self.title, self.year

        print('\033[31mTMDb Not found: [%s] [%s]\033[0m ' % (title, cntitle))
        return 0, title, intyear


    # TODO: to be continue
    def checkNameContainsId(self, torname):
        m = re.search(r'\[imdb(id)?\=(tt\d+)\]', torname, flags=re.A | re.I)
        if m:
            tmdbid, title, year = self.searchTMDbByIMDbId(m[2])
            if tmdbid > 0:
                return True
        m = re.search(r'\[tmdb(id)?\=(\d+)\]', torname, flags=re.A | re.I)
        if m:
            tmdbid, title, year = self.searchTMDbByTMDbId(self.tmdbcat, m[2])
            if tmdbid > 0:
                return True
        return False

    def searchTMDbByIMDbId(self, imdbid):
        f = Find(self.tmdb)
        print("Search : " + imdbid)
        t = f.find_by_imdb_id(imdb_id=imdbid)
        if t:
            # print(t)
# (Pdb) p t.movie_results
# [{'adult': False, 'backdrop_path': '/rcmjVmKBKONXk2LCe7GOAIHaIAO.jpg', 'id': 1068249, 'title': 'Reborn Rich', 'original_language': 'ko', 'original_title': '재벌집 막내아들', 'overview': '...', 'poster_path': '/xVtekQdaJ00cQqK2oyVJg5P7a6H.jpg', 'media_type': 'movie', 'genre_ids': [18, 14], 'popularity': 1.4, 'release_date': '2022-11-18', 'video': False, 'vote_average': 0.0, 'vote_count': 0}]
# (Pdb) t.tv_results
# [{'adult': False, 'backdrop_path': '/jG8mKDxe0LIDFBPB8uCeYGSBWCH.jpg', 'id': 153496, 'name': 'Reborn Rich', 'original_language': 'ko', 'original_name': '재벌집 막내아들', 'overview': '....', 'poster_path': '/ioywelRYOfNJ5w8aNQ5ttJo9dk1.jpg', 'media_type': 'tv', 'genre_ids': [18, 10765], 'popularity': 70.232, 'first_air_date': '2022-11-18', 'vote_average': 8.094, 'vote_count': 32, 'origin_country': ['KR']}]
            if self.tmdbcat == "tv":
                if t.tv_results:
                    self.tmdbcat = "tv"
                    r = t['tv_results'][0]
                    self.saveTmdbTVResultMatch(r)
                elif t.movie_results:
                    self.tmdbcat = "movie"
                    r = t['movie_results'][0]
                    self.saveTmdbMovieResult(r)
                else:
                    pass
            else: 
                if t.movie_results:
                    self.tmdbcat = "movie"
                    r = t['movie_results'][0]
                    self.saveTmdbMovieResult(r)
                elif t.tv_results:
                    self.tmdbcat = "tv"
                    r = t['tv_results'][0]
                    self.saveTmdbTVResultMatch(r)
                else:
                    pass

        return self.tmdbid, self.title, self.year


    def searchTMDbByTMDbIdTv(self, tmdbid):
        tv = TV(self.tmdb)
        print("Search tmdbid in TV: " + tmdbid)
        try:
            t = tv.details(tmdbid)
            if t:
                self.saveTmdbTVResultMatch(t)
        except:
            pass
        return self.tmdbid, self.title, self.year 

    def searchTMDbByTMDbIdMovie(self, tmdbid):
        movie = Movie(self.tmdb)
        print("Search tmdbid in Movie: " + tmdbid)
        try:
            m = movie.details(tmdbid)
            if m:
                self.saveTmdbMovieResult(m)
        except:
            pass
        return self.tmdbid, self.title, self.year 

    def searchTMDbByTMDbId(self, cat, tmdbid):
        if cat == 'tv':
            return self.searchTMDbByTMDbIdTv(tmdbid)
        elif cat == 'movie':
            return self.searchTMDbByTMDbIdMovie(tmdbid)
        else:
            self.searchTMDbByTMDbIdTv(tmdbid)
            if self.tmdbid <= 0:
                return self.searchTMDbByTMDbIdMovie(tmdbid)

        return self.tmdbid, self.title, self.year 
