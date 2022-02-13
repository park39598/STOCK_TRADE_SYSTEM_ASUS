# -*- coding: utf-8 -*-
"""
Spyder Editor

This is a temporary script file.
"""

import requests
import pandas as pd
from Finance import finance_data
from DataBase import SQLITE_control
import numpy as np

class i_invest_crolling_year:
    def __init__(self):
        self.profit_total_url = 'http://www.itooza.com/vclub/y10_page.php?mode=dy&ss=10&sv=2&lsmode=1&accmode=1&pmode=1&exmode=1&lkmode=1&cmp_cd='
        self.profit_individual_url = 'http://www.itooza.com/vclub/y10_page.php?mode=dy&ss=10&sv=2&lsmode=1&accmode=1&pmode=1&exmode=1&lkmode=2&cmp_cd='

        self.cashflow_total_url = 'http://www.itooza.com/vclub/y10_page.php?mode=dy&ss=10&sv=4&lsmode=1&accmode=1&pmode=1&exmode=1&lkmode=1&cmp_cd='
        self.cashflow_individual_url = 'http://www.itooza.com/vclub/y10_page.php?mode=dy&ss=10&sv=4&lsmode=1&lkmode=2&pmode=1&exmode=1&accmode=1&cmp_cd='

        self.fs_total_url = 'http://www.itooza.com/vclub/y10_page.php?mode=dy&ss=10&sv=1&lsmode=1&lkmode=1&pmode=1&exmode=1&accmode=1&cmp_cd='
        self.fs_individual_url = 'http://www.itooza.com/vclub/y10_page.php?mode=dy&ss=10&sv=1&lsmode=1&lkmode=2&pmode=1&exmode=1&accmode=1&cmp_cd='

        self.invest_total_url = 'http://www.itooza.com/vclub/y10_page.php?mode=dy&ss=10&sv=10&lsmode=1&lkmode=1&cmp_cd='
        self.invest_individual_url = 'http://www.itooza.com/vclub/y10_page.php?mode=dy&ss=10&sv=10&lsmode=1&lkmode=2&cmp_cd='

        #        self.kw = Kiwoom()
        self.I_INVEST_YEAR = 'f:\\OneDrive - Moedog, Inc\\STOCK_DB\\I_INVEST_DB.db'
        self.LOGIN_INFO = {'txtUserId': 'valcan02', 'txtPassword': 'tldldh0201'}
        self.LOGIN_URL = 'https://login.itooza.com/login_process.php'
        self.fs = finance_data.Finance_data()
        self.request_list=[]
        
    def get_want_factor_in_list(self, include_string, string_list):
        new_list = []
        for factor in string_list:
            if include_string in factor:
                new_list.append(factor)
        return new_list
        
    def get_total_finance_df(self):
        Code_df = SQLITE_control.DB_LOAD_Table(self.fs.TOTAL_JONGMOK_NAME_TABLE, self.fs.DB_TOTAL_JONGMOK_PATH)
        fail_list = []
        for num, code in enumerate(Code_df.index):
            #if num == 30 : break
            print(num, code)
            self.request_list = []
            # fs_temp_df가 무조건 첫번째로 request_list를 'get_financeState_data'에서 만듬
            try:
                fs_temp_df = self.get_financeState_data(code, Code_df['IFRS'][num])
                invest_temp_df = self.get_invest_data(code, Code_df['IFRS'][num])
                cashflow_temp_df = self.get_cashflow_data(code, Code_df['IFRS'][num])
                #profit_temp_df = self.get_profit_data(code, Code_df['IFRS'][num])
                if num == 0:
                    invest_df = invest_temp_df
                    cashflow_df = cashflow_temp_df
                    fs_df = fs_temp_df
                    #profit_df = profit_temp_df
                else:
                    invest_df = pd.concat([invest_df, invest_temp_df])
                    cashflow_df = pd.concat([cashflow_df, cashflow_temp_df])
                    fs_df = pd.concat([fs_df, fs_temp_df])
                    #profit_df = pd.concat([profit_df, profit_temp_df])
            except:
                fail_list.append(code)
        temp = list(set(cashflow_df.columns.levels[0]).intersection(fs_df.columns.levels[0]))
        temp = list(set(temp).intersection(invest_df.columns.levels[0]))
        temp.sort()
        temp = pd.DataFrame(data=temp)
        for col in temp[0]:
            temp_df1 = pd.merge(fs_df[col], cashflow_df[col], left_index=True, right_index=True)
            total_df = pd.merge(temp_df1, invest_df[col], left_index=True, right_index=True)
            total_df.columns = [[col] * len(total_df.columns), total_df.columns]
            SQLITE_control.DB_SAVE(total_df, self.I_INVEST_YEAR, col, True)
        print(fail_list)
        return total_df
    
    def get_financeState_data_func(self, fs_url_total, profit_url_total, type_fs):
        with requests.Session() as s:
            login_req = s.post(self.LOGIN_URL, data=self.LOGIN_INFO, verify=False)
            fs_page_total = s.get(fs_url_total)
            fs_page_total.encoding = 'euc-kr'
            fs_tables_total = pd.read_html(fs_page_total.text)
            fs_tables_total[2]['재무상태표'] = fs_tables_total[1]['재무상태표']
            fs_df = fs_tables_total[2].set_index('재무상태표')
            fs_df = fs_df.loc[['건설중인자산', '기계장치','단기금융부채', '단기금융상품','유동자산',
                               '단기금융자산', '단기매도가능금융자산','단기매매금융자산', '단기사채', '단기차입금', '단기충당부채', '당기법인세부채',
                               '당좌자산', '매입채무', '매입채무및기타채무', '매출채권', '매출채권및기타채권', '무형자산',
                               '부채총계', '부채총계(지분법적용, 주석)', '비유동부채', '비유동자산', '비지배주주지분', '사채',
                                '영업권', '유동부채', '유동성사채', '이익잉여금','자본금', '자본잉여금', '유동성장기부채',
                               '자본총계', '자산총계', '장기금융부채','장기차입금',
                               '장기매입채무', '재고자산', '지배주주지분', '현금및현금성자산']]
            fs_df.loc['유보율(%)'] = ((fs_df.loc['이익잉여금'].replace(np.nan,0).astype("float") + fs_df.loc['자본잉여금'].replace(np.nan,0).astype("float")) / fs_df.loc['자본금'].replace(np.nan,0).astype("float")) * 100
            fs_df.loc['현금성자산'] = fs_df.loc['유동자산'].replace(np.nan,0).astype("float") - fs_df.loc['매출채권및기타채권'].replace(np.nan,0).astype("float") - fs_df.loc['재고자산'].replace(np.nan,0).astype("float")
            fs_df.loc['단기금융부채'] = fs_df.loc['단기사채'].replace(np.nan,0).astype("float") + fs_df.loc['단기차입금'].replace(np.nan,0).astype("float") + fs_df.loc['유동성장기부채'].replace(np.nan,0).astype("float")
            fs_df.loc['장기금융부채종합'] = fs_df.loc['사채'].replace(np.nan, 0).astype("float") + fs_df.loc['장기차입금'].replace(np.nan,0).astype("float") + fs_df.loc['장기금융부채'].replace(np.nan,0).astype("float")
            fs_df.loc['순현금'] = fs_df.loc['현금성자산'].replace(np.nan,0).astype("float") - (fs_df.loc['단기금융부채'].replace(np.nan,0).astype("float") + fs_df.loc['장기금융부채종합'].replace(np.nan,0).astype("float"))
            fs_df = fs_df[self.get_want_factor_in_list('12', fs_df.columns)]
            fs_df.columns = list(map(lambda x: x.replace(".", "/").replace("월", ""), fs_df.columns))
            fs_df.index.name = "재무상태표"
            fs_df = fs_df.fillna(0)
            fs_df = fs_df.reset_index().drop_duplicates("재무상태표").set_index("재무상태표")
            profit_page_total = s.get(profit_url_total)
            profit_page_total.encoding = 'euc-kr'
            profit_tables_total = pd.read_html(profit_page_total.text)
            profit_tables_total[2]['손익계산서'] = profit_tables_total[1]['손익계산서']
            profit_df = profit_tables_total[2].set_index('손익계산서')
            profit_df = profit_df.loc[['*EBITDA', '*순이익(지분법적용,아이투자)', '감가상각비', '매출액(수익)', '매출원가', '매출총이익',
                                       '법인세비용', '법인세비용차감전계속사업이익', '비지배지분 순이익', '시가총액', '연구개발비', '영업이익',
                                       '재고자산의변동', '주가', '주식수', '지배지분 순이익', '지배지분 총포괄이익',
                                       '지분법이익', '총포괄이익', '판매비와관리비']]
            try:
                profit_df.index = ['EBITDA', '순이익', '감가상각비', '감가상각비(판관비)', '매출액', '매출원가', '매출총이익',
                                   '법인세비용', '법인세비용차감전계속사업이익', '비지배지분 순이익', '시가총액', '연구개발비', '영업이익',
                                   '재고자산의변동', '주가', '주식수', '지배지분 순이익', '지배지분총포괄이익',
                                   '지분법이익', '총포괄이익', '판매비와관리비']
            except:
                profit_df.index = ['EBITDA', '순이익', '감가상각비', '매출액', '매출원가', '매출총이익',
                                   '법인세비용', '법인세비용차감전계속사업이익', '비지배지분 순이익', '시가총액', '연구개발비', '영업이익',
                                   '재고자산의변동', '주가', '주식수', '지배지분 순이익', '지배지분총포괄이익',
                                   '지분법이익', '총포괄이익', '판매비와관리비']
            profit_df = profit_df[self.get_want_factor_in_list('12', profit_df.columns)]
            profit_df.columns = list(map(lambda x: x.replace(".", "/").replace("월", ""), profit_df.columns))
            profit_df.index.name = "손익계산서"
            profit_df = profit_df.reset_index().drop_duplicates("손익계산서").set_index("손익계산서")
            profit_df = profit_df.fillna(0)
            profit_df.loc['주식수'] = profit_df.loc['시가총액'] * 100000000 / profit_df.loc['주가']
            fs_df = pd.concat([profit_df, fs_df])
            try:
                if type_fs == '연결':
                    fs_df.loc['ROE'] = fs_df.loc['지배지분 순이익'].astype("float")*100 / fs_df.loc['지배주주지분'].replace(0,1).astype("float")
                    fs_df.loc['RIM_ROE'] = self.fs.Calc_ROE_AVG(fs_df.loc['ROE'])
                else:
                    fs_df.loc['ROE'] = fs_df.loc['순이익'].astype("float") * 100 / fs_df.loc['지배주주지분'].replace(0,1).astype("float")
                    fs_df.loc['RIM_ROE'] = self.fs.Calc_ROE_AVG(fs_df.loc['ROE'])
            except:
                if type_fs == '연결':
                    fs_df.loc['ROE'] = fs_df.loc['지배지분 순이익'].astype("float") * 100 / fs_df.loc['지배주주지분'].replace(0,1).astype("float")
                    fs_df.loc['RIM_ROE'] = fs_df.loc['ROE']
                else:
                    fs_df.loc['ROE'] = fs_df.loc['순이익'].astype("float") * 100 / fs_df.loc['지배주주지분'].replace(0,1).astype("float")
                    fs_df.loc['RIM_ROE'] = fs_df.loc['ROE']
        return fs_df
        
    def get_financeState_data(self, code, type_fs):  # ROE계산을 위해 합치자
        type_fs_flag = False
        if type_fs == '연결':
            fs_url_total = self.fs_total_url + code.replace("A", "")
            profit_url_total = self.profit_total_url + code.replace("A", "")
            type_fs_flag = True
        else:
            fs_url_total = self.fs_individual_url + code.replace("A", "")
            profit_url_total = self.profit_individual_url + code.replace("A", "") 
            
        fs_df = self.get_financeState_data_func(fs_url_total, profit_url_total, type_fs)
        fs_df = fs_df.T
        #research
        self.request_list = list(fs_df[(fs_df['EBITDA'].astype('float') == 0.0) & (fs_df['매출액'].astype('float') == 0.0)].index)
        if type_fs_flag:
            fs_df_indiv = self.get_financeState_data_func(self.fs_individual_url + code.replace("A", ""), self.profit_individual_url + code.replace("A", ""),'개별')

            fs_df_indiv = fs_df_indiv.T
            for col in fs_df[(fs_df['EBITDA'].astype('float') == 0.0) & (fs_df['매출액'].astype('float') == 0.0)].index:
                try:
                    fs_df.loc[col] = fs_df_indiv.loc[col]
                except:
                    pass
        fs_df = fs_df.T
        fs_df = pd.DataFrame(fs_df.unstack("재무상태표"), columns=[code]).T          
        return fs_df

    def get_cashflow_data_func(self, cashflow_url_total):
        with requests.Session() as s:
            login_req = s.post(self.LOGIN_URL, data=self.LOGIN_INFO, verify=False)
            cashflow_page_total = s.get(cashflow_url_total)
            cashflow_page_total.encoding = 'euc-kr'
            cashflow_tables_total = pd.read_html(cashflow_page_total.text)
            cashflow_tables_total[2]['현금흐름표'] = cashflow_tables_total[1]['현금흐름표']
            cashflow_df = cashflow_tables_total[2].set_index('현금흐름표')
            cashflow_df = cashflow_df.loc[['Free Cash Flow1', '건물및부속설비의증가', '건설중인자산의증가', '당기순이익',
                                           '기계장치의증가','단기차입금의감소', '단기차입금의증가', '대손상각비',
                                           '매입채무 증가','매출채권감소', '영업활동으로인한현금흐름', '유형자산의증가','자본금 및 자본잉여금 감소', '자본금 및 자본잉여금 증가',
                                           '재고자산의감소', '재무활동으로인한현금흐름', '중장비의 증가', '투자활동으로인한현금흐름',
                                           '현금의 증감']]
            cashflow_df.index = ['FCF', '건물및부속설비의증가', '건설중인자산의증가', '당기순이익',
                                   '기계장치의증가','단기차입금의감소', '단기차입금의증가','대손상각비',
                                   '매입채무 증가','매출채권감소', '영업활동으로인한현금흐름', '유형자산의증가','자본금 및 자본잉여금 감소', '자본금 및 자본잉여금 증가',
                                   '재고자산의감소', '재무활동으로인한현금흐름', '중장비의 증가', '투자활동으로인한현금흐름',
                                   '현금의 증감']
            cashflow_df = cashflow_df[self.get_want_factor_in_list('12', cashflow_df.columns)]
            cashflow_df.columns = list(map(lambda x: x.replace(".", "/").replace("월", ""), cashflow_df.columns))
            cashflow_df.index.name = "현금흐름표"
            cashflow_df = cashflow_df.fillna(0)
            cashflow_df = cashflow_df.reset_index().drop_duplicates("현금흐름표").set_index("현금흐름표")
        return cashflow_df
        
    def get_cashflow_data(self, code, type_fs):
        type_fs_flag = False
        if type_fs == '연결':
            cashflow_url_total = self.cashflow_total_url + code.replace("A", "")
            type_fs_flag = True
        else:
            cashflow_url_total = self.cashflow_individual_url + code.replace("A", "")
        cashflow_df = self.get_cashflow_data_func(cashflow_url_total)
        cashflow_df = cashflow_df.T
        if type_fs_flag:
            cashflow_df_indiv = self.get_cashflow_data_func(self.cashflow_individual_url + code.replace("A", ""))
            cashflow_df_indiv = cashflow_df_indiv.T
            #for col in cashflow_df[(cashflow_df['당기순이익'].astype('float') == 0.0) & (cashflow_df['투자활동으로인한현금흐름'].astype('float') == 0.0)].index:
            for col in self.request_list: 
                try:
                    cashflow_df.loc[col] = cashflow_df_indiv.loc[col]
                except:
                    pass
        cashflow_df = cashflow_df.T
        cashflow_df = pd.DataFrame(cashflow_df.unstack("현금흐름표"), columns=[code]).T
        return cashflow_df

    def get_invest_data_func(self, invest_url_total):
        with requests.Session() as s:
            login_req = s.post(self.LOGIN_URL, data=self.LOGIN_INFO, verify=False)
            invest_page_total = s.get(invest_url_total)
            invest_page_total.encoding = 'euc-kr'
            invest_tables_total = pd.read_html(invest_page_total.text)
            invest_tables_total[2]['재무비율/가치평가'] = invest_tables_total[1]['재무비율/가치평가']
            invest_df = invest_tables_total[2].set_index("재무비율/가치평가")
            invest_df.index = ['가치평가 지표', '주당순이익(EPS,연결지배)', '주당순이익(EPS,개별)',
                            '주가수익배수(PER)', '주당순자산(BPS, 지배)','주가순자산배수(PBR)',
                            '주당현금흐름(CFPS)','주가현금흐름배수(PCR)','주당매출액(SPS)',
                            '주가매출액배수(PSR)',      '주당배당금(DPS)',        '시가배당률(%)',
                            '수익성 지표',   '자기자본 이익률(ROE)',      '=순이익률(ROS)',
                            'x 총자산회전율(S/A)',   'x 재무레버리지(A/E)', np.nan,   '총자산 이익률(ROA)',
                            np.nan, '매출액 순이익률', '매출액 영업이익률', '성장성 지표',
                            '매출액 증가율',        '영업이익 증가율',     '순이익 증가율(지배)',
                            np.nan, '자기자본 증가율(지배)', '안전성 지표', '부채비율(%)',
                            '유동비율(%)', np.nan, '이자보상 배율(배)', np.nan, '자본잠식률(%)']
            invest_df = invest_df.loc[['매출액 순이익률', '매출액 영업이익률', '매출액 증가율', '부채비율(%)', '순이익 증가율(지배)',
                                    '시가배당률(%)', '영업이익 증가율', '유동비율(%)', '이자보상 배율(배)',
                                    '자기자본 증가율(지배)', '자본잠식률(%)', '주가매출액배수(PSR)', '주가수익배수(PER)', '주가순자산배수(PBR)',
                                    '주가현금흐름배수(PCR)', '주당매출액(SPS)', '주당배당금(DPS)', '주당순이익(EPS,연결지배)',
                                    '주당순자산(BPS, 지배)', '주당현금흐름(CFPS)', '총자산 이익률(ROA)']]
            invest_df.index = ['매출액 순이익률', '매출액 영업이익률', '매출액 증가율', '부채비율(%)', '순이익 증가율',
                                '시가배당률(%)', '영업이익 증가율', '유동비율(%)', '이자보상 배율',
                                '자기자본 증가율', '자본잠식률(%)', 'PSR', 'PER', 'PBR', 'PCR', 'SPS', 'DPS', 'EPS',
                                'BPS', 'CFPS', 'ROA']

            invest_df = invest_df[self.get_want_factor_in_list('12', invest_df.columns)]
            invest_df.columns = list(map(lambda x: x.replace(".", "/").replace("월", ""), invest_df.columns))
            invest_df.index.name = "재무비율"
            invest_df = invest_df.fillna(0)
            invest_df = invest_df.reset_index().drop_duplicates("재무비율").set_index("재무비율")
        return invest_df
    
    def get_invest_data(self, code, type_fs):
        type_fs_flag = False
        if type_fs == '연결':
            invest_url_total = self.invest_total_url + code.replace("A", "")
            type_fs_flag = True
        else:
            invest_url_total = self.invest_individual_url + code.replace("A", "")
        invest_df = self.get_invest_data_func(invest_url_total)
        invest_df = invest_df.T
        if type_fs_flag:
            invest_df_indiv = self.get_invest_data_func(self.invest_individual_url + code.replace("A", ""))
            invest_df_indiv = invest_df_indiv.T
            #for col in invest_df[(invest_df['당기순이익'].astype('float') == 0.0) & (invest_df['투자활동으로인한현금흐름'].astype('float') == 0.0)].index:
            for col in self.request_list:
                try:
                    invest_df.loc[col] = invest_df_indiv.loc[col]
                except:
                    pass
        invest_df = invest_df.T
        invest_df = pd.DataFrame(invest_df.unstack("재무비율"), columns=[code]).T
        return invest_df


if __name__ == "__main__":
    test = i_invest_crolling_year()
    test.get_total_finance_df()



