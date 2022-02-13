# -*- coding: utf-8 -*-
"""
Created on Thu Mar 26 15:33:27 2020

@author: PARK BUMJIN
"""
import numpy as np
import matplotlib.pyplot as plt
from Finance import finance_data
import mpl_finance
import matplotlib.ticker as ticker
from matplotlib import font_manager, rc
plt.rcParams["axes.unicode_minus"]=False
path="c:\Windows\Fonts\H2GTRM.TTF"
font_name = font_manager.FontProperties(fname=path).get_name()
rc("font", family=font_name)

class Visualization():
    def __init__(self):
        self.pr = finance_data.Price_data()

    def make_candle_chart(self, code, stick_num):
        price_data = self.pr.make_jongmok_price_data(code, stick_num)
        fig = plt.figure(figsize=(12, 8))
        ax = fig.add_subplot(111)
        if (code == 'KOSPI') or (code == 'KOSDAQ'): final_price = code
        else : final_price = 'A' + code
        day_list = range(len(price_data))
        name_list = []
        for day in price_data.index:
            name_list.append(day.strftime('%d'))

        ax.xaxis.set_major_locator(ticker.FixedLocator(day_list))
        ax.xaxis.set_major_formatter(ticker.FixedFormatter(name_list))

        mpl_finance.candlestick2_ohlc(ax, price_data['시가'], price_data['고가'], price_data['저가'], price_data[final_price], width=0.5, colorup='r',
                                      colordown='b')
        plt.show()
    def make_result_visualize(self, test, tag):
        test = test.set_index('년월')
        test['수익률'] = np.array(list(map(lambda x : float(x.replace("%","")), test['수익률'])))
        test['승률'] = np.array(list(map(lambda x : float(x.replace("%","")), test['승률'])))
        test['수익종목평균수익률'] = np.array(list(map(lambda x : float(x.replace("%","")), test['수익종목평균수익률'])))
        test['손실종목평균손실률'] = np.array(list(map(lambda x : float(x.replace("%","")), test['손실종목평균손실률'])))
        #수익률 막대챠트
        plt.figure(figsize=(16, 9))
        plt.subplot(2, 2, 1)
        test['수익률'].plot(color='r',label=tag+'_수익률', kind='bar', width=0.8)
        plt.title(tag+"_월별 수익률")
        plt.ylabel('수익률(%)')
        plt.xlabel('월별')
        #수익률 히스토그램
        plt.subplot(2, 2, 2)
        test['수익률'].plot(color='b',label=tag+'_수익 히스토그램',kind='hist',width=1.5)
        plt.title(tag+"_손익률 분포도")
        plt.ylabel('분포수(개)')
        plt.xlabel('구간(%)')
        #pie chart
        plt.subplot(2, 2, 3)
        label=['수익','손실']
        xs = [test['수익종목'][0],test['손실종목'][0]]
        patches, texts, autotexts = plt.pie(
            labels=label, ## label
            labeldistance=1.0,## label이 파이로부터 얼마나 떨어지는가, 1일경우 딱 붙어있음.
            x = xs, ## 값
            explode=(0.0, 0.0), ##pie가 튀어나오는지 정해줌
            startangle=90,## 어디에서 시작할지, 정해줌
            shadow=False, ##그림자
            counterclock=False, ## 시계방향으로 가는지, 시계 반대 방향으로 가는지 정해줌
            autopct='%1.1f%%', ## pi 위에 표시될 글자 형태, 또한 알아서 %로 변환해서 알려줌
            pctdistance=0.7, ## pct가 radius 기준으로 어디쯤에 위치할지 정함
            colors=['red', 'blue'],
        )
        ## add circle
        ## 도넛처럼 만들기 위해서 아래처럼
        centre_circle = plt.Circle((0,0),0.50,color='white')
        plt.gca().add_artist(centre_circle)
        #######
        ## label만 변경해주기
        for t in texts:
            t.set_color("black")
            t.set_fontsize(25)
        ## pie 위의 텍스트를 다른 색으로 변경해주기
        for t in autotexts:
            t.set_color("white")
            t.set_fontsize(25)
        plt.tight_layout()
        #테이블 삽입 예제
        plt.subplot(2, 2, 4)
        values = [[test.columns[-1],format(test[test.columns[-1]][0],"3.2f")],[test.columns[-2],format(test[test.columns[-2]][0],"3.2f")],[test.columns[-3],str(format(test[test.columns[-3]][0],"3.2f"))+'%'],[test.columns[-4],format(test[test.columns[-4]][0],"10d")],[test.columns[-5],str(format(test[test.columns[-5]][0],"3.2f"))+'%'], [test.columns[-6],str(format(test[test.columns[-6]][0],"3.2f"))+'%']]
        table = plt.table(cellText=values, colWidths=[0.4]*3,loc = 'center')
        plt.show()
    
