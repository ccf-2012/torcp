import requests
import logging
import re


logger = logging.getLogger(__name__)

DOUBAN_API_KEY = '???'

class DoubanApi:
    def __init__(self, douban_api_key, ccfcat_hard=None):
        self.douban_api_key = douban_api_key
        self.ccfcatHard = ccfcat_hard
        self.douban_id = ''
        self.id_url = ''
        self.is_tv = False
        self.title = ''

    """
    jsondata
    'rating': {'max': 10, 'average': '8.4', 'numRaters': 11026, 'min': 0}
    'author': [{'name': '比尔·哈德尔 Bill Hader'}, {'name': '亚力克·博格 Alec Berg'}, {'name': '玛姬·凯瑞 Maggie Carey'}]
    'alt_title': '巴瑞 / 巴里逐梦演艺圈'
    'image': 'https://img1.doubanio.com/view/photo/s_ratio_poster/public/p2514748438.jpg'
    'title': 'Barry'
    'summary': '海军陆战队退役军人巴瑞，在美国中西部地区当杀手，但收入微薄。当他前往洛杉矶执行刺杀任务，却意外参加了一门表演课程，很快和表演伙伴们打成一片。巴瑞在洛杉矶的剧场里，找到一群满怀希望的人们，让他想要开始新生活，但之前背负的罪行却不愿意轻易放过他，巴瑞能否在两个世界找到平衡？'
    'attrs': {'pubdate': ['2018-03-25(美国)'], 'language': ['英语'], 'title': ['Barry'], 'country': ['美国'], 'writer': ['亚力克·博格 Alec Berg', '比尔·哈德尔 Bill Hader'], 'director': ['比尔·哈德尔 Bill Hader', '亚力克·博格 Alec Berg', '玛姬·凯瑞 Maggie Carey'], 'cast': ['比尔·哈德尔 Bill Hader', '斯蒂芬·鲁特 Stephen Root', '萨拉·古德伯格 Sarah Goldberg', '亨利·温克勒 Henry Winkler', '格伦·弗莱舍尔 Glenn Fleshler', '安东尼·凯瑞根 Anthony Carrigan', '达雷尔·布里特-吉布森 Darrell ...itt-Gibson', '安迪·凯瑞 Andy Carey', '亚利桑德罗·弗思 Alejandro Furth', ...], 'episodes': ['8'], 'movie_duration': ['30分钟'], 'year': ['2018'], 'movie_type': ['喜剧']}
        'pubdate': ['2018-03-25(美国)']
        'language': ['英语']
        'title': ['Barry']
        'country': ['美国']
        'writer': ['亚力克·博格 Alec Berg', '比尔·哈德尔 Bill Hader']
        'director': ['比尔·哈德尔 Bill Hader', '亚力克·博格 Alec Berg', '玛姬·凯瑞 Maggie Carey']
        'cast': ['比尔·哈德尔 Bill Hader', '斯蒂芬·鲁特 Stephen Root', '萨拉·古德伯格 Sarah Goldberg', '亨利·温克勒 Henry Winkler', '格伦·弗莱舍尔 Glenn Fleshler', '安东尼·凯瑞根 Anthony Carrigan', '达雷尔·布里特-吉布森 Darrell ...itt-Gibson', '安迪·凯瑞 Andy Carey', '亚利桑德罗·弗思 Alejandro Furth', '柯比·豪厄-尔巴普蒂斯特 Kirby H...l-Baptiste', '宝拉纽森 Paula Newsome', 'John Pirruccello', '马库斯·布朗 Marcus Brown', '马克·伊瓦涅 Mark Ivanir', ...]
        'episodes': ['8']
        'movie_duration': ['30分钟']
        'year': ['2018']
        'movie_type': ['喜剧']
    'id': 'https://api.douban.com/movie/26707518'
    'mobile_link': 'https://m.douban.com/movie/subject/26707518/'
    'alt': 'https://movie.douban.com/movie/26707518'
    'tags': [{'count': 1364, 'name': '美剧'}, {'count': 1106, 'name': '黑色幽默'}, {'count': 1031, 'name': 'HBO'}, {'count': 1019, 'name': '喜剧'}, {'count': 684, 'name': '美国'}, {'count': 509, 'name': '2018'}, {'count': 504, 'name': '杀手'}, {'count': 361, 'name': '剧情'}]
    """
    def searchDoubanByIMDb(self, imdbid):
        url = 'https://api.douban.com/v2/movie/imdb/'+imdbid
        header = {
            'Accept': '*/*',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36',
        }
        auth_data = {
            'apikey': self.douban_api_key
        }
        resp = requests.post(url, data=auth_data, headers=header)
        if not resp:
            logger.error('fail to connect')
            return None
        try:
            jsondata = resp.json()
            self.title = jsondata['title']
            self.alt_title = jsondata['alt_title']
            self.image = jsondata['image']
            self.id_url = jsondata['id']
            self.rating = jsondata['rating']['average']
            self.rating_num = jsondata['rating']['numRaters']
            # self.author = jsondata['author'][0]['name']
            self.summary = jsondata['summary']
            self.tags = jsondata['tags'] 
            # self.attrs 
            if 'attrs' in jsondata:
                self.lanuage = jsondata['attrs']['language'][0]
                self.pubdate = jsondata['attrs']['pubdate'][0]
                self.country = jsondata['attrs']['country'][0]
                self.year = jsondata['attrs']['year'][0] if len(jsondata['attrs']['year']) > 0 else ''
                self.movie_type = jsondata['attrs']['movie_type']
                if 'episodes' in jsondata['attrs']:
                    self.is_tv = True
                    self.episodes = jsondata['attrs']['episodes'][0]

            if m := re.search(r'douban.com/movie/(\d+)', self.id_url):
                self.douban_id = m.group(1)
        except:
            logger.error('Fail to get douban id.')
            return None
        
    def getSubjectPageKeyword(self):
        url = 'https://movie.douban.com/subject/'+self.douban_id
        header = {
            'Accept': '*/*',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36',
        }
        resp = requests.get(url, headers=header)
        if not resp:
            logger.error('fail to connect')
            return False
        html = resp.content.decode("utf-8")
        if m := re.search(r'meta\s+name="keywords"\s+content="([^"]*)"', str(html), re.I):
            # 巴瑞 第一季,Barry Season 1,巴瑞 第一季影评,剧情介绍,图片,论坛"
            keywordstr = m.group(1)
            if m2 := re.search(r'(\w+)\s+第(\w+)季,(.*)\s+Season\s+(\d+)', keywordstr, re.I):
                self.chs_name = m2.group(1)
                self.chs_season = m2.group(2)
                self.eng_name = m2.group(3)
                self.season = m2.group(4)
                logger.debug(f"{self.chs_name}, {self.season}")
                return True
        return False




if __name__ == '__main__':
    d1 = DoubanApi(DOUBAN_API_KEY)
    d1.searchDoubanByIMDb(imdb_id)
    d1.getSubjectPageKeyword()

    # t1 = TMDbNameParser(TMDB_API_KEY, 'zh-CN')
    # t1.searchTMDbByIMDbId(imdb_id)
    # file_info = f'({d1.year})_{t1.title}_{d1.title}_tmdb-{t1.tmdbid}_{imdb_id}_douban-{d1.douban_id}\n'
    # print(file_info)
