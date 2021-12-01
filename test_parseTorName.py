import pytest
import torcp
from torguess import GuessCategoryUtils


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
     '2021 Snooker UK Championship 20211129', '2021', ''),
    ('CCTV5+.2021.World.Table.Tennis.Championship.20211130.HDTV.1080i.H264-HDSTV.ts',
     '2021 World Table Tennis Championship 20211130', '2021', ''),
    ('CCTV5.Total.Soccer.20211129.HDTV.1080i.H264-HDSTV.ts',
     'Total Soccer 20211129', '', ''),
    ('CCTV9.The.Legend.Of.Film.Ep01-Ep06.HDTV.1080i.H264-HDSTV',
     'The Legend Of Film', '', 'Ep01-Ep06'),
    ('The.Boys.S02.2020.1080p.BluRay.DTS.x265-10bit-HDS', 'The Boys', '2020',
     'S02'),
    ('Doctor.X.Surgeon.Michiko.Daimon.S06.1080p.BluRay.x265.10bit.FLAC.MNHD-FRDS',
     'Doctor X Surgeon Michiko Daimon', '', 'S06'),
    ('逆世界.Upside.Down.2012.BluRay.1080p.x265.10bit.2Audio.MNHD-FRDS',
     'Upside Down', '2012', ''),
    ('野战排.Platoon.1986.BluRay.1080p.x265.10bit.2Audio.MNHD-FRDS', 'Platoon',
     '1986', ''),
    ('Stargate.Atlantis.S04.Multi.1080p.BluRay.DTS-HDMA.5.1.H.264-CELESTIS',
     'Stargate Atlantis', '', 'S04'),
    ('谍影重重1-5.The.Bourne.2002-2016.1080p.Blu-ray.x265.DTS￡cXcY@FRDS',
     'The Bourne', '2002-2016', ''),
    ('豹.1963.JPN.1080p.意大利语中字￡CMCT风潇潇', '豹', '1963', ''),
    ('过界男女.2013.国粤双语.简繁中字￡CMCT紫卿醺', '过界男女', '2013', ''),
    ('金刚狼3殊死一战.Logan.2017.BluRay.1080p.x265.10bit.MNHD-FRDS', 'Logan', '2017',
     ''),
    ('(BDMV)Anneke Gronloh - De Regenboog Serie (2009) FLAC-CD] {NL,Telstar B.V,TCD 70316-2}',
     'Anneke Gronloh - De Regenboog Serie', '2009', ''),
    ('Foundation.2021.S01.2160p.ATVP.WEB-DL.DDP5.1.DV.HEVC-CasStudio',
     'Foundation', '2021', 'S01'),
    ('我是你的眼.I\'m.Your.Eyes.2016.S01.2160p.WEB-DL.H265.AAC-LeagueWEB',
     'I\'m Your Eyes', '2016', 'S01'),
])
def test_parseTVName(test_input, e1, e2, e3):
    a1, a2, a3, a4 = torcp.parseMovieName(test_input)
    assert a1 == e1 and a2 == e2 and a3 == e3


@pytest.mark.parametrize("test_input, e1, e2", [
    ('权力的游戏.第S01-S08.Game.Of.Thrones.S01-S08.1080p.Blu-Ray.AC3.x265.10bit-Yumi',
     'TV', 'YUMI'),
    ('辅佐官：改变世界的人们S01-S02.Chief.of.Staff.2019.1080p.WEB-DL.x265.AC3￡cXcY@FRDS',
     'TV', 'FRDS'),
    ('半暖时光.The.Memory.About.You.S01.2021.2160p.WEB-DL.AAC.H265-HDSWEB', 'TV',
     'HDSWEB'),
    ('不惑之旅.To.the.Oak.S01.2021.2160p.WEB-DL.AAC.H265-HDSWEB', 'TV', 'HDSWEB'),
])
def test_guessByName(test_input, e1, e2):
    a1, a2 = GuessCategoryUtils.guessByName(test_input)
    assert a1 == e1 and a2 == e2
