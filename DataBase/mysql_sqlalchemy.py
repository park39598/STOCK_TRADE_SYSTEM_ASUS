# -*- coding: utf-8 -*-
"""
Created on Sat Feb 29 16:29:08 2020

@author: parkbumjin
"""
import pymysql
import pandas as pd
from sqlalchemy import create_engine
from sqlalchemy.types import VARCHAR
import time

def insert():
    
    #password는 본인의 DB에 접근할 수 있는 비밀번호를 변수로 설정하시면 됩니다.
    password = '#wkdhrl1024'
    conn = pymysql.connect(user='root',password=password,host='localhost',port=3306, charset='utf8')
    cursor = conn.cursor()

    # 엔진 역시, 본인의 DB설정에 맞춰 변경하시면 됩니다.
    engine = create_engine('mysql+pymysql://root:'+password+"@localhost/kospi_종목_주가?charset=utf8",encoding = 'utf-8')
    
    
    # 기업명 가져오기
    data = pd.read_excel('C:/Users/KK/Desktop/Python/Crawling/KOSPI_IPO.xlsx')

    data['종목코드'] = data['수정 종목코드'].map(lambda x : x.replace("!",''))

    name_list = data['회사명'].tolist()
    #return name_list
    
    err_count = 0
    
    for i in name_list:
        try:
            # 이전 포스팅에서 크롤링한 주가자료가 담긴 csv 파일의 위치입니다.
            temp = pd.read_csv('C:/Users/KK/Desktop/Python/Crawling/Data_set/KOSPI_stock/%s.csv'%(i), engine = 'python')
            temp.to_sql(name = i, con = engine, if_exists = 'append')
        
        except:
            err_count+=1
            print(i)
            

    cursor.close()
    
def DB_MYSQL_SET(table_name):
    password = '#wkdhrl1024'
    conn = pymysql.connect(user='root',password=password,host='localhost',port=3306, charset='utf8')
    cursor = conn.cursor()
    # 엔진 역시, 본인의 DB설정에 맞춰 변경하시면 됩니다.
    engine = create_engine('mysql+pymysql://root:'+password+"@localhost/"+table_name+"?charset=utf8",encoding = 'utf-8')
    return (conn, cursor, engine)    


def DB_SAVE_Finance(temp, DB_Name):
    time_finance = time.strftime('%Y-%m-%d', time.localtime(time.time()))
    (conn, cursor, engine) = DB_MYSQL_SET(DB_Name)
 #   new_year_fr_df.to_sql('indexes',engine,if_exists='replace',index_label='index',dtype={new_year_fr_df.index.name:VARCHAR(5)})
    temp = temp.T
    temp.to_sql(time_finance, engine, if_exists='replace',dtype={temp.index.name:VARCHAR(100)})
    conn.close()
    
def DB_LOAD_Finance(DB_Name):
    (conn, cursor, engine) = DB_MYSQL_SET(DB_Name)
    cursor.execute("SELECT name FROM sqlite_master WHERE type IN ('table', 'view') AND name NOT LIKE 'sqlite_%' UNION ALL SELECT name FROM sqlite_temp_master WHERE type IN ('table', 'view') ORDER BY 1")
    name_tuple =cursor.fetchall()
    table_name = str(name_tuple[-1]).replace(",","")   
    load_df = pd.read_sql("SELECT * FROM "+ table_name, con = engine)
    conn.close()
    return load_df

    