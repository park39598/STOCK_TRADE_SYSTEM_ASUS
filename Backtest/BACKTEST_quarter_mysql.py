# coding: utf-8
import sys
import os
ROOT_DIR = os.path.dirname(os.path.abspath(os.path.dirname(__file__)))
sys.path.append(ROOT_DIR)
#sys.path.append(r'F:\OneDrive\Data\STOCK_PRG\STOCK_TRADE_SYSTEM_ASUS')
import matplotlib.pyplot as plt
from matplotlib import font_manager, rc
from Kiwoom.config.log_class import Logging

plt.rcParams["axes.unicode_minus"] = False
plt.rcParams['font.family'] = 'Malgun Gothic'
'''
path = "c:\Windows\Fonts\H2GTRM.TTF"
font_name = font_manager.FontProperties(fname=path).get_name()
rc("font", family=font_name)
'''
import calendar
from Trade_Algrithm.python_quant import *
import DataBase.MySQL_control
# 스키마 분류
stocklist = 'stocks_lists'
stockfinance = 'stocks_finance'
stockfinance_year = 'stocks_finance_year'
stocksprice = 'stocks_price'
system_parameter = 'system_parameter'
TOTAL_JONGMOK_NAME_TABLE = 'stocks_lists_all'

class BACK_TEST:
    def __init__(self):
        self.ROOT_DIR = os.path.abspath(os.curdir)
        self.logging = Logging(self.ROOT_DIR + '\\config\\logging.conf')
        self.fs = Finance_data()
        self.pr = Price_data()
        self.quant = Quant_Strategy()
        self.SQLITE_control = DataBase.MySQL_control.DB_control()
        self.CodebyName_df = self.SQLITE_control.DB_LOAD_Table(system_parameter, self.fs.TOTAL_JONGMOK_NAME_TABLE)
        self.CodebyName_df = self.CodebyName_df[['종목']]
        self.prev_strategy_df = pd.DataFrame(data=None)
        self.trans_tax = 0.0033
        # 백테스트 도출 변수
        self.plus_jongmok = 0
        self.minus_jongmok = 0
        self.total_trade_num = 0
        self.per_profitSum = 0
        self.per_lossSum = 0
        self.KOSPI = pd.DataFrame()
        self.KOSDAQ = pd.DataFrame()
        self.test_log_on = False
        self.start_date = '2000-01-01'
        self.end_date = '2020-12-31'
        self.price_in_df = None
        self.rebal_firsttime_flag = True
        self.code_list = self.SQLITE_control.DB_LOAD_Col_From_Table("stocks_lists", "stocks_lists_all", ["Symbol", "Name"])

    def back_test_Beta(self, price_df, strategy_df, start_date, end_date, initial_money, money_ratio, tax_on=True):
        # 전략의 상위종목들 DF의 종목코드를 추려내기
        #        jongmok_status_df = pd.DataFrame(data=strategy_df, index = strategy_df.index , columns =strategy_df.columns + ['START금액','END금액','수량', '손익','수익률'], dtype='float')
        jongmok_status_df = strategy_df.copy()
        jongmok_status_df['START금액'] = 0
        jongmok_status_df['END금액'] = 0
        jongmok_status_df['수량'] = 0
        jongmok_status_df['손익'] = 0
        jongmok_status_df['수익률'] = 0
        jongmok_status_df['종목명'] = 0
        jongmok_status_df['현금비율'] = money_ratio
        jongmok_status_df['수익종목'] = 0
        jongmok_status_df['손실종목'] = 0
        jongmok_status_df['Name'] = ""
        self.total_trade_num = self.total_trade_num + 1
        strategy_price = price_df[strategy_df.index][start_date:end_date].astype('float').dropna()
        # cash 계산
        pf_stock_num = {}
        stock_amount = 0
        stock_pf = 0
        cash_amount = int(initial_money * money_ratio)
        try:
            each_money = (initial_money - cash_amount) / len(strategy_df.index)
        except:
            each_money = 0
        for code in strategy_price.columns:
            #self.logging.logger.debug("%s / %s :  " % (each_money, strategy_price[code][0]))
            temp = int(each_money / strategy_price[code][0])

            pf_stock_num[code] = temp
            if tax_on:
                stock_amount = stock_amount + temp * strategy_price[code][0] * (1 - self.trans_tax)  # 구입시 거래세+수수료 0.33%
            else:
                stock_amount = stock_amount + temp * int(strategy_price[code][0])
            stock_pf = stock_pf + strategy_price[code].astype('int') * pf_stock_num[code] * (1 - self.trans_tax)
            jongmok_status_df['START금액'][code] = int(strategy_price[code][0])
            jongmok_status_df['END금액'][code] = int(strategy_price[code][-1])
            jongmok_status_df['수량'][code] = int(pf_stock_num[code])
            jongmok_status_df['손익'][code] = (int(strategy_price[code][-1]) - int(strategy_price[code][0])) * \
                                            pf_stock_num[code]
            jongmok_status_df['수익률'][code] = ((float(strategy_price[code][-1]) / float(
                strategy_price[code][0])) - 1) * 100
            if jongmok_status_df['수익률'][code] > 0:
                jongmok_status_df['수익종목'][code] = 1
            else:
                jongmok_status_df['손실종목'][code] = 1
            jongmok_status_df['Name'][code] = self.code_list.loc[code][0]
        if tax_on:
            cash_amount = initial_money - stock_amount - stock_amount * (self.trans_tax)
            backtest_df = pd.DataFrame({'주식포트폴리오': stock_pf * (1 - self.trans_tax)})
        else:
            cash_amount = initial_money - stock_amount
            backtest_df = pd.DataFrame({'주식포트폴리오': stock_pf})
        self.per_profitSum = self.per_profitSum + jongmok_status_df[jongmok_status_df['수익률'] > 0]['수익률'].sum()
        self.per_lossSum = self.per_lossSum + jongmok_status_df[jongmok_status_df['수익률'] <= 0]['수익률'].sum()
        backtest_df['수수료'] = stock_amount * (self.trans_tax) * 2
        backtest_df['현금포트폴리오'] = cash_amount
        backtest_df['종합포트폴리오'] = backtest_df['주식포트폴리오'] + backtest_df['현금포트폴리오']
        backtest_df['일변화율'] = backtest_df['종합포트폴리오'].pct_change()
        backtest_df['총변화율'] = backtest_df['종합포트폴리오'] / initial_money - 1
        backtest_df['cash_ratio'] = money_ratio
        # backtest_log make
        try:
            if strategy_df.columns[1] == '종목':
                self.get_backtest_log(strategy_df.index[0], None,
                                      jongmok_status_df, True)
            else:
                self.get_backtest_log(strategy_df.columns[0], strategy_df.columns[2],
                                      jongmok_status_df, True)
        except:
            self.get_backtest_log(strategy_df.columns[0], "_NONE", jongmok_status_df, True)
        return backtest_df

    def select_code_by_price(self, price_df, data_df):
        new_code_list = []
        for code in price_df[self.start_date].iloc[0].dropna().index:
            new_code_list.append('A' + code)
        select_df = data_df.loc[new_code_list]
        return select_df

    def select_code_by_price_excel(self, price_df, data_df, start, end, index_date, comp_size,
                                   rim_on=True, fs_comp_del_on=True, BJ_Filter=True, apply_rim_L=2):
        #price invest의 중복 종목들만 추려내자 Pricedf종목수가 너무 불필요하게 많다
        '''
        temp=list(price_df.columns)
        temp2=list(data_df.index)
        new_code_list = list(set(temp2).intersection(temp))
        '''
        new_code_list = []
        for code in price_df.loc[start].iloc[0].dropna().index:
            new_code_list.append(code)

        temp2 = list(data_df.index)
        new_code_list = list(set(temp2).intersection(new_code_list))
        select_invest_df = data_df.loc[new_code_list]
        select_price_df = price_df[new_code_list]
        if self.test_log_on == True:
            data_df.to_excel('F:\\test_log\\data_df.xlsx')
        total_comp = int(len(select_invest_df) / 3)

        select_invest_df = select_invest_df[index_date]
        current_price_list = price_df[start][select_invest_df.index].astype('float')
        select_invest_df['현재가'] = current_price_list.iloc[0]
        select_invest_df['시가총액'] = select_invest_df['현재가']*select_invest_df['주식수']
        #try:  # 시가총액이 없는 에러때문에
        if comp_size == 'TOTAL':
            pass
        elif comp_size == '대형주':
            select_invest_df = select_invest_df.sort_values(by='시가총액', ascending=False)
            select_invest_df = select_invest_df.iloc[:total_comp]
            select_price_df = select_price_df[select_invest_df.index]
        elif comp_size == '중형주':
            select_invest_df = select_invest_df.sort_values(by='시가총액', ascending=False)
            select_invest_df = select_invest_df.iloc[total_comp + 1:total_comp * 2]
            select_price_df = select_price_df[select_invest_df.index]
        elif comp_size == '소형주':
            select_invest_df = select_invest_df.sort_values(by='시가총액', ascending=False)
            select_invest_df = select_invest_df.iloc[(total_comp * 2) + 1:(total_comp * 3) - 1]
            select_price_df = select_price_df[select_invest_df.index]
        #except:
        #    pass
        if BJ_Filter:
            select_invest_df = select_invest_df[(select_invest_df['부채비율(%)'].astype('float') < 200) & (select_invest_df['유보율(%)'].astype('float') > 300) & (select_invest_df['유동비율(%)'].astype('float') > 150)]
        if rim_on:
            select_invest_df = self.quant.RIM_ON(select_invest_df, apply_rim_L)
            # 금융회사/지주사/중국회사 제외
        if fs_comp_del_on:
            select_invest_df = self.quant.Finance_company_del(select_invest_df)
        if self.test_log_on: select_invest_df.to_excel('F:\\test_log\\total_df_copsize_sort.xlsx')
        select_invest_df.columns = [[index_date] * len(select_invest_df.columns), select_invest_df.columns]
        return (select_invest_df, select_price_df)

    def decision_strategy_date(self, start):
        start = str(start)
        start_year = start.split('-')[0]
        start_month = start.split('-')[1]
        if (int(start_month) > 3) & (int(start_month) < 6):
            strategy_date = str(int(start_year) - 1) + '/' + '12'
        elif (int(start_month) > 5) & (int(start_month) < 9):
            strategy_date = str(start_year) + '/' + '03'
        elif (int(start_month) > 8) & (int(start_month) < 12):
            strategy_date = str(start_year) + '/' + '06'
        else:
            if int(start_month) == 12:
                strategy_date = str(start_year) + '/' + '09'
            else:
                strategy_date = str(int(start_year) - 1) + '/' + '09'
        return strategy_date

    def calc_month_enddate(self, date):
        year = int(date.split('-')[0])
        month = int(date.split('-')[1])
        end_date = calendar.monthrange(year, month)[1]
        date = date + '-' + str(end_date)
        return date

    def rebal_peri_stochastics(self, comp_type):
        if comp_type == '소형주':
            rebal_date = self.SQLITE_control.DB_LOAD_Table(stocksprice, self.pr.KOSDAQ_PRICE_TABLE)
        else:
            rebal_date = self.SQLITE_control.DB_LOAD_Table(stocksprice, self.pr.KOSPI_PRICE_TABLE)
        rebal_date.index = pd.to_datetime(rebal_date.index)
        rebal_date = rebal_date[['rebalancing']].dropna()
        rebal_date = rebal_date.loc[self.start_date:self.end_date]
        rebal_peri_list = []
        for num in range(1, len(rebal_date.index)):
            if num == len(rebal_date.index):
                rebal_peri_list.append([rebal_date.index[num], self.end_date, rebal_date.iloc[num][0]])
            else:
                rebal_peri_list.append([rebal_date.index[num - 1], rebal_date.index[num], rebal_date.iloc[num - 1][0]])
        end = self.calc_month_enddate(self.end_date)
        rebal_peri_list.append([rebal_date.index[-1], end, rebal_date.iloc[-1][0]])
        rebal_peri_df = pd.DataFrame(data=rebal_peri_list, columns=['start_time', 'end_date', 'strategy'])

        return rebal_peri_df

    def adjust_absolute_momentum(self, start, comp_type, cash_ratio, ref_duration=6):
        test = self.pr.DB_LOAD_Price_Data()
        if comp_type == '소형주':
            rebal_date = test[['KOSDAQ']]
        else:
            rebal_date = test[['KOSPI']]
        # 절대모멘텀 1~12개월 가중치 계산
        # 1개월 평균 22일 계산...
        if rebal_date.astype('float').pct_change(ref_duration * 22).loc[start].iloc[0][0] >= 0:
            cash_ratio = 0.0
        else:
            cash_ratio = 1.0
        return cash_ratio

    def average_momentum_score(self, start, comp_type):
        test = self.pr.DB_LOAD_Price_Data()
        if comp_type == '소형주':
            rebal_date = test[['KOSDAQ']]
        else:
            rebal_date = test[['KOSPI']]
        pos = 0
        neg = 0
        for num in range(1, 13):
            if rebal_date.astype('float').pct_change(num * 22).loc[start].iloc[0][0] >= 0:
                if num > 7:
                    pos = pos + 0.5
                else:
                    pos = pos + 1.5
            else:
                if num > 7:
                    neg = neg + 0.5
                else:
                    neg = neg + 1.5
        cash_ratio = float(neg / 12)
        return cash_ratio

    def average_momentum_score2(self, start, comp_type):
        test = self.pr.DB_LOAD_Price_Data()
        if comp_type == '소형주':
            rebal_date = test[['KOSDAQ']]
        else:
            rebal_date = test[['KOSPI']]
        pos = 0
        neg = 0
        range = [1, 3, 6, 9, 12]
        for num in range:
            if rebal_date.astype('float').pct_change(num * 22).loc[start].iloc[0][0] >= 0:
                pos = pos + 1
            else:
                neg = neg + 1
        cash_ratio = float(neg / 5)
        return cash_ratio

    def rebal_peri_calc(self, rebal_P):
        temp_S_year = self.start_date.split('-')[0]
        temp_S_month = self.start_date.split('-')[1]
        temp_E_year = self.end_date.split('-')[0]
        temp_E_month = self.end_date.split('-')[1]
        period = 12 * (int(temp_E_year) - int(temp_S_year)) + int(temp_E_month) - int(temp_S_month) + 1
        period_repeat = int(period / rebal_P)
        rebal_peri_list = []
        start_month = temp_S_month
        start_year = temp_S_year
        for i in range(period_repeat):
            if i == period_repeat - 1:
                if start_year == temp_E_year and start_month == temp_E_month:
                    if rebal_P == 1:
                        end_month = temp_E_month
                        end_year = temp_E_year
                        start = start_year + '-' + start_month
                        end = end_year + '-' + end_month
                        rebal_peri_list.append([start, end, '매수'])
                        rebal_peri_df = pd.DataFrame(data=rebal_peri_list,
                                                     columns=['start_time', 'end_date', 'strategy'])
                    else:
                        rebal_peri_df = pd.DataFrame(data=rebal_peri_list,
                                                     columns=['start_time', 'end_date', 'strategy'])
                else:
                    end_month = temp_E_month
                    end_year = temp_E_year
                    start = start_year + '-' + start_month
                    end = end_year + '-' + end_month
                    rebal_peri_list.append([start, end, '매수'])
                    rebal_peri_df = pd.DataFrame(data=rebal_peri_list, columns=['start_time', 'end_date', 'strategy'])
            else:
                if int(start_month) + rebal_P - 1 > 12:
                    end_month = str(int(start_month) + rebal_P - 12 - 1)
                    end_year = str(int(start_year) + 1)
                    while int(end_month) > 12:
                        end_month = str(int(end_month) - 12)
                        end_year = str(int(end_year) + 1)

                else:
                    end_month = str(int(start_month) + rebal_P - 1)
                    end_year = str(int(start_year))
                start = start_year + '-' + start_month
                end = end_year + '-' + end_month
                rebal_peri_list.append([start, end, '매수'])
                if int(end_month) + 1 > 12:
                    start_month = '1'
                    start_year = str(int(end_year) + 1)
                else:
                    start_month = str(int(end_month) + 1)
                    start_year = end_year
        return rebal_peri_df

    def get_mdd_cagr(self, back_test_df):
        max_list = [0]
        mdd_list = [0]
        for i in back_test_df.index[1:]:
            max_list.append(back_test_df['총변화율'][:i].max())
            if max_list[-1] > max_list[-2]:
                mdd_list.append(0)
            else:
                mdd_list.append(min(back_test_df['총변화율'][i] - max_list[-1], mdd_list[-1]))
        back_test_df['max'] = max_list
        back_test_df['MDD'] = mdd_list
        num_of_year = int(self.end_date.split('-')[0]) - int(self.start_date.split('-')[0])
        CAGR = (back_test_df.iloc[-1]['종합포트폴리오'] / back_test_df.iloc[0]['종합포트폴리오']) ** (1 / num_of_year) - 1
        #print(CAGR)
        return back_test_df, float(CAGR)

    def get_backtest_log(self, value_type, quality_type, jongmok_status_df, export_log=False):
        start_date = pd.to_datetime(self.start_date)
        end_date = pd.to_datetime(self.end_date)
        self.plus_jongmok = self.plus_jongmok + jongmok_status_df['수익종목'].astype('int').sum()
        self.minus_jongmok = self.minus_jongmok + jongmok_status_df['손실종목'].astype('int').sum()
        if export_log:
            if (value_type == 'KOSPI') or (value_type == 'KOSDAQ'):
                log_name = str(value_type.replace("/", "_")) + '_' + '_' + str(start_date.year) + str(
                    start_date.month) + '_' + str(end_date.year) + str(end_date.month) + '.xlsx'
            elif quality_type == None:
                log_name = str(value_type.replace("/", "_")) + '_' + str(start_date.year) + str(
                    start_date.month) + '_' + str(end_date.year) + str(end_date.month) + '.xlsx'
            else:
                log_name = str(value_type.replace("/", "_")) + '_' + str(quality_type.replace("/", "_")) + '_' + str(
                    start_date.year) + str(start_date.month) + '_' + str(end_date.year) + str(end_date.month) + '.xlsx'
            cols = jongmok_status_df.columns.tolist()
            cols = cols[-1:] + cols[:-1]
            jongmok_status_df = jongmok_status_df[cols]
            jongmok_status_df.to_excel(self.fs.Backtest_Log_Path + log_name)
        return

    def make_invest_from_quarter(self, index_date, start):
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
        prev_quarter_index = sum_index.copy()
        if int(index_date.split('/')[0]) >= 2020:
            # 2022의 경우 전년도 데이터와 현재년도 데이터모두 Valuetool 데이터이므로 sum 가능
            if int(index_date.split('/')[0]) >= 2022:
                sum_index.append('유형자산취득')
                sum_index.append('무형자산취득')
                prev_sum_index.append('유형자산취득')
                prev_sum_index.append('무형자산취득')
            # 2021의 경우 전년도 데이터는 아이투자데이터와 섞임... 현재년도 데이터 Valuetool 데이터이므로 sum/quarter 구분필요
            elif int(index_date.split('/')[0]) < 2022:
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
            prev_quarter_index=prev_quarter_index+['사채','단기차입금','장기차입금','유동성장기부채']
            prev_sum_index.append('FCF')
        # ==========================================================================================================================
        # table list 읽어오도록 수정하자....
        date_list = self.SQLITE_control.DB_LOAD_TABLE_LIST("stocks_finance")
        date_index_num = date_list.index(index_date)
        #전년대비 증가율 팩터 계산하기 위해 index_date의 전년도 정보도 계산하자
        for num in range(4,8):
            temp_df = self.SQLITE_control.DB_LOAD_Table(stockfinance, date_list[date_index_num - num], True)
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
                if num == 5 :
                    prev_asset = temp_df['자산총계'].copy()
                    prev_total_df['자산성장률_QOQ'] = (cur_asset-prev_asset)/prev_asset
                for s_index in sum_index:
                    #total_df[s_index] = total_df[s_index] + temp_df[(date_list[date_index_num - num], s_index)]
                    prev_total_df[s_index] = prev_total_df[s_index] + temp_df[s_index]
        prev_total_df['영업이익-차입금'] = prev_total_df['영업이익']-(prev_total_df['단기금융부채']+prev_total_df['장기금융부채'])
        for num in range(4):
            temp_df = self.SQLITE_control.DB_LOAD_Table(stockfinance, date_list[date_index_num - num], True)
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
        year_month = index_date.split("/")
        try:
            #expect_profit_mean = expect_profit_df.loc[str(start)].mean()
            #total_df['할인율'] = expect_profit_mean['수익률(%)'] * 100
            total_df['할인율'] = 0.08
        except:
            total_df['할인율'] = 0.08
        # ROE 적용 알고리즘

        RIM_ROE = self.SQLITE_control.DB_LOAD_Table("system_parameter" , "rim_roe_quarter", False)
        RIM_ROE = RIM_ROE[index_date]
        RIM_ROE.name="RIM_ROE"
        total_df=pd.merge(total_df, RIM_ROE, how='outer', left_index=True, right_index=True)
        total_df['수정BPS'] = (total_df['지배주주지분'].astype("float") - total_df['무형자산'].astype("float"))/total_df['주식수'].replace(0, 1).astype("float")
        total_df['RIM_ROE'] = total_df['RIM_ROE'].astype('float')
        #total_df['ROE'] = RIM_ROE[(index_date, 'ROE')].astype('float')
        total_df['RIM'] = total_df['수정BPS'].astype("float") + (
                total_df['BPS'].astype("float") * (total_df['RIM_ROE'].astype("float") - total_df['할인율']) / total_df['할인율'])
        total_df['RIM_L1'] = total_df['수정BPS'].astype("float") + (
                total_df['BPS'].astype("float") * (total_df['RIM_ROE'].astype("float") * self.fs.rim_L1 - total_df['할인율']) / (
                1 + total_df['할인율'] - self.fs.rim_L1))
        total_df['RIM_L2'] = total_df['수정BPS'].astype("float") + (
                total_df['BPS'].astype("float") * (total_df['RIM_ROE'].astype("float") * self.fs.rim_L2 - total_df['할인율']) / (
                1 + total_df['할인율'] - self.fs.rim_L2))

        total_df = total_df.dropna(axis=0, subset=['지배주주지분'], inplace=False)
        total_df.columns = [[index_date] * len(total_df.columns), total_df.columns]
        #total_df['지배주주지분'].replace(0, np.nan).dropna()

        return total_df

    def get_backtest_result(self, data, KOSPI, KOSDAQ):
        # monthly profit_calculation
        start_year = data.iloc[0].name.year
        start_month = data.iloc[0].name.month
        end_year = data.iloc[-1].name.year
        end_month = data.iloc[-1].name.month
        period = []
        profitability = []
        while (start_year != end_year) or (start_month != end_month):
            index_month = str(start_year) + '-' + str(start_month)
            period.append(index_month)
            profitability.append(
                str(((data[index_month]['종합포트폴리오'].iloc[-1] / data[index_month]['종합포트폴리오'].iloc[0]) - 1) * 100) + '%')
            if start_month == 12:
                start_month = 1
                start_year = start_year + 1
            else:
                start_month = start_month + 1
        result = {'년월': period, '수익률': profitability}
        result_backtest = pd.DataFrame(result)
        result_backtest = result_backtest.set_index('년월')
        result_backtest['수익종목'] = self.plus_jongmok
        result_backtest['손실종목'] = self.minus_jongmok
        result_backtest['승률'] = str(self.plus_jongmok * 100 / (self.plus_jongmok + self.minus_jongmok)) + '%'
        result_backtest['수익종목평균수익률'] = str(self.per_profitSum / self.plus_jongmok) + '%'
        result_backtest['손실종목평균손실률'] = str(self.per_lossSum / self.minus_jongmok) + '%'
        result_backtest['총 매매횟수'] = self.total_trade_num
        temp = np.array(list(map(lambda x: float(x.replace("%", "")), result_backtest['수익률'])))
        result_backtest['월평균수익률'] = np.mean(temp)
        result_backtest['코스피_상관성'] = KOSPI['일변화율'].corr(data['일변화율'])
        result_backtest['코스닥_상관성'] = KOSDAQ['일변화율'].corr(data['일변화율'])
        return result_backtest

    def cash_ratio_adjust_algorithm(self, cash_ratio, signal_trans, strategy):
        if strategy == 'buy_increase':
            if signal_trans == '매도':
                if cash_ratio > 0.7:
                    cash_ratio = 0.7
                else:
                    cash_ratio = cash_ratio + 0.05
            else:
                if cash_ratio <= 0.0:
                    cash_ratio = 0.0
                else:
                    cash_ratio = cash_ratio - 0.05
        elif strategy == 'buy_decrease':

            if signal_trans == '매수':
                if cash_ratio > 0.7:
                    cash_ratio = 0.7
                else:
                    cash_ratio = cash_ratio + 0.05
            else:
                if cash_ratio <= 0.0:
                    cash_ratio = 0.0
                else:
                    cash_ratio = cash_ratio - 0.05
        return cash_ratio

    def Make_Price_Data(self):
        # Database의 가격 skima의 Table 리스트를 불러온다.
        jongmok_list = self.SQLITE_control.DB_LOAD_TABLE_LIST(self.SQLITE_control.skima_stocks_price)
        # LOAD 종목별 가격 정보 중 "종가"만...우선
        Price_data = pd.DataFrame(data = None)
        load_col_list = ['Date', 'Close']
        for num, name in enumerate(jongmok_list):
            if name == 'price_data_a' or name == 'price_data_b' or name == 'price_data_c' or name == 'price_data_d':
                continue
            if name == 'ks11' or name == 'kq11':
                pass
            try:
                print(num)
                temp_data  = self.SQLITE_control.DB_LOAD_Col_From_Table(self.SQLITE_control.skima_stocks_price, name, load_col_list)
                temp_data = temp_data.loc[self.start_date : self.end_date]
                temp_data.rename(columns={'Close': name}, inplace = True)
                if num == 0 :
                    Price_data = temp_data
                else :
                    Price_data = pd.concat([Price_data, temp_data], axis=1)
            except:
                pass
                    #Price_data = pd.merge(Price_data, temp_data, how='outer', left_index=False, right_index=False)
                    
        self.SQLITE_control.DB_SAVE_Price_Data(Price_data)
        return Price_data

    def rebal_backtest_excel(self, initial_money, strategy_sel, rebal_P, comp_size='TOTAL',
                             rim_on=True, comp_del=True, BJ_Filter=True, money_ratio=0.0, money_ratio_method='buy_increase',
                             tax_on=True, portpolio=None):
        # 리밸런싱 결과 변수 초기화
        self.plus_jongmok = 0
        self.minus_jongmok = 0
        self.total_trade_num = 0
        self.per_profitSum = 0
        self.per_lossSum = 0
        # 계속 Price_data를 로드할 필요X ,  초기한번만...
        if self.rebal_firsttime_flag :
            self.price_in_df = self.SQLITE_control.DB_LOAD_Price_Data()
            temp_col =[]
            for col in self.price_in_df.columns:
                if len(col)>4:temp_col.append(str(col).upper())
                else:temp_col.append(str(col))
            self.price_in_df.columns = temp_col
            #self.price_in_df.columns=[str(x).upper() for x in list(self.price_in_df.columns) if len(x)>4]
            self.rebal_firsttime_flag = False
        else : pass
        #price_in_df = self.pr.DB_LOAD_Price_Data()
        if portpolio == '스토캐스틱':
            Rebalance_selections = self.rebal_peri_stochastics(comp_size)
        else:
            Rebalance_selections = self.rebal_peri_calc(rebal_P)
        #Rebalance_selections.to_excel('f:\\' + strategy_sel + '.xlsx')
        REBALANCE_DF = pd.DataFrame(data=None)
        KOSPI_flag = False
        KOSDAQ_flag = False
        for i in tqdm.tqdm(range(len(Rebalance_selections))):
            start = Rebalance_selections.iloc[i][0]
            end = Rebalance_selections.iloc[i][1]
            if portpolio == '스토캐스틱':
                money_ratio = self.cash_ratio_adjust_algorithm(money_ratio, Rebalance_selections.iloc[i][2],
                                                               money_ratio_method)
            elif portpolio == '절대모멘텀':
                money_ratio = self.adjust_absolute_momentum(start, comp_size, 12)
            elif portpolio == '평균모멘텀':
                money_ratio = self.average_momentum_score(start, comp_size)
            elif portpolio == '평균모멘텀2':
                money_ratio = self.average_momentum_score2(start, comp_size)
            else:
                pass
            strategy_date = self.decision_strategy_date(start)
            stock_num = 30
            if strategy_sel == '저PER':
                invest_in_df = self.make_invest_from_quarter(strategy_date, start)
                # price_in_df = self.pr.DB_LOAD_Price_Data()
                (invest_df, price_df) = self.select_code_by_price_excel(self.price_in_df, invest_in_df, start, end,
                                                                        strategy_date, comp_size, rim_on, comp_del, BJ_Filter, 2)
                low_per = self.quant.get_value_rank_quarter(invest_df, price_df, start, end, strategy_date, 'PER', None,
                                                            stock_num).dropna()
                temp_df = self.back_test_Beta(price_df, low_per,  start, end, initial_money, money_ratio, tax_on)
            elif strategy_sel == '저PBR':
                invest_in_df = self.make_invest_from_quarter(strategy_date, start)
                # price_in_df = self.pr.DB_LOAD_Price_Data()
                (invest_df, price_df) = self.select_code_by_price_excel(self.price_in_df, invest_in_df, start, end,
                                                                        strategy_date, comp_size,rim_on, comp_del, BJ_Filter, 2)
                low_pbr = self.quant.get_value_rank_quarter(invest_df, price_df, start, end, strategy_date, 'PBR', None,
                                                            stock_num).dropna()
                temp_df = self.back_test_Beta(price_df, low_pbr,  start, end, initial_money, money_ratio, tax_on)
            elif strategy_sel == 'F스코어':
                fs_in_df = self.make_invest_from_quarter(strategy_date, start)
                # price_in_df = self.pr.DB_LOAD_Price_Data()
                (fs_df, price_df) = self.select_code_by_price_excel(self.price_in_df, fs_in_df, start, end, strategy_date,
                                                                    comp_size,rim_on, comp_del, BJ_Filter, 2)
                fs_score = self.quant.get_fscore(fs_df, strategy_date, stock_num)
                temp_df = self.back_test_Beta(price_df, fs_score,  start, end, initial_money, money_ratio, tax_on)
            elif strategy_sel == '모멘텀':
                temp = list(self.price_df.T.dropna().index)
                momentum_price = self.price_df[temp]
                momentum = self.quant.get_momentum_rank(momentum_price, self.price_df[start].index[0], 3,
                                                        stock_num).dropna()
                temp_df = self.back_test_Beta(self.price_df, momentum,  start, end, initial_money, money_ratio, tax_on)
            elif strategy_sel == '마법공식':
                invest_in_df = self.make_invest_from_quarter(strategy_date, start)
                # price_in_df = self.pr.DB_LOAD_Price_Data()
                (invest_df, price_df) = self.select_code_by_price_excel(self.price_in_df, invest_in_df, start, end,
                                                                        strategy_date, comp_size, rim_on, comp_del, BJ_Filter, 2)
                magic = self.quant.get_value_rank_quarter(invest_df, price_df, start, end, strategy_date, '자본수익률',
                                                          '이익수익률', stock_num).dropna()
                temp_df = self.back_test_Beta(price_df, magic,  start, end, initial_money, money_ratio, tax_on)

            elif strategy_sel == 'PER_ROA':
                invest_in_df = self.make_invest_from_quarter(strategy_date, start)
                # price_in_df = self.pr.DB_LOAD_Price_Data()
                (invest_df, price_df) = self.select_code_by_price_excel(self.price_in_df, invest_in_df, start, end,
                                                                        strategy_date, comp_size, rim_on, comp_del, BJ_Filter, 2)
                magic = self.quant.get_value_rank_quarter(invest_df, price_df, start, end, strategy_date, 'PER', 'ROA',
                                                          stock_num).dropna()
                temp_df = self.back_test_Beta(price_df, magic,  start, end, initial_money, money_ratio, tax_on)
            elif strategy_sel == '마법공식2':
                invest_in_df = self.make_invest_from_quarter(strategy_date, start)
                # invest_in_df.to_excel('f:\\invest_in_df.xlsx')
                # price_in_df = self.pr.DB_LOAD_Price_Data()
                (invest_df, price_df) = self.select_code_by_price_excel(self.price_in_df, invest_in_df, start, end,
                                                                        strategy_date, comp_size, rim_on, comp_del, BJ_Filter, 2)
                # invest_df.to_excel('f:\\invest_df.xlsx')
                magic = self.quant.get_value_rank_quarter(invest_df, price_df, start, end, strategy_date, 'PBR', 'GP/A',
                                                          stock_num).dropna()
                # magic.to_excel('f:\\magic.xlsx')
                temp_df = self.back_test_Beta(price_df, magic,  start, end, initial_money, money_ratio, tax_on)
            elif strategy_sel == '슈퍼가치전략':
                invest_in_df = self.make_invest_from_quarter(strategy_date, start)
                # invest_in_df.to_excel('f:\\invest_in_df.xlsx')
                # price_in_df = self.pr.DB_LOAD_Price_Data()
                print(len(invest_in_df),strategy_date, start)
                (invest_df, price_df) = self.select_code_by_price_excel(self.price_in_df, invest_in_df, start, end,
                                                                        strategy_date, comp_size, rim_on, comp_del,
                                                                        BJ_Filter, 2)
                # invest_df.to_excel('f:\\invest_df.xlsx')
                super_value = self.quant.super_value_strategy_by_kang(invest_df, price_df, start, end, strategy_date,
                                                          stock_num).dropna()
                # magic.to_excel('f:\\magic.xlsx')
                temp_df = self.back_test_Beta(price_df, super_value, start, end, initial_money, money_ratio, tax_on)

            elif strategy_sel == 'SJ_LOGIC':
                invest_in_df = self.make_invest_from_quarter(strategy_date, start)
                # price_in_df = self.pr.DB_LOAD_Price_Data()
                (invest_df, price_df) = self.select_code_by_price_excel(self.price_in_df, invest_in_df, start, end,
                                                                        strategy_date, comp_size, rim_on, comp_del, BJ_Filter, 2)
                self.quant.MAX_PBR = 1.8
                self.quant.MIN_ROE = 0.15
                low_per = self.quant.get_value_rank_quarter(invest_df, price_df, start, end, strategy_date, 'PBR',
                                                            'ROE', stock_num).dropna()
                temp_df = self.back_test_Beta(price_df, low_per,  start, end, initial_money, money_ratio, tax_on)
            elif strategy_sel == '정량모멘텀':
                invest_in_df = self.make_invest_from_quarter(strategy_date, start)
                (invest_df, price_df) = self.select_code_by_price_excel(self.price_in_df, invest_in_df, start, end,
                                                                        strategy_date, comp_size, rim_on, comp_del, BJ_Filter, 2)
                fixed_df = self.quant.get_Fixed_Quantity_Momentum(price_df, start, 12)
                temp_df = self.back_test_Beta(price_df, fixed_df,  start, end, initial_money, money_ratio, tax_on)
            elif strategy_sel == '52주_신고가_근접':
                # invest_in_df = self.make_invest_from_quarter(strategy_date, start)
                # price_in_df = self.pr.DB_LOAD_Price_Data()
                # (invest_df, price_df) = self.select_code_by_price_excel(price_in_df, invest_in_df, start, end)
                week_high_52 = self.quant.get_near_52WeeksHighPrice_under(start, stock_num).dropna()
                temp_df = self.back_test_Beta(self.price_in_df, week_high_52,  start, end, initial_money, money_ratio, tax_on)

            elif strategy_sel == '52주_신고가_돌파':
                # invest_in_df = self.make_invest_from_quarter(strategy_date, start)
                # price_in_df = self.pr.DB_LOAD_Price_Data()
                # (invest_df, price_df) = self.select_code_by_price_excel(price_in_df, invest_in_df, start, end)
                week_high_52 = self.quant.get_near_52WeeksHighPrice_upper(start, stock_num).dropna()
                temp_df = self.back_test_Beta(self.price_in_df, week_high_52, initial_money, money_ratio, tax_on)

            elif strategy_sel == '그랜빌_4법칙':
                total = {'code': [], '종목':[]}
                #code_list = self.SQLITE_control.DB_LOAD_Table(stocklist , self.fs.TOTAL_JONGMOK_NAME_TABLE)

                for idx, code in enumerate(self.code_list.index):
                    self.logging.logger.debug("%s / %s :  KOSDAQ Stock Code : %s is updating... " % (idx + 1, len(self.code_list), code))
                    pass_success, price_data_latest = self.quant.Average_Break_Strategy(code.replace('A',""), 120, self.logging, real_trade=False, start = start)
                    if pass_success == True:
                        total['code'].append(code)
                        total['종목'].append(self.code_list.loc[code][1])
                total_df = pd.DataFrame(data = total)
                total_df = total_df.set_index('code')
                if len(total_df) == 0 :
                    pass
                else:
                    temp_df = self.back_test_Beta(self.price_in_df, total_df,  start, end, initial_money, money_ratio, tax_on)
            # Custom_strategy
            elif strategy_sel == '강환국_울트라':
                invest_in_df = self.make_invest_from_quarter(strategy_date, start)
                #print(len(invest_in_df),strategy_date, start)
                (invest_df, price_df) = self.select_code_by_price_excel(self.price_in_df, invest_in_df, start, end,
                                                                        strategy_date, comp_size, rim_on, comp_del,
                                                                        BJ_Filter, 2)
                # invest_df.to_excel('f:\\invest_df.xlsx')

                value_factor=[]
                value_factor.append(['PER',"오름차순",0.2,None])
                value_factor.append(['PBR', "오름차순", 0.2, None])
                value_factor.append(['PFCR', "오름차순", 0.0, None])
                value_factor.append(['GP_A', "내림차순", 0.0, None])
                value_factor.append(['영업이익-차입금_증가비율', "내림차순", None, None])
                value_factor.append(['자산성장률_QOQ', "내림차순", None, None])
                value_factor.append(['영업이익성장률_QOQ', "내림차순", None, None])
                value_factor.append(['지배지분순이익성장률_QOQ', "내림차순", None, None])

                ultra_value = self.quant.ultra_value_strategy_by_kang(invest_df, price_df, start, end, strategy_date, value_factor,
                                                          stock_num).dropna()
                self.logging.logger.debug("%s / %s/ %s/ %s /%s /%s " % (strategy_sel, comp_size, rebal_P, start, end, len(ultra_value)))
                # magic.to_excel('f:\\magic.xlsx')
                temp_df = self.back_test_Beta(price_df, ultra_value, start, end, initial_money, money_ratio, tax_on)

            elif strategy_sel == 'KOSPI':
                if KOSPI_flag == False:
                    #code_list = self.SQLITE_control.DB_LOAD_Table(stocklist , self.fs.TOTAL_JONGMOK_NAME_TABLE, self.fs.DB_TOTAL_JONGMOK_PATH)

                    #code_list = code_list.set_index("Symbol")
                    KOSPI = self.code_list.loc[['ks11']]
                    temp_df = self.back_test_Beta(self.price_in_df, KOSPI, self.start_date, self.end_date, initial_money, money_ratio, tax_on)
                    KOSPI_flag = True  # flag처리하여 리벨런싱 안하도록 처리...

            elif strategy_sel == 'KOSDAQ':
                if KOSDAQ_flag == False:
                    #code_list = self.SQLITE_control.DB_LOAD_Table(stocklist , self.fs.TOTAL_JONGMOK_NAME_TABLE)
                    #price_in_df = self.pr.DB_LOAD_Price_Data()

                    KOSDAQ = self.code_list.loc[['kq11']]
                    temp_df = self.back_test_Beta(self.price_in_df, KOSDAQ, self.start_date, self.end_date, initial_money, money_ratio, tax_on)
                    KOSDAQ_flag = True
                else:
                    pass
            else:
                pass
            if strategy_sel == 'KOSPI' or strategy_sel == 'KOSDAQ':
                REBALANCE_DF = temp_df
            else:
                if i == 0:
                    REBALANCE_DF = temp_df
                    initial_money = temp_df['종합포트폴리오'][-2]
                else:
                    REBALANCE_DF = pd.concat([REBALANCE_DF[:-1], temp_df])
                    initial_money = temp_df['종합포트폴리오'][-2]
        REBALANCE_DF['일변화율'] = REBALANCE_DF['종합포트폴리오'].pct_change()
        REBALANCE_DF['총변화율'] = REBALANCE_DF['종합포트폴리오'] / REBALANCE_DF['종합포트폴리오'][0] - 1
        if strategy_sel == 'KOSPI' or strategy_sel == 'KOSDAQ':
            result = None
        else:
            result = self.get_backtest_result(REBALANCE_DF, self.KOSPI, self.KOSDAQ)
        return (REBALANCE_DF, result)

    def make_result_visualize(self, test, tag):
        # test = test.set_index('년월')
        test['수익률'] = np.array(list(map(lambda x: float(x.replace("%", "")), test['수익률'])))
        test['승률'] = np.array(list(map(lambda x: float(x.replace("%", "")), test['승률'])))
        test['수익종목평균수익률'] = np.array(list(map(lambda x: float(x.replace("%", "")), test['수익종목평균수익률'])))
        test['손실종목평균손실률'] = np.array(list(map(lambda x: float(x.replace("%", "")), test['손실종목평균손실률'])))
        # 수익률 막대챠트
        plt.figure(figsize=(16, 9))
        plt.subplot(2, 2, 1)
        test['수익률'].plot(color='r', label=tag + '_수익률', kind='bar', width=0.8)
        plt.title(tag + "_월별 수익률")
        plt.ylabel('수익률(%)')
        plt.xlabel('월별')

        # 수익률 히스토그램
        plt.subplot(2, 2, 2)
        test['수익률'].plot(color='b', label=tag + '_수익 히스토그램', kind='hist', width=1.5)
        plt.title(tag + "_손익률 분포도")
        plt.ylabel('분포수(개)')
        plt.xlabel('구간(%)')
        # pie chart
        plt.subplot(2, 2, 3)
        label = ['수익', '손실']
        xs = [test['수익종목'][0], test['손실종목'][0]]
        patches, texts, autotexts = plt.pie(
            labels=label,  ## label
            labeldistance=1.0,  ## label이 파이로부터 얼마나 떨어지는가, 1일경우 딱 붙어있음.
            x=xs,  ## 값
            explode=(0.0, 0.0),  ##pie가 튀어나오는지 정해줌
            startangle=90,  ## 어디에서 시작할지, 정해줌
            shadow=False,  ##그림자
            counterclock=False,  ## 시계방향으로 가는지, 시계 반대 방향으로 가는지 정해줌
            autopct='%1.1f%%',  ## pi 위에 표시될 글자 형태, 또한 알아서 %로 변환해서 알려줌
            pctdistance=0.7,  ## pct가 radius 기준으로 어디쯤에 위치할지 정함
            colors=['red', 'blue'],
        )
        ## add circle
        ## 도넛처럼 만들기 위해서 아래처럼
        centre_circle = plt.Circle((0, 0), 0.50, color='white')
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
        # 테이블 삽입 예제
        plt.subplot(2, 2, 4)
        values = [[test.columns[-1], format(test[test.columns[-1]][0], "3.2f")],
                  [test.columns[-2], format(test[test.columns[-2]][0], "3.2f")],
                  [test.columns[-3], str(format(test[test.columns[-3]][0], "3.2f")) + '%'],
                  [test.columns[-4], format(test[test.columns[-4]][0], "10d")],
                  [test.columns[-5], str(format(test[test.columns[-5]][0], "3.2f")) + '%'],
                  [test.columns[-6], str(format(test[test.columns[-6]][0], "3.2f")) + '%']]
        table = plt.table(cellText=values, colWidths=[0.4] * 3, loc='center')
        #plt.show()


if __name__ == "__main__":
    test = BACK_TEST()
    quant = Quant_Strategy()
    #strategy_date = '2015/12'
    test.start_date = '2007-1'
    test.end_date = '2020-12'
    initial_money = 100000000
    plt.figure(figsize=(16, 9))
    plt.subplot(2, 1, 1)
    REF_rebal_P = 12
    # 리밸런스 백테스트
    (test.KOSPI, result_KOSPI) = test.rebal_backtest_excel(initial_money, 'KOSPI', REF_rebal_P,
                                                           BJ_Filter=True, comp_size='TOTAL',
                                                           rim_on=True, comp_del=False, money_ratio=0.0, tax_on=True,
                                                           portpolio=None)
    #test.KOSPI.to_excel('F:\\OneDrive\\EXCEL\\BACKTEST_Quarter_RESULT\\REF_KOSPI.xlsx')
    (test.KOSDAQ, result_KOSPI) = test.rebal_backtest_excel(initial_money, 'KOSDAQ', REF_rebal_P,
                                                            BJ_Filter=True, comp_size='TOTAL',
                                                            rim_on=True, comp_del=False, money_ratio=0.0, tax_on=True,
                                                            portpolio=None)
    #test.KOSDAQ.to_excel('F:\\OneDrive\\EXCEL\\BACKTEST_Quarter_RESULT\\REF_KOSDAQ.xlsx')
    #===================================================================================================================
    # 저PER, F스코어, 마법공식, 밸류콤보, 모멘텀 중 택1
    rebal_P1 = 12
    strategy1 = '강환국_울트라'
    compsize1='소형주'
    portpolio1 = None
    BJ_Filter1 = False
    rim_on1 = True
    comp_del1= True
    (TEST_DF1, RESULT_DF1) = test.rebal_backtest_excel(initial_money, strategy1, rebal_P1,
                                                       BJ_Filter=BJ_Filter1, comp_size=compsize1,
                                                       rim_on=rim_on1, comp_del=comp_del1, money_ratio=0.0,
                                                       money_ratio_method='buy_increase', tax_on=True, portpolio=portpolio1)
    #TEST_DF1.to_excel('F:\\OneDrive - Office 365\\EXCEL\\BACKTEST_RESULT\\TEST_DF1.xlsx')
    #RESULT_DF1.to_excel('F:\\OneDrive - Office 365\\EXCEL\\BACKTEST_Quarter_RESULT\\RESULT_DF1.xlsx')
    TEST_DF1_TAG = strategy1 + compsize1 + str(BJ_Filter1) + str(rim_on1) + str(comp_del1) + str(portpolio1)
    # ==================================================================================================================
    rebal_P2 = 12
    strategy2 = '마법공식'
    compsize2 = '소형주'
    portpolio2 = None
    BJ_Filter2 = False
    rim_on2 = True
    comp_del2 = True
    (TEST_DF2, RESULT_DF2) = test.rebal_backtest_excel(initial_money, strategy2, rebal_P2,
                                                       BJ_Filter=BJ_Filter2, comp_size=compsize2,
                                                       rim_on=rim_on2, comp_del=comp_del2, money_ratio=0.0,
                                                       money_ratio_method='buy_increase', tax_on=True, portpolio=portpolio2)
    #TEST_DF2.to_excel('F:\\OneDrive - Office 365\\EXCEL\\BACKTEST_Quarter_RESULT\\TEST_DF2.xlsx')
    #RESULT_DF2.to_excel('F:\\OneDrive - Office 365\\EXCEL\\BACKTEST_Quarter_RESULT\\RESULT_DF2.xlsx')
    TEST_DF2_TAG = strategy2 + compsize2 + str(BJ_Filter2) + str(rim_on2) + str(comp_del2) + str(portpolio2)
    # ==================================================================================================================
    rebal_P3 = 12
    strategy3 = '마법공식2'
    compsize3 = '소형주'
    portpolio3 = None
    BJ_Filter3 = False
    rim_on3 = True
    comp_del3 = True
    (TEST_DF3, RESULT_DF3) = test.rebal_backtest_excel(initial_money, strategy3, rebal_P3,
                                                       BJ_Filter=BJ_Filter3, comp_size=compsize3,
                                                       rim_on=rim_on3, comp_del=comp_del3, money_ratio=0.0,
                                                       money_ratio_method='buy_increase', tax_on=True, portpolio=portpolio3)
    #RESULT_DF3.to_excel('F:\\OneDrive - Office 365\\EXCEL\\BACKTEST_Quarter_RESULT\\RESULT_DF3.xlsx')
    TEST_DF3_TAG = strategy3 + compsize3 + str(BJ_Filter3) + str(rim_on3) + str(comp_del3) + str(portpolio3)
    # ==================================================================================================================
    rebal_P4 = 12
    strategy4 = '슈퍼가치전략'
    compsize4 = '소형주'
    portpolio4 = None
    BJ_Filter4 = False
    rim_on4 = True
    comp_del4 = True
    (TEST_DF4, RESULT_DF4) = test.rebal_backtest_excel(initial_money, strategy4, rebal_P4,
                                                       BJ_Filter=BJ_Filter4, comp_size=compsize4,
                                                       rim_on=rim_on4, comp_del=comp_del4, money_ratio=0.0,
                                                       money_ratio_method='buy_increase', tax_on=True, portpolio=portpolio4)
    #RESULT_DF4.to_excel('F:\\OneDrive - Office 365\\EXCEL\\BACKTEST_Quarter_RESULT\\RESULT_DF4.xlsx')
    TEST_DF4_TAG = strategy4 + compsize4 + str(BJ_Filter4) + str(rim_on4) + str(comp_del4) + str(portpolio4)
    # ==================================================================================================================
    (test.KOSPI, CAGR_KOSPI) = test.get_mdd_cagr(test.KOSPI)
    (test.KOSDAQ, CAGR_KOSDAQ) = test.get_mdd_cagr(test.KOSDAQ)
    (TEST_DF1, CAGR1) = test.get_mdd_cagr(TEST_DF1)
    (TEST_DF2, CAGR2) = test.get_mdd_cagr(TEST_DF2)
    (TEST_DF3, CAGR3) = test.get_mdd_cagr(TEST_DF3)
    (TEST_DF4, CAGR4) = test.get_mdd_cagr(TEST_DF4)

    test.KOSPI['총변화율'].plot(label='KOSPI' + ' = ' + str(CAGR_KOSPI * 100) + '%')
    test.KOSDAQ['총변화율'].plot(label='KOSDAQ' + ' = ' + str(CAGR_KOSDAQ * 100) + '%')
    TEST_DF1['총변화율'].plot(label=TEST_DF1_TAG + ' = ' + str(CAGR1 * 100) + '%')
    TEST_DF2['총변화율'].plot(label=TEST_DF2_TAG + ' = ' + str(CAGR2 * 100) + '%')
    TEST_DF3['총변화율'].plot(label=TEST_DF3_TAG + ' = ' + str(CAGR3 * 100) + '%')
    TEST_DF4['총변화율'].plot(label=TEST_DF4_TAG + ' = ' + str(CAGR4 * 100) + '%')
    plt.legend()
    plt.subplot(2, 1, 2)
    test.KOSPI['MDD'].plot(label='KOSPI')
    test.KOSDAQ['MDD'].plot(label='KOSDAQ')
    TEST_DF1['MDD'].plot(label=TEST_DF1_TAG)
    TEST_DF2['MDD'].plot(label=TEST_DF2_TAG)
    TEST_DF3['MDD'].plot(label=TEST_DF3_TAG)
    TEST_DF4['MDD'].plot(label=TEST_DF4_TAG)
    plt.legend()
    test.make_result_visualize(RESULT_DF1, 'DF1')
    test.make_result_visualize(RESULT_DF2, 'DF2')
    test.make_result_visualize(RESULT_DF3, 'DF3')
    test.make_result_visualize(RESULT_DF4, 'DF4')
    plt.show()
