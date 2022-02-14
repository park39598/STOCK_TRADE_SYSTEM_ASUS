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
import FinanceDataReader as fdr

class i_invest_crolling:
    def __init__(self):

        self.profit_total_url = 'http://www.itooza.com/vclub/y10_page.php?mode=db&ss=10&sv=2&lsmode=1&accmode=1&pmode=1&exmode=1&lkmode=1&cmp_cd='
        self.profit_individual_url = 'http://www.itooza.com/vclub/y10_page.php?mode=db&ss=10&sv=2&lsmode=1&lkmode=2&pmode=1&exmode=1&accmode=1&cmp_cd='
        
        self.cashflow_total_url = 'http://www.itooza.com/vclub/y10_page.php?mode=db&ss=10&sv=4&lsmode=1&lkmode=1&pmode=1&exmode=1&accmode=1&cmp_cd='
        self.cashflow_individual_url = 'http://www.itooza.com/vclub/y10_page.php?mode=db&ss=10&sv=4&lsmode=1&lkmode=2&pmode=1&exmode=1&accmode=1&cmp_cd='
        
        self.fs_total_url = 'http://www.itooza.com/vclub/y10_page.php?mode=db&ss=10&sv=1&lsmode=1&lkmode=1&pmode=1&exmode=1&accmode=1&cmp_cd='
        self.fs_individual_url = 'http://www.itooza.com/vclub/y10_page.php?mode=db&ss=10&sv=1&lsmode=1&lkmode=2&pmode=1&exmode=1&accmode=1&cmp_cd='
        
        self.invest_total_url = 'http://www.itooza.com/vclub/y10_page.php?mode=db&ss=10&sv=10&lsmode=1&lkmode=1&cmp_cd='
        self.invest_individual_url = 'http://www.itooza.com/vclub/y10_page.php?ss=10&sv=10&mode=db&cmp_cd='
                                
        #self.kw = Kiwoom()
        self.DB_FS_EXCEL_PATH = 'd:\\OneDrive\\STOCK_DB\\finance_excel_DB.db'
        self.LOGIN_INFO = {'txtUserId': 'naver_19101784', 'txtPassword': '#wkdhrl1024'}
        self.LOGIN_URL = 'https://login.itooza.com/login_process.php'
        self.request_list = []
        self.fs = finance_data.Finance_data()
    def get_stock_code_name(self):
        df_krx = fdr.StockListing('KRX')
        df_krx_dellist = fdr.StockListing('KRX-DELISTING')
        df_krx = df_krx[['Symbol', 'Name']]
        df_krx_dellist = df_krx_dellist[['Symbol', 'Name']]
        df_krx = pd.concat([df_krx, df_krx_dellist])
        df_krx = df_krx.set_index('Symbol')
        return df_krx
    def get_total_finance_df(self):        
        #Code_df = SQLITE_control.DB_LOAD_Table(self.fs.TOTAL_JONGMOK_NAME_TABLE, self.fs.DB_TOTAL_JONGMOK_PATH)
        Code_df = self.get_stock_code_name()
        fail_list = []
        for num, code in enumerate(Code_df.index):            
            try:
                #if num == 10:break
                print(num, code)
                self.request_list = []                
                #profit_temp_df = self.get_profit_data(code, Code_df['IFRS'][num])
                #invest_temp_df = self.get_invest_data(code, Code_df['IFRS'][num])
                #cashflow_temp_df = self.get_cashflow_data(code, Code_df['IFRS'][num])
                #fs_temp_df = self.get_financeState_data(code, Code_df['IFRS'][num])
                profit_temp_df = self.get_profit_data(code, '개별')
                invest_temp_df = self.get_invest_data(code, '개별')
                cashflow_temp_df = self.get_cashflow_data(code,'개별')
                fs_temp_df = self.get_financeState_data(code, '개별')
                if num == 0:
                    invest_df = invest_temp_df
                    cashflow_df = cashflow_temp_df
                    fs_df = fs_temp_df
                    profit_df = profit_temp_df
                else:
                    invest_df = pd.concat([invest_df, invest_temp_df])
                    cashflow_df = pd.concat([cashflow_df, cashflow_temp_df])
                    fs_df = pd.concat([fs_df, fs_temp_df])
                    profit_df = pd.concat([profit_df, profit_temp_df])
            except:
               fail_list.append(code)
        temp = list(set(cashflow_df.columns.levels[0]).intersection(fs_df.columns.levels[0]))
        temp = list(set(temp).intersection(invest_df.columns.levels[0]))
        temp = list(set(temp).intersection(profit_df.columns.levels[0]))
        temp.sort()
        temp = pd.DataFrame(data=temp)
        for num, col in enumerate(temp[0]):
            temp_df1 = pd.merge(invest_df[col], cashflow_df[col], left_index=True, right_index=True)
            temp_df2 = pd.merge(fs_df[col], profit_df[col], left_index=True, right_index=True)
            total_df = pd.merge(temp_df1, temp_df2, left_index=True, right_index=True)
            total_df.columns = [[col]*len(total_df.columns),total_df.columns]
            SQLITE_control.DB_SAVE(total_df, self.fs.DB_FS_EXCEL_PATH, col, True)
        return

    def get_financeState_data_func(self, fs_url_total):
        with requests.Session() as s:
            login_req = s.post(self.LOGIN_URL, data=self.LOGIN_INFO, verify=False)
            fs_page_total = s.get(fs_url_total)
            fs_page_total.encoding = 'euc-kr'
            fs_tables_total = pd.read_html(fs_page_total.text)
            fs_tables_total[2]['재무상태표'] = fs_tables_total[1]['재무상태표']
            fs_df = fs_tables_total[2].set_index('재무상태표')
            fs_df = fs_df.loc[['유동자산', '현금및현금성자산', '매출채권', '재고자산', '비유동자산', '유형자산', '기계장치', '건설중인자산', '무형자산',
                               '영업권', '자산총계', '유동부채', '매입채무', '미지급금', '비유동부채', '부채총계', '단기차입금', '단기사채', '유동성장기부채',
                               '사채', '장기차입금', '장기금융부채', '지배주주지분', '자본금', '자본잉여금', '이익잉여금', '자본총계']]
            '''
            if len(fs_df.columns) < 40:
                pass
            else:
                fs_df = fs_df[['2019.12월', '2019.09월', '2019.06월', '2019.03월', '2018.12월', '2018.09월',
                               '2018.06월', '2018.03월', '2017.12월', '2017.09월', '2017.06월', '2017.03월',
                               '2016.12월', '2016.09월', '2016.06월', '2016.03월', '2015.12월', '2015.09월',
                               '2015.06월', '2015.03월', '2014.12월', '2014.09월', '2014.06월', '2014.03월',
                               '2013.12월', '2013.09월', '2013.06월', '2013.03월', '2012.12월', '2012.09월',
                               '2012.06월', '2012.03월', '2011.12월', '2011.09월', '2011.06월', '2011.03월',
                               '2010.12월', '2010.09월', '2010.06월', '2010.03월']] '''
            fs_df.columns = list(map(lambda x: x.replace(".", "/").replace("월", ""), fs_df.columns))
            fs_df.index = ['유동자산', '현금및현금성자산', '매출채권', '재고자산', '비유동자산', '유형자산', '기계장치', '건설중인자산', '무형자산',
                           '영업권', '자산총계', '유동부채', '매입채무', '미지급금', '비유동부채', '부채총계', '단기차입금', '단기사채', '유동성장기부채',
                           '사채', '장기차입금', '장기금융부채', '지배주주지분', '자본금', '자본잉여금', '이익잉여금', '자본총계']
            fs_df.index.name = "재무상태표"
            fs_df = fs_df.fillna(0)
            fs_df = fs_df.reset_index().drop_duplicates("재무상태표").set_index("재무상태표")
            #쿼터에서 RIM/ROE는 4분기데이터 가져올때 수행...
        return fs_df

    def get_financeState_data(self, code, type_fs):
        type_fs_flag = False
        if type_fs == '연결':
            fs_url_total = self.fs_total_url + code.replace("A","")
            type_fs_flag = True
        else:
            fs_url_total = self.fs_individual_url + code.replace("A","")
        fs_df = self.get_financeState_data_func(fs_url_total)
        #빠진쿼터데이터를 개별 재무제표로 채워넣기
        fs_df = fs_df.T
        # research        
        if type_fs_flag:
            fs_df_indiv = self.get_financeState_data_func(self.fs_individual_url + code.replace("A", ""))
            fs_df_indiv = fs_df_indiv.T
            for col in self.request_list:
                try:
                    fs_df.loc[col] = fs_df_indiv.loc[col]
                except:
                    pass
        fs_df = fs_df.T
        fs_df = pd.DataFrame(fs_df.unstack("재무상태표"), columns=[code]).T
        return fs_df

    def get_profit_data_func(self, profit_url_total):
        with requests.Session() as s:
            login_req = s.post(self.LOGIN_URL, data=self.LOGIN_INFO, verify=False)
            profit_page_total = s.get(profit_url_total)
            profit_page_total.encoding = 'euc-kr'
            profit_tables_total = pd.read_html(profit_page_total.text)
            profit_tables_total[2]['손익계산서'] = profit_tables_total[1]['손익계산서']
            profit_df = profit_tables_total[2].set_index('손익계산서')
            profit_df = profit_df.loc[['매출액(수익)', '매출원가', '재고자산의변동', '감가상각비', '매출총이익', '연구개발비', '영업이익',
                                       '법인세비용차감전계속사업이익', '법인세비용', '당기순이익', '지배지분 순이익', '총포괄이익', '지배지분 총포괄이익',
                                       '비지배지분 총포괄이익', '*EBITDA', '시가총액', '주가']]
            try:
                profit_df.index = ['매출액', '매출원가', '재고자산의변동', '감가상각비', '감가상각비(판관비)', '매출총이익', '연구개발비', '영업이익',
                                   '법인세비용차감전계속사업이익', '법인세비용', '당기순이익', '지배지분순이익', '총포괄이익', '지배지분총포괄이익',
                                   '비지배지분총포괄이익', 'EBITDA', '시가총액', '주가']
            except:
                profit_df.index = ['매출액', '매출원가', '재고자산의변동', '감가상각비', '매출총이익', '연구개발비', '영업이익',
                                   '법인세비용차감전계속사업이익', '법인세비용', '당기순이익', '지배지분순이익', '총포괄이익', '지배지분총포괄이익',
                                   '비지배지분총포괄이익', 'EBITDA', '시가총액', '주가']
            '''
            if len(profit_df.columns) < 40:
                pass
            else:
                profit_df = profit_df[['2019.12월', '2019.09월', '2019.06월', '2019.03월', '2018.12월', '2018.09월',
                                       '2018.06월', '2018.03월', '2017.12월', '2017.09월', '2017.06월', '2017.03월',
                                       '2016.12월', '2016.09월', '2016.06월', '2016.03월', '2015.12월', '2015.09월',
                                       '2015.06월', '2015.03월', '2014.12월', '2014.09월', '2014.06월', '2014.03월',
                                       '2013.12월', '2013.09월', '2013.06월', '2013.03월', '2012.12월', '2012.09월',
                                       '2012.06월', '2012.03월', '2011.12월', '2011.09월', '2011.06월', '2011.03월',
                                       '2010.12월', '2010.09월', '2010.06월', '2010.03월']]'''
            profit_df.columns = list(map(lambda x: x.replace(".", "/").replace("월", ""), profit_df.columns))
            profit_df.index.name = "손익계산서"
            profit_df = profit_df.reset_index().drop_duplicates("손익계산서").set_index("손익계산서")
            profit_df.index.name = "손익계산서"
            profit_df = profit_df.fillna(0)
            profit_df.loc['주식수'] = profit_df.loc['시가총액'].astype('int') / profit_df.loc['주가'].astype('int')
        return profit_df

    def get_profit_data(self, code, type_fs):
        type_fs_flag = False
        if type_fs == '연결':
            profit_url_total = self.profit_total_url + code.replace("A","")
            type_fs_flag = True
        else:
            profit_url_total = self.profit_individual_url + code.replace("A","")
        # 빠진쿼터데이터를 개별 재무제표로 채워넣기
        profit_df = self.get_profit_data_func(profit_url_total)
        profit_df = profit_df.T
        # research
        self.request_list = list(profit_df[(profit_df['EBITDA'].astype('float') == 0.0) & (profit_df['매출액'].astype('float') == 0.0)].index)
        if type_fs_flag:
            profit_df_indiv = self.get_profit_data_func(self.profit_individual_url + code.replace("A",""))
            profit_df_indiv = profit_df_indiv.T
            for col in self.request_list:
                try:
                    profit_df.loc[col] = profit_df_indiv.loc[col]
                except:
                    pass
        profit_df = profit_df.T
        profit_df = pd.DataFrame(profit_df.unstack("손익계산서"), columns=[code]).T
        return profit_df

    def get_cashflow_data_func(self, cashflow_url_total):
        with requests.Session() as s:
            login_req = s.post(self.LOGIN_URL, data=self.LOGIN_INFO, verify=False)
            cashflow_page_total = s.get(cashflow_url_total)
            cashflow_page_total.encoding = 'euc-kr'
            cashflow_tables_total = pd.read_html(cashflow_page_total.text)
            cashflow_tables_total[2]['현금흐름표'] = cashflow_tables_total[1]['현금흐름표']
            cashflow_df = cashflow_tables_total[2].set_index('현금흐름표')
            cashflow_df = cashflow_df.loc[['영업활동으로인한현금흐름', '유형자산감가상각비', '개발비상각', '무형자산상각비', '매출채권감소',
                                           '재고자산의감소', '선급금 감소', '선급비용 감소', '매입채무 증가', '선수금 증가', '투자활동으로인한현금흐름',
                                           '유형자산의증가', '토지의증가', '건물및부속설비의증가', '기계장치의증가', '건설중인자산의증가', '재무활동으로인한현금흐름',
                                           '현금의 증감', 'Free\xa0Cash\xa0Flow1']]
            '''
            if len(cashflow_df.columns) < 40:
                pass
            else:
                cashflow_df = cashflow_df[['2019.12월', '2019.09월', '2019.06월', '2019.03월', '2018.12월', '2018.09월',
                                           '2018.06월', '2018.03월', '2017.12월', '2017.09월', '2017.06월', '2017.03월',
                                           '2016.12월', '2016.09월', '2016.06월', '2016.03월', '2015.12월', '2015.09월',
                                           '2015.06월', '2015.03월', '2014.12월', '2014.09월', '2014.06월', '2014.03월',
                                           '2013.12월', '2013.09월', '2013.06월', '2013.03월', '2012.12월', '2012.09월',
                                           '2012.06월', '2012.03월', '2011.12월', '2011.09월', '2011.06월', '2011.03월',
                                           '2010.12월', '2010.09월', '2010.06월', '2010.03월']]'''
            cashflow_df.columns = list(map(lambda x: x.replace(".", "/").replace("월", ""), cashflow_df.columns))
            cashflow_df.index = ['영업활동으로인한현금흐름', '유형자산감가상각비', '개발비상각', '무형자산상각비', '매출채권감소',
                                 '재고자산의감소', '선급금 감소', '선급비용 감소', '매입채무 증가', '선수금 증가', '투자활동으로인한현금흐름',
                                 '유형자산의증가', '토지의증가', '건물및부속설비의증가', '기계장치의증가', '건설중인자산의증가', '재무활동으로인한현금흐름',
                                 '현금의증감', 'FCF']
            cashflow_df.index.name = "현금흐름표"
            cashflow_df = cashflow_df.fillna(0)
            cashflow_df = cashflow_df.reset_index().drop_duplicates("현금흐름표").set_index("현금흐름표")
        return cashflow_df

    def get_cashflow_data(self, code, type_fs):
        type_fs_flag = False
        if type_fs == '연결':
            cashflow_url_total = self.cashflow_total_url + code.replace("A","")
            type_fs_flag = True
        else:
            cashflow_url_total = self.cashflow_individual_url + code.replace("A","")
        cashflow_df = self.get_cashflow_data_func(cashflow_url_total)
        cashflow_df = cashflow_df.T
        # research
        if type_fs_flag:
            cashflow_df_indiv = self.get_cashflow_data_func(self.cashflow_individual_url + code.replace("A",""))
            cashflow_df_indiv = cashflow_df_indiv.T
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
                               '주가수익배수(PER)', '주당순자산(BPS, 지배)', '주가순자산배수(PBR)',
                               '주당현금흐름(CFPS)', '주가현금흐름배수(PCR)', '주당매출액(SPS)',
                               '주가매출액배수(PSR)', '주당배당금(DPS)', '시가배당률(%)',
                               '수익성 지표', '자기자본 이익률(ROE)', '=순이익률(ROS)',
                               'x 총자산회전율(S/A)', 'x 재무레버리지(A/E)', np.nan, '총자산 이익률(ROA)',
                               np.nan, '매출액 순이익률', '매출액 영업이익률', '성장성 지표',
                               '매출액 증가율', '영업이익 증가율', '순이익 증가율(지배)',
                               np.nan, '자기자본 증가율(지배)', '안전성 지표', '부채비율(%)',
                               '유동비율(%)', np.nan, '이자보상 배율(배)', np.nan, '자본잠식률(%)']
            invest_df = invest_df.loc[['주당순이익(EPS,연결지배)', '주가수익배수(PER)', '주당순자산(BPS, 지배)', '주가순자산배수(PBR)',
                                       '자기자본 이익률(ROE)', '=순이익률(ROS)', '총자산 이익률(ROA)', '주당현금흐름(CFPS)', '주가현금흐름배수(PCR)',
                                       '매출액 증가율', '영업이익 증가율', '순이익 증가율(지배)', '자기자본 증가율(지배)', '부채비율(%)', '유동비율(%)',
                                       '이자보상 배율(배)', '자본잠식률(%)', '주당매출액(SPS)']]
            '''
            if len(invest_df.columns) < 40:
                pass
            else:
                invest_df = invest_df[['2019.12월', '2019.09월', '2019.06월', '2019.03월', '2018.12월', '2018.09월',
                                       '2018.06월', '2018.03월', '2017.12월', '2017.09월', '2017.06월', '2017.03월',
                                       '2016.12월', '2016.09월', '2016.06월', '2016.03월', '2015.12월', '2015.09월',
                                       '2015.06월', '2015.03월', '2014.12월', '2014.09월', '2014.06월', '2014.03월',
                                       '2013.12월', '2013.09월', '2013.06월', '2013.03월', '2012.12월', '2012.09월',
                                       '2012.06월', '2012.03월', '2011.12월', '2011.09월', '2011.06월', '2011.03월',
                                       '2010.12월', '2010.09월', '2010.06월', '2010.03월']]'''
            invest_df.columns = list(map(lambda x: x.replace(".", "/").replace("월", ""), invest_df.columns))

            invest_df.index = ['EPS', 'PER', 'BPS', 'PBR', 'ROE', 'ROS', 'ROA', 'CFPS', 'PCR',
                               '매출액 증가율', '영업이익 증가율', '순이익 증가율(지배)',
                               '자기자본 증가율(지배)', '부채비율(%)', '유동비율(%)', '이자보상 배율(배)', '자본잠식률(%)',
                               '주당매출액(SPS)']
            invest_df.index.name = "재무비율"
            invest_df = invest_df.fillna(0)
            invest_df = invest_df.reset_index().drop_duplicates("재무비율").set_index("재무비율")
        return invest_df

    def get_invest_data(self, code, type_fs):
        type_fs_flag=False
        if type_fs == '연결':
            invest_url_total = self.invest_total_url + code.replace("A","")
            type_fs_flag = True
        else:
            invest_url_total = self.invest_individual_url + code.replace("A","")
        invest_df = self.get_invest_data_func(invest_url_total)
        invest_df = invest_df.T
        # research
        if type_fs_flag:
            invest_df_indiv = self.get_invest_data_func(self.invest_individual_url + code.replace("A",""))
            invest_df_indiv = invest_df_indiv.T
            for col in self.request_list:
                try:
                    invest_df.loc[col] = invest_df_indiv.loc[col]
                except:
                    pass
        invest_df = invest_df.T
        invest_df = pd.DataFrame(invest_df.unstack("재무비율"), columns=[code]).T
        return invest_df


if __name__ == "__main__":
    test = i_invest_crolling()
    test.get_total_finance_df()

        
        
        