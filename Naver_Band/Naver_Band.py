import urllib
import requests
#import pandas as pd
import os
import DataBase.MySQL_control
from datetime import datetime
import FinanceDataReader as fdr
import numpy as np
import re
import Band_type
#토큰화 및 데이터준비

import logging
import pandas as pd
#from pykospacing import spacing
from hanspell import spell_checker
from config.log_class import Logging

class Naver_Band():
    def __init__(self):
        self.actoken = 'ZQAAAS8VjFnwouVo7VtfoZMFOuaLRtMq8FYHR4_2iF58PTedL7M7gSed5swJYn0Y8GOLH0x5ODXE64d4nxK5amyojrOumVpD0olsXnVgAPhPtK5b'
        self.profile_url = "http://openapi.band.us/v2/profile"
        self.bandlist_url = "https://openapi.band.us/v2.1/bands"
        self.postlist_url = 'https://openapi.band.us/v2/band/posts'
        self.ROOT_DIR = os.path.abspath(os.curdir)
        self.SQL = DataBase.MySQL_control.DB_control()
        self.Skima = 'system_parameter'
        self.TABLE_NAVER_BAND = 'naver_band_밴드목록조회'
        self.ROI_band_name = '추세선을보라! 믿어라 벌것이다.'
        self.ROI_author_name = '강한로직27세 ☆ 훈 (운영자)'
        self.comment_df = pd.DataFrame(data=None)
        self.comment_check_flag = False
        self.diff_comment_pass = True
        self.comment_list_prev = []
        self._latest_post = None
        self._latest_comment = None
        self.NB_meme_dict = {}
        # 초기에 band 정보 업데이트
        self.list_update = False
        if self.list_update:
            self._profile_load()
            self._bandlist_load()
        self.list_update = False
        format = "%(asctime)s: %(message)s"
        self.ROOT_DIR = os.path.abspath(os.curdir)
        path = self.ROOT_DIR+'\\config\\logging.conf'
        self.logging = Logging(path)
        self.logging.logger.debug("Naver_Band class start.")

        self.HTH_CMD = Band_type.HTH_CMD()

    def data_spell_spacing_func(self, data_Series):
        # print('sub-process {}: starting'.format(name))
        data_list = list(data_Series['spell_spacing_correction_filter'])
        spacing_list = []
        spell_list = []
        new_respacing_data = []
        no_spacing_data = []
        # 띄워쓰기 제거 후 띄워쓰기 재설정/ 스펠 검사
        for num, data in enumerate(data_list):
            try:
                #self.logging.logger.debug("noSpacing_data {}/{}".format(num, len(data_list)))
                no_spacing_data.append(data.replace(" ",""))
            except:
                no_spacing_data.append(data)
                self.logging.logger.debug("noSpacing_data {}/{}".format(num, len(data_list)))
                pass

        for num, data in enumerate(no_spacing_data):
            try:
                #self.logging.logger.debug("spacing_data {}/{}".format(num, len(no_spacing_data)))
                spacing_list.append(spacing(data))
            except:
                spacing_list.append(data)
                self.logging.logger.debug("spacing_data {}/{}".format(num, len(no_spacing_data)))
                pass

        for num, content in enumerate(spacing_list):
            try:
                #self.logging.logger.debug("spell_data {}/{}".format(num, len(spacing_list)))
                spelled_sent = spell_checker.check(content)
                spell_list.append(spelled_sent.checked)
            except:
                self.logging.logger.debug("spell_data {}/{}".format(num, len(spacing_list)))
                spell_list.append(content)
                pass

        for num, data in enumerate(spell_list):
            try:
                #self.logging.logger.debug("respacing_data {}/{}".format(num, len(spell_list)))
                new_respacing_data.append(spacing(data))
            except:
                self.logging.logger.debug("respacing_data {}/{}".format(num, len(spell_list)))
                new_respacing_data.append(data)
                pass

        data_Series['spell_spacing_correction_filter'] = new_respacing_data
        # print('sub-process {}: Finishing'.format(name))
        return data_Series

    def _get_data_decode(self, cmd, data):
        if cmd == 'NAVER_BAND_profile':
            data_result = pd.DataFrame(data=data)
            data_result.to_csv(self.ROOT_DIR + "\\files\\profilelist.csv", encoding='euc-kr')
        elif cmd == 'NAVER_BAND_밴드목록조회':
            data_result = pd.DataFrame(data=data)
            data_result.to_csv(self.ROOT_DIR + "\\files\\bandlist.csv", encoding='euc-kr')
        elif cmd == 'NAVER_BAND_글목록조회':
            return data
            # data_result = pd.DataFrame(data = data)
            # data_result.to_csv(self.ROOT_DIR +"\\files\\postlist.csv",encoding='euc-kr')

        if self.list_update:
            self.SQL.DB_SAVE(self.Skima, self.TABLE_NAVER_BAND, data_result)

        return data_result

    def _profile_load(self):
        cmd_type = 'NAVER_BAND_profile'
        authorization_code = 'access_token='
        url = self.profile_url + "?" + authorization_code + self.actoken
        get_data = requests.get(url).json()
        result = self._get_data_decode(cmd_type, get_data)
        return result

    def _bandlist_load(self):
        cmd_type = 'NAVER_BAND_밴드목록조회'
        authorization_code = 'access_token='
        url = self.bandlist_url + "?" + authorization_code + self.actoken
        get_data = requests.get(url).json()
        get_data = get_data['result_data']['bands']
        result = self._get_data_decode(cmd_type, get_data)
        return result

    # 여기서는 최신의 글만 넘겨주자...댓글분석은 다른곳에서...
    def _latest_post_comment_list_load(self, band_name):
        cmd_type = 'NAVER_BAND_글목록조회'
        bandlist = self.SQL.DB_LOAD_Table(self.Skima, self.TABLE_NAVER_BAND)
        bandlist = bandlist.set_index('name')
        ROI_bandkey = bandlist.loc[band_name]['band_key']
        authorization_code = 'access_token='
        url = self.postlist_url + "?" + authorization_code + self.actoken + "&band_key=" + ROI_bandkey + "&locale=kr_KR"
        get_data = requests.get(url).json()
        get_data = get_data['result_data']['items']
        comment_list = []
        for data in get_data:
            temp_post = [data['created_at'], data['content']]
            comment_list.append(temp_post)
            if data['comment_count']:
                for comment in data['latest_comments']:
                    comment_list.append([comment['created_at'], comment['body']])
        temp_df = pd.DataFrame(data=comment_list, columns=['created_at', 'content'])
        temp_df = temp_df.set_index('created_at').sort_values(by='created_at', ascending=False)
        today = datetime.today().strftime("%Y%m%d")
        # 알고리즘 통과하도록...여기서는 Df형태로 최신 댓글 및 post를 전달하기만 하자
        # 조건식을 넣어서 이전 데이터와 차이나는 부분만 넘기자...
        if self.diff_comment_pass:
            try:
                diff_index = list(set(temp_df.index).intersection(self.comment_df.index))
            except:
                diff_index = []
            temp_df = temp_df.drop(diff_index)
        if not self.comment_check_flag:
            self.comment_df = temp_df
            self.comment_check_flag = True
        else:
            self.comment_df = pd.concat([self.comment_df, temp_df])
            # self.comment_df = pd.merge(self.comment_df, temp_df, how='outer', left_index=True, right_index=True)
        self.comment_df = self.comment_df.sort_values(by='created_at')
        today = datetime.today().strftime("%Y%m%d")
        self.SQL.DB_SAVE(self.Skima, '한태훈_' + today, self.comment_df)

        return temp_df

    # 대문자 변환
    def transfer(self, my_str):
        my_str_list = list(my_str)
        # aeiou_list = ['a', 'e', 'i', 'o', 'u']
        new_str_list = []
        for each_str in my_str_list:
            if each_str == " ":
                pass
            else :
                new_str_list.append(each_str.upper())
        return ''.join(new_str_list)

    # 스크리닝 단어 들어가있는 comment는 삭제 함수

    def HTH_Comment_Screen_Filter(self, content_df):
        screen_list = []
        total_list = []
        #content_df = content_df[['spell_spacing_correction_filter']].dropna()
        #for i, content in enumerate(content_df['spell_spacing_correction_filter']):
        for i, content in enumerate(content_df['content']):
            total_list.append(i)
            for screen in self.HTH_CMD.HTH_CMD['스크리닝']:
                if screen in content:
                    screen_list.append(i)
                    break

        not_screen_list=[x for x in total_list if x not in screen_list]
        result_df = content_df.iloc[not_screen_list]
        return result_df

    # 매매기준으로 '매수','매도', '매도후매수'로 분류
    def HTH_Comment_Meme_Filter(self, content_df):
        buy_update_list = []
        sell_update_list = []
        sell_buy_update_list = []
        ambiguous_update_list = []
        #content_df.columns = ['content']

        #content_df = content_df[['content_screen_filter']].dropna()
        # or_list = list(self.HTH_CMD.HTH_CMD['매매'].keys()) + self.HTH_CMD.HTH_CMD['매매']['매수'] + self.HTH_CMD.HTH_CMD['매매']['매도'] + self.HTH_CMD.HTH_CMD['매매']['매도후매수']
        for i, content in enumerate(content_df['content']):
            cnt = 0
            sell_buy_update_flag = False
            sell_update_flag = False
            buy_update_flag = False
            ambiguous_flag = False
            for buy in self.HTH_CMD.HTH_CMD['매매']['매수']:
                if buy in content:
                    buy_update_flag = True
                    cnt = cnt + 1
                    break

            for sell in self.HTH_CMD.HTH_CMD['매매']['매도']:
                if sell in content:
                    sell_update_flag = True
                    cnt = cnt + 1
                    break

            for sell_buy in self.HTH_CMD.HTH_CMD['매매']['매도후매수']:
                if sell_buy in content:
                    sell_buy_update_flag = True
                    cnt = cnt + 1
                    break

            for sell_buy in self.HTH_CMD.HTH_CMD['매매']['매수매도']:
                if sell_buy in content:
                    ambiguous_flag = True
                    cnt = cnt + 1
                    break

            if (buy_update_flag == True) and (cnt == 1):
                buy_update_list.append(content_df.iloc[i].name)
            elif sell_update_flag == True and cnt == 1:
                sell_update_list.append(content_df.iloc[i].name)
            elif sell_buy_update_flag == True and cnt == 1:
                sell_buy_update_list.append(content_df.iloc[i].name)
            elif ambiguous_flag == True and cnt == 1:
                ambiguous_update_list.append(content_df.iloc[i].name)
            elif cnt >= 2:
                ambiguous_update_list.append(content_df.iloc[i].name)
        #content_df.columns = ['content']
        buy_result_df = content_df.loc[buy_update_list]
        sell_result_df = content_df.loc[sell_update_list]
        sell_buy_result_df = content_df.loc[sell_buy_update_list]
        ambiguous_result_df = content_df.loc[ambiguous_update_list]
        cur_path = os.getcwd()
        # buy_result_df.to_excel(cur_path+"\\buylist.xlsx")
        # sell_result_df.to_excel(cur_path+"\\selllist.xlsx")
        # sell_buy_result_df.to_excel(cur_path+"\\sell_buylist.xlsx")
        # result_df = content_df.loc[]
        # if i == 0:
        #    sort_index = temp_list.copy()
        # else:
        #    sort_index = set(sort_index).intersection(temp_list)
        return buy_result_df, sell_result_df, sell_buy_result_df, ambiguous_result_df
    def spacing_check(self, content):
        spelled_sent = spell_checker.check(content)
        checked_sent = spelled_sent.checked
        return checked_sent

    def stock_name_sort(self, content):
        # market = pd.read_excel('f:\\koreamarketlist.xlsx')
        #market = fdr.StockListing('KRX')
        market = pd.read_html('http://kind.krx.co.kr/corpgeneral/corpList.do?method=download', header=0)[0]
        market = market[['종목코드', '회사명']]
        market.columns = ['code', 'Name']
        # buy case
        # 21.06.06 name 찾는 알고리즘 변경 시도
        # 단순 matching만으로는 종목이름 find rate 너무 떨어짐...

        # transfer func에 띄워쓰기 제거 추가 21.06.06
        #temp_list=content.split(" ")

        content_NoSpace = self.transfer(content)
        # 현대564890 이럴경우를 대비
        #spell_data=self.spacing_check(content_NoSpace)
        # buy_content_line = []
        name_list = []
        for name in market['Name']:
            buy_content_line = []
            # name_list=[]
            name = name.replace(" ","")
            p = re.compile(name, re.DOTALL)
            search_name = p.search(content_NoSpace)
            if search_name is not None:
                buy_content_line.append(content)
                name_list.append(name)
                '''
                # 우선 전체라인 다 들어가는걸로 수정함 왜냐하면 버려지는정보중 문자의 가격정보가 있을수있다  21.06.06
                temp = content.split("\n")
                # name과 숫자만 있는 라인만 담겠다.... 다른 줄들은 제거
                for content_line in temp:
                    if name in content_line:
                        buy_content_line.append(content_line)
                        name_list.append(name)
                    elif bool(re.search(r'\d', content_line)):
                        buy_content_line.append(content_line)
                    elif '현재가' in content_line:
                        buy_content_line.append(content_line)
                    if len(buy_content_line) == 2: buy_content_line = [
                        buy_content_line[0] + buy_content_line[1]]
                    # if len(name_list) == 2: name_list = [name_list[0] + " "+ name_list[1]]
                '''
            # 두개의 name이 들어간 content경우 같은 content가 두번 buy_content_line에 포함되므로 한개만 쓰자
            #if len(buy_content_line) != 0: buy_data['sort_content'].iloc[i] = buy_content_line.pop()
        return name_list


    def jongmok_name_sort(self, buy_data, sell_data, sell_buy_data, ambigous_data):
        # market = pd.read_excel('f:\\koreamarketlist.xlsx')
        #market = fdr.StockListing('KRX')
        market = pd.read_html('http://kind.krx.co.kr/corpgeneral/corpList.do?method=download', header=0)[0]
        market = market[['종목코드', '회사명']]
        market.columns = ['code', 'Name']
        # buy case
        # 21.06.06 name 찾는 알고리즘 변경 시도
        # 단순 matching만으로는 종목이름 find rate 너무 떨어짐...
        if len(buy_data) > 0:
            buy_data['sort_content'] = None
            buy_data['종목'] = None
            for i, content in enumerate(buy_data['content']):
                # transfer func에 띄워쓰기 제거 추가 21.06.06
                temp_list=content.split(" ")
                for split_content in temp_list:
                    #content_NoSpace = self.transfer(split_content)
                    # 현대564890 이럴경우를 대비
                    spell_data=self.spacing_check(content_NoSpace)
                # buy_content_line = []
                name_list = []
                for name in market['Name']:
                    buy_content_line = []
                    # name_list=[]
                    name = name.replace(" ","")
                    p = re.compile(name, re.DOTALL)
                    search_name = p.search(content_NoSpace)
                    if search_name is not None:
                        buy_content_line.append(content)
                        name_list.append(name)
                        '''
                        # 우선 전체라인 다 들어가는걸로 수정함 왜냐하면 버려지는정보중 문자의 가격정보가 있을수있다  21.06.06
                        temp = content.split("\n")
                        # name과 숫자만 있는 라인만 담겠다.... 다른 줄들은 제거
                        for content_line in temp:
                            if name in content_line:
                                buy_content_line.append(content_line)
                                name_list.append(name)
                            elif bool(re.search(r'\d', content_line)):
                                buy_content_line.append(content_line)
                            elif '현재가' in content_line:
                                buy_content_line.append(content_line)
                            if len(buy_content_line) == 2: buy_content_line = [
                                buy_content_line[0] + buy_content_line[1]]
                            # if len(name_list) == 2: name_list = [name_list[0] + " "+ name_list[1]]
                        '''
                    # 두개의 name이 들어간 content경우 같은 content가 두번 buy_content_line에 포함되므로 한개만 쓰자
                    if len(buy_content_line) != 0: buy_data['sort_content'].iloc[i] = buy_content_line.pop()
                if len(name_list) != 0:
                    name_list = list(set(name_list)) #중복제거
                    # 원래순서 그대로 반환하기 위해 temp 변수하나더 쓰자
                    temp = name_list.copy()
                    temp.sort(key=len)
                    new_name_list = name_list.copy()
                    if len(temp) > 1:
                        for name_i, name in enumerate(temp):
                            for j in range(name_i + 1, len(temp)):
                                if name in temp[j]:
                                    new_name_list.remove(name)
                        # new_name_list = name_list
                    else:
                        new_name_list = name_list
                    try:
                        new_name_list = " ".join(new_name_list)
                        buy_data['종목'].iloc[i] = new_name_list
                    except:
                        pass

        # 매도 데이터 정리
        if len(sell_data) > 0:
            sell_data['sort_content'] = None
            sell_data['종목'] = None
            for i, content in enumerate(sell_data['content']):
                content_NoSpace = self.transfer(content)
                # buy_content_line = []
                name_list = []
                for name in market['Name']:
                    sell_content_line = []
                    # name_list=[]
                    name = name.replace(" ", "")
                    p = re.compile(name, re.DOTALL)
                    search_name = p.search(content_NoSpace)
                    if search_name is not None:
                        sell_content_line.append(content)
                        name_list.append(name)
                    '''    
                    if name in content:
                        temp = content.split("\n")
                        for content_line in temp:
                            if name in content_line:
                                sell_content_line.append(content_line)
                                name_list.append(name)
                            elif bool(re.search(r'\d', content_line)):
                                sell_content_line.append(content_line)
                            elif '현재가' in content_line:
                                sell_content_line.append(content_line)
                            if len(sell_content_line) == 2: sell_content_line = [
                                sell_content_line[0] + sell_content_line[1]]
                            # if len(name_list) == 2: name_list = [name_list[0] + " "+ name_list[1]]
                    '''
                    if len(sell_content_line) != 0: sell_data['sort_content'].iloc[i] = sell_content_line.pop()
                if len(name_list) != 0:
                    name_list = list(set(name_list))
                    temp = name_list.copy()
                    temp.sort(key=len)
                    new_name_list = name_list.copy()
                    if len(temp) > 1:
                        for name_i, name in enumerate(temp):
                            for j in range(name_i + 1, len(temp)):
                                if name in temp[j]:
                                    new_name_list.remove(name)
                        # new_name_list = name_list
                    else:
                        new_name_list = name_list
                    try:
                        new_name_list = new_name_list
                        new_name_list = " ".join(new_name_list)
                        sell_data['종목'].iloc[i] = new_name_list
                    except:
                        pass
        # 매도후 매수 데이터 정리
                        '''        
                        for name in market['Name']:
                            sell_buy_content_line = []
                            # name_list=[]
                            if name in content:
                                temp = content.split("\n")
                                for content_line in temp:
                                    if name in content_line:
                                        sell_buy_content_line.append(content_line)
                                        name_list.append(name)
                                    elif bool(re.search(r'\d', content_line)):
                                        sell_buy_content_line.append(content_line)
                                    elif '현재가' in content_line:
                                        sell_buy_content_line.append(content_line)
                                    if len(sell_buy_content_line) == 2: sell_buy_content_line = [
                                        sell_buy_content_line[0] + sell_buy_content_line[1]]
                                    # if len(name_list) == 2: name_list = [name_list[0] + " "+ name_list[1]]
                        '''
        if len(sell_buy_data) > 0:
            sell_buy_data['sort_content'] = None
            sell_buy_data['종목'] = None
            for i, content in enumerate(sell_buy_data['content']):
                content_NoSpace = self.transfer(content)
                name_list = {}
                for name in market['Name']:
                    sell_buy_content_line = []
                    search_index = []
                    # name_list=[]
                    name = name.replace(" ", "")
                    p = re.compile(name, re.DOTALL)
                    search_name = p.search(content_NoSpace)
                    if search_name is not None:
                        sell_buy_content_line.append(content)
                        name_list[name] = search_name.start()

                    if len(sell_buy_content_line) != 0: sell_buy_data['sort_content'].iloc[i] = sell_buy_content_line.pop()
                if len(name_list) != 0:
                    # sell buy에서는 하나의 리스트를 더 두고 순서를 바꾸지말자... 매도 매수 순서가 얽힐수도 있으니...
                    # new_name_list = name_list.copy()
                    #name_list = list(set(name_list))
                    #temp = name_list.copy()
                    #temp.sort(key=len)
                    new_name_list = name_list.copy()
                    if len(name_list) > 1:
                        for name_i, name in enumerate(list(name_list.keys())):
                            for j in range(name_i + 1, len(name_list.keys())):
                                if name in list(name_list.keys())[j]:
                                    new_name_list.pop(name)
                        new_name_list = sorted(new_name_list, key=lambda x: new_name_list[x])
                        # new_name_list = name_list

                    else:
                        pass
                    try:
                        #new_name_list = new_name_list
                        new_name_list = " ".join(new_name_list)
                        sell_buy_data['종목'].iloc[i] = new_name_list
                    except:
                        pass
        # 매도후 매수 데이터 정리
        if len(ambigous_data) > 0:
            ambigous_data['sort_content'] = None
            ambigous_data['종목'] = None

            for i, content in enumerate(ambigous_data['content']):
                content_NoSpace = self.transfer(content)
                # buy_content_line = []
                name_list = {}
                for name in market['Name']:
                    ambigous_content_line = []
                    search_index = []

                    name = name.replace(" ", "")
                    p = re.compile(name, re.DOTALL)
                    search_name = p.search(content_NoSpace)
                    if search_name is not None:
                        ambigous_content_line.append(content)
                        name_list[name] = search_name.start()
                    if len(ambigous_content_line) != 0: ambigous_data['sort_content'].iloc[i] = ambigous_content_line.pop()
                if len(name_list) != 0:
                    # sell buy에서는 하나의 리스트를 더 두고 순서를 바꾸지말자... 매도 매수 순서가 얽힐수도 있으니...
                    # new_name_list = name_list.copy()
                    new_name_list = name_list.copy()
                    if len(name_list) > 1:
                        for name_i, name in enumerate(list(name_list.keys())):
                            for j in range(name_i + 1, len(name_list.keys())):
                                if name in list(name_list.keys())[j]:
                                    new_name_list.pop(name)
                        new_name_list = sorted(new_name_list, key=lambda x: new_name_list[x])
                        # new_name_list = name_list
                    else:
                        pass
                    try:
                        new_name_list = " ".join(new_name_list)
                        ambigous_data['종목'].iloc[i] = new_name_list
                    except:
                        pass
        return buy_data, sell_data, sell_buy_data, ambigous_data

    def post_comment_analysis_algo(self, data):
        # test = pd.read_excel("f:\\test22.xlsx")
        # test = test.set_index('created_at')
        sort_index = []
        # market_list = pd.read_excel("f:\\koreamarketlist.xlsx")
        #market_list = fdr.StockListing('KRX')

        # total_list = list(market_list['name'])+ROI_list
        '''
        if  os.path.isfile('d:\\spell_spacing_correction_df.xlsx') :
            spell_spacing_correction_df = pd.read_excel('d:\\spell_spacing_correction_df.xlsx')
            spell_spacing_correction_df = spell_spacing_correction_df.set_index('created_at')
            spell_spacing_correction_df = spell_spacing_correction_df[['content']]
            spell_spacing_correction_df.columns = ['spell_spacing_correction_filter']
        else:
            spell_spacing_correction_df = self.data_spell_spacing_func(data)
            spell_spacing_correction_df = spell_spacing_correction_df.set_index('created_at')
            spell_spacing_correction_df.columns = ['spell_spacing_correction_filter']
            temp_df = pd.merge(data, spell_spacing_correction_df, on='created_at', how='left')
            temp_df.to_excel('d:\\spell_spacing_correction_df.xlsx')
        '''
        screen_sort_df = self.HTH_Comment_Screen_Filter(data)
        #screen_sort_df.columns=[screen_sort_df.columns[0]+'_screen_sort',screen_sort_df.columns[1]+'_screen_sort',screen_sort_df.columns[2]+'_screen_sort']
        data = pd.merge(data, screen_sort_df, on='created_at', how='left')
        data.to_excel(os.path.join(os.getcwd(),'screen_sort_df_total.xlsx'))
        self.logging.logger.debug("HTH_Comment_Screen_Filter_END!")

        buy, sell, sell_buy, ambiguous = self.HTH_Comment_Meme_Filter(screen_sort_df)
        temp_df = pd.concat([buy, sell, sell_buy, ambiguous])
        #temp_df = temp_df[['content']]
        #temp_df.columns = ['Meme_Filter']
        data = pd.merge(data, temp_df, on='created_at', how='left')
        data.to_excel(os.path.join(os.getcwd(),'Meme_Filter_df_total.xlsx'))
        self.logging.logger.debug("HTH_Comment_Meme_Filter_END!")

        buy_price_ratio_sort = self.buy_price_ratio_sort(buy)
        buy_price_ratio_sort.to_excel('f:\\buy_price_ratio_sort.xlsx')
        self.logging.logger.debug("buy_price_ratio_sort_END!")
        sell_price_ratio_sort = self.sell_price_ratio_sort(sell)
        self.logging.logger.debug("sell_price_ratio_sort_END!")
        sell_buy_price_ratio_sort = self.sell_buy_price_ratio_sort(sell_buy)
        self.logging.logger.debug("sell_buy_price_ratio_sort_END!")

        '''
        buy_name_sort, sell_name_sort, sell_buy_name_sort, ambiguous_sort = self.jongmok_name_sort(buy_price_ratio_sort,sell_price_ratio_sort,sell_buy_price_ratio_sort, ambiguous)
        temp_df = pd.concat([buy_name_sort, sell_name_sort, sell_buy_name_sort, ambiguous_sort])
        temp_df = temp_df[['sort_content', '종목']]
        temp_df.columns = ['name_sort_content', '종목']
        data = pd.merge(data, temp_df, on='created_at', how='left')
        data.to_excel(os.path.join(os.getcwd(),'jongmok_name_sort_df_total.xlsx'))
        self.logging.logger.debug("jongmok_name_sort_END!")
        '''
        
        cur_path = os.getcwd()
        buy_price_ratio_sort.to_excel(cur_path + "\\buy_name_sort.xlsx")
        sell_price_ratio_sort.to_excel(cur_path + "\\sell_name_sort.xlsx")
        sell_buy_price_ratio_sort.to_excel(cur_path + "\\sell_buy_name_sort.xlsx")
        # test = test.loc[sort_index]
        # test = test.drop_duplicates()
        # print(test)
        return test

    def buy_price_ratio_sort(self, data):
        data=data.dropna(axis=0)
        data['매수가'] = None
        data['비중'] = None
        data['종목'] = None
        col_list=list(data.columns)
        name_pattern_pattern = re.compile(r'((\w{2,}) (\d{3,}))|((\w{2,})  (\d{3,}))|((\w{2,})   (\d{3,}))|((\w{2,})(\d{3,}))')
        price_pattern = re.compile(r'(\d{4,10})')
        #name_pattern = re.compile(r'(\w{2,})')
        name_pattern = re.compile(r'[가-힣]+[a-z]+|[가-힣]+')
        ratio_pattern = re.compile(r'((\d{,3})%)|((\d{,3}) %)')
        for i, content in enumerate(data['content']):
            '''
            content_list = content.split(" ")
            for text in content_list:
            '''            
            #text = text.replace(" ","")
            text = content
            
            ratio=ratio_pattern.findall(text)
            name_price=name_pattern_pattern.search(text)
            # 1. 비중구하기
            if len(ratio)>0:
                # 2개의 %가능성이 있다... 80% 중 20% 매수 이렇게 그러면 거의 뒷에 것이 기준이 되어야함
                if len(ratio)>1:
                    length=len(ratio)
                    data.iloc[i, col_list.index('비중')]=ratio[length-1][0]
                else:
                    data.iloc[i,col_list.index('비중')]=ratio[0][0]
            else:
                for ratio_text in self.HTH_CMD.HTH_CMD['비중']:
                    if ratio_text in text:
                        if ratio_text == "절반":
                            data.iloc[i, col_list.index('비중')]='50%'
                        if ratio_text == "전부":
                            data.iloc[i, col_list.index('비중')]='100%'
            # 2. 가격구하기
               # 가격은 추후 보완이 필요하며 당장은 2가지 Case만적용
               # EX>'현대58600', '현대 58600'
            # 3. 종목명
            if name_price!=None:
                temp_price=price_pattern.findall(name_price[0])
                # name_price에서 없으면 content 한 문장에서 다시 찾는다...
                if len(temp_price) == 0:
                    temp_price=price_pattern.search(text)
                    if temp_price!=None:
                        data.iloc[i, col_list.index('매수가')] = temp_price[0]
                    else:
                        pass
                else:
                    data.iloc[i,col_list.index('매수가')]=temp_price[0]

                #try:
                name_list=self.stock_name_sort(text)
                #name_list = name_list.sort(key=len, reverse=True)
                if len(name_list)!=0:
                    if len(name_list)==1:data.iloc[i, col_list.index('종목')] = name_list[0]
                    else:
                        #길이가 긴것이 찾는 종목명일 확률이 높음
                        name_list.sort(key=len, reverse=True)
                        data.iloc[i, col_list.index('종목')] = name_list[0]
                else:
                    try:
                        data.iloc[i, col_list.index('종목')] = name_pattern.findall(name_price[0])[0]
                    except:
                        self.logging.logger.debug("There is no name_price")
                #except: pass
        '''
        for i in range(len(data)):
            try:
                temp = re.findall('\d+', data['sort_content'].iloc[i])
                for list_data in temp:
                    # 세자리수 이상의 숫자데이터는 매수가/매도가
                    if len(list_data) > 3:
                        data['매수가'].iloc[i] = int(list_data)
                    else:
                        data['비중'].iloc[i] = int(list_data)
            # 숫자 데이터가 없을때...
            except:
                pass
        # 추가적으로 보완
        # 비중이 없는 경우, 매수가가 없는 경우
        # 종목이 두개인 경우 확인
        for i in range(len(data)):
            if data['종목'].iloc[i] == None:
                pass
            elif data['종목'].iloc[i] != None and data['비중'].iloc[i] != None and data['매수가'].iloc[i] == None:
                data['매수가'].iloc[i] = '현재가'
            elif data['종목'].iloc[i] != None and data['매수가'].iloc[i] != None and data['비중'].iloc[i] == None:
                data['비중'].iloc[i] = 10
            else:
                pass
        '''
        return data

    def sell_price_ratio_sort(self, data):
        data['매도가'] = None
        data['비중'] = None
        for i in range(len(data)):
            try:
                temp = re.findall('\d+', data['sort_content'].iloc[i])
                for list_data in temp:
                    # 세자리수 이상의 숫자데이터는 매수가/매도가
                    if len(list_data) > 3:
                        data['매도가'].iloc[i] = int(list_data)
                    else:
                        data['비중'].iloc[i] = int(list_data)
            # 숫자 데이터가 없을때...
            except:
                pass
        # 추가적으로 보완
        # 비중이 없는 경우, 매수가가 없는 경우
        # 종목이 두개인 경우 확인
        for i in range(len(data)):
            if data['종목'].iloc[i] == None:
                pass
            elif data['종목'].iloc[i] != None and data['비중'].iloc[i] != None and data['매도가'].iloc[i] == None:
                data['매도가'].iloc[i] = '현재가'
            elif data['종목'].iloc[i] != None and data['매도가'].iloc[i] != None and data['비중'].iloc[i] == None:
                data['비중'].iloc[i] = 10
            else:
                pass
        return data

    def sell_buy_price_ratio_sort(self, data):
        # 우선 이동 이란 단어로 필터링 했기에 전부 팔고 전부 이동
        data['매도가'] = None
        data['매수가'] = None
        data['매수종목'] = None
        data['매도종목'] = None
        data['비중'] = None
        for i in range(len(data)):
            try:
                temp = re.findall('\d+', data['sort_content'].iloc[i])
                for list_data in temp:
                    # 세자리수 이상의 숫자데이터는 매수가/매도가
                    if len(list_data) > 3:
                        data['매도가'].iloc[i] = int(list_data)
                    else:
                        data['비중'].iloc[i] = int(list_data)
            # 숫자 데이터가 없을때...
            except:
                pass
        # 추가적으로 보완
        # 비중이 없는 경우, 매수가가 없는 경우
        # 종목이 두개인 경우 확인
        for i in range(len(data)):
            if data['종목'].iloc[i] == None:
                pass
            elif data['종목'].iloc[i] != None:
                if len(temp) == 1: break
                temp = data['종목'].iloc[i]
                temp = temp.split(" ")
                if len(temp) == 2:
                    data['매도종목'].iloc[i] = temp[0]
                    data['매수종목'].iloc[i] = temp[1]
                    data['매도가'].iloc[i] = '현재가'
                    data['매수가'].iloc[i] = '현재가'
            else:
                pass
        return data

    def _All_post_comment_Read(self):
        bandlist = self.SQL.DB_LOAD_Table(self.Skima, self.TABLE_NAVER_BAND)
        bandlist = bandlist.set_index('name')
        ROI_bandkey = bandlist.loc[self.ROI_band_name]['band_key']
        authorization_code = 'access_token='
        url = self.postlist_url + "?" + authorization_code + self.actoken + "&band_key=" + ROI_bandkey + "&locale=kr_KR"
        original_data = requests.get(url).json()
        cnt = 0
        fail_cnt = 0
        total_df = pd.DataFrame(data=None)
        while original_data['result_data']['paging']['next_params']['limit'] == '20':
            original_data = requests.get(url).json()
            get_data = original_data['result_data']['items']
            comment_list = []
            for data in get_data:
                temp_post = [data['created_at'], data['content']]
                comment_list.append(temp_post)
                if data['comment_count']:
                    try:
                        for comment in data['latest_comments']:
                            comment_list.append([comment['created_at'], comment['body']])
                    except:
                        fail_cnt = fail_cnt + 1
            temp_df = pd.DataFrame(data=comment_list, columns=['created_at', 'content'])
            temp_df = temp_df.set_index('created_at').sort_values(by='created_at', ascending=False)
            if cnt == 0:
                total_df = temp_df
            else:
                total_df = pd.concat([total_df, temp_df])
            if original_data['result_data']['paging']['next_params'] == None:
                break
            else:
                url = self.postlist_url + "?" + "after=" + original_data['result_data']['paging']['next_params'][
                    'after'] + "&" + authorization_code + self.actoken + "&band_key=" + ROI_bandkey + "&locale=kr_KR"

            cnt = cnt + 1
            print(cnt)
        return total_df

    def HTH_Algo_fnc(self):
        temp_data = self._latest_postlist_load(self.ROI_band_name)
        #
        # try:
        #   temp_data = self._latest_postlist_load(self.ROI_band_name)
        # except :
        #   return
        latest_post_temp = temp_data['created_at']
        latest_comment_temp = None
        new_post = False
        new_comment = False
        meme_list = []
        # 첫 부팅상태라면?
        if self._latest_post is None:
            if temp_data['comment_count'] == 0:
                new_comment = False
            else:
                new_comment = True
                latest_comment_temp = temp_data['latest_comments'][0]['created_at']
            new_post = True

        elif self._latest_post == latest_post_temp:
            if self._latest_comment == latest_comment_temp:
                pass
            else:
                self._latest_comment = latest_comment_temp
                new_comment = True
        else:
            if temp_data['comment_count'] == 0:
                self._latest_post = latest_post_temp
                new_post = True
                new_comment = False
            else:
                self._latest_post = latest_post_temp
                self._latest_comment = latest_comment_temp
                new_post = True
                new_comment = True
        # post / comment 업데이트 시 알고리즘 수행
        if new_post:
            #post_data = temp_data['content']
            post_data = temp_data
            meme_list.append(self.post_comment_analysis_algo(post_data))  # data 형식 : ['종목', '매수가', '비중']
        if new_comment:
            comment_data = temp_data['latest_comments'][0]['body']
            temp = self.post_comment_analysis_algo(comment_data)  # data 형식 : ['종목', '매수가', '비중']
            if temp[0] == meme_list[0]:
                pass
            else:
                meme_list.append(temp)
        meme_list = [['삼성전자', '53000', 20], ['아이쓰리시스템', '33000', 20]]
        return meme_list


from PyQt5.QtWidgets import *
import sys

if __name__ == "__main__":
    app = QApplication(sys.argv)
    band = Naver_Band()
    band_name = '추세선을보라! 믿어라 벌것이다.'
    cnt = 0
    #test = pd.read_excel('d:\\HTH_RAW_0606.xlsx')
    #a = band.HTH_Algo_fnc()
    temp_data = pd.read_excel(os.path.join(os.getcwd(), 'files/meme_df.xlsx'))
    band.post_comment_analysis_algo(temp_data)
    # print(b)
    app.exec_()
    # print(b)

# while True:
#    get_data = requests.get(url).json()
# limit = get_data['result_data']['paging']['next_params']['limit']
#    if get_data['result_data']['paging']['next_params'] == None:
#        break
# else:
#    temp = get_data['result_data']['paging']['next_params']
#    repaging_list = list(temp)
#    url = self.postlist_url + "?"
#     for i, string in enumerate(repaging_list):
#        url = url + repaging_list[i] + '=' + temp[string] + "&"
#      url = url + "locale=en_US"
#      print(url)



