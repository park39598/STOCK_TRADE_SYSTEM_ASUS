# -*- coding: utf-8 -*-
"""
Created on Sat Jun 20 12:56:50 2020

@author: parkbumjin
"""
import matplotlib.pyplot as plt
from matplotlib import font_manager, rc
from DataBase import SQLITE_control

plt.rcParams["axes.unicode_minus"] = False
plt.rcParams['figure.constrained_layout.use'] = True
path = "c:\Windows\Fonts\H2GTRM.TTF"
font_name = font_manager.FontProperties(fname=path).get_name()
rc("font", family=font_name)

class ASSET_CORR_TEST:
    def __init__(self):
        self.DB_asset = 'f:\\OneDrive - Office 365\\STOCK_DB\\STOCK_DB.db'
        self.table_asset_return = 'portfolio_returns'
        self.table_asset_strategy = 'portfolio_strategy'
    
    def calc_assets_corr(self, asset_list, start, end, strategy = None):
        if strategy == None: asset_len = len(asset_list)
        else: 
            asset_strategy = SQLITE_control.DB_LOAD_Table(self.table_asset_strategy, self.DB_asset)
            asset_strategy = asset_strategy.loc[strategy].dropna().drop("Total Portfolio")
            if asset_strategy.sum() != 1: pass
            else: 
                asset_list = list(asset_strategy.index)
                asset_len = len(asset_list)  
            
        asset_df = SQLITE_control.DB_LOAD_Table(self.table_asset_return, self.DB_asset)
        asset_df = asset_df[asset_list].loc[start:end]
        corr_asset_df = asset_df.astype('float').corr()
        self.make_corr_visualize(asset_len, asset_df, corr_asset_df)
        
    def make_corr_visualize(self, asset_num, data_df, corr_df):
        if asset_num < 3 :
            subplot_num_H = 1
            subplot_num_V= 1
        elif asset_num < 4 :
            subplot_num_H = 2
            subplot_num_V = 2
        elif asset_num < 5 :
            subplot_num_H = 3
            subplot_num_V = 2
        elif asset_num < 6 :
            subplot_num_H = 4
            subplot_num_V = 3
        else :
            subplot_num_H = 4
            subplot_num_V = 4
        plt.figure(figsize=(20,20))

        scatter_sel = 0
        for j in range(0,asset_num-1):
            for i in range(j+1, asset_num):
                scatter_sel = scatter_sel + 1
                plt.subplot(subplot_num_H,subplot_num_V, scatter_sel)
                plt.scatter(data_df[data_df.columns[j]],data_df[data_df.columns[i]], label='corr='+format(corr_df[data_df.columns[j]][i], '3.2f')+'%')
                plt.xlabel(data_df.columns[j], labelpad=10)
                plt.ylabel(data_df.columns[i], labelpad=1)
                plt.legend()
        plt.tight_layout()
        plt.subplots_adjust(left=None, bottom=0.1, right=None, top=None, wspace=None, hspace=0.4)


    def korea_ETF_test(self, test_list, start, end):
        code_list = SQLITE_control.DB_LOAD_Table("JONGMOK_CODE_NAME", self.DB_asset)
        price_data = SQLITE_control.DB_LOAD_Price_Data()
        jongmok_name_list = []
        ETF_data = price_data[test_list].loc[start:end].dropna()
        ETF_data = ETF_data.astype('float').pct_change()
        for code in test_list:
            jongmok_name_list.append(code_list.loc[code][1])
        ETF_data.columns = jongmok_name_list
        corr_ETF_data = ETF_data.astype('float').corr()
        self.make_corr_visualize(len(test_list), ETF_data, corr_ETF_data)
            
        
        
if __name__ == "__main__":
    test = ASSET_CORR_TEST()
    test_list = ['A227570','A267440','A261240','A310080','A220130','A150460','A329750','A261220']         #타이거우량가치 VS 달러, 원유, 중국, 미국 장단기채
    test_list2 = ['A322150', 'A267440', 'A261240', 'A310080', 'A220130', 'A150460', 'A329750', 'A261220'] #KINDEX 스마트하이베타 VS 달러, 원유, 중국, 미국 장단기채
    test_list3 = ['A337140', 'A310080', 'A174360', 'A168580', 'A219900', 'A169950', 'A283580', 'A220130','A150460'] #코스피대형 VS KBSTAR 중국MSCI China선물(H),KBSTAR 중국본토대형주CSI100,KINDEX 중국본토CSI300,KINDEX 중국본토CSI300레버리지(합성),KODEX 중국본토 A50,중국본토CSI300,SMART 중국본토 중소형 CSI500(합성 H),TIGER 중국소비테마
    test_list4 = ['A277650', 'A310080', 'A174360', 'A168580', 'A219900', 'A169950', 'A283580', 'A220130',
                  'A150460']  # 코스피중형 VS KBSTAR 중국MSCI China선물(H),KBSTAR 중국본토대형주CSI100,KINDEX 중국본토CSI300,KINDEX 중국본토CSI300레버리지(합성),KODEX 중국본토 A50,중국본토CSI300,SMART 중국본토 중소형 CSI500(합성 H),TIGER 중국소비테마
    test_list5 = ['A233740', 'A310080', 'A174360', 'A168580', 'A219900', 'A169950', 'A283580', 'A220130',
                  'A150460']  # 코스닥150 VS KBSTAR 중국MSCI China선물(H),KBSTAR 중국본토대형주CSI100,KINDEX 중국본토CSI300,KINDEX 중국본토CSI300레버리지(합성),KODEX 중국본토 A50,중국본토CSI300,SMART 중국본토 중소형 CSI500(합성 H),TIGER 중국소비테마
    test_list6 = ['A337140', 'A342140', 'A181480', 'A316300', 'A352540', 'A352560', 'A182480']# 코스피대형 VS 리츠
    test_list7 = ['A233740', 'A342140', 'A181480', 'A316300', 'A352540', 'A352560', 'A182480']  # 코스피대형 VS 리츠
    test_list8 = ['A337140', 'A144600', 'A160580', 'A334690', 'A138920', 'A271060', 'A139310']  # 코스피대형 VS 원자재(KODEX 은선물(H) TIGER 구리실물 KBSTAR 팔라듐선물(H) TIGER 금속선물(H) KODEX 3대농산물선물 KODEX 콩선물
    test_list9 = ['A233740', 'A144600', 'A160580', 'A334690', 'A138920', 'A271060',
                  'A139310']  # 코스닥150 VS 원자재(KODEX 은선물(H) TIGER 구리실물 KBSTAR 팔라듐선물(H) TIGER 금속선물(H) KODEX 3대농산물선물 KODEX 콩선물

    test.korea_ETF_test(test_list6,'2010','2020')
    test.korea_ETF_test(test_list9, '2010', '2020')
    test.korea_ETF_test(test_list8, '2010', '2020')
    plt.show()
