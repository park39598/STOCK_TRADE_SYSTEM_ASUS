# -*- coding: utf-8 -*-
"""
Created on Thu Mar 26 15:33:27 2020

@author: PARK BUMJIN
"""

from pykrx import stock
import pandas as pd
import requests
from bs4 import BeautifulSoup
import time, datetime
import sqlite3
import numpy as np


def make_total_price():
    Code_df = DB_LOAD_Table(TOTAL_JONGMOK_NAME_TABLE, DB_TOTAL_JONGMOK_PATH)
    new_code = []
    for num, code in enumerate(Code_df.index):
        new_code.append(code.replace("A", ""))
    Code_df.index = new_code
    for code in Code_df.index:
        df = pykrx.stock.get_market_ohlcv_by_date("20090101", "20200326", code, adjusted=False)
        if num == 0:
            total_df = df['종가']
            total_df
        else:
            total_df = pd.merge


# 설비투자에 따른 주가 추이 분석 20.07.26
def load_investment_data_quarter():
    date_list = ['2019/12', '2019/09', '2019/06', '2019/03', '2018/12', '2018/09', '2018/06', '2018/03', '2017/12',
                 '2017/09', '2017/06', '2017/03',
                 '2016/12', '2016/09', '2016/06', '2016/03', '2015/12', '2015/09', '2015/06', '2015/03', '2014/12',
                 '2014/09', '2014/06', '2014/03',
                 '2013/12', '2013/09', '2013/06', '2013/03', '2012/12', '2012/09', '2012/06', '2012/03', '2011/12',
                 '2011/09', '2011/06', '2011/03',
                 '2010/12', '2010/09', '2010/06', '2010/03', '2009/12', '2009/09', '2009/06', '2009/03',
                 '2008/12', '2008/09', '2008/06', '2008/03', '2007/12', '2007/09', '2007/06', '2007/03',
                 '2006/12', '2006/09', '2006/06', '2006/03', '2005/12', '2005/09', '2005/06', '2005/03',
                 '2004/12', '2004/09', '2004/06', '2004/03', '2003/12', '2003/09', '2003/06', '2003/03',
                 '2002/12', '2002/09', '2002/06', '2002/03', '2001/12', '2001/09', '2001/06', '2001/03',
                 '2000/12', '2000/09', '2000/06', '2000/03']
    date_index_num = date_list.index(index_date)
    for num in range(len(date_list)):
        temp_df = SQLITE_control.DB_LOAD_Table(date_list[num], self.fs.DB_FS_EXCEL_PATH, True)
        if num == 0:
            total_df = pd.DataFrame(data=None)
            total_df[date_list[num]] = temp_df[(date_list[num], "유형자산의증가")].astype("float")
        else:
            total_df[date_list[num]] = temp_df[(date_list[num], "유형자산의증가")].astype("float")

    return total_df

