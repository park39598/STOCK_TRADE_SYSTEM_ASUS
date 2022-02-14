# -*- coding: utf-8 -*-
"""
Created on Thu Feb 20 21:33:28 2020
@author: parkbumjin
"""
# 크롤링 분기/연간 재무제표 클래스 추가할것 21.01.03

import pandas as pd
import requests
from bs4 import BeautifulSoup
import datetime
import sqlite3
import numpy as np
import DataBase.MySQL_control
import os
import logging.config
from datetime import datetime

# from Kiwoom import *
class fnguide_finance:
    def __init__(self):
        self.SQL = DataBase.MySQL_control.DB_control()
        #분기재무재표 수집
        #연결 재무제표
        self.연결_fs = 'http://comp.fnguide.com/SVO2/ASP/SVD_Finance.asp?pGB=1&cID=&MenuYn=Y&ReportGB=D&NewMenuID=103&stkGb=701&gicode='
        self.연결_invest = 'http://comp.fnguide.com/SVO2/ASP/SVD_Invest.asp?pGB=1&cID=&MenuYn=Y&ReportGB=D&NewMenuID=105&stkGb=701&gicode='
        self.연결_fr = 'http://comp.fnguide.com/SVO2/ASP/SVD_FinanceRatio.asp?pGB=1&cID=&MenuYn=Y&ReportGB=D&NewMenuID=104&stkGb=701&gicode='
        #별도 재무재표
        self.별도_fs = 'http://comp.fnguide.com/SVO2/ASP/SVD_Finance.asp?pGB=1&cID=&MenuYn=Y&ReportGB=B&NewMenuID=103&stkGb=701&gicode='
        self.별도_invest = 'http://comp.fnguide.com/SVO2/ASP/SVD_Invest.asp?pGB=1&cID=&MenuYn=Y&ReportGB=&NewMenuID=105&stkGb=701&gicode='
        self.별도_fr = 'http://comp.fnguide.com/SVO2/ASP/SVD_FinanceRatio.asp?pGB=1&cID=&MenuYn=Y&ReportGB=B&NewMenuID=104&stkGb=701&gicode='
        self.ROOT_DIR = os.path.abspath(os.curdir)
        self.logging = Logging(self.ROOT_DIR + '\\config\\logging.conf')
        self.logging.logger.debug("fnguide_finance class start.")


    def set_web_fs_indexname(self, df):
        new_index = []
        for index in df.index:
            new_index.append(index.replace('계산에 참여한 계정 펼치기', ''))
        df.index = new_index
        return df

    def get_fs_data(self, code, IFRS):
        if IFRS =='연결' : fs_url_total = self.연결_fs + code
        else : fs_url_total = self.별도_fs + code

        fs_page_total = requests.get(fs_url_total)

        try:
            fs_tables_total = pd.read_html(fs_page_total.text)
        except:
            self.logging.logger.debug("fs_tables Empty!")
            return (False, None, None)
        temp_df = fs_tables_total[0]
        if IFRS == '연결' : temp_df = temp_df.set_index(temp_df.columns[0])
        else : temp_df = temp_df.set_index(temp_df.columns[0])
        temp_df = self.set_web_fs_indexname(temp_df)
        df_year1 = temp_df.filter(like='/12')
        temp_df = fs_tables_total[2]
        if IFRS == '연결':
            temp_df = temp_df.set_index(temp_df.columns[0])
        else:
            temp_df = temp_df.set_index(temp_df.columns[0])
        temp_df = self.set_web_fs_indexname(temp_df)
        df_year2 = temp_df.filter(like='/12')
        temp_df = fs_tables_total[4]
        if IFRS == '연결':
            temp_df = temp_df.set_index(temp_df.columns[0])
        else:
            temp_df = temp_df.set_index(temp_df.columns[0])
        temp_df = self.set_web_fs_indexname(temp_df)
        df_year3 = temp_df.filter(like='/12')
        temp_df = fs_tables_total[1]
        #        temp_df.columns = temp_df.columns.droplevel()
        #        temp_df.columns = temp_df.columns[:-1].insert(0,'IFRS(연결)')
        if IFRS == '연결':
            temp_df = temp_df.set_index(temp_df.columns[0])
        else:
            temp_df = temp_df.set_index(temp_df.columns[0])
        temp_df = self.set_web_fs_indexname(temp_df)
        df_quarter1 = temp_df.filter(regex='\d')
        temp_df = fs_tables_total[3]
        #        temp_df.columns = temp_df.columns.droplevel()
        #        temp_df.columns = temp_df.columns[:-1].insert(0,'IFRS(연결)')
        if IFRS == '연결':
            temp_df = temp_df.set_index(temp_df.columns[0])
        else:
            temp_df = temp_df.set_index(temp_df.columns[0])
        temp_df = self.set_web_fs_indexname(temp_df)
        df_quarter2 = temp_df.filter(regex='\d')
        temp_df = fs_tables_total[5]
        #       temp_df.columns = temp_df.columns.droplevel()
        #       temp_df.columns = temp_df.columns[:-1].insert(0,'IFRS(연결)')
        if IFRS == '연결':
            temp_df = temp_df.set_index(temp_df.columns[0])
        else:
            temp_df = temp_df.set_index(temp_df.columns[0])
        temp_df = self.set_web_fs_indexname(temp_df)
        df_quarter3 = temp_df.filter(regex='\d')
        year_fs_df = pd.concat([df_year1, df_year2, df_year3])
        quarter_fs_df = pd.concat([df_quarter1, df_quarter2, df_quarter3])
        return (True, year_fs_df, quarter_fs_df)

    def get_fr_data(self, code, IFRS):
        if IFRS == '연결':
            fr_url_total = self.연결_fr + code
        else:
            fr_url_total = self.별도_fr + code
        fr_page_total = requests.get(fr_url_total)
        fr_tables_total = pd.read_html(fr_page_total.text)
        temp_df = fr_tables_total[0]
        if IFRS == '연결':
            temp_df = temp_df.set_index(temp_df.columns[0])
        else:
            temp_df = temp_df.set_index(temp_df.columns[0])
        temp_df = self.set_web_fs_indexname(temp_df)
        df_year = temp_df.filter(like='/12')
        temp_df = fr_tables_total[1]
        #        temp_df.columns = temp_df.columns.droplevel()
        #        temp_df.columns = temp_df.columns[:-1].insert(0,'IFRS(연결)')
        if IFRS == '연결':
            temp_df = temp_df.set_index(temp_df.columns[0])
        else:
            temp_df = temp_df.set_index(temp_df.columns[0])
        temp_df = self.set_web_fs_indexname(temp_df)
        df_quarter = temp_df.filter(regex='\d')
        return (df_year, df_quarter)

    def get_invest_data(self, code, IFRS):
        if IFRS == '연결':
            invest_url_total = self.연결_invest + code
        else:
            invest_url_total = self.별도_invest + code
        invest_page_total = requests.get(invest_url_total)
        invest_tables_total = pd.read_html(invest_page_total.text)
        temp_df = invest_tables_total[1]
        if IFRS == '연결':
            temp_df = temp_df.set_index(temp_df.columns[0])
        else:
            temp_df = temp_df.set_index(temp_df.columns[0])
        temp_df = self.set_web_fs_indexname(temp_df)
        df_year = temp_df.filter(like='/12')
        return df_year

    def get_finance_company_data(self):
        temp = pd.read_excel(self.Finance_Jongmok_Path)
        new_code = []
        for code in temp[temp.columns[0]]:
            new_code.append('A' + str(code))
        temp[temp.columns[0]] = new_code
        temp = temp.set_index(temp.columns[1])
        self.SQL.DB_SAVE('system_parameter', self.FINANCE_COMPANY_TABLE, temp[temp.columns[0]])
        return temp[temp.columns[0]]
    def change_finance_format(self, dataframe, code):
        total_df = pd.DataFrame(data=None)
        for num, col in enumerate(dataframe.columns):
            temp_df = pd.DataFrame({code: dataframe[col]})
            temp_df = temp_df.T
            temp_df.columns = [[col] * len(dataframe), temp_df.columns]
            if num == 0:
                total_df = temp_df.copy()
            else:
                total_df = pd.merge(total_df, temp_df, how='outer', left_index=True, right_index=True)
        return total_df
    def Crolling_fs_jokmok(self, code, IFRS):
        (valid, fs_year, fs_quarter) = self.get_fs_data(code, IFRS)
        if valid == False:
            return (False, None, None, None, None, None)
        (fr_year, fr_quarter) = self.get_fr_data(code, IFRS)
        invest_year = self.get_invest_data(code, IFRS)
        year_finance_df = pd.concat([fs_year, fr_year, invest_year])
        #       year_finance_df = year_finance_df.loc[
        #           ['매출액', '영업이익', '당기순이익', '자산', '부채', '자본', '*영업에서창출된현금흐름', '투자활동으로인한현금흐름',
        #            '재무활동으로인한현금흐름']]
        quarter_finance_df = pd.concat([fs_quarter, fr_quarter])
        #        quarter_finance_df = quarter_finance_df.loc[
        #            ['매출액', '영업이익', '당기순이익', '자산', '부채', '자본', '*영업에서창출된현금흐름', '투자활동으로인한현금흐름',
        #             '재무활동으로인한현금흐름']]
        # 더블인덱스 처리
        if year_finance_df.empty == False and quarter_finance_df.empty == False:
            new_year_fs_df = self.change_finance_format(fs_year, code)
            new_year_fr_df = self.change_finance_format(fr_year, code)
            new_year_invest_df = self.change_finance_format(invest_year, code)
            new_quarter_fs_df = self.change_finance_format(fs_quarter, code)
            new_quarter_fr_df = self.change_finance_format(fr_quarter, code)
        else:
            new_year_fs_df = pd.DataFrame(data=None)
            new_year_fr_df = pd.DataFrame(data=None)
            new_year_invest_df = pd.DataFrame(data=None)
            new_quarter_fs_df = pd.DataFrame(data=None)
            new_quarter_fr_df = pd.DataFrame(data=None)
        return (True, new_year_fs_df, new_year_fr_df, new_year_invest_df, new_quarter_fs_df, new_quarter_fr_df)

    def Crolling_fs_Total(self):
        prev_data = 0
        code_list = self.SQL.DB_LOAD_Table('stocks_lists', self.SQL.skima_stocks_list)
        code_list=code_list.set_index('Symbol')
        total_fs_year = pd.DataFrame(data=None)
        total_fr_year = pd.DataFrame(data=None)
        total_invest_year = pd.DataFrame(data=None)
        total_fs_quarter = pd.DataFrame(data=None)
        total_fr_quarter = pd.DataFrame(data=None)

        for num, code in enumerate(code_list.index):
            print(num, code)
            if num == 10 :
                test = 1
            if prev_data == int((num / len(code_list)) * 100):
                pass
            else:
                print(str(int((num / len(code_list)) * 100)) + '%')
                prev_data = int((num / len(code_list)) * 100)
            #try:
            (valid, temp_fs_year, temp_fr_year, temp_invest_year, temp_fs_quarter,
             temp_fr_quarter) = self.Crolling_fs_jokmok(code, code_list['IFRS'].loc[code])
            if valid == False : continue
            if num == 0 :
                total_fs_year = temp_fs_year
                total_fr_year = temp_fr_year
                total_invest_year = temp_invest_year
                total_fs_quarter = temp_fs_quarter
                total_fr_quarter = temp_fr_quarter
            else:
                total_fs_year = pd.concat([total_fs_year, temp_fs_year])
                total_fr_year = pd.concat([total_fr_year, temp_fr_year])
                total_invest_year = pd.concat([total_invest_year, temp_invest_year])
                total_fs_quarter = pd.concat([total_fs_quarter, temp_fs_quarter])
                total_fr_quarter = pd.concat([total_fr_quarter, temp_fr_quarter])
            #except:
            #    print(num, code)

        return total_fs_year, total_fr_year,total_invest_year,total_fs_quarter,total_fr_quarter

class Logging():
    def __init__(self, config_path, log_path='log'):
        self.config_path = config_path
        self.log_path = log_path
        logging.config.fileConfig(self.config_path)
        self.logger = logging.getLogger('finance_data')
        self.fnguide_finance_log()

    #로그설정
    def fnguide_finance_log(self):
        fh = logging.FileHandler(self.log_path+'/{:%Y-%m-%d}.log'.format(datetime.now()), encoding="utf-8")
        formatter = logging.Formatter('[%(asctime)s] I %(filename)s | %(name)s-%(funcName)s-%(lineno)04d I %(levelname)-8s > %(message)s')

        fh.setFormatter(formatter)
        self.logger.addHandler(fh)

class Finance_data:
    def __init__(self):
        self.SQL = DataBase.MySQL_control.DB_control()
        #self.SQL = DataBase.SQLITE_control.DB_control()
        self.ROOT_DIR = os.path.abspath(os.curdir)
        self.fs_url = 'http://comp.fnguide.com/SVO2/ASP/SVD_Finance.asp?pGB=1&cID=&MenuYn=Y&ReportGB=D&NewMenuID=103&stkGb=701&gicode='
        self.invest_url = 'http://comp.fnguide.com/SVO2/ASP/SVD_Invest.asp?pGB=1&cID=&MenuYn=Y&ReportGB=D&NewMenuID=105&stkGb=701&gicode='
        self.fr_url = 'http://comp.fnguide.com/SVO2/ASP/SVD_FinanceRatio.asp?pGB=1&cID=&MenuYn=Y&ReportGB=D&NewMenuID=104&stkGb=701&gicode='
        #        self.kw = Kiwoom()
        self.DB_FS_EXCEL_PATH = 'F:\\OneDrive - Office 365\\STOCK_DB\\finance_excel_DB.db'  # now & past 둘다 저장
        self.DB_FS_YEAR_PATH = 'F:\\OneDrive - Office 365\\STOCK_DB\\I_INVEST_DB.db'
        self.DB_FS_WEB_YEAR_PATH = 'F:\\OneDrive - Office 365\\STOCK_DB\\fs_web_year.db'
        self.DB_FS_WEB_QUARTER_PATH = 'F:\\OneDrive - Office 365\\STOCK_DB\\fs_web_quarter.db'
        self.DB_FR_WEB_YEAR_PATH = 'F:\\OneDrive - Office 365\\STOCK_DB\\fr_web_year.db'
        self.DB_FR_WEB_QUARTER_PATH = 'F:\\OneDrive - Office 365\\STOCK_DB\\fr_web_quarter.db'
        self.DB_INVEST_WEB_YEAR_PATH = 'F:\\OneDrive - Office 365\\STOCK_DB\\invest_web_year.db'
        self.DB_RIM_PATH = 'F:\\OneDrive - Office 365\\STOCK_DB\\STOCK_DB.db'
        self.DB_EXPECT_PROFIT_PATH = 'F:\\OneDrive - Office 365\\STOCK_DB\\STOCK_DB.db'
        self.DB_FINANCE_COMPANY_PATH = 'F:\\OneDrive - Office 365\\STOCK_DB\\STOCK_DB.db'
        self.DB_TOTAL_JONGMOK_PATH = 'F:\\OneDrive - Office 365\\STOCK_DB\\STOCK_DB.db'

        self.Excel_Value_now_Path = './DataBase\\FS_EXCEL\\value.xlsx'
        self.Excel_Eval_now_Path = '../DataBase\\FS_EXCEL\\가치평가.xlsx'
        self.Excel_FS_past_Path = '../DataBase\\FS_EXCEL\\종목별_재무\\'
        self.Finance_Jongmok_Path = '../DataBase\\FS_EXCEL\\금융권_종목.xlsx'
        self.Expect_Profit_Path = '../DataBase\\FS_EXCEL\\회사채_BBB-_수익률.xlsx'
        self.Backtest_Log_Path = '../Backtest\\BACKTEST_LOG\\'

        self.rim_L1 = 0.9
        self.rim_L2 = 0.8
        self.sale_factor = 0.085

        self.TOTAL_JONGMOK_NAME_TABLE = "jongmok_code_name"
        self.EXCEL_PAST_FS_TABLE = "PAST_10DECADE"
        self.EXPECT_PROFIT_TABLE = "expect_profit"
        self.FINANCE_COMPANY_TABLE = "finance_company"
        self.EXCEL_NOW_FS_TABLE = 'now_finance_excel'# 금융, 지주사, 중국기업 포함
        kospi = 0
        kosdaq = 10

    def set_web_fs_indexname(self, df):
        new_index = []
        for index in df.index:
            new_index.append(index.replace('계산에 참여한 계정 펼치기', ''))
        df.index = new_index
        return df

    def get_fs_data(self, code):
        fs_url_total = self.fs_url + code
        fs_page_total = requests.get(fs_url_total)
        fs_tables_total = pd.read_html(fs_page_total.text)
        temp_df = fs_tables_total[0]
        temp_df = temp_df.set_index('IFRS(연결)')
        temp_df = self.set_web_fs_indexname(temp_df)
        df_year1 = temp_df.filter(like='/12')
        temp_df = fs_tables_total[2]
        temp_df = temp_df.set_index('IFRS(연결)')
        temp_df = self.set_web_fs_indexname(temp_df)
        df_year2 = temp_df.filter(like='/12')
        temp_df = fs_tables_total[4]
        temp_df = temp_df.set_index('IFRS(연결)')
        temp_df = self.set_web_fs_indexname(temp_df)
        df_year3 = temp_df.filter(like='/12')
        temp_df = fs_tables_total[1]
        #        temp_df.columns = temp_df.columns.droplevel()
        #        temp_df.columns = temp_df.columns[:-1].insert(0,'IFRS(연결)')
        temp_df = temp_df.set_index('IFRS(연결)')
        temp_df = self.set_web_fs_indexname(temp_df)
        df_quarter1 = temp_df.filter(regex='\d')
        temp_df = fs_tables_total[3]
        #        temp_df.columns = temp_df.columns.droplevel()
        #        temp_df.columns = temp_df.columns[:-1].insert(0,'IFRS(연결)')
        temp_df = temp_df.set_index('IFRS(연결)')
        temp_df = self.set_web_fs_indexname(temp_df)
        df_quarter2 = temp_df.filter(regex='\d')
        temp_df = fs_tables_total[5]
        #       temp_df.columns = temp_df.columns.droplevel()
        #       temp_df.columns = temp_df.columns[:-1].insert(0,'IFRS(연결)')
        temp_df = temp_df.set_index('IFRS(연결)')
        temp_df = self.set_web_fs_indexname(temp_df)
        df_quarter3 = temp_df.filter(regex='\d')
        year_fs_df = pd.concat([df_year1, df_year2, df_year3])
        quarter_fs_df = pd.concat([df_quarter1, df_quarter2, df_quarter3])
        return (year_fs_df, quarter_fs_df)

    def get_fr_data(self, code):
        fr_url_total = self.fr_url + code
        fr_page_total = requests.get(fr_url_total)
        fr_tables_total = pd.read_html(fr_page_total.text)
        temp_df = fr_tables_total[0]
        temp_df = temp_df.set_index('IFRS(연결)')
        temp_df = self.set_web_fs_indexname(temp_df)
        df_year = temp_df.filter(like='/12')
        temp_df = fr_tables_total[1]
        #        temp_df.columns = temp_df.columns.droplevel()
        #        temp_df.columns = temp_df.columns[:-1].insert(0,'IFRS(연결)')
        temp_df = temp_df.set_index('IFRS(연결)')
        temp_df = self.set_web_fs_indexname(temp_df)
        df_quarter = temp_df.filter(regex='\d')
        return (df_year, df_quarter)

    def get_invest_data(self, code):
        invest_url_total = self.invest_url + code
        invest_page_total = requests.get(invest_url_total)
        invest_tables_total = pd.read_html(invest_page_total.text)
        temp_df = invest_tables_total[1]
        temp_df = temp_df.set_index('IFRS 연결')
        temp_df = self.set_web_fs_indexname(temp_df)
        df_year = temp_df.filter(like='/12')
        return df_year

    def get_finance_company_data(self):
        temp = pd.read_excel(self.Finance_Jongmok_Path)
        new_code = []
        for code in temp[temp.columns[0]]:
            new_code.append('A' + str(code))
        temp[temp.columns[0]] = new_code
        temp = temp.set_index(temp.columns[1])
        self.SQL.DB_SAVE('system_parameter', self.FINANCE_COMPANY_TABLE, temp[temp.columns[0]])
        return temp[temp.columns[0]]

    def Crolling_fs_jokmok(self, code):
        (fs_year, fs_quarter) = self.get_fs_data(code)
        (fr_year, fr_quarter) = self.get_fr_data(code)
        invest_year = self.get_invest_data(code)
        year_finance_df = pd.concat([fs_year, fr_year, invest_year])
        #       year_finance_df = year_finance_df.loc[
        #           ['매출액', '영업이익', '당기순이익', '자산', '부채', '자본', '*영업에서창출된현금흐름', '투자활동으로인한현금흐름',
        #            '재무활동으로인한현금흐름']]
        quarter_finance_df = pd.concat([fs_quarter, fr_quarter])
        #        quarter_finance_df = quarter_finance_df.loc[
        #            ['매출액', '영업이익', '당기순이익', '자산', '부채', '자본', '*영업에서창출된현금흐름', '투자활동으로인한현금흐름',
        #             '재무활동으로인한현금흐름']]
        # 더블인덱스 처리
        if year_finance_df.empty == False and quarter_finance_df.empty == False:
            new_year_fs_df = self.change_finance_format(fs_year, code)
            new_year_fr_df = self.change_finance_format(fr_year, code)
            new_year_invest_df = self.change_finance_format(invest_year, code)
            new_quarter_fs_df = self.change_finance_format(fs_quarter, code)
            new_quarter_fr_df = self.change_finance_format(fr_quarter, code)
        else:
            new_year_fs_df = pd.DataFrame(data=None)
            new_year_fr_df = pd.DataFrame(data=None)
            new_year_invest_df = pd.DataFrame(data=None)
            new_quarter_fs_df = pd.DataFrame(data=None)
            new_quarter_fr_df = pd.DataFrame(data=None)
        return (new_year_fs_df, new_year_fr_df, new_year_invest_df, new_quarter_fs_df, new_quarter_fr_df)

    def Crolling_fs_Total(self, code_list):
        prev_data = 0
        for num, code in enumerate(code_list):
            print(num, code)
            if prev_data == int((num / len(code_list)) * 100):
                pass
            else:
                print(str(int((num / len(code_list)) * 100)) + '%')
                prev_data = int((num / len(code_list)) * 100)
            try:
                (temp_fs_year, temp_fr_year, temp_invest_year, temp_fs_quarter,
                 temp_fr_quarter) = self.Crolling_fs_jokmok(code)
                if num == 0:
                    total_fs_year = temp_fs_year
                    total_fr_year = temp_fr_year
                    total_invest_year = temp_invest_year
                    total_fs_quarter = temp_fs_quarter
                    total_fr_quarter = temp_fr_quarter
                else:
                    total_fs_year = pd.concat([total_fs_year, temp_fs_year])
                    total_fr_year = pd.concat([total_fr_year, temp_fr_year])
                    total_invest_year = pd.concat([total_invest_year, temp_invest_year])
                    total_fs_quarter = pd.concat([total_fs_quarter, temp_fs_quarter])
                    total_fr_quarter = pd.concat([total_fr_quarter, temp_fr_quarter])
            except:
                pass
        self.SQL.DB_SAVE_Finance_Data(total_fs_year, self.DB_FS_WEB_YEAR_PATH)
        self.SQL.DB_SAVE_Finance_Data(total_fr_year, self.DB_FR_WEB_YEAR_PATH)
        self.SQL.DB_SAVE_Finance_Data(total_invest_year, self.DB_INVEST_WEB_YEAR_PATH)
        self.SQL.DB_SAVE_Finance_Data(total_fs_quarter, self.DB_FS_WEB_QUARTER_PATH)
        self.SQL.DB_SAVE_Finance_Data(total_fr_quarter, self.DB_FR_WEB_QUARTER_PATH)

        return total_fs_year, total_fr_year,total_invest_year,total_fs_quarter,total_fr_quarter

    def change_finance_format(self, dataframe, code):
        for num, col in enumerate(dataframe.columns):
            temp_df = pd.DataFrame({code: dataframe[col]})
            temp_df = temp_df.T
            temp_df.columns = [[col] * len(dataframe), temp_df.columns]
            if num == 0:
                total_df = temp_df
            else:
                total_df = pd.merge(total_df, temp_df, how='outer', left_index=True, right_index=True)
        return total_df

    def get_Finance_now_excel(self):  # file_path는 나중에 UI에서 지정되도록....
        mutiindex = True
        singleindex = False
        temp = pd.read_excel(self.Excel_Value_now_Path, sheet_name='종합')
        temp = temp.iloc[3:]
        temp.columns = list(temp.iloc[0])
        temp = temp.iloc[1:].set_index('code')
        #print(temp.columns)
        temp.columns = list(map(lambda x: str(x).replace(" ", ""), temp.columns))
        '''
        temp.columns = ['IFRS', '지분율', '실적', '종목', '현재가(원)', '시가총액(억)', '업종', '섹터',
                       '자사주', '부채비율', '유동비율', 'PER자사주', 'PER조정', 'PER', 'PBR',
                       'PSR', 'PCR', 'PGR', 'POR', 'EV/EBITDA', 'DY', 'ROE', 'ROA', 'OCF/A',
                       'GP/A', 'GP/S', '유형자산 이익률', '영업이익률', '순이익률', 'fscore', '신저가 괴리율', '수익률1년',
                       '변동성1년', '자본수익률', '이익수익률', '순현금비율', '19.1Q', '19.2Q',
                       '19.3Q', '19.4Q', '20.1Q', '20.2Q', 'YnY', 'QnQ', '19.1Q', '19.2Q',
                       '19.3Q', '19.4Q', '20.1Q', '20.2Q', 'YnY', 'QnQ', '19.1Q', '19.2Q',
                       '19.3Q', '19.4Q', '20.1Q', '20.2Q', 'YnY', 'QnQ', 'BPS 증가율', '매출액',
                       '매출총이익', '영업이익', '순이익', '자본총계', '자산총계', 'DPS(원)', 'OCF', '순현금',
                       '감가상각비', '현금성', '금융부채', '영업권', '유형자산', '신저가', '상장일', '시장', '자사주', '주식수',
                       '특이사항']
        '''
        temp = temp[['IFRS', '업종', '섹터', '실적', '지분율', '종목', '현재가(원)', '시가총액(억)',
                     '부채비율', '유동비율', 'PER조정', 'PER', 'PBR', 'PSR',
                     'PCR', 'PGR', 'POR', 'EV/EBITDA', 'DY', 'ROE', 'ROA', 'OCF/A', 'GP/A',
                     'GP/S', '영업이익률', '순이익률', 'fscore', '신저가괴리율', '수익률1년',
                     '변동성1년', '자본수익률', '이익수익률', '순현금비율', 'BPS증가율', '업종',
                     '매출액', '매출총이익', '영업이익', '순이익', '자본총계', '자산총계', 'DPS(원)', 'OCF',
                     '순현금', '감가상각비', '현금성', '금융부채', '영업권', '신저가', '상장일', '시장', '주식수',
                     '특이사항']]
        temp.columns = ['IFRS', '업종', '섹터', '실적', '지분율', '종목', '현재가', '시가총액',
                     '부채비율', '유동비율', 'PER조정', 'PER', 'PBR', 'PSR',
                     'PCR', 'PGR', 'POR', 'EV/EBITDA', 'DY', 'ROE', 'ROA', 'OCF/A', 'GP/A',
                     'GP/S', '영업이익률', '순이익률', 'fscore', '신저가  괴리율', '수익률1년',
                     '변동성1년', '자본수익률', '이익수익률', '순현금비율', 'BPS  증가율', '업종',
                     '매출액', '매출총이익', '영업이익', '순이익', '자본총계', '자산총계', 'DPS', 'OCF',
                     '순현금', '감가상각비', '현금성', '금융부채', '영업권', '신저가', '상장일', '시장', '주식수',
                     '특이사항']
        #temp = temp.iloc[3:]
        #temp = temp.set_index('code')
        Rim_df = self.Calc_RIM_now_excel(self.Excel_Eval_now_Path)
        temp = pd.merge(temp, Rim_df, how='outer', left_index=True, right_index=True)
        temp.index.name = 'code'
        temp.index = list(map(lambda x: x.replace("A", ""), temp.index))
        # time_table = time.strftime('%Y-%m-%d', time.localtime(time.time()))
        test = temp.reset_index()
        test.rename(columns={'index': 'code'}, inplace=True)
        #test
        self.SQL.DB_SAVE('finance', self.EXCEL_NOW_FS_TABLE, test)

        return temp

    def get_Finance_past_excel(self):
        CodebyName_df = self.SQL.DB_LOAD_Table('system_parameter', self.TOTAL_JONGMOK_NAME_TABLE)
        CodebyName_df = CodebyName_df[['종목']]
        total_df = pd.DataFrame(data=None)
        test_num = 0
        for num, code in enumerate(CodebyName_df.index):
            try:
                temp_df = self.get_Finance_past_excel_jongmok(CodebyName_df, code)
                if num == 0:
                    total_df = temp_df
                else:
                    total_df = pd.concat([total_df, temp_df])
            except:
                test_num = test_num + 1
                print(num, test_num, code)

                pass
        self.SQL.DB_SAVE('system_parameter', self.EXCEL_PAST_FS_TABLE, True)
        return True

    def get_Finance_past_excel_jongmok(self, CodebyName_df, code):
        jongmok = CodebyName_df.loc[code].values[0]
        file_path = self.Excel_FS_past_Path + jongmok + '.xlsx'
        temp = pd.read_excel(file_path)
        df_index = []
        df_col = []
        temp = temp.drop_duplicates("10년").set_index("10년")
        for index in temp.index:
            df_index.append(index.replace("(%)", "").strip())
        for col in temp.columns:
            df_col.append(str(col) + '/12')
        temp.index = df_index
        temp.columns = df_col
        temp.index.name = '항목'
        # 중복요소 제거
        temp_row = temp.loc['감가상각비'].iloc[1].copy()
        temp = temp.drop(['감가상각비'])
        temp.loc['감가상각비'] = temp_row
        temp_c = []
        expect_profit_df = self.SQL.DB_LOAD_Table('system_parameter', self.EXPECT_PROFIT_TABLE, False)
        expect_profit_df.index = pd.to_datetime(expect_profit_df.index)
        for col in temp.columns:
            temp_col = col.split('/')
            try:
                expect_profit_mean = expect_profit_df.loc[temp_col[0]].mean()
                temp_c.append(expect_profit_mean[expect_profit_df.columns[0]])
            except:
                temp_c.append(self.sale_factor)
        temp.loc['할인율'] = pd.Series(data=temp_c, index=temp.columns)
        temp = temp.loc[['BPS', 'EPS', 'ROA', 'ROE', 'capex', '감가상각비', '당기순이익', '단기금융부채',
                         '매입채무', '매출액', '매출액증가율', '매출원가', '매출채권', '장기금융부채',
                         '매출총이익', '무형자산', '무형자산취득', '법인세비용', '법인세율',
                         '법인세차감전순이익', '비유동부채', '비유동자산', '설비', '순운전자본',
                         '영업이익', '영업활동현금흐름', '유동부채', '유동자산', '유형자산',
                         '유형자산취득', '이익잉여금', '이자비용', '자기주식', '자본금', '자본잉여금',
                         '재고자산', '재무활동현금흐름', '지배주주지분', '총부채', '총자산', '할인율',
                         '투자활동현금흐름', '판매비와관리비', '현금성자산', '지배주주순이익', '배당성향(우)',
                         '배당수익률(우)', 'EV(기업가치)(억)', '잉여현금흐름(억)', 'EBITDA(억)','영업권']]
        temp.loc['순현금'] = temp.loc['현금성자산'] - temp.loc['단기금융부채'] - temp.loc['장기금융부채']
        temp.loc['주식수'] = temp.loc['지배주주지분'] * 100000000 / temp.loc['BPS'].replace(0, 1)
        temp.loc['수정BPS'] = (temp.loc['지배주주지분'] - temp.loc['무형자산']) * 100000000 / temp.loc['주식수'].replace(0, 1)
        temp.loc['RIM_ROE'] = self.Calc_ROE_AVG(temp.loc['ROE'])
        temp.loc['RIM'] = temp.loc['수정BPS'] + (
                    temp.loc['BPS'] * (temp.loc['RIM_ROE'] - temp.loc['할인율']) / temp.loc['할인율'])
        temp.loc['RIM_L1'] = temp.loc['수정BPS'] + (
                    temp.loc['BPS'] * (temp.loc['RIM_ROE'] * self.rim_L1 - temp.loc['할인율']) / (
                        1 + temp.loc['할인율'] - self.rim_L1))
        temp.loc['RIM_L2'] = temp.loc['수정BPS'] + (
                    temp.loc['BPS'] * (temp.loc['RIM_ROE'] * self.rim_L2 - temp.loc['할인율']) / (
                        1 + temp.loc['할인율'] - self.rim_L2))
        temp.loc['부채비율(%)'] = (temp.loc['총부채'] / temp.loc['지배주주지분'].replace(0, 1)) * 100
        temp.loc['유동비율(%)'] = (temp.loc['유동자산'] / temp.loc['유동부채'].replace(0, 1)) * 100
        temp.loc['유보율(%)'] = ((temp.loc['이익잉여금'] + temp.loc['자본잉여금']) / temp.loc['자본금'].replace(0, 1)) * 100
        temp.loc['재고회전율(%)'] = (temp.loc['매출액'] / temp.loc['재고자산'].replace(0, 1)) * 100
        temp = temp.reset_index().drop_duplicates("항목").set_index("항목")
        temp = pd.DataFrame(temp.unstack("항목"), columns=[code]).T

        return temp

    def shift_fwd(self, lst):
        lst_new = lst.copy()
        temp = lst[0]
        for i in range(1, len(lst)):
            lst_new[i - 1] = lst[i]
            if i == len(lst) - 1:
                lst_new[i] = np.nan
        return lst_new

    def shift_back(self, lst):
        lst_new = lst.copy()
        for i in range(len(lst)):
            if i == 0:
                lst_new[i + 1] = np.nan
            elif i == len(lst) - 1:
                pass
            else:
                lst_new[i + 1] = lst[i]
        return lst_new

    def Calc_ROE_AVG(self, data):
        ROE_data = data
        ROE_data.index.name = '일자'
        ROE_data = ROE_data.reset_index().sort_values('일자').set_index('일자')
        ROE_data_pct = pd.to_numeric(ROE_data['ROE'], errors='coerce').pct_change()
        ROE_data_pct_shift = self.shift_back(ROE_data_pct)
        ROE_data_pct_shift2 = self.shift_back(ROE_data_pct_shift)
        ROE_data_pct.name = 'ROE_PCT'
        ROE_data_pct_shift.name = 'ROE_PCT_shift'
        ROE_data_pct_shift2.name = 'ROE_PCT_shift2'
        ROE_data = pd.concat([ROE_data, ROE_data_pct], axis=1)
        ROE_data = pd.concat([ROE_data, ROE_data_pct_shift], axis=1)
        ROE_data = pd.concat([ROE_data, ROE_data_pct_shift2], axis=1)
        ROE_data['ROE'] = ROE_data['ROE'].replace("-", 0).astype('float')
        ROE_data['ROE평균'] = ROE_data['ROE'].rolling(3).sum() / 3
        ROE_data['ROE평균_shift'] = self.shift_back(ROE_data['ROE평균'])
        ROE_data['ROE추세'] = self.shift_back(ROE_data['ROE'])
        RIM_ROE = []
        for num, index in enumerate(ROE_data.index):            
            try:
                if ROE_data.iloc[num][2] * ROE_data.iloc[num][3] < 0:
                    RIM_ROE.append(ROE_data.iloc[num][5])
                else:
                    RIM_ROE.append(ROE_data.iloc[num][6])
            except:
                RIM_ROE.append(ROE_data.iloc[num][0])
                pass
        ROE_data = pd.concat([ROE_data, pd.Series(RIM_ROE, index=ROE_data.index, name='RIM_ROE')], axis=1)
        return ROE_data['RIM_ROE']

    def Calc_RIM_now_excel(self, Eval_file_path):  # file_path는 나중에 UI에서 지정되도록....
        # RIM SHEET COPY & SET
        temp_total = pd.read_excel(Eval_file_path, sheet_name='종합')
        temp_total = temp_total.iloc[3:]
        temp_total.columns = list(temp_total.iloc[0])
        temp_total = temp_total.iloc[1:]
        temp_total= temp_total.reset_index(drop=False)
        temp_total.columns = list(map(lambda x: str(x).replace(" ", ""), temp_total.columns))
        col = ['CODE', 'IFRS', '실적', '종목','PER', 'PBR', 'ROE',
               '시가총액(억)', '현재가(원)', 'RIM(원)', '숙향(원)', 'EPS성장율(원)', '눈덩이(원)',
               '야마구치(원)', '무성장가치(원)', 'BPS증가율(%)', '가치비교', '저평가수', '업종', '순이익', '자본총계',
               '주식수', 'nan', 'RIM', '숙향', 'EPS성장율', 'roe&pbr', '야마구치', '무성장가치']
        temp_total = temp_total[col]
        temp_total = temp_total.set_index('CODE')
        
        temp_rim = pd.read_excel(Eval_file_path, sheet_name='RIM')
        temp_rim = temp_rim.iloc[2:]
        temp_rim.columns = list(temp_rim.iloc[0])
        temp_rim.columns = list(map(lambda x: str(x).replace(" ", ""), temp_rim.columns))
        temp_rim = temp_rim.iloc[1:]
        temp_rim= temp_rim.reset_index(drop=False)
        col = ['CODE', '종목', '실적', '시가총액(억)', '현재가(원)', '기대수익율', '할인율',
               'V(원)', '자산가치(원)', '수익가치(원)', 'ROE평균', '순보통주', '수정BPS', 'BPS', '자본총계',
               '무형자산', '업종']
        temp_rim = temp_rim[col]
        temp_rim = temp_rim.set_index('CODE')
        temp_rim.columns = ['종목',  '실적', '시가총액(억)', '현재가(원)', '기대수익율', '할인율',
                            'RIM_V', '자산가치(원)', '수익가치(원)', 'ROE평균',
                            '순보통주', '수정BPS', 'BPS', '자본총계', '무형자산', '업종']
        
        temp_rim['ROE평균'] = temp_rim['ROE평균'].replace('-', temp_total['ROE']).replace('-', np.nan).astype('float')
        #temp_rim = temp_rim[['ROE평균']].dropna()
        # RIM 계산
        temp_rim['RIM_L2'] = temp_rim['수정BPS'].replace('-', np.nan).astype('float') + (temp_rim['BPS'].replace('-', np.nan).astype('float') * (temp_rim['ROE평균'] * self.rim_L2 - temp_rim['할인율'].replace('-', np.nan).astype('float')) / (
                1 + temp_rim['할인율'].replace('-', np.nan).astype('float') - self.rim_L2))
        temp_rim['RIM_L1'] = temp_rim['수정BPS'].replace('-', np.nan).astype('float') + (temp_rim['BPS'].replace('-', np.nan).astype('float') * (temp_rim['ROE평균'] * self.rim_L1 - temp_rim['할인율'].replace('-', np.nan).astype('float')) / (
                1 + temp_rim['할인율'].replace('-', np.nan).astype('float') - self.rim_L1))
        temp_rim['RIM'] = temp_rim['수정BPS'].replace('-', np.nan).astype('float') + (temp_rim['BPS'].replace('-', np.nan).astype('float') * (temp_rim['ROE평균'] - temp_rim['할인율'].replace('-', np.nan).astype('float')) / temp_rim['할인율'].replace('-', np.nan).astype('float'))
        temp_rim = temp_rim[['RIM', 'RIM_L1', 'RIM_L2']].dropna()
        return temp_rim

    def Calc_RIM_now_Web(self):
        # ROE, BPS로드, 무형자산
        # Sqlite Fr_data load , ROE
        fr_df = self.SQL.DB_LOAD_Finance_Data(self.DB_FR_WEB_YEAR_PATH)
        # 무형자산
        fs_df = self.SQL.DB_LOAD_Finance_Data(self.DB_FS_WEB_YEAR_PATH)
        # BPS(원)
        invest_df = self.SQL.DB_LOAD_Finance_Data(self.DB_INVEST_WEB_YEAR_PATH)
        common_col = list(set(list(set(fs_df.columns.levels[0]).intersection(fr_df.columns.levels[0]))).intersection(
            invest_df.columns.levels[0]))
        common_col.sort()
        for num, col in enumerate(common_col):
            fr_df[(col, 'ROE')] = pd.to_numeric(fr_df[(col, 'ROE')], errors='coerce')
            fs_df[(col, '무형자산')] = pd.to_numeric(fs_df[(col, '무형자산')], errors='coerce')
            fs_df[(col, '무형자산')] = fs_df[(col, '무형자산')].fillna(0)
            invest_df[(col, 'BPS')] = pd.to_numeric(invest_df[(col, 'BPS(원)')], errors='coerce')
            temp_df = pd.DataFrame(fr_df[(col, 'ROE')].copy())
            if num == 0:
                temp_df['ROE_평균'] = fr_df[(col, 'ROE')].copy()
                temp_df['무형자산'] = fs_df[(col, '무형자산')].copy()
                temp_df['BPS'] = invest_df[(col, 'BPS(원)')].copy()
            elif num == 1:
                temp_df['ROE_평균'] = (fr_df[(col, 'ROE')].copy() + fr_df[
                    (fr_df.columns.levels[0][num - 1], 'ROE')].copy()) / 2
                temp_df['무형자산'] = fs_df[(col, '무형자산')].copy()
                temp_df['BPS'] = invest_df[(col, 'BPS(원)')].copy()
            else:
                temp_df['ROE_평균'] = (fr_df[(col, 'ROE')].copy() + fr_df[
                    (fr_df.columns.levels[0][num - 1], 'ROE')].copy() + fr_df[
                                         (fr_df.columns.levels[0][num - 2], 'ROE')].copy()) / 3
                temp_df['무형자산'] = fs_df[(col, '무형자산')].copy()
                temp_df['BPS'] = invest_df[(col, 'BPS(원)')].copy()
                # fr_data, ROE추출
            temp_df.columns = [[col] * 4, ['ROE', 'ROE_평균', '무형자산', 'BPS']]
            if num == 0:
                total_RIM = temp_df
            else:
                total_RIM = pd.merge(total_RIM, temp_df, how='outer', left_index=True, right_index=True)


class Price_data:
    def __init__(self):
        self.DB_PRICE_PATH = 'f:\\OneDrive - Office 365\\STOCK_DB\\PRICE_DB.db'
        self.KOSPI_PRICE_TABLE = 'KOSPI_PRICE'
        self.KOSDAQ_PRICE_TABLE = 'KODAQ_PRICE'
        self.fs = Finance_data()

    def code_name_setup(self, code_list):
        new_code_list = []
        for code in code_list:
            if code == 'KOSDAQ' or code=='KOSPI':
                new_code_list.append(code)
            else:
                new_code_list.append(code.replace('A', ''))
        return new_code_list
    
    def make_KOSPI_KODAQ_price_data(self, stick_num):
        price_url_KOSPI = 'https://fchart.stock.naver.com/sise.nhn?symbol=KOSPI&timeframe=day&requestType=0&count='
        price_url_KOSDAQ = 'https://fchart.stock.naver.com/sise.nhn?symbol=KOSDAQ&timeframe=day&requestType=0&count='
        #코스피 날짜별 데이타
        price_url = price_url_KOSPI + str(stick_num)
        price_page = requests.get(price_url)
        price_page_bs = BeautifulSoup(price_page.text, 'lxml')
        price_data_temp = price_page_bs.find_all('item')
        price_data = []
        for i in range(len(price_data_temp)):
            price_data.append(price_data_temp[i]['data'])
            price_data[i] = price_data[i].split('|')        
        price_df = pd.DataFrame(data=price_data, columns=['일자', '시가', '고가', '저가', '종가', '거래량'])
        price_df.set_index('일자')
        #SQLITE_control.DB_SAVE(price_df, self.DB_PRICE_PATH, self.KOSPI_PRICE_TABLE)
        #코스닥 날짜별 데이타
        price_url = price_url_KOSDAQ + str(stick_num)
        price_page = requests.get(price_url)
        price_page_bs = BeautifulSoup(price_page.text, 'lxml')
        price_data_temp = price_page_bs.find_all('item')
        price_data = []
        for i in range(len(price_data_temp)):
            price_data.append(price_data_temp[i]['data'])
            price_data[i] = price_data[i].split('|')        
        price_df_b = pd.DataFrame(data=price_data, columns=['일자', '시가', '고가', '저가', '종가', '거래량'])
        price_df_b.set_index('일자')
        #SQLITE_control.DB_SAVE(price_df_b, self.DB_PRICE_PATH, self.KOSDAQ_PRICE_TABLE)
        return (price_df,price_df_b)
    
    def make_jongmok_price_data(self, code, stick_num):
        price_url = 'https://fchart.stock.naver.com/sise.nhn?timeframe=day&count='+str(stick_num)+'&requestType=0&symbol='
        price_url = price_url + code
        price_page = requests.get(price_url)
        price_page_bs = BeautifulSoup(price_page.text, 'lxml')
        price_data_temp = price_page_bs.find_all('item')
        price_data = []
        for i in range(len(price_data_temp)):
            price_data.append(price_data_temp[i]['data'])
            price_data[i] = price_data[i].split('|')
        if (code == 'KOSDAQ') or (code == 'KOSPI'):
            new_code = code
        else:
            new_code = 'A' + code
        price_df = pd.DataFrame(data=price_data, columns=['일자', '시가', '고가', '저가', new_code, '거래량'])        
        price_df['일자'] = pd.to_datetime(price_df['일자'])
        #price_df = price_df.set_index('일자')
        return price_df

    def make_total_price_df(self):
        code_list = self.SQL.DB_LOAD_Table('system_parameter', self.fs.TOTAL_JONGMOK_NAME_TABLE)
        new_code_list = self.code_name_setup(code_list.index)
        Code_Price = pd.DataFrame(data=None)
        prev_data = 0
        # 현재날짜와 price_db의 마지막날짜의 빈간격만큼만 크롤링해서 온다... 추후 다시 적용
        con_temp = sqlite3.connect(self.DB_PRICE_PATH)
        DB_cursor = con_temp.cursor()
        DB_cursor.execute("SELECT * FROM price_data_a ORDER BY 일자 DESC LIMIT 1")
        temp_df = DB_cursor.fetchone()
        time_last = pd.to_datetime(temp_df[0])
        time_now = datetime.datetime.now()
        #stick_num = time_now - time_last
        #stick_num = stick_num.days + 1        
        stick_num = 6000
        con_temp.close()
        for num, code in enumerate(new_code_list):
            if prev_data == int((num / len(new_code_list)) * 100):
                pass
            else:
                print(str(int((num / len(new_code_list)) * 100)) + '%')
                prev_data = int((num / len(new_code_list)) * 100)
            #            if (num == 100):
            #                break
            price_df = self.make_jongmok_price_data(code, stick_num)
            if (code == 'KOSDAQ') or (code == 'KOSPI'):
                new_code = code
            else:
                new_code = 'A' + code
            if num == 0:
                Code_Price = price_df[['일자', new_code]]
            else:
                Code_Price = pd.merge(Code_Price, price_df[['일자', new_code]], how='outer')
        #Code_Price['일자'] = pd.to_datetime(Code_Price['일자'])
        Code_Price = Code_Price.sort_values(by='일자').set_index('일자')
        #DB에 저장된 price_data 불러와 추가하여 다시 저장
        #prev_price_data = self.DB_LOAD_Price_Data()
        #Code_Price = pd.concat([prev_price_data, Code_Price])
        #Code_Price = Code_Price.sort_values(by='일자')
        self.DB_SAVE_Price_Data(Code_Price)
        return Code_Price
    
    def Calc_Stochastick_Slow_market(self, nF, nM1, nM2, market = 'kospi'):
        (kospi, kosdaq) = self.make_KOSPI_KODAQ_price_data(3000)
        if market == 'kospi':
            data = kospi
        else:
            data = kosdaq
        maxV = data.고가.rolling(nF).max()
        minV = data.저가.rolling(nF).min()
        maxV.fillna(0)
        minV.fillna(0)        
        data['fast_K'] = (data['종가'].astype('float') - minV)*100 / (maxV-minV)
        data['slow_K'] = data['fast_K'].rolling(nM1).mean()
        data['slow_D'] = data['slow_K'].rolling(nM2).mean()
        data = data.set_index('일자')
        data['K-D']=data['slow_K'] - data['slow_D'] 
        data['K-D_shift'] = data['K-D'].shift()
        data['cross_point'] = np.nan
        for date in data.index:
            temp = data['K-D_shift'].loc[date] * data['K-D'].loc[date]
            if temp < 0:
                if data['K-D'].loc[date] < 0:
                    if data['slow_K'].loc[date] > 75:
                        data['cross_point'].loc[date] = 'D_75'
                    else:
                        data['cross_point'].loc[date] = 'D'
                else:
                    if data['slow_K'].loc[date] < 25:
                        data['cross_point'].loc[date] = 'G_25'
                    else:
                        data['cross_point'].loc[date] = 'G'
            else:
                pass
        data = data[['cross_point']].dropna()
        data['cross_point_1shift'] = data['cross_point'].shift()
        data['cross_point_2shift'] = data['cross_point_1shift'].shift()
        data['rebalancing'] = np.nan
        for date in data.index:
            c = data['cross_point'].loc[date]
            b = data['cross_point_1shift'].loc[date]
            a = data['cross_point_2shift'].loc[date]
            if (a == 'D_75') & (b == 'G') & (c == 'D'):
                data['rebalancing'].loc[date] = '매도'
            elif (a == 'G_25') & (b == 'D') & (c == 'G'):
                data['rebalancing'].loc[date] = '매수'
            else:
                pass
        rebal_time = data[['rebalancing']].dropna() 
        if market == 'kospi':
            self.SQL.DB_SAVE('system_parameter', self.KOSPI_PRICE_TABLE, data)
        else:
            self.SQL.DB_SAVE('system_parameter', self.KOSPI_PRICE_TABLE, data)
        return rebal_time
        
    def DB_SAVE_Price_Data(self, price_df):
        '''
        con_temp = sqlite3.connect(self.DB_PRICE_PATH)
        DB_cursor = con_temp.cursor()
        DB_cursor.execute("SELECT * FROM price_data_a ORDER BY 일자 DESC LIMIT 1")
        temp_df = DB_cursor.fetchone()
        price_df = price_df.loc[temp_df[0]:]
        price_df = price_df.iloc[1:]
        '''
        price_df = price_df.reset_index().drop_duplicates("일자").set_index("일자")
        con_temp = sqlite3.connect(self.DB_PRICE_PATH)
        length_col = len(price_df.T)
        temp_a = price_df.T.iloc[:int(length_col / 3)].T
        temp_b = price_df.T.iloc[int(length_col / 3):int(length_col * 2 / 3)].T
        temp_c = price_df.T.iloc[int(length_col * 2 / 3):length_col].T
        temp_a.to_sql('price_data_a', con_temp, if_exists='replace')
        temp_b.to_sql('price_data_b', con_temp, if_exists='replace')
        temp_c.to_sql('price_data_c', con_temp, if_exists='replace')
        con_temp.close()

    def DB_LOAD_Price_Data(self):
        DB_PRICE_PATH = 'f:\\OneDrive - Office 365\\STOCK_DB\\price_DB.db'
        con_temp = sqlite3.connect(DB_PRICE_PATH)
        temp_a = pd.read_sql("SELECT * FROM price_data_a", con_temp, index_col=None)
        temp_b = pd.read_sql("SELECT * FROM price_data_b", con_temp, index_col=None)
        temp_c = pd.read_sql("SELECT * FROM price_data_c", con_temp, index_col=None)
        price_df = pd.merge(temp_a, temp_b, how='outer', left_index=False, right_index=False)
        price_df = pd.merge(price_df, temp_c, how='outer', left_index=False, right_index=False)
        con_temp.close()
        price_df = price_df.set_index(price_df.columns[0])
        price_df.index = pd.to_datetime(price_df.index)
        return price_df


if __name__ == "__main__":
    test = fnguide_finance()
    a,b,c,d,e = test.Crolling_fs_Total()
    a.to_excel('f:\\a.xlsx')
    b.to_excel('f:\\b.xlsx')
    c.to_excel('f:\\c.xlsx')
    d.to_excel('f:\\d.xlsx')
    e.to_excel('f:\\e.xlsx')



    #fs = Finance_data()
    #pr = Price_data()
    #Excel_Value_Path = 'F:\\OneDrive - Office 365\\EXCEL\\value.xlsx'
 #   price_df = pr.make_total_price_df()
    #temp = fs.get_Finance_now_excel()
    #print(temp)
    #(kospi,kosdaq) = pr.make_KOSPI_KODAQ_price_data(3000)
   #pr.Calc_Stochastick_Slow(5,3,3,kospi)
    #temp = fs.get_Finance_now_excel(Excel_Value_Path)

#    code_list = SQLITE_control.DB_LOAD_Table(fs.TOTAL_JONGMOK_NAME_TABLE, fs.DB_TOTAL_JONGMOK_PATH)
 #   past = fs.get_Finance_past_excel()
#    temp = fs.get_Finance_now_excel(Excel_Value_Path)

#    price_df = pr.make_total_price_df()

#   print(temp.head())
