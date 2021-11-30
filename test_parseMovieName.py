import pytest
import torcp


@pytest.mark.parametrize("test_input, e1, e2, e3", [
    ('权力的游戏.第S01-S08.Game.Of.Thrones.S01-S08.1080p.Blu-Ray.AC3.x265.10bit-Yumi',
     'Game Of Thrones', '', 'S01-S08'),
    ('辅佐官：改变世界的人们S01-S02.Chief.of.Staff.2019.1080p.WEB-DL.x265.AC3￡cXcY@FRDS',
     'Chief of Staff', '2019', 'S01-S02'),
    ('半暖时光.The.Memory.About.You.S01.2021.2160p.WEB-DL.AAC.H265-HDSWEB',
     'The Memory About You', '2021', 'S01'),
    ('不惑之旅.To.the.Oak.S01.2021.2160p.WEB-DL.AAC.H265-HDSWEB', 'To the Oak',
     '2021', 'S01'),
    ('不惑之旅.To.the.Oak.S01.2021.V2.2160p.WEB-DL.AAC.H265-HDSWEB', 'To the Oak',
     '2021', 'S01'),
    ('当家主母.Marvelous.Women.S01.2021.V3.2160p.WEB-DL.AAC.H265-HDSWEB',
     'Marvelous Women', '2021', 'S01'),
    ('民警老林的幸福生活.The.Happy.Life.of.People\'s.Policeman.Lao.Lin.S01.2021.2160p.WEB-DL.AAC.H265-HDSWEB',
     'The Happy Life of People\'s Policeman Lao Lin', '2021', 'S01'),
    ('千古风流人物.Qian.Gu.Feng.Liu.Ren.Wu.S01.2021.2160p.WEB-DL.AAC.H265-HDSWEB',
     'Qian Gu Feng Liu Ren Wu', '2021', 'S01'),
    ('太平间闹鬼事件 The Haunting in Connecticut 2009 Blu-ray 1080p AVC DTS-HD MA 7.1-Pete@HDSky',
     'The Haunting in Connecticut', '2009', ''),
    ('一片冰心在玉壶.Heart.of.Loyalty.S01.2021.2160p.WEB-DL.AAC.H265-HDSWEB',
     'Heart of Loyalty', '2021', 'S01'),
    ('住在我隔壁的甲方.Party.A.Who.Lives.Beside.Me.S01.2021.1080p.WEB-DL.AAC.H264-HDSWEB',
     'Party A Who Lives Beside Me', '2021', 'S01'),
    ('铸匠.The.Builders.S01.2021.2160p.WEB-DL.AAC.H265-HDSWEB', 'The Builders',
     '2021', 'S01'),
    ('CCTV1.Yuan.Meng.Zhong.Guo.De.Yao.Zhong.Hua.20211129.HDTV.1080i.H264-HDSTV.ts',
     'Yuan Meng Zhong Guo De Yao Zhong Hua 20211129', '', ''),
    ('CCTV5+.2021.Snooker.UK.Championship.20211129.HDTV.1080i.H264-HDSTV.ts',
     '2021 Snooker UK Championship 20211129', '', ''),
    ('CCTV5+.2021.World.Table.Tennis.Championship.20211130.HDTV.1080i.H264-HDSTV.ts',
     '2021 World Table Tennis Championship 20211130', '', ''),
    ('CCTV5.Total.Soccer.20211129.HDTV.1080i.H264-HDSTV.ts', 'Total Soccer 20211129',
     '', ''),
    ('CCTV9.The.Legend.Of.Film.Ep01-Ep06.HDTV.1080i.H264-HDSTV',
     'The Legend Of Film', '', ''),
    ('The.Boys.S02.2020.1080p.BluRay.DTS.x265-10bit-HDS', 'The Boys', '2020',
     'S02'),
])
def test_parseTVName(test_input, e1, e2, e3):
    a1, a2, a3 = torcp.parseMovieName(test_input)
    assert a1 == e1 and a2 == e2 and a3 == e3
    # assert (a1==e1 and a2==e2 and a3==e3)


# def test_parseTVName():
# ss = [
#     ('权力的游戏.第S01-S08.Game.Of.Thrones.S01-S08.1080p.Blu-Ray.AC3.x265.10bit-Yumi',
#      'Game Of Thrones', '', 'S01-S08'),
#     ('辅佐官：改变世界的人们S01-S02.Chief.of.Staff.2019.1080p.WEB-DL.x265.AC3￡cXcY@FRDS',
#      'Chief of Staff', '2019', 'S01-S02'),

# ]
# for s in ss:
#     assert torcp.parseMovieName(s[0]) == (s[1], s[2], s[3])
