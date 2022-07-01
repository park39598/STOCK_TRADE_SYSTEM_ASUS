import requests
from PyQt5.QtCore import pyqtSignal, QObject
from bs4 import BeautifulSoup
import os
import FinanceDataReader as fdr

from pykrx import stock
import pandas as pd
import DataBase.MySQL_control
import re
from datetime import datetime, timedelta

thread_num = 4
import tqdm
import datetime
from pathlib import Path
import re

#thema_url='http://m.infostock.co.kr/sector/sector_detail.asp?theme=2%uCC28%uC804%uC9C0&mode=w&code='

class Crolling_ThemaList_Infostock(QObject):
    Msg_trigger = pyqtSignal(str)
    UpdateState = pyqtSignal(int)
    def __init__(self, logging=False):
        super().__init__()
        if logging == False: pass
        else : self.logging = logging
        self.main_url='http://m.infostock.co.kr/sector/sector.asp?mode=w'
        self.thema_url='http://m.infostock.co.kr/sector/sector_detail.asp?theme=2%uCC28%uC804%uC9C0&mode=w&code='
        self.DB = DataBase.MySQL_control.DB_control()
        self.Updatemin_val = 1
        self.Updatemax_val = 262
        self.SectorMemNum = 5
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

    # 인덱스 만드는 함수
    def Make_Sector_index(self, sector, start, end):
        total_price = pd.DataFrame(data=None)
        total_ratio = pd.DataFrame(data=None)
        stocks = pd.DataFrame(data=None)
        '''
        table_list=self.DB.DB_LOAD_TABLE_LIST("stocks_thema_list")
        table_list=[x for x in table_list if sector in x]
        if len(table_list)==1:
            sector_sel=table_list[0]
        else:
            print(table_list)
            sector_sel=min(table_list)
        '''
        sector_list = self.DB.DB_LOAD_Table("stocks_thema_list", sector)
        #get price_sector
        #count=0
        #섹터 구성종목의 평균profit(동일가중)으로 수익률 계산
        for num, code in enumerate(sector_list.index):
            # 1. 섹터 별 기간 별 종목들의 평균 수익률 구하자
            try:
                price_df = fdr.DataReader(code.replace("a", ""), start, end)
                if len(price_df) == 0:
                    price_df = fdr.DataReader(code.replace("a", ""))
                    price_df = price_df[start:end]

                price_df[code] = price_df['Close'].pct_change()
                price_df = price_df.dropna(axis=0)
                if num == 0:
                    total_price = price_df[[code]]
                else:
                    total_price = pd.concat([total_price, price_df[code]], axis=1)
            except:
                # print(num, code)
                continue
        #total_price = total_price.dropna(axis=1)
        #total_price[sector] = 0
        temp_list=[]
        for day in total_price.index:
            temp_list.append(total_price.loc[day].mean())
        total_price["Profit_AVG"] = temp_list
        if(len(total_price) <= self.SectorMemNum) :
            self.logging.logger.info("{} It seems that sector stocks can't exceed 5".format(sector))
        else :
            self.DB.DB_SAVE("stocks_thema_index", sector, total_price)
        return total_price["Profit_AVG"]
        '''
                for num, code in enumerate(sector_list.index):
            # print(num, code)
            try:
                price_df = fdr.DataReader(code.replace("a", ""), start, end)
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
                # print(num, code)
                continue

        total_price = total_price.dropna(axis=1)
        total_ratio = total_ratio.dropna(axis=1)
        for day in total_price.index:
            total_ratio.loc[day] = total_ratio.loc[day] / total_ratio.loc[day].sum()
        # total_stock = total_stock.dropna(axis=1)
        total_index = pd.DataFrame(data=None, index=total_price.index, columns=['sector_index'])
        for day in total_price.index:
            temp=total_price.loc[day]*total_ratio.loc[day]
            total_index['sector_index'].loc[day]=temp.sum()
        return total_index
        '''
    def Make_Thema_Profit_List(self, start, end, update='replace'):
        table_list = self.DB.DB_LOAD_TABLE_LIST("stocks_thema_list")
        #self.Updatemin_val = 0
        #self.Updatemax_val = len(table_list)-1
        for i, sector in enumerate(tqdm.tqdm(table_list)):
            sector_profit_AVG = self.Make_Sector_index(sector, start, end)
            sector_profit_AVG.name = str(sector)
            if i == 0 : total_profit_AVG_df =  sector_profit_AVG.copy()
            else : total_profit_AVG_df = pd.concat([total_profit_AVG_df, sector_profit_AVG], axis=1)
            self.UpdateState.emit(i)
        self.DB.DB_SAVE("stocks_thema_index", 'total_avg', total_profit_AVG_df)
        self.Msg_trigger.emit("DB_ThemaUpdate 완료")
        return total_profit_AVG_df

    def Make_Thema_Period_Profit(self):
        total_profit_AVG_df=self.DB.DB_LOAD_Table("stocks_thema_index",'total_AVG')
        # 1주, 2주, 3주, 4주, 5주전
        now = datetime.datetime.today()
        if datetime.date.weekday(now) == 5:  # if it's Saturday
            now = now - datetime.timedelta(days=1)  # then make it Friday
        elif datetime.date.weekday(now) == 6:  # if it's Sunday
            now = now - datetime.timedelta(days=2)

        if total_profit_AVG_df.index[-1] != now:
            self.Msg_trigger.emit("Thema별 최신가격 정보 UPDATE 필요")

        total_thema_period_profit_df = pd.DataFrame(data=None, columns=['0주전','1주전','2주전','3주전','4주전','5일','10일','15일','20일','25일'], index=total_profit_AVG_df.columns)
        term_e = 0
        term_s = 5
        for x in range(1,6):
            end_day = now - datetime.timedelta(weeks=x-1)
            start_day = now - datetime.timedelta(weeks=(x))- datetime.timedelta(days=(1))
            temp = total_profit_AVG_df.loc[start_day:end_day]
            col = str(x-1) + "주전"
            total_thema_period_profit_df[col] = temp.sum(axis=0)*100

            end_day = now - datetime.timedelta(weeks=0)
            start_day = now - datetime.timedelta(days=x*5)- datetime.timedelta(days=(1))
            temp = total_profit_AVG_df.loc[start_day:end_day]
            col = str(x*5) + "일"
            total_thema_period_profit_df[col] = temp.sum(axis=0)*100

        return total_thema_period_profit_df

    def Make_Visualize_Thema_Period_Profit(self, period, update=True):
        #period=[1주전, 2주전, 3주전, 4주전, 5주전, 5일, 10일, 15일, 20일, 25일]
        df = self.Make_Thema_Period_Profit()
        df = df.sort_values(by=period, ascending=False)
        #df.iloc[:10].plot()
        return df



if __name__ == "__main__":
    #path = r'D:\OneDrive - Office 365\ValueTool\차단해제및재무분기데이터 수집\20_4Q_21_1Q\value tool 20210319.xlsb'
    test = Crolling_ThemaList_Infostock()
    sector='정치/인맥(조국)'
    start='2021-05-28'
    end = datetime.datetime.now()
    sector_profit_AVG = test.Make_Sector_index(sector, start, end)
    #test.Get_Thema_Number_Name()

    #tt = test.Make_Thema_Profit_List()
    print(tt.head())
