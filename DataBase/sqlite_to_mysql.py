# -*- coding: utf-8 -*-
"""
Spyder Editor

This is a temporary script file.
"""
import sqlite3
import pymysql
from sqlalchemy import create_engine
import pandas as pd
import sys
pymysql.install_as_MySQLdb()


def DB_LOAD_TABLE_LIST(data_path):
    con_temp = sqlite3.connect(data_path)
    DB_cursor = con_temp.cursor()
    try:
        DB_cursor.execute(
            "SELECT name FROM sqlite_master WHERE type IN('table', 'view') AND name NOT LIKE 'sqlite_%' UNION ALL SELECT name FROM sqlite_temp_master WHERE type IN('table', 'view') ORDER BY 1")
        table_list = DB_cursor.fetchall()
    except:
        return None
    con_temp.close()
    return table_list

def DB_LOAD_Table(table_name, DB_Path, multi_index=False):
    con = sqlite3.connect(DB_Path)
    table_df = pd.read_sql("SELECT * FROM " + "'"+table_name+"'", con, index_col=None)
    if multi_index == True:
        table_df = table_df.set_index(table_df.columns[0])
        table_df.columns = [table_df.iloc[0], table_df.iloc[1]]
        table_df = table_df[2:]
        table_df.columns.names = [None, None]
        #table_df.index.name = 'code'
    else: pass
        #table_df = table_df.set_index(table_df.columns[0])
    con.close()
    return table_df

def mysql_save(skima_name, table_name, temp_df, multi_index = False):
    engine = create_engine("mysql+mysqldb://root:" + "#wkdhrl1024" + "@localhost/{}".format(skima_name),
                                    encoding='utf-8')
    conn = engine.connect()
    if multi_index == True:
        temp_df = temp_df.T.reset_index().T
    else:
        pass
    ##### DB체크
    #temp_df = temp_df.reset_index()
    #print(temp_df.index)
    temp_df.to_sql(name = table_name, con=engine, if_exists='replace', index=False)

    ##### 조회 결과는 테이블이 없을경우 None을 반환하고 있을 경우 1을 반환한다.
    #if_exists = cursor.fetchone()

    ##### 커서를 종료한다.
    #conn.commit()
    conn.close()
    print("success")
    
def save_sqlite_to_mysql(DB_path, skima):
    table_list = list(DB_LOAD_TABLE_LIST(DB_path))
    cnt = 0

    for table_name in table_list:
        temp_df = DB_LOAD_Table(table_name[0], DB_path, False)
        mysql_save(skima, table_name[0], temp_df, False)
        print(cnt)
        cnt = cnt+1


if __name__ == '__main__':
    PATH = 'D:\\OneDrive - Office 365\\STOCK_DB\\price_DB.db'
    save_sqlite_to_mysql(PATH, 'stocks_finance')
