# -*- coding: utf-8 -*-
"""
Created on Thu Feb 27 00:42:43 2020

@author: parkbumjin
"""

import sqlite3
import time
import pandas as pd
from Finance import finance_data
import numpy as np

class DB_control():
    def __init__(self):
        pass
    def DB_LOAD_TABLE_LIST(self, data_path):
        con_temp = sqlite3.connect(data_path)
        DB_cursor = con_temp.cursor()
        try:
            DB_cursor.execute("SELECT name FROM sqlite_master WHERE type IN('table', 'view') AND name NOT LIKE 'sqlite_%' UNION ALL SELECT name FROM sqlite_temp_master WHERE type IN('table', 'view') ORDER BY 1")
            table_list = DB_cursor.fetchall()
        except :
            return None
        con_temp.close()
        return table_list

    def DB_TABLE_MAKE(self, data_path, table_name, column_name, column_type):
        con_temp = sqlite3.connect(data_path)
        DB_cursor = con_temp.cursor()
        try:
            DB_cursor.execute("CREATE TABLE "+table_name+"("+column_name+" "+column_type)
        except :
            return False
        con_temp.close()
        return True

    def DB_SAVE(self, temp, data_path, table_name, multi_index=False, method = 'replace'):
        con_temp = sqlite3.connect(data_path)
        if multi_index == True:
            temp = temp.T.reset_index().T
        else:
            pass
        temp.to_sql(table_name, con_temp, if_exists=method)
        con_temp.close()
        return True


    def DB_LOAD_Table(self, table_name, DB_Path, multi_index=False):
        con = sqlite3.connect(DB_Path)
        table_df = pd.read_sql("SELECT * FROM " + "'"+table_name+"'", con, index_col=None)
        if multi_index == True:
            table_df = table_df.set_index(table_df.columns[0])
            table_df.columns = [table_df.iloc[0], table_df.iloc[1]]
            table_df = table_df[2:]
            table_df.columns.names = [None, None]
            table_df.index.name = 'code'
        else:
            table_df = table_df.set_index(table_df.columns[0])
        con.close()
        return table_df


    def DB_LOAD_Col( self,col_name, table_name, DB_Path):
        con = sqlite3.connect(DB_Path)
        col_df = pd.read_sql("SELECT " + col_name + " FROM " + table_name, con, index_col=None)
        con.close()
        return col_df


    def DB_SAVE_Finance_Data(self, temp, DB_Path):
        time_finance = time.strftime('%Y-%m-%d', time.localtime(time.time()))
        con_temp = sqlite3.connect(DB_Path)
        temp = temp.T.reset_index().T
        temp.to_sql(time_finance, con_temp, if_exists='replace')
        con_temp.close()
        return


    def DB_LOAD_Finance_Data(self, DB_Path):
        con = sqlite3.connect(DB_Path)
        DB_cursor = con.cursor()
        DB_cursor.execute(
            "SELECT name FROM sqlite_master WHERE type IN ('table', 'view') AND name NOT LIKE 'sqlite_%' UNION ALL SELECT name FROM sqlite_temp_master WHERE type IN ('table', 'view') ORDER BY 1")
        name_tuple = DB_cursor.fetchall()
        temp = str(name_tuple[-1]).replace(",", "")
        table_df = pd.read_sql("SELECT * FROM " + temp, con, index_col=None)
        table_df = table_df.set_index('index')
        table_df.columns = [table_df.iloc[0], table_df.iloc[1]]
        table_df = table_df[2:]
        table_df.columns.names = [None, None]
        table_df.index.name = 'code'
        con.close()
        return table_df


    def DB_LOAD_Latest_Table(self, DB_Path):
        con = sqlite3.connect(DB_Path)
        DB_cursor = con.cursor()
        DB_cursor.execute(
            "SELECT name FROM sqlite_master WHERE type IN ('table', 'view') AND name NOT LIKE 'sqlite_%' UNION ALL SELECT name FROM sqlite_temp_master WHERE type IN ('table', 'view') ORDER BY 1")
        name_tuple = DB_cursor.fetchall()
        temp = str(name_tuple[-1]).replace(",", "")
        table_df = pd.read_sql("SELECT * FROM " + temp, con, index_col=None)
        #    time.sleep(0.2)
        table_df = table_df.set_index(table_df.columns[0])
        con.close()
        return table_df


    def DB_SAVE_Price_Data(self, price_df, update_msg=False):
        if update_msg == True:
            update = 'append'
        else:
            update = 'replace'
        con_temp = sqlite3.connect(finance_data.Price_data.DB_PRICE_PATH)
        DB_cursor = con_temp.cursor()
        DB_cursor.execute("SELECT * FROM price_data_a ORDER BY 일자 DESC LIMIT 1")
        temp_df = DB_cursor.fetchone()
        price_df = price_df.loc[temp_df[0]:]
        price_df = price_df.iloc[1:]
        length_col = len(price_df.T)
        temp_a = price_df.T.iloc[:int(length_col / 3)].T
        temp_b = price_df.T.iloc[int(length_col / 3):int(length_col * 2 / 3)].T
        temp_c = price_df.T.iloc[int(length_col * 2 / 3):length_col].T
        temp_a.to_sql('price_data_a', con_temp, if_exists=update)
        temp_b.to_sql('price_data_b', con_temp, if_exists=update)
        temp_c.to_sql('price_data_c', con_temp, if_exists=update)
        con_temp.close()


    def DB_LOAD_Price_Data(self):
        DB_PRICE_PATH = 'f:\\OneDrive - Office 365\\STOCK_DB\\PRICE_DB.db'
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