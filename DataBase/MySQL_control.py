# -*- coding: utf-8 -*-
"""
Created on Thu Feb 27 00:42:43 2020

@author: parkbumjin
"""
from sqlalchemy import create_engine
import pandas as pd
import sys

import pymysql
pymysql.install_as_MySQLdb()
import time
import pandas as pd
from Finance import finance_data
import numpy as np

class Create_DB:
    def __init__(self):
        self.mysql_ID = 'root'
        self.mysql_pass = '#wkdhrl1024'
    ##### DB에 접근 하기 위해 cursor를 많이 사용할 예정이기때문에 함수로 생성해둔다.
    ##### DB에 접근 할 cursor생성 함수
    def create_cursor(self, skima_name):
        ##### pymysql라이브러리로 내 데이터베이스에 접속
        self.conn = pymysql.connect(host='localhost', user='root', password=self.mysql_pass, charset='utf8', db= skima_name)

        ##### cursor객체 생성, cursor를 반복적으로 사용하기 위해 전역변수로 선언한다.
        self.cursor = self.conn.cursor()

    ##### DB접근을 종료 할 cursor삭제 함수
    def delete_cursor(self):
        self.conn.commit()
        self.conn.close()

    ##### to_sql메서드를 활용 하기위한 engine을 생성
    def create_engine(self, db_name):
        self.engine = create_engine("mysql+mysqldb://"+self.mysql_ID+":" + self.mysql_pass + "@localhost/{}".format(db_name),
                                    encoding='utf-8')
        self.conn2 = self.engine.connect()

        ##### 생성한 engine 삭제

    def delete_engine(self):
        self.conn2.close()


class DB_control(Create_DB):
    def __init__(self, logging=None):
        if logging == None:
            self.logging = None
        else:
            self.logging = logging

        self.mysql_ID = 'root'
        self.mysql_pass = '#wkdhrl1024'
        self.skima_stocks_list = 'stocks_lists_all'
        self.skima_stocks_finance = 'stocks_finance'
        self.skima_stocks_price = 'stocks_price'

    def logging_print(self, str):
        if self.logging == None:
            pass
        else:
            self.logging.logger.debug(str)

    def DB_SAVE(self, skima_name, table_name, temp_df, multi_index=False):
        self.create_engine(skima_name)
        if multi_index == True:
            temp_df = temp_df.reset_index().T.reset_index().T
        else:
            temp_df = temp_df.reset_index()
        ##### DB체크
        temp_df.to_sql(table_name, con=self.engine, if_exists='replace', index=False)
        self.logging_print("SAVE SUCCESS TO DB!")

        ##### 조회 결과는 테이블이 없을경우 None을 반환하고 있을 경우 1을 반환한다.
        #if_exists = self.cursor.fetchone()
        #print("SAVE SUCCESS TO DB!")
        #else : print("SAVE FAIL TO DB!")
        ##### 커서를 종료한다.
        self.delete_engine()

    def DB_SAVE_Price_Data(self, price_df, update_msg=False):
        if update_msg == True:
            update = 'append'
        else:
            update = 'replace'
        self.create_engine(self.skima_stocks_price)
        #con_temp = sqlite3.connect(finance_data.Price_data.DB_PRICE_PATH)
        #price_df = price_df.iloc[1:]
        #price_df = price_df.fillna(0)
        length_col = len(price_df.T)
        temp_a = price_df.T.iloc[:int(length_col / 4)].T.reset_index()
        temp_b = price_df.T.iloc[int(length_col / 4):int(length_col * 2 / 4)].T.reset_index()
        temp_c = price_df.T.iloc[int(length_col * 2 / 4):int(length_col * 3 / 4)].T.reset_index()
        temp_d = price_df.T.iloc[int(length_col * 3 / 4):length_col].T.reset_index()
        temp_a.to_sql('price_data_a', con=self.engine, if_exists='replace', index=False)
        temp_b.to_sql('price_data_b', con=self.engine, if_exists='replace', index=False)
        temp_c.to_sql('price_data_c', con=self.engine, if_exists='replace', index=False)
        temp_d.to_sql('price_data_d', con=self.engine, if_exists='replace', index=False)
        self.logging_print("SUCCESS SAVE PRICE_DATA TO DB!")

        self.delete_engine()

    def DB_LOAD_Price_Data(self):
        self.create_engine(self.skima_stocks_price)
        temp_a = pd.read_sql('price_data_a', con=self.engine, index_col=None)
        temp_b = pd.read_sql('price_data_b', con=self.engine, index_col=None)
        temp_c = pd.read_sql('price_data_c', con=self.engine, index_col=None)
        temp_d = pd.read_sql('price_data_d', con=self.engine, index_col=None)

        price_df = pd.merge(temp_a, temp_b, how='outer', left_index=False, right_index=False)
        price_df = pd.merge(price_df, temp_c, how='outer', left_index=False, right_index=False)
        price_df = pd.merge(price_df, temp_d, how='outer', left_index=False, right_index=False)
        self.delete_engine()
        price_df = price_df.set_index(price_df.columns[0])
        price_df.index = pd.to_datetime(price_df.index)
        self.logging_print("SUCCESS LOAD PRICE_DATA FROM DB!")
        return price_df

    def DB_LOAD_Table(self, skima_name, table_name, multi_index=False):
        skima_name = skima_name.lower()
        table_name = table_name.lower()
        self.create_engine(skima_name)
        table_df = pd.read_sql(table_name, con=self.engine, index_col=None)
        if multi_index == True:
            table_df = table_df.set_index(table_df.columns[0])
            table_df.columns = [table_df.iloc[0], table_df.iloc[1]]
            table_df = table_df[2:]
            table_df.columns.names = [None, None]
            #table_df.index.name = 'code'
        else:
            table_df = table_df.set_index(table_df.columns[0])
        self.delete_engine()
        self.logging_print("SUCCESS LOAD {}_DATA FROM DB!".format(table_name))
        return table_df

    def DB_LOAD_Col_From_Table(self, skima_name, table_name, col_names_list, multi_index=False):
        self.create_engine(skima_name)
        table_df = pd.read_sql(table_name, columns = col_names_list, con=self.engine, index_col=None)
        if multi_index == True:
            table_df = table_df.set_index(table_df.columns[0])
            table_df.columns = [table_df.iloc[0], table_df.iloc[1]]
            table_df = table_df[2:]
            table_df.columns.names = [None, None]
            #table_df.index.name = 'code'
        else:
            table_df = table_df.set_index(table_df.columns[0])
        self.delete_engine()
        self.logging_print("SUCCESS LOAD {} of {} DATA FROM DB!".format(col_names_list,table_name))
        return table_df

    def DB_LOAD_Close_Price_Data(self, start_date = '2009-01-01'):
        self.create_engine('stocks_price')
        code_list = self.engine.table_names()
        total_price = pd.DataFrame(data=None)
        cnt = 1
        for num, code in enumerate(code_list):
            #if num == 30 : break
            try:
                temp_df = pd.read_sql(code, con=self.engine, index_col=None)
                temp_df = temp_df.set_index(temp_df.columns[0])
                temp_df = temp_df[['Close']]
                temp_df.columns = [code]
                if num == 0:
                    total_price = temp_df.copy()
                else :
                    total_price = pd.merge(total_price, temp_df, how='outer', left_index=True, right_index=True)
                print(cnt)
                cnt = cnt + 1
            except: pass
        self.logging_print("SUCCESS LOAD CLOSE PRICE DATA FROM DB!")
        return total_price.loc[start_date:]

    def DB_LOAD_TABLE_LIST(self, skima_name):
        self.create_cursor(skima_name)
        sql = "SHOW TABLES"
        self.cursor.execute(sql)
        table_temp_list = self.cursor.fetchall()
        table_list = []
        for table in table_temp_list:
            table_list.append(table[0])
        self.logging_print("SUCCESS LOAD {} TABLE LIST FROM DB!".format(skima_name))
        return table_list

    # 특정행 제거
    def DB_DEL_ROW_FROM_TABLE(self, skima_name, sql):
        self.create_cursor(skima_name)
        self.logging_print(sql)
        self.cursor.execute(sql)
        # sql = "DELETE FROM {}.{} WHERE {}={};".format(skima_name, table_name, col_name, match_val)

    def DB_ADD_ROW_INTO_TABLE(self, skima_name, sql):
        self.create_cursor(skima_name)
        self.logging_print(sql)
        self.cursor.execute(sql)
        #INSERT INTO system_parameter.meme_portfolio(code, name, meme_price, meme, ratio) VALUES(271, 'parkbumjin', 200, 1700, 0.3)



    '''
    def System_Parameter_SAVE(self, algo1=None, algo2=None, algo3=None):
        temp_df = pd.DataFrame(index=['algo1','algo2','algo3'], columns=['start', 'end', 'algorithm'])
        for i in range(0, 3):
            if algo1 is not None : temp_df.loc['algo1'][i] = algo1[i]
            else : temp_df.loc['algo1'][i] = np.nan
            if algo2 is not None : temp_df.loc['algo2'][i] = algo2[i]
            else : temp_df.loc['algo2'][i] = np.nan
            if algo3 is not None : temp_df.loc['algo3'][i] = algo3[i]
            else : temp_df.loc['algo3'][i] = np.nan
        DB_PATH = 'f:\\OneDrive - Moedog, Inc\\STOCK_DB\\Parameter.db'
        con_temp = sqlite3.connect(DB_PATH)
        temp_df.to_sql('system_parameter', con_temp, if_exists='replace')
        if algo1 is not None : stocklist1 = pd.Series(algo1[3], name='algo1')
        else: stocklist1 = pd.Series(np.nan, name='algo1')
        if algo2 is not None : stocklist2 = pd.Series(algo2[3], name='algo2')
        else: stocklist2 = pd.Series(np.nan, name='algo2')
        if algo3 is not None : stocklist3 = pd.Series(algo3[3], name='algo3')
        else: stocklist3 = pd.Series(np.nan, name='algo3')
        stocklist_df = pd.concat([stocklist1, stocklist2], axis=1)
        stocklist_df = pd.concat([stocklist_df, stocklist3], axis=1)
        stocklist_df = stocklist_df.T
        stocklist_df.to_sql('stock_list', con_temp, if_exists='replace')
        con_temp.close()

    '''

if __name__ == '__main__':
    #DB_FS_EXCEL_PATH = 'F:\\OneDrive - Office 365\\STOCK_DB\\finance_excel_DB.db'
    test = DB_control()
    #price_data = test.DB_LOAD_Close_Price_Data('2000-01')
    #print(price_data.head())
    #test.DB_SAVE_Price_Data(price_data)