# coding: utf-8
import os
from Finance import finance_data
from Finance.finance_data import *

from Finance import finance_data
from Finance.finance_data import *

import DataBase.SQLITE_control
import tqdm
import FinanceDataReader as fdr
from pandas.tseries.offsets import BDay
import os,sys
ROOT_DIR = os.path.dirname(os.path.abspath(os.path.dirname(__file__)))
#from Kiwoom.config.log_class import Logging
import datetime
class Quant_Strategy:
    def __init__(self):
        self.fs = finance_data.Finance_data()
        self.SQL = DataBase.MySQL_control.DB_control()
        self.MIN_PER = 0.1
        self.MAX_PER = 30
        self.MIN_PBR = 0.0
        self.MAX_PBR = 3.0
        self.MIN_ROE = 0
        self.MAX_ROE = 0.5
        self.MIN_ROA = 0
        self.MAX_ROA = 0.9
        self.pr = Price_data()
        self.protfolio_path = 'f:\\OneDrive - Office 365\\STOCK_DB\\STOCK_DB.db'
        self.portfolio_stratey_table = "portfolio_strategy"
        self.portfolio_price_table = "portfolio_price"
        self.test_log_on = False
        self.test_log_on = False
        self.AV_algo_on = False

        # 현재 주가데이터 수집 (현재날짜)
        # 현재 기준 가장가까운 영업일 과거
        lastBusDay = datetime.datetime.today()
        if datetime.date.weekday(lastBusDay) == 5:  # if it's Saturday
            lastBusDay = lastBusDay - datetime.timedelta(days=1)  # then make it Friday
        elif datetime.date.weekday(lastBusDay) == 6:  # if it's Sunday
            lastBusDay = lastBusDay - datetime.timedelta(days=2)

        self.current_day = "{}-{}-{}".format(lastBusDay.year, lastBusDay.month, lastBusDay.day)


    def get_finance_data(self, fs_path):
        data_path = fs_path
        raw_data = pd.read_excel(data_path)
        big_col = list(raw_data.columns)
        small_col = list(raw_data.iloc[0])

        new_big_col = big_col.copy()

        for num, col in enumerate(big_col):
            if 'Unnamed' in col:
                new_big_col.insert(num, new_big_col[num - 1])
                del new_big_col[len(big_col):]
                # new_big_col.append(new_big_col[num - 1])
            else:
                new_big_col.insert(num, big_col[num])

        raw_data.columns = [new_big_col, small_col]
        clean_df = raw_data.loc[raw_data.index.dropna()]
        return clean_df

    def low_per(self, invest_df, index_date, num):
        invest_df[(index_date, 'PER')] = pd.to_numeric(invest_df[(index_date, 'PER')], errors='coerce')
        per_sorted = invest_df.sort_values(by=(index_date, 'PER'))
        return per_sorted[index_date][:num]

    def high_roa(self, fr_df, index_date, num):
        fr_df[(index_date, 'ROA')] = fr_df[(index_date, 'ROA')].apply(self.check_IFRS)
        fr_df[(index_date, 'ROA')] = pd.to_numeric(fr_df[(index_date, 'ROA')])
        sorted_roa = fr_df.sort_values(by=(index_date, 'ROA'), ascending=False)
        return sorted_roa[index_date][:num]

    def RIM_ON(self, input_df, apply_rim_L=2):
        if apply_rim_L == 0:
            rim_l = 'RIM'
        elif apply_rim_L == 1:
            rim_l = 'RIM_L1'
        else:
            rim_l = 'RIM_L2'
        #value_sorted = input_df[(input_df[rim_l].astype('float')) > (input_df['시가총액(억)'].astype('float')*100000000/input_df['주식수'].astype('float'))]
        value_sorted = input_df[input_df[rim_l].astype('float') > input_df['현재가'].astype('float')]
        return value_sorted

    def Finance_company_del(self, input_df):
        company_code = self.SQL.DB_LOAD_Table('system_parameter', self.fs.FINANCE_COMPANY_TABLE)
        for code in company_code['종목코드']:
            try:
                input_df = input_df.drop(code)
            except:
                pass
        input_df = input_df.loc[input_df.index.str.contains('A9') == False]
        # 중국기업 제외...'A9'로 시작

        return input_df

    def update_invest_now(self):
        pass
    def get_value_rank_now(self, total_df, value_type=None, quality_type=None, num=20, rim_on=True, fs_comp_del_on=True, BJ_Filter=True, apply_rim_L=2):
        #total_df = self.SQL.DB_LOAD_Table(self.fs.EXCEL_NOW_FS_TABLE, self.fs.DB_FS_EXCEL_PATH)
        #total_df = self.fs.get_Finance_now_excel()
        #code_list = SQLITE_control.DB_LOAD_Table(self.fs.TOTAL_JONGMOK_NAME_TABLE, self.fs.DB_TOTAL_JONGMOK_PATH)

        #현재가를 크롤링하여서 업데이트 시킴
        #total_df = total_df.set_index('code')
        #code_list = self.pr.code_name_setup(total_df.index)
        #for num, code in enumerate(code_list):
        #    temp_data = self.pr.make_jongmok_price_data(code, 1)
        #    total_df.loc['A'+ code]['현재가'] = temp_data['A'+code][0]
        #total_df['EV'] = total_df['시가총액(억)'].astype('float') - total_df['순현금'].astype('float')
        total_df['부채비율'] = total_df['부채비율'].replace("-",0).astype('float')*100
        total_df['유동비율'] = total_df['유동비율'].replace("-", 0).astype('float') * 100
        print_list = ['종목']
        if BJ_Filter:
            total_df = total_df[(total_df['부채비율'] < 100) & (total_df['유동비율'] > 200)]
        if rim_on == True:
            total_df = self.RIM_ON(total_df, apply_rim_L)
            # 금융회사/지주사/중국회사 제외
        if fs_comp_del_on == True:
            total_df = self.Finance_company_del(total_df)
        if value_type == 'PER':
                total_df = total_df[(total_df['PER조정'].replace("-",0).astype('float') > self.MIN_PER) & (total_df['PER조정'].replace("-",0).astype('float') < self.MAX_PER)].sort_values(
                    by=value_type)
                value_sorted = total_df.sort_values(by=value_type)
                value_sorted[value_type + '순위'] = value_sorted[value_type].rank()
                print_list.append(value_type)
                print_list.append(value_type + '순위')
        elif value_type == 'PBR':
                total_df = total_df[(total_df['PBR'].replace("-",0).astype('float') > self.MIN_PBR) & (total_df['PBR'].replace("-",0).astype('float') < self.MAX_PBR)].sort_values(
                    by=value_type)
                value_sorted = total_df.sort_values(by=value_type)
                value_sorted[value_type + '순위'] = value_sorted[value_type].rank()
                print_list.append(value_type)
                print_list.append(value_type + '순위')

        elif value_type == '자본수익률':
                value_sorted = total_df.sort_values(by=value_type, ascending=False)
                value_sorted[value_type + '순위'] = value_sorted[value_type].rank(ascending=False)
                print_list.append(value_type)
                print_list.append(value_type + '순위')
        else:
                value_sorted = total_df        

        if quality_type == 'ROE':
                value_sorted = value_sorted[
                    (value_sorted['ROE'].replace("-",0).astype('float') > self.MIN_ROE) & (value_sorted['ROE'].replace("-",0).astype('float') < self.MAX_ROE)].sort_values(
                    by=quality_type)
                quality_sorted = value_sorted.sort_values(by=quality_type, ascending=False)
                quality_sorted[quality_type + '순위'] = quality_sorted[quality_type].rank(ascending=False)
                print_list.append(quality_type)
                print_list.append(quality_type + '순위')    
        elif quality_type == 'ROA':
                value_sorted = value_sorted[
                    (value_sorted['ROA'].replace("-",0).astype('float') > self.MIN_ROA) & (value_sorted['ROA'].replace("-",0).astype('float') < self.MAX_ROA)].sort_values(
                    by=quality_type)
                quality_sorted = value_sorted.sort_values(by=quality_type, ascending=False)
                quality_sorted[quality_type + '순위'] = quality_sorted[quality_type].rank(ascending=False)
                print_list.append(quality_type)
                print_list.append(quality_type + '순위')
        elif quality_type == '이익수익률':
                quality_sorted = value_sorted.sort_values(by=quality_type, ascending=False)
                quality_sorted[quality_type + '순위'] = quality_sorted[quality_type].rank(ascending=False)
                print_list.append(quality_type)
                print_list.append(quality_type + '순위')   
   
        elif quality_type == 'GP/A':
                value_sorted[quality_type] = value_sorted[quality_type].replace("-", 0).astype('float')
                quality_sorted = value_sorted.sort_values(by=quality_type, ascending=False)
                quality_sorted[quality_type + '순위'] = quality_sorted[quality_type].rank(ascending=False)
                print_list.append(quality_type)
                print_list.append(quality_type + '순위')

        else:
                quality_sorted = value_sorted   

        try:
                quality_sorted['합산'] = quality_sorted[value_type + '순위'] + quality_sorted[quality_type + '순위']
                quality_sorted = quality_sorted.sort_values(by='합산')
                quality_sorted['합산순위'] = quality_sorted['합산'].rank()
                print_list.append('합산')
                print_list.append('합산순위')
                print_list.append('현재가')
        except:
                pass              

        return quality_sorted[print_list][:num]

    def super_value_strategy_by_kang(self, invest_df, price_df, start_date, end_date, index_date, num=30, value1 = 'PER', value2 = 'PBR', value3 = 'PCR', value4 = 'PSR'):
        total_df = pd.DataFrame(data=invest_df[index_date], index=invest_df.index, columns=None)
        total_df['현재가'] = price_df[start_date:end_date].iloc[0].astype('float')
        total_df['시가총액'] = total_df['주식수'].astype('float') * total_df['현재가']
        total_df['EV'] = total_df['시가총액'].astype('float') - total_df['순현금'].astype('float')
        print_list = []
        # 분기데이터에는 PER정보가 없고 지배지분순이익 정보가 2010년 밑으로는 없음... 당기순이익 사용하자

        if int(index_date.split('/')[0]) < 2011:
            total_df['PER'] = (total_df['주식수'].astype('float') / total_df['당기순이익'].astype('float')) * total_df['현재가']
        else:
            total_df['PER'] = (total_df['주식수'].astype('float') / total_df['지배지분순이익'].astype('float')) * total_df['현재가']

        total_df['PCR'] = total_df['시가총액'] / (total_df['영업활동으로인한현금흐름'])
        total_df['PSR'] = total_df['시가총액'] / total_df['매출액']
        total_df = total_df.replace([np.inf, -np.inf], np.nan)
        # 1. Value1 RANKING
        total_df = total_df[total_df[value1] > 0]
        total_df[value1+'_'+'reverse'] = 1 / total_df[value1]
        #total_df = total_df[(total_df[value1] > self.MIN_PER) & (total_df[value1] < self.MAX_PER)]
        val1_sorted = total_df.sort_values(by=value1+'_'+'reverse', ascending=False)
        val1_sorted[value1 + '순위'] = val1_sorted[value1].rank()
        print_list.append(value1)
        print_list.append(value1 + '순위')
        # 2. PBR RANK
        val1_sorted['PBR'] = (val1_sorted['주식수'].astype('float') / val1_sorted['지배주주지분'].astype('float')) * \
                          val1_sorted['현재가'].astype('float')
        val1_sorted = val1_sorted[val1_sorted[value2] > 0]
        val1_sorted[value2+'_'+'reverse'] = 1 / val1_sorted[value2]
        val2_sorted = val1_sorted.sort_values(by=value2+'_'+'reverse', ascending=False)
        val2_sorted[value2 + '순위'] = val2_sorted[value2].rank()
        
        print_list.append(value2)
        print_list.append(value2 + '순위')
        
        # 3. PSR RANK
        val2_sorted = val2_sorted[val2_sorted[value3] > 0]
        val2_sorted[value3+'_'+'reverse'] = 1 / val2_sorted[value3]
        val3_sorted = val2_sorted.sort_values(by=value3+'_'+'reverse', ascending=False)
        val3_sorted[value3 + '순위'] = val3_sorted[value3].rank()
        print_list.append(value3)
        print_list.append(value3 + '순위')
        
        #4. PCR RANK
        val3_sorted = val3_sorted[val3_sorted[value4] > 0]
        val3_sorted[value4+'_'+'reverse'] = 1 / val3_sorted[value4]
        val4_sorted = val3_sorted.sort_values(by=value4+'_'+'reverse', ascending=False)
        val4_sorted[value4 + '순위'] = val4_sorted[value4].rank()
        print_list.append(value4)
        print_list.append(value4 + '순위')
        try:
            val4_sorted['합산'] = val4_sorted[value1 + '순위'] + val4_sorted[value2 + '순위'] + val4_sorted[value3 + '순위'] + val4_sorted[value4 + '순위']
            val4_sorted = val4_sorted.sort_values(by='합산')
            val4_sorted['합산순위'] = val4_sorted['합산'].rank()
            print_list.append('합산')
            print_list.append('합산순위')
            val4_sorted.to_excel("f:\\test.xlsx")
        except:
            pass
        #print(val4_sorted[print_list][:num].head())
        return val4_sorted[print_list][:num]

    def ultra_value_strategy_by_kang(self, invest_df, value_factor, stock_num=20):
        # value_factor 형태
        # factor1=[value, "오름차순"or"내림차순", Min, Max]
        # value_factor = [factor1, factor2,.....]
        index_date=invest_df.columns.levels[0][0]
        total_df = pd.DataFrame(data=invest_df[index_date], index=invest_df.index, columns=None)
        total_df['시가총액'] = total_df['주식수'].astype('float') * total_df['현재가']
        total_df['EV'] = total_df['시가총액'].astype('float') - total_df['순현금'].astype('float')
        total_df['PBR'] = (total_df['주식수'].astype('float') / total_df['지배주주지분'].astype('float')) * \
                             total_df['현재가'].astype('float')
        if int(index_date.split('/')[0]) >= 2020:
            total_df['CAPEX'] = 0-(total_df['유형자산취득'].astype('float')+total_df['무형자산취득'].astype('float'))
            total_df['FCF'] = (total_df['영업활동으로인한현금흐름'].astype('float') + total_df['CAPEX'])
            total_df['PFCR'] = total_df['시가총액'].astype('float') / total_df['FCF']
        else:
            total_df['PFCR'] = total_df['시가총액'].astype('float') / total_df['FCF']
        # GP/A
        total_df['GP_A'] = total_df['매출총이익'].astype('float')/total_df['자산총계'].astype('float')
        print_list = []
        # 분기데이터에는 PER정보가 없고 지배지분순이익 정보가 2010년 밑으로는 없음... 당기순이익 사용하자

        if int(index_date.split('/')[0]) < 2011:
            total_df['PER'] = (total_df['주식수'].astype('float') / total_df['당기순이익'].astype('float')) * total_df['현재가']
        else:
            total_df['PER'] = (total_df['주식수'].astype('float') / total_df['지배지분순이익'].astype('float')) * total_df['현재가']

        total_df['PCR'] = total_df['시가총액'] / (total_df['영업활동으로인한현금흐름'])
        total_df['PSR'] = total_df['시가총액'] / total_df['매출액']
        total_df = total_df.replace([np.inf, -np.inf], np.nan)
        total_df['합산'] = 0
        #total_df = self.get_fscore2(total_df)
        for num, factor in enumerate(value_factor):
            if (factor[2] == None) and (factor[3] != None):
                total_df = total_df[(total_df[factor[0]] < factor[3])]
            elif (factor[2] != None) and (factor[3] == None):
                total_df = total_df[(total_df[factor[0]] > factor[2])]
            elif (factor[2] != None) and (factor[3] != None):
                total_df = total_df[(total_df[factor[0]] > factor[2])&(total_df[factor[0]] < factor[3])]
            else:
                pass
            if factor[1] == "오름차순":sort=True
            else:sort=False
            total_df[factor[0] + '_' + 'reverse'] = 1 / total_df[factor[0]]
            total_df = total_df.sort_values(by=factor[0] + '_' + 'reverse', ascending=sort)
            total_df[factor[0] + '순위'] = total_df[factor[0]].rank(ascending=sort)
            total_df['합산'] = total_df['합산'] + total_df[factor[0] + '순위']
            print_list.append(factor[0])
            print_list.append(factor[0] + '순위')
            total_df.to_excel(os.path.join(ROOT_DIR,'Backtest/BACKTEST_LOG/'+factor[0]+'.xlsx'))
        try:
            total_df = total_df.sort_values(by='합산')
            total_df['합산순위'] = total_df['합산'].rank(ascending=True)
            print_list.append('합산')
            print_list.append('합산순위')
            #total_df.to_excel("f:\\test.xlsx")
        except:
            pass
        print_list.append('현재가')
        return total_df[print_list][:stock_num]
    
    def get_value_rank_quarter(self, invest_df, price_df, start_date, end_date, index_date, value_type=None, quality_type=None,
                             num=20):
        total_df = pd.DataFrame(data=invest_df[index_date], index=invest_df.index, columns=None)            
        total_df['현재가'] = price_df[start_date:end_date].iloc[0].astype('float')
        #total_df['시가총액'] = total_df['주식수'].astype('float') * total_df['현재가']
        total_df['EV'] = total_df['시가총액'].astype('float') - total_df['순현금'].astype('float')
        print_list = []
        # 분기데이터에는 PER정보가 없고 지배지분순이익 정보가 2010년 밑으로는 없음... 당기순이익 사용하자
        if value_type == 'PER':
            if int(index_date.split('/')[0]) < 2011:
                total_df['PER'] = (total_df['주식수'].astype('float') / total_df['당기순이익'].astype('float')) * total_df['현재가']
            else:
                total_df['PER'] = (total_df['주식수'].astype('float') / total_df['지배지분순이익'].astype('float')) * total_df['현재가']
            total_df = total_df[(total_df['PER'] > self.MIN_PER) & (total_df['PER'] < self.MAX_PER)].sort_values(by=value_type)
            value_sorted = total_df.sort_values(by=value_type)
            value_sorted[value_type + '순위'] = value_sorted[value_type].rank()
            print_list.append(value_type)
            print_list.append(value_type + '순위')
        elif value_type == 'PBR':
            total_df['PBR'] = (total_df['주식수'].astype('float') / total_df['지배주주지분'].astype('float')) * \
                              total_df['현재가']
            total_df = total_df[(total_df['PBR'] > self.MIN_PBR) & (total_df['PBR'] < self.MAX_PBR)].sort_values(
                by=value_type)
            value_sorted = total_df.sort_values(by=value_type)
            value_sorted[value_type + '순위'] = value_sorted[value_type].rank()
            print_list.append(value_type)
            print_list.append(value_type + '순위')

        elif value_type == '자본수익률':
            total_df['자본수익률'] = total_df['영업이익'].replace("-", 0).astype('float') / (
                    total_df['유동자산'].replace("-", 0).astype('float') - total_df['유동부채'].replace("-", 0).astype(
                'float') + total_df['비유동자산'].replace("-", 0).astype('float') - total_df['감가상각비'].replace("-",
                                                                                                         0).astype(
                'float'))
            value_sorted = total_df.sort_values(by=value_type, ascending=False)
            value_sorted[value_type + '순위'] = value_sorted[value_type].rank(ascending=False)
            print_list.append(value_type)
            print_list.append(value_type + '순위')
        else:
            value_sorted = total_df

        if quality_type == 'ROE':
            value_sorted['ROE'] = value_sorted['ROE'].replace("-", 0).astype('float')
            value_sorted = value_sorted[
                (value_sorted['ROE'] > self.MIN_ROE) & (value_sorted['ROE'] < self.MAX_ROE)].sort_values(
                by=quality_type)
            quality_sorted = value_sorted.sort_values(by=quality_type, ascending=False)
            quality_sorted[quality_type + '순위'] = quality_sorted[quality_type].rank(ascending=False)
            print_list.append(quality_type)
            print_list.append(quality_type + '순위')
        elif quality_type == 'ROA':
            if int(index_date.split('/')[0]) > 2010:
                value_sorted['ROA'] = value_sorted['지배지분순이익'].astype('float') / value_sorted['자산총계'].replace("-",
                                                                                                          1).astype(
                'float')
            elif int(index_date.split('/')[0]) < 2008:
                value_sorted['ROA'] = value_sorted['당기순이익'].astype('float') / value_sorted['자산총계'].replace("-",
                                                                                                             1).astype(
                    'float')
            else:
                pass
            value_sorted = value_sorted[
                (value_sorted['ROA'].astype('float') > self.MIN_ROA) & (value_sorted['ROA'].astype('float') < self.MAX_ROA)].sort_values(
                by=quality_type)
            quality_sorted = value_sorted.sort_values(by=quality_type, ascending=False)
            quality_sorted[quality_type + '순위'] = quality_sorted[quality_type].rank(ascending=False)
            print_list.append(quality_type)
            print_list.append(quality_type + '순위')
        elif quality_type == '이익수익률':
            value_sorted['이익수익률'] = value_sorted['영업이익'].replace("-", 0).astype('float') / value_sorted[
                'EV'].replace("-", 0).astype('float')
            quality_sorted = value_sorted.sort_values(by=quality_type, ascending=False)
            quality_sorted[quality_type + '순위'] = quality_sorted[quality_type].rank(ascending=False)
            print_list.append(quality_type)
            print_list.append(quality_type + '순위')

        elif quality_type == 'GP/A':
            value_sorted['GP/A'] = value_sorted['매출총이익'].replace("-", 0).astype('float') / value_sorted['자산총계'].replace(
                "-", 1).astype('float')
            value_sorted['GP/A'] = value_sorted['GP/A'].replace("-", 0)
            quality_sorted = value_sorted.sort_values(by=quality_type, ascending=False)
            quality_sorted[quality_type + '순위'] = quality_sorted[quality_type].rank(ascending=False)
            print_list.append(quality_type)
            print_list.append(quality_type + '순위')

        else:
            quality_sorted = value_sorted

        try:
            quality_sorted['합산'] = quality_sorted[value_type + '순위'] + quality_sorted[quality_type + '순위']
            quality_sorted = quality_sorted.sort_values(by='합산')
            quality_sorted['합산순위'] = quality_sorted['합산'].rank()
            print_list.append('합산')
            print_list.append('합산순위')
        except:
            pass

        return quality_sorted[print_list][:num]

    def get_value_rank_year(self, invest_df, price_df, start_date, end_date, index_date, value_type=None,
                       quality_type=None, num=30):
        total_df = pd.DataFrame(data=invest_df[index_date], index=invest_df.index)
        total_df['EV'] = (total_df['시가총액'].astype('float') - total_df['순현금'].astype('float'))
        total_df['현재가'] = price_df[start_date:end_date].iloc[0].astype('float')
        if self.test_log_on: total_df.to_excel('F:\\test_log\\total_df_get_value_rank.xlsx')
        print_list = []
        if value_type == 'PER':
            total_df['PER'] = (total_df['주식수'].astype('float') / total_df['지배지분 순이익'].astype('float')) * \
                              total_df['현재가']
            total_df = total_df[(total_df['PER'] > self.MIN_PER) & (total_df['PER'] < self.MAX_PER)].sort_values(
                by=value_type)
            value_sorted = total_df.sort_values(by=value_type)
            value_sorted[value_type + '순위'] = value_sorted[value_type].rank()
            print_list.append(value_type)
            print_list.append(value_type + '순위')
        elif value_type == 'PBR':
            total_df['PBR'] = (total_df['주식수'].astype('float') / total_df['지배주주지분'].astype('float')) * \
                              total_df['현재가']
            total_df = total_df[(total_df['PBR'] > self.MIN_PBR) & (total_df['PBR'] < self.MAX_PBR)].sort_values(
                by=value_type)
            value_sorted = total_df.sort_values(by=value_type)
            value_sorted[value_type + '순위'] = value_sorted[value_type].rank()
            print_list.append(value_type)
            print_list.append(value_type + '순위')

        elif value_type == '자본수익률':
            total_df['자본수익률'] = total_df['영업이익'].replace("-", 0).astype('float') / (
                    total_df['유동자산'].replace("-", 0).astype('float') - total_df['유동부채'].replace("-", 0).astype(
                'float') + total_df['비유동자산'].replace("-", 0).astype('float') - total_df['감가상각비'].replace("-",
                                                                                                         0).astype(
                'float'))
            value_sorted = total_df.sort_values(by=value_type, ascending=False)
            value_sorted[value_type + '순위'] = value_sorted[value_type].rank(ascending=False)
            print_list.append(value_type)
            print_list.append(value_type + '순위')
        else:
            value_sorted = total_df

        if quality_type == 'ROE':
            value_sorted['ROE'] = value_sorted['ROE'].replace("-", 0).astype('float')
            value_sorted = value_sorted[
                (value_sorted['ROE'] > self.MIN_ROE) & (value_sorted['ROE'] < self.MAX_ROE)].sort_values(
                by=quality_type)
            quality_sorted = value_sorted.sort_values(by=quality_type, ascending=False)
            quality_sorted[quality_type + '순위'] = quality_sorted[quality_type].rank(ascending=False)
            print_list.append(quality_type)
            print_list.append(quality_type + '순위')
        elif quality_type == 'ROA':
            value_sorted['ROA'] = value_sorted['지배지분 순이익 '].astype('float') / value_sorted['자산총계'].replace("-",
                                                                                                          1).astype(
                'float')
            value_sorted = value_sorted[
                (value_sorted['ROA'] > self.MIN_ROA) & (value_sorted['ROA'] < self.MAX_ROA)].sort_values(
                by=quality_type)
            quality_sorted = value_sorted.sort_values(by=quality_type, ascending=False)
            quality_sorted[quality_type + '순위'] = quality_sorted[quality_type].rank(ascending=False)
            print_list.append(quality_type)
            print_list.append(quality_type + '순위')
        elif quality_type == '이익수익률':
            value_sorted['이익수익률'] = value_sorted['영업이익'].replace("-", 0).astype('float') / value_sorted[
                'EV'].replace("-", 0).astype('float')
            quality_sorted = value_sorted.sort_values(by=quality_type, ascending=False)
            quality_sorted[quality_type + '순위'] = quality_sorted[quality_type].rank(ascending=False)
            print_list.append(quality_type)
            print_list.append(quality_type + '순위')

        elif quality_type == 'GP/A':
            value_sorted['GP/A'] = value_sorted['매출총이익'].replace("-", 0).astype('float') / value_sorted['자산총계'].replace(
                "-", 1).astype('float')
            value_sorted['GP/A'] = value_sorted['GP/A'].replace("-", 0)
            quality_sorted = value_sorted.sort_values(by=quality_type, ascending=False)
            quality_sorted[quality_type + '순위'] = quality_sorted[quality_type].rank(ascending=False)
            print_list.append(quality_type)
            print_list.append(quality_type + '순위')

        else:
            quality_sorted = value_sorted

        try:
            quality_sorted['합산'] = quality_sorted[value_type + '순위'] + quality_sorted[quality_type + '순위']
            quality_sorted = quality_sorted.sort_values(by='합산')
            quality_sorted['합산순위'] = quality_sorted['합산'].rank()
            print_list.append('합산')
            print_list.append('합산순위')
        except:
            pass

        return quality_sorted[print_list][:num]

    def make_value_combo(self, value_list, invest_df, index_date, num):
        for i, value in enumerate(value_list):
            temp_df = self.get_value_rank(invest_df, value, index_date, None)
            if i == 0:
                value_combo_df = temp_df
                rank_combo = temp_df[value + '순위']
            else:
                value_combo_df = pd.merge(value_combo_df, temp_df, how='outer', left_index=True, right_index=True)
                rank_combo = rank_combo + temp_df[value + '순위']

        value_combo_df['종합순위'] = rank_combo.rank()
        value_combo_df = value_combo_df.sort_values(by='종합순위')

        return value_combo_df[:num]

    def get_fscore(self, fs_df, index_date, num, type = None):
        fscore_df = fs_df[index_date].copy()
        fscore_df['당기순이익점수'] = pd.to_numeric(fscore_df['당기순이익'], errors='coerce') > 0
        fscore_df['영업활동점수'] = pd.to_numeric(fscore_df['영업활동으로인한현금흐름'], errors='coerce') > 0
        fscore_df['더큰영업활동점수'] = pd.to_numeric(fscore_df['영업활동으로인한현금흐름'], errors='coerce') > pd.to_numeric(
            fscore_df['당기순이익'], errors='coerce')
        fscore_df['종합점수'] = fscore_df[['당기순이익점수', '영업활동점수', '더큰영업활동점수']].sum(axis=1)
        fscore_df = fscore_df[fscore_df['종합점수'] == 3]
        if type == '콤보':
            num = int(len(fscore_df))
        else:
            pass
        return fscore_df[:num]

    def get_fscore2(self, fs_df, type = None):
        fscore_df = fs_df.copy()
        fscore_df['당기순이익점수'] = pd.to_numeric(fscore_df['당기순이익'], errors='coerce') > 0
        fscore_df['영업활동점수'] = pd.to_numeric(fscore_df['영업활동으로인한현금흐름'], errors='coerce') > 0
        fscore_df['신규주식발행점수'] = pd.to_numeric(fscore_df['전년대비주식수변동'], errors='coerce') <= 0
        fscore_df['종합점수'] = fscore_df[['당기순이익점수', '영업활동점수', '신규주식발행점수']].sum(axis=1)
        fscore_df = fscore_df[fscore_df['종합점수'] == 3]
        return fscore_df

    def get_momentum_rank(self, price_df, index_date, data_range, num):
        momentum_df = pd.DataFrame(price_df.astype('float').pct_change(data_range).loc[index_date])
        momentum_df.columns = ['모멘텀']
        momentum_df['모멘텀순위'] = momentum_df['모멘텀'].rank(ascending=False)
        momentum_df = momentum_df.sort_values(by='모멘텀순위')
        return momentum_df[:num]

    def get_value_quality(self, invest_df, fs_df, index_date, num):
        value = self.make_value_combo(['PER', 'PBR', 'PSR', 'PCR'], invest_df, index_date, None)
        quality = self.get_fscore(fs_df, index_date, None)
        value_quality = pd.merge(value, quality, how='outer', left_index=True, right_index=True)
        value_quality_filtered = value_quality[value_quality['종합점수'] == 3]
        vq_df = value_quality_filtered.sort_values(by='종합순위')
        return vq_df[:num]

    def check_IFRS(self, x):
        if x == 'N/A(IFRS)':
            return np.NaN
        else:
            return x

    def get_near_52WeeksHighPrice_under(self, start_date, number):
        price_in_df = self.pr.DB_LOAD_Price_Data()
        price_in_df = price_in_df.drop(['KOSPI','KOSDAQ'], axis=1)
        code_list = self.SQL.DB_LOAD_Table('system_parameter',self.fs.TOTAL_JONGMOK_NAME_TABLE)
        start = start_date + '-' + '01'
        new_code_list = price_in_df.loc[:start].iloc[-260].dropna().index
        price_df = price_in_df[new_code_list].loc[:start]
        price_52_df = price_df.iloc[-260:]
        #price_52_df.to_excel('f:\\test_52.xlsx')
        for num, code in enumerate(code_list.index) :
            try:
                weeks_max_52 = price_52_df[code].astype('int').dropna().max()
                current_price = price_df[code].iloc[-1]
                disparate_ratio = (float(weeks_max_52) - float(current_price)) / float(current_price)
                name =code_list.loc[code][1]
                temp_Series = pd.Series([disparate_ratio, name], name=code)
                if num == 0 :
                    total_df = pd.DataFrame(data=temp_Series)
                else :
                    total_df = pd.concat([total_df, temp_Series], axis=1)
            except:
                #print(num, code)
                pass
        total_df.index = ['괴리율', '종목']
        total_df = total_df.T
        total_df = total_df[total_df['괴리율'] > 0].sort_values(by='괴리율', ascending=True)
        total_df['52주근접순위'] = total_df['괴리율'].rank(ascending=True)
        return total_df[:number]

    def get_near_52WeeksHighPrice_upper(self, start_date, number):
        price_in_df = self.pr.DB_LOAD_Price_Data()
        price_in_df = price_in_df.drop(['KOSPI','KOSDAQ'], axis=1)
        code_list = self.SQL.DB_LOAD_Table('system_parameter', self.fs.TOTAL_JONGMOK_NAME_TABLE)
        start = start_date + '-' + '01'
        new_code_list = price_in_df.loc[:start].iloc[-260].dropna().index
        price_df = price_in_df[new_code_list].loc[:start]
        price_52_df = price_df.iloc[-260:]
        #price_52_df.to_excel('f:\\test_52.xlsx')
        for num, code in enumerate(code_list.index) :
            try:
                weeks_max_52 = price_52_df[code].astype('int').dropna().max()
                current_price = price_df[code].iloc[-1]
                disparate_ratio = (float(weeks_max_52) - float(current_price)) / float(current_price)
                name =code_list.loc[code][1]
                temp_Series = pd.Series([disparate_ratio, name], name=code)
                if num == 0 :
                    total_df = pd.DataFrame(data=temp_Series)
                else :
                    total_df = pd.concat([total_df, temp_Series], axis=1)
            except:
                #print(num, code)
                pass
        total_df.index = ['괴리율', '종목']
        total_df = total_df.T
        total_df = total_df[total_df['괴리율'] == 0].sort_values(by='괴리율', ascending=True)
        total_df['52주근접순위'] = total_df['괴리율'].rank(ascending=True)
        return total_df[:number]

    def get_near_52WeeksHighPrice_now(self,stock_num):
        code_list = self.SQL.DB_LOAD_Table('system_parameter', self.fs.TOTAL_JONGMOK_NAME_TABLE)
        P_url = 'https://finance.naver.com/item/sise.nhn?code='
        #total_df = pd.DataFrame(data=None)
        for num, code in enumerate(code_list.index) :
            try:
                url = P_url + code.replace("A","")
                fs_page_total = requests.get(url)
                fs_tables_total = pd.read_html(fs_page_total.text)
                test = fs_tables_total[1]
                test = test.loc[[0,10]]
                test = test[[0,1]]
                test = test.set_index(0)            
                test.loc['괴리율'] = 1 - float(test.loc['현재가'].astype('float')/test.loc['52주 최고'].astype('float'))
                test.columns = [code]
                test = test.T
                if num == 0 :
                    total_df = pd.DataFrame(data=test)
                else:
                    total_df = pd.concat([total_df,test])
                
            except : 
                pass
        total_df = total_df[total_df['괴리율'] > 0].sort_values(by='괴리율', ascending=False)
        total_df['52주근접순위'] = total_df['괴리율'].rank(ascending=False)
        return total_df[:stock_num]
     
    def Calc_General_Momentum(self, price_data, start_date, loopback_period):
         if loopback_period == 12:
             loopback = -252
         elif loopback_period == 6:
             loopback = -126
         elif loopback_period == 3:
             loopback = -63
         else : 
             loopback = -252
             
         if start_date.split('-')[1] == '1':
             index_month = '12'
             index_year = str(int(start_date.split('-')[0]) - 1)
             index_date = index_year +'-'+ index_month
         else :
             index_month = str(int(start_date.split('-')[1]) - 1)
             index_year = start_date.split('-')[0]
             index_date = index_year +'-'+ index_month
         price_data = price_data.loc[:start_date]
         price_data = price_data.iloc[loopback:]
         stock_num = int(len(price_data.iloc[0].dropna().index) * 0.1)
         price_data = price_data.loc[:index_date]
         GM_df = price_data.iloc[[0,-1]].T
         GM_df['loopback_profit'] = (GM_df[GM_df.columns[1]].astype('float') / GM_df[GM_df.columns[0]].astype('float')) - 1
         GM_df = GM_df.sort_values(by='loopback_profit', ascending=False)
         GM_df = GM_df.dropna()
         # 일반모멘텀으로 10프로 상위 종목 걸러낸다
         return GM_df[:stock_num]
     
    def Calc_FIP_Algorithm(self, price_data, GM_df):
         FIP_df = price_data[GM_df.index]
         FIP_df = FIP_df.loc[GM_df.columns[0]:GM_df.columns[1]]
         FIP_PCT_df = pd.DataFrame(data=None)
         total_num = len(FIP_df)
         FIP_final = pd.DataFrame(data=None)
         for code in FIP_df.columns:
             FIP_PCT_df[code] = FIP_df[code].astype('float').pct_change()
             temp = FIP_PCT_df[FIP_PCT_df[code] > 0]
             plus_ratio = float(len(temp) / total_num)
             temp = FIP_PCT_df[FIP_PCT_df[code] < 0]
             minus_ratio = float(len(temp) / total_num)             
             if GM_df.loc[code]['loopback_profit'] > 0:
                 FIP_final[code] = [minus_ratio - plus_ratio]
             else: 
                 FIP_final[code] = [plus_ratio - minus_ratio]
         FIP_final = FIP_final.T
         FIP_final.columns = ['FIP_Value']
         FIP_final = FIP_final.sort_values(by='FIP_Value', ascending=True)
         return FIP_final[:50]
             
             
             
    def get_Fixed_Quantity_Momentum(self, price_df, start_date, loopback_period = 12):
         # 일반모멘텀 계산(12개월 기준)
         GM_df = self.Calc_General_Momentum(price_df, start_date, loopback_period)
         FIP_df = self.Calc_FIP_Algorithm(price_df, GM_df)
         return FIP_df
    '''
        def magic_formula(self, price_df, invest_df, value_type, quality_type, index_date, start_date, rim_on=True, fs_comp_del_on=True, apply_rim_L=2, num=20):
            filter_invest_df = self.get_value_rank_excel(price_df, invest_df,  index_date, start_date, num=-1, apply_rim_L=3)         
            per['per순위'] = per['PER'].rank()
            roa['roa순위'] = roa['ROA'].rank(ascending=False)
            magic = pd.merge(per, roa, how='outer', left_index=True, right_index=True)
            magic['마법공식 순위'] = (magic['per순위'] + magic['roa순위']).rank().sort_values()
            magic = magic.sort_values(by='마법공식 순위')
            return magic[:num]
    '''
    def Average_Break_Strategy(self, data, code, duration, log, tick_day="day", real_trade=True, start=None):
        if real_trade :
            if tick_day == "day":
                price_data_latest = self.pr.make_jongmok_price_data(code, 3000)
                price_data_latest.columns = ['date', 'open', 'high', 'low', 'close']
                price_data_latest = price_data_latest.set_index('date')
                price_data_latest = price_data_latest.loc[::-1]
                stock_info = price_data_latest
            else:
                stock_info = data.loc[::-1]

        else :
            price_data_latest = self.pr.make_jongmok_price_data(code, 6000)
            price_data_latest.columns = ['date', 'open', 'high', 'low', 'close']
            price_data_latest = price_data_latest.set_index('date')
            price_data_latest = price_data_latest.loc[::-1]
            stock_info = data.loc[start:]
        if len(stock_info['close']) < duration:
            pass_success = False
        else:
            total_price = 0
            for value in stock_info['close'][:duration]:
                total_price += int(float(value))
            moving_average_price = total_price / duration

            # 오늘자 주가가 120일 이평선에 걸쳐있는지 확인
            bottom_stock_price = False
            check_price = None
            if int(float(stock_info['low'][0])) <= moving_average_price and moving_average_price <= int(float(
                    stock_info['high'][0])):
                log.logger.debug("오늘 주가 120이평선 아래에 걸쳐있는 것 확인")
                bottom_stock_price = True
                check_price = int(float(stock_info['high'][0]))

            prev_price = None
            pass_success = False
            if bottom_stock_price == True:
                moving_average_price_prev = 0
                price_top_moving = False
                idx = 1
                while True:
                    if len(stock_info['close'][idx:]) < duration:  # 120일치가 있는지 계속 확인
                        log.logger.debug("120일치가 없음")
                        break

                    total_price = 0
                    for value in stock_info['close'][idx:duration + idx]:
                        total_price += int(float(value))
                    moving_average_price_prev = total_price / duration

                    if moving_average_price_prev <= int(float(stock_info['high'][idx])) and idx <= 10:
                        log.logger.debug("20일 동안 주가가 120일 이평선과 같거나 위에 있으면 조건 통과 못함")
                        price_top_moving = False
                        break

                    elif int(float(stock_info['low'][idx])) > moving_average_price_prev and idx > 10:  # 120일 이평선 위에 있는 구간 존재
                        log.logger.debug("120일치 이평선 위에 있는 구간 확인됨")
                        price_top_moving = True
                        prev_price = int(float(stock_info['low'][idx]))
                        break
                    idx += 1
                # 해당부분 이평선이 가장 최근의 이평선 가격보다 낮은지 확인
                if price_top_moving == True:
                    if moving_average_price > moving_average_price_prev and check_price > prev_price:
                        log.logger.debug("포착된 이평선의 가격이 오늘자 이평선 가격보다 낮은 것 확인")
                        log.logger.debug("포착된 부분의 저가가 오늘자 주가의 고가보다 낮은지 확인")
                        pass_success = True
                else:
                    pass_success = False
        return pass_success, stock_info

    def bollinger_band(self, price_df, n , sigma):
        n= 20
        sigma=2
        bb = price_df.copy()
        bb['center'] = price_df['Adj Close'].rolling(n).mean()
        bb['ub'] = bb['center'] + sigma*price_df['Adj Close'].rolling(n).std()
        bb['lb'] = bb['center'] - sigma * price_df['Adj Close'].rolling(n).std()
        return bb
    # 투자용 분기데이터 로드 (no 백테스트)
    def make_invest_from_quarter(self, index_date, ROE_type='ROE_AVG', RIM_SaleRate=0.09):
        # index_date 기분 4개 quarter를 불러온다
        # 합쳐야하는 요소 확인
        # 기존 아이투자 크롤링 Factor
        '''
        sum_index = ['매출액', '매출원가', '재고자산의변동', '감가상각비', '매출총이익', '연구개발비', '영업이익',
                     '법인세비용차감전계속사업이익', '법인세비용', '당기순이익', '지배지분순이익', '총포괄이익', '지배지분총포괄이익',
                     '비지배지분총포괄이익', 'EBITDA', '영업활동으로인한현금흐름', '유형자산감가상각비', '개발비상각', '무형자산상각비', '매출채권감소',
                     '재고자산의감소', '선급금 감소', '선급비용 감소', '매입채무 증가', '선수금 증가', '투자활동으로인한현금흐름',
                     '유형자산의증가', '토지의증가', '건물및부속설비의증가', '기계장치의증가', '건설중인자산의증가', '재무활동으로인한현금흐름',
                     '현금의증감', 'FCF', 'EPS', 'CFPS', '주당매출액(SPS)']
        quarter_index = ['주가', '시가총액', '유동자산', '현금및현금성자산', '매출채권', '재고자산', '비유동자산', '유형자산', '기계장치',
                         '영업권', '자산총계', '유동부채', '매입채무', '건설중인자산', '무형자산', '미지급금', '비유동부채', '부채총계',
                         '지배주주지분', '자본금', '자본잉여금', '이익잉여금', '자본총계', 'BPS', 'PBR', 'ROS',
                         '자기자본 증가율(지배)', '부채비율(%)', '유동비율(%)', '자본잠식률(%)']
        '''
        # Value Tool 크롤링 factor
        # 여기서 실제로 쓰이는 데이터만 정리해서 넣어주자
        sum_index = ['매출액', '매출원가', '매출총이익', '연구개발비', '영업이익','당기순이익', '감가상각비',
                     '지배지분순이익', '영업활동으로인한현금흐름', '투자활동으로인한현금흐름', '재무활동으로인한현금흐름'
                     ]
        quarter_index = ['유동자산', '매출채권', '재고자산', '비유동자산', '유형자산',
                         '영업권', '자산총계', '유동부채', '매입채무', '무형자산', '비유동부채', '부채총계',
                         '지배주주지분', '자본금', '자본잉여금', '이익잉여금','단기금융부채','장기금융부채','BPS',
                         '부채비율(%)','유동비율(%)','유보율(%)','현금성자산', '순현금', '주식수']

        #==========================================================================================================================
        # 2020년에 quart 재무제표 index 년이 걸리면 2019분기데이터가 합쳐질수있는관계로 2020년의 경우는 quarter data로 sum하지말고 계산한다
        # 2020년과 이이전 아이투자 크롤링 데이터 컬럼명 맞춰주기
        prev_sum_index = sum_index.copy()
        prev_quarter_index = quarter_index.copy()
        if int(index_date.split('/')[0]) >= 2020:
            # 2022의 경우 전년도 데이터와 현재년도 데이터모두 Valuetool 데이터이므로 sum 가능
            if int(index_date.split('/')[0]) >= 2022:
                sum_index.append('유형자산취득')
                sum_index.append('무형자산취득')
                prev_sum_index.append('유형자산취득')
                prev_sum_index.append('무형자산취득')
            # 2021의 경우 전년도 데이터는 아이투자데이터와 섞임... 현재년도 데이터 Valuetool 데이터이므로 sum/quarter 구분필요
            elif int(index_date.split('/')[0]) == 2021:
                if int(index_date.split('/')[1]) == 12:
                    sum_index.append('유형자산취득')
                    sum_index.append('무형자산취득')
                    prev_sum_index.append('유형자산취득')
                    prev_sum_index.append('무형자산취득')
                else:
                    sum_index.append('유형자산취득')
                    sum_index.append('무형자산취득')
                    prev_quarter_index.append('유형자산취득')
                    prev_quarter_index.append('무형자산취득')
            # 2020의 경우 전년도 데이터와 현재년도 데이터모두 아이투자 데이터이므로 sum 불가능
            else:
                if int(index_date.split('/')[1]) == 12:
                    sum_index.append('유형자산취득')
                    sum_index.append('무형자산취득')
                    prev_quarter_index = prev_quarter_index + ['사채', '단기차입금', '장기차입금', '유동성장기부채']
                    prev_sum_index.append('FCF')
                else:
                    quarter_index.append('유형자산취득')
                    quarter_index.append('무형자산취득')
                    prev_quarter_index = prev_quarter_index + ['사채', '단기차입금', '장기차입금', '유동성장기부채']
                    prev_sum_index.append('FCF')
        else:
            prev_quarter_index = prev_quarter_index + ['사채', '단기차입금', '장기차입금', '유동성장기부채']
            prev_sum_index.append('FCF')
        # ==========================================================================================================================
        # table list 읽어오도록 수정하자....
        date_list = self.SQL.DB_LOAD_TABLE_LIST("stocks_finance")
        date_index_num = date_list.index(index_date)
        #전년대비 증가율 팩터 계산하기 위해 index_date의 전년도 정보도 계산하자
        for num in range(4,8):
            temp_df = self.SQL.DB_LOAD_Table("stocks_finance", date_list[date_index_num - num], True)
            temp_df = temp_df[date_list[date_index_num - num]].replace(np.nan, 0).astype('float')
            if num == 4:
                # 증가율 계산_직전분기
                # 1. 자산증가율
                cur_asset = temp_df['자산총계'].copy()
                # 2. (영업이익 - 차입금) 증가율

                #total_df = temp_df[date_list[date_index_num - num]]
                prev_total_df = pd.DataFrame(data=None)
                # 최근분기의 데이터만 display되면 되는 항목들+
                for q_index in prev_quarter_index:
                    try:
                        #total_df[q_index] = temp_df[(date_list[date_index_num - num], q_index)]
                        prev_total_df[q_index] = temp_df[q_index]
                    except:
                        print("fail make invest_df")
                        pass
                for s_index in prev_sum_index:
                    #total_df[s_index] = temp_df[(date_list[date_index_num - num], s_index)]
                    prev_total_df[s_index] = temp_df[s_index]
            else:
                if num == 5:
                    prev_asset = temp_df['자산총계'].copy()
                    prev_total_df['자산성장률_QOQ'] = (cur_asset-prev_asset)/prev_asset
                for s_index in prev_sum_index:
                    #total_df[s_index] = total_df[s_index] + temp_df[(date_list[date_index_num - num], s_index)]
                    prev_total_df[s_index] = prev_total_df[s_index] + temp_df[s_index]
        prev_total_df['영업이익-차입금'] = prev_total_df['영업이익']-(prev_total_df['단기금융부채']+prev_total_df['장기금융부채'])
        for num in range(4):
            temp_df = self.SQL.DB_LOAD_Table("stocks_finance", date_list[date_index_num - num], True)
            temp_df = temp_df[date_list[date_index_num - num]].replace(np.nan, 0).astype('float')
            if num == 0:
                #=======================================================================================================
                # 직전분기 대비 계산 Factor list!
                # 1. 자산증가율
                cur_asset = temp_df['자산총계'].copy()
                # 2. 영업이익 증가율
                cur_quarter_income = temp_df['영업이익'].copy()
                # 3. 지배지분순이익 증가율율
                cur_quarter_pure_income = temp_df['지배지분순이익'].copy()
                # ======================================================================================================
                #total_df = temp_df[date_list[date_index_num - num]]
                total_df = pd.DataFrame(data=None)
                # 최근분기의 데이터만 display되면 되는 항목들+
                for q_index in quarter_index:
                    try:
                        #total_df[q_index] = temp_df[(date_list[date_index_num - num], q_index)]
                        total_df[q_index] = temp_df[q_index]
                    except:
                        print("fail make invest_df")
                        pass
                for s_index in sum_index:
                    #total_df[s_index] = temp_df[(date_list[date_index_num - num], s_index)]
                    total_df[s_index] = temp_df[s_index]
            else:
                if num == 1 :
                    prev_asset = temp_df['자산총계'].copy()
                    prev_quarter_income = temp_df['영업이익'].copy()
                    prev_quarter_pure_income = temp_df['지배지분순이익'].copy()

                    total_df['자산성장률_QOQ'] = (cur_asset-prev_asset)/prev_asset
                    total_df['영업이익성장률_QOQ'] = (cur_quarter_income - prev_quarter_income) / prev_quarter_income
                    total_df['지배지분순이익성장률_QOQ'] = (cur_quarter_pure_income - prev_quarter_pure_income) / prev_quarter_pure_income
                for s_index in sum_index:
                    #total_df[s_index] = total_df[s_index] + temp_df[(date_list[date_index_num - num], s_index)]
                    total_df[s_index] = total_df[s_index] + temp_df[s_index]
        # ROE데이터 크롤링해서 받아옴으로 따로 계산하지말자
        # total_df['ROE'] = total_df['지배지분순이익'].astype("float") / total_df['지배주주지분'].replace(0, 1).astype("float")
        #sumdata 필요X
        # sum data 필요
        total_df['재고회전율(%)'] = (total_df['매출액'].astype("float") / total_df['재고자산'].replace(0, 1).astype(
            "float")) * 100
        # 영업이익-차입금 증가비율
        total_df['영업이익-차입금'] =total_df['영업이익']-(total_df['단기금융부채']+total_df['장기금융부채'])
        total_df['전년_영업이익-차입금'] = prev_total_df['영업이익-차입금']
        total_df['영업이익-차입금_증가비율'] = (total_df['영업이익-차입금']/total_df['전년_영업이익-차입금'])-1

        # 신규주식 발행 체크
        total_df['전년주식수'] = prev_total_df['주식수']
        total_df['전년대비주식수변동'] = total_df['주식수'] - total_df['전년주식수']
        # RIM_ROE = SQLITE_control.DB_LOAD_Table(self.fs.EXCEL_PAST_FS_TABLE, self.fs.DB_FS_EXCEL_PATH, True)
        col_list = ['BPS', 'EBITDA(억)', 'EPS', 'EV(기업가치)(억)', 'RIM', 'RIM_L1', 'RIM_L2', 'ROA', 'ROE', 'capex', '감가상각비',
                    '당기순이익', '매입채무', '매출액',
                    '매출액증가율', '매출원가', '매출채권', '매출총이익', '무형자산', '무형자산취득', '배당성향(우)', '배당수익률(우)', '법인세비용', '법인세율',
                    '법인세차감전순이익', '부채비율(%)', '비유동부채', '비유동자산',
                    '설비', '수정BPS', '순운전자본', '영업권', '영업이익', '영업활동현금흐름', '유동부채', '유동비율(%)', '유동자산', '유보율(%)', '유형자산',
                    '유형자산취득', '이익잉여금', '이자비용', '잉여현금흐름(억)',
                    '자기주식', '자본금', '자본잉여금', '재고자산', '재고회전율(%)', '재무활동현금흐름', '주식수', '지배주주순이익', '지배주주지분', '총부채', '총자산',
                    '투자활동현금흐름', '판매비와관리비', '할인율',
                    '현금성자산']

        # RIM_ROE = RIM_ROE.drop(columns=col_list, level=1)
        # 할인율 LOAD
        year_month = index_date.split("/")
        #expect_profit_df = self.SQLITE_control.DB_LOAD_Table(system_parameter, self.fs.EXPECT_PROFIT_TABLE)
        #expect_profit_df.index = pd.to_datetime(expect_profit_df.index)
        try:
            #expect_profit_mean = expect_profit_df.loc[str(start)].mean()
            #total_df['할인율'] = expect_profit_mean['수익률(%)'] * 100
            total_df['할인율'] = RIM_SaleRate
            total_df['rim_L2'] = self.fs.rim_L2
            total_df['rim_L1'] = self.fs.rim_L1
        except:
            total_df['할인율'] = RIM_SaleRate
            total_df['rim_L2'] = self.fs.rim_L2
            total_df['rim_L1'] = self.fs.rim_L1
        # ROE 적용 알고리즘
        date_list = self.SQL.DB_LOAD_TABLE_LIST("stocks_rim")
        date_list.sort()
        if ROE_type == 'ROE_AVG' :
            RIM_ROE = self.SQL.DB_LOAD_Table("stocks_rim" , date_list[-1], False)
            RIM_ROE = RIM_ROE.drop(columns=['할인율'])
            total_df=total_df.drop(columns=['BPS','무형자산'])
            total_df = pd.merge(total_df, RIM_ROE, how='outer', left_index=True, right_index=True)
            total_df=total_df.replace("-",np.nan)
            #print(total_df['BPS'])
            total_df['RIM_ROE'] = total_df['ROE평균']
            total_df['RIM'] = total_df['수정BPS'].astype("float") + ((
                    total_df['BPS'].astype("float") * (total_df['RIM_ROE'].astype("float") - total_df['할인율']) /
                    total_df['할인율']))
            total_df['RIM_L1'] = total_df['수정BPS'].astype("float") + ((
                    total_df['BPS'].astype("float") * (total_df['RIM_ROE'].astype("float")-total_df['할인율']) * self.fs.rim_L1) / (
                            total_df['할인율'] + (1-self.fs.rim_L1)))
            total_df['RIM_L2'] = total_df['수정BPS'].astype("float") + ((
                    total_df['BPS'].astype("float") * (total_df['RIM_ROE'].astype("float")-total_df['할인율']) * self.fs.rim_L2) / (
                            total_df['할인율'] + (1-self.fs.rim_L2)))
        else :
            RIM_ROE = self.SQL.DB_LOAD_Table("system_parameter" , "rim_roe_quarter", False)
            RIM_ROE.name = "RIM_ROE"
            total_df = pd.merge(total_df, RIM_ROE[index_date], how='outer', left_index=True, right_index=True)
            total_df['수정BPS'] = (total_df['지배주주지분'].astype("float") - total_df['무형자산'].astype("float"))/total_df['주식수'].replace(0, 1).astype("float")
            total_df['RIM_ROE'] = total_df['RIM_ROE'].astype('float')
            #total_df['ROE'] = RIM_ROE[(index_date, 'ROE')].astype('float')
            total_df['RIM'] = total_df['수정BPS'].astype("float") + (
                    total_df['BPS'].astype("float") * (total_df['RIM_ROE'].astype("float") - total_df['할인율']) / total_df['할인율'])
            total_df['RIM_L1'] = total_df['수정BPS'].astype("float") + (
                    total_df['BPS'].astype("float") * (total_df['RIM_ROE'].astype("float")-total_df['할인율']) * self.fs.rim_L1) / (
                            total_df['할인율'] + (1-self.fs.rim_L1))
            total_df['RIM_L2'] = total_df['수정BPS'].astype("float") + (
                    total_df['BPS'].astype("float") * (total_df['RIM_ROE'].astype("float")-total_df['할인율']) * self.fs.rim_L2) / (
                            total_df['할인율'] + (1-self.fs.rim_L2))

        #RIM_ROE = RIM_ROE[index_date]

        total_df = total_df.dropna(axis=0, subset=['지배주주지분'], inplace=False)
        total_df.columns = [[index_date] * len(total_df.columns), total_df.columns]
        #total_df['지배주주지분'].replace(0, np.nan).dropna()

        return total_df

    def select_code_by_price_excel(self, data_df, comp_size,
                                   rim_on=True, fs_comp_del_on=True, BJ_Filter=True, apply_rim_L=2):

        select_invest_df = data_df.copy()
        total_comp = int(len(select_invest_df) / 3)
        select_invest_df = select_invest_df[select_invest_df.columns.levels[0][0]]
        select_invest_df['현재가'] = 0
        for code in tqdm.tqdm(select_invest_df.index):
            try:
                price_df = fdr.DataReader(code.replace("A", ""), self.current_day, self.current_day)
                select_invest_df.loc[code,'현재가']=price_df['Close'][0].copy()
                #print(self.current_day)
            except:
                print(code)
                continue
        select_invest_df['시가총액'] = select_invest_df['현재가']*select_invest_df['주식수']
        #try:  # 시가총액이 없는 에러때문에
        if comp_size == 'TOTAL':
            pass
        elif comp_size == '대형주':
            select_invest_df = select_invest_df.sort_values(by='시가총액', ascending=False)
            select_invest_df = select_invest_df.iloc[:total_comp]
            #select_price_df = select_price_df[select_invest_df.index]
        elif comp_size == '중형주':
            select_invest_df = select_invest_df.sort_values(by='시가총액', ascending=False)
            select_invest_df = select_invest_df.iloc[total_comp + 1:total_comp * 2]
            #select_price_df = select_price_df[select_invest_df.index]
        elif comp_size == '소형주':
            select_invest_df = select_invest_df.sort_values(by='시가총액', ascending=False)
            select_invest_df = select_invest_df.iloc[(total_comp * 2) + 1:(total_comp * 3) - 1]
            #select_price_df = select_price_df[select_invest_df.index]
        #except:
        #    pass
        if BJ_Filter:
            select_invest_df = select_invest_df[(select_invest_df['부채비율(%)'].astype('float') < 200) & (select_invest_df['유보율(%)'].astype('float') > 300) & (select_invest_df['유동비율(%)'].astype('float') > 150)]
        if rim_on:
            select_invest_df = self.RIM_ON(select_invest_df, apply_rim_L)
            # 금융회사/지주사/중국회사 제외
        if fs_comp_del_on:
            select_invest_df = self.Finance_company_del(select_invest_df)

        select_invest_df.columns = [[data_df.columns.levels[0][0]] * len(select_invest_df.columns), select_invest_df.columns]
        return select_invest_df

if __name__ == "__main__":
    test = Quant_Strategy()
    
    