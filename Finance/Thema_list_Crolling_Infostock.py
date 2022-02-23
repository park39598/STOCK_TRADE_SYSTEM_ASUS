import requests
from bs4 import BeautifulSoup
import os
import FinanceDataReader as fdr

from pykrx import stock
import pandas as pd
import DataBase.MySQL_control
import re

thread_num = 4
import tqdm
from pathlib import Path
import re

#thema_url='http://m.infostock.co.kr/sector/sector_detail.asp?theme=2%uCC28%uC804%uC9C0&mode=w&code='

class Crolling_ThemaList_Infostock():
    def __init__(self):
        self.main_url='http://m.infostock.co.kr/sector/sector.asp?mode=w'
        self.thema_url='http://m.infostock.co.kr/sector/sector_detail.asp?theme=2%uCC28%uC804%uC9C0&mode=w&code='
        self.DB = DataBase.MySQL_control.DB_control()
    # 크롤릴을 위해서는 Thema의 넘버가 필요함...
    def preprocess_ThemaList(self,df):
        thema = df[1]
        thema = thema.iloc[3:]
        thema.columns = thema.iloc[0]
        thema = thema.iloc[1:]
        thema['관련종목'] = thema['관련종목'].map(lambda x:str(x).replace("- ", ""))
        thema['Name'] = thema['관련종목'].map(lambda x: str(x).split(" ")[0])
        thema['Code']=thema['관련종목'].map(lambda x: 'a'+(str(x).split(" ")[1].replace("(","").replace(")","")))
        thema=thema.drop(["관련종목"], axis=1)
        thema=thema.set_index("Code")
        return thema

    def Get_Thema_Number_Name(self):
        s=requests.get(self.main_url)
        s.encoding = 'euc-kr'
        html = s.text
        soup = BeautifulSoup(html, 'html.parser')
        html_list = soup.select('td > a')
        total_df=pd.DataFrame(data=None, columns=['num','name'])
        for i, data in enumerate(tqdm.tqdm(html_list[1:])):
            num=int(str(data).split("'")[3])
            name=data.string.split("◎ ")[1].lower().replace(" ","")
            total_df=total_df.append(pd.Series([num,name],index=['num','name']),ignore_index=True)

            thema_list=pd.read_html(self.thema_url+str(num))
            try:
                thema=self.preprocess_ThemaList(thema_list)
            except:
                print(num, name)
                continue
            self.DB.DB_SAVE("stocks_thema_list",name,thema)

    def Make_Sector_index(self, sector, start,end):
        total_price=pd.DataFrame(data=None)
        total_ratio = pd.DataFrame(data=None)
        stocks = pd.DataFrame(data=None)
        table_list=self.DB.DB_LOAD_TABLE_LIST("stocks_thema_list")
        table_list=[x for x in table_list if sector in x]
        if len(table_list)==1:
            sector_sel=table_list[0]
        else:
            print(table_list)
            sector_sel=table_list[0]
        sector_list = self.DB.DB_LOAD_Table("stocks_thema_list",sector_sel)
        #get price_sector
        count=0
        for num, code in enumerate(sector_list.index):
            print(num, code)
            try:
                price_df = fdr.DataReader(code.replace("a",""), start, end)
                price = stock.get_market_cap_by_date(start.replace("-", ""), end.replace("-", ""),
                                                     code.replace("a", ""))
                price_df[code] = price_df['Close']
                stocks = price[['시가총액']].copy()
                stocks[code] = stocks['시가총액']

                if num == 0:
                    total_price = price_df[code]
                    total_ratio = stocks[code]
                else:
                    total_price = pd.concat([total_price, price_df[code]], axis=1)
                    total_ratio = pd.concat([total_ratio, stocks[code]], axis=1)
            except:
                print(num, code)
                continue

        total_price = total_price.dropna(axis=1)
        total_ratio = total_ratio.dropna(axis=1)
        for day in total_price.index:
            total_ratio.loc[day] = total_ratio.loc[day]/total_ratio.loc[day].sum()
        #total_stock = total_stock.dropna(axis=1)
        total_index = pd.DataFrame(data=None, index=total_price.index,columns=['sector_index'])
        for day in total_price.index:
            temp=total_price.loc[day]*total_ratio.loc[day]
            total_index['sector_index'].loc[day]=temp.sum()
        return total_index


if __name__ == "__main__":
    #path = r'D:\OneDrive - Office 365\ValueTool\차단해제및재무분기데이터 수집\20_4Q_21_1Q\value tool 20210319.xlsb'
    test = Crolling_ThemaList_Infostock()
    sector='자율주행'
    start='2018-01-01'
    end = '2019-01-01'
    #test.Get_Thema_Number_Name()
    total=test.Make_Sector_index(sector,start,end)
    print(total.head())
    total['sector_index'].plot()

