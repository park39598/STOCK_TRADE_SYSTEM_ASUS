# coding: utf-8

import matplotlib.pyplot as plt
from matplotlib import font_manager, rc
plt.rcParams["axes.unicode_minus"]=False
path="c:\Windows\Fonts\H2GTRM.TTF"
font_name = font_manager.FontProperties(fname=path).get_name()
rc("font", family=font_name)

import calendar
from Trade_Algrithm.python_quant import *



class BACK_TEST:
    def __init__(self):
        self.fs = Finance_data()
        self.pr = Price_data()
        self.quant = Quant_Strategy()
        self.CodebyName_df = SQLITE_control.DB_LOAD_Table(self.fs.TOTAL_JONGMOK_NAME_TABLE, self.fs.DB_TOTAL_JONGMOK_PATH)
        self.CodebyName_df = self.CodebyName_df[['종목']]
        self.prev_strategy_df = pd.DataFrame(data=None)
        self.trans_tax = 0.0033
        #백테스트 도출 변수
        self.plus_jongmok = 0
        self.minus_jongmok = 0
        self.total_trade_num = 0
        self.per_profitSum = 0
        self.per_lossSum = 0
        self.KOSPI = pd.DataFrame()
        self.KOSDAQ = pd.DataFrame()
        self.test_log_on = False

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
        self.total_trade_num = self.total_trade_num + 1
        strategy_price = price_df[strategy_df.index][start_date:end_date].astype('float').dropna() #20/5/24 dropna 추가 가격데이터에 nan값이 끼어져 있는것이 있다
        pf_stock_num = {}
        stock_amount = 0
        stock_pf = 0
        cash_amount = int(initial_money * money_ratio)
        try:
            each_money = (initial_money - cash_amount) / len(strategy_df.index)
        except:
            each_money = 0
        for code in strategy_price.columns:
            temp = int(each_money / float(strategy_price[code][0]))
            pf_stock_num[code] = temp
            if tax_on:
                stock_amount = stock_amount + temp * strategy_price[code][0]*(1-self.trans_tax) #구입시 거래세+수수료 0.33%
            else:
                stock_amount = stock_amount + temp * int(strategy_price[code][0])
            stock_pf = stock_pf + strategy_price[code].astype('int') * pf_stock_num[code] * (1-self.trans_tax)
            jongmok_status_df['START금액'][code] = int(strategy_price[code][0])
            jongmok_status_df['END금액'][code] = int(strategy_price[code][-1])
            jongmok_status_df['수량'][code] = int(pf_stock_num[code])
            jongmok_status_df['손익'][code] = (int(strategy_price[code][-1]) - int(strategy_price[code][0])) * pf_stock_num[code]
            jongmok_status_df['수익률'][code] = ((float(strategy_price[code][-1]) / float(strategy_price[code][0])) - 1)*100
            if jongmok_status_df['수익률'][code] > 0:
                jongmok_status_df['수익종목'][code] = 1
            else:
                jongmok_status_df['손실종목'][code] = 1
            jongmok_status_df['종목명'][code] = self.CodebyName_df.loc[code][0]
        if tax_on:
            cash_amount = initial_money - stock_amount - stock_amount*(self.trans_tax)
            backtest_df = pd.DataFrame({'주식포트폴리오': stock_pf * (1 - self.trans_tax)})
        else:
            cash_amount = initial_money - stock_amount
            backtest_df = pd.DataFrame({'주식포트폴리오': stock_pf})
        self.per_profitSum = self.per_profitSum + jongmok_status_df[jongmok_status_df['수익률'] > 0]['수익률'].sum()
        self.per_lossSum = self.per_lossSum + jongmok_status_df[jongmok_status_df['수익률'] <= 0]['수익률'].sum()
        backtest_df['수수료'] = stock_amount*(self.trans_tax)*2
        backtest_df['현금포트폴리오'] = cash_amount
        backtest_df['종합포트폴리오'] = backtest_df['주식포트폴리오'] + backtest_df['현금포트폴리오']
        backtest_df['일변화율'] = backtest_df['종합포트폴리오'].pct_change()
        backtest_df['총변화율'] = backtest_df['종합포트폴리오'] / initial_money - 1
        backtest_df['cash_ratio'] = money_ratio
        # backtest_log make
        try:
            if strategy_df.columns[1] == '종목':
                self.get_backtest_log(start_date, end_date, strategy_df.index[0], None,
                                      jongmok_status_df, True)
            else:
                self.get_backtest_log(start_date, end_date, strategy_df.columns[0], strategy_df.columns[2], jongmok_status_df, True)
        except:
            self.get_backtest_log(start_date, end_date, strategy_df.columns[0], "_NONE", jongmok_status_df, True)
        return backtest_df
    '''
    def select_code_by_price(self, price_df, data_df, start_date):
        new_code_list = []
        for code in price_df[start_date].iloc[0].dropna().index:
            new_code_list.append('A' + code)
        select_df = data_df.loc[new_code_list]
        return select_df
    '''
    def select_code_by_price_excel(self, price_df, data_df, start_date, end_date, index_date, comp_size,
                                   rim_on=True, fs_comp_del_on=True, BJ_Filter=True, apply_rim_L=2):
        new_code_list = []
        for code in price_df.loc[start_date:end_date].iloc[0].dropna().index:
            new_code_list.append(code)
        select_invest_df = data_df.loc[new_code_list]
        select_price_df = price_df[new_code_list]
        if self.test_log_on == True:
            data_df.to_excel('F:\\test_log\\data_df.xlsx')
        total_comp = int(len(select_invest_df) / 3)
        select_invest_df = select_invest_df[index_date]
        select_invest_df['현재가'] = price_df[start_date:end_date].iloc[0].astype('float')
        try:  #시가총액이 없는 에러때문에
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
        except:
            pass

        if BJ_Filter:
            select_invest_df = select_invest_df[
                (select_invest_df['부채비율(%)'].astype('float') < 200) & (select_invest_df['유보율(%)'].astype('float') > 300) & (
                            select_invest_df['유동비율(%)'].astype('float') > 150)]
            if self.test_log_on: select_invest_df.to_excel('F:\\test_log\\total_df_BJ_Filter.xlsx')
        if rim_on == True:
            select_invest_df = self.quant.RIM_ON(select_invest_df, apply_rim_L)
            if self.test_log_on: select_invest_df.to_excel('F:\\test_log\\total_df_rim_on.xlsx')
            # 금융회사/지주사/중국회사 제외
        if fs_comp_del_on == True:
            select_invest_df = self.quant.Finance_company_del(select_invest_df)
            if self.test_log_on: select_invest_df.to_excel('F:\\test_log\\total_df_fs_comp_del_on.xlsx')

        if self.test_log_on: select_invest_df.to_excel('F:\\test_log\\total_df_copsize_sort.xlsx')
        select_invest_df.columns = [[index_date] * len(select_invest_df.columns), select_invest_df.columns]
        return (select_invest_df, select_price_df)

    def decision_strategy_date(self, start_date):
        start_year = start_date.split('-')[0]
        start_month = start_date.split('-')[1]
        if int(start_month) > 3:
            strategy_date = str(int(start_year) - 1) + '/' + '12'
        else:
            strategy_date = str(int(start_year) - 2) + '/' + '12'
        return strategy_date
    
    def calc_month_enddate(self, date):
        year = int(date.split('-')[0])
        month = int(date.split('-')[1])
        end_date = calendar.monthrange(year, month)[1]
        date = date + '-'+ str(end_date)
        return date

    def rebal_peri_stochastics(self, start_date, end_date, comp_type):
        if comp_type == '소형주':
            rebal_date = SQLITE_control.DB_LOAD_Table(self.pr.KOSDAQ_PRICE_TABLE, self.pr.DB_PRICE_PATH)
        else:
            rebal_date = SQLITE_control.DB_LOAD_Table(self.pr.KOSPI_PRICE_TABLE, self.pr.DB_PRICE_PATH)
        rebal_date.index = pd.to_datetime(rebal_date.index)
        rebal_date = rebal_date[['rebalancing']].dropna()
        rebal_date = rebal_date.loc[start_date:end_date]
        rebal_peri_list = []
        for num in range(1,len(rebal_date.index)):
            if num == len(rebal_date.index):
                rebal_peri_list.append([rebal_date.index[num], end_date, rebal_date.iloc[num][0]])
            else:
                rebal_peri_list.append([rebal_date.index[num-1],rebal_date.index[num],rebal_date.iloc[num-1][0]])
        end_date = self.calc_month_enddate(end_date)
        rebal_peri_list.append([rebal_date.index[-1], end_date, rebal_date.iloc[-1][0]])
        rebal_peri_df = pd.DataFrame(data=rebal_peri_list, columns=['start_time', 'end_date', 'strategy'])
        
        return rebal_peri_df

    def adjust_absolute_momentum(self, start_date, comp_type, cash_ratio, ref_duration = 6):
        test = self.pr.DB_LOAD_Price_Data()
        if comp_type == '소형주' : rebal_date = test[['KOSDAQ']]
        else : rebal_date = test[['KOSPI']]
        #절대모멘텀 1~12개월 가중치 계산
        #1개월 평균 22일 계산...
        if rebal_date.astype('float').pct_change(ref_duration * 22).loc[start_date].iloc[0][0] >= 0 : cash_ratio = 0.0
        else : cash_ratio = 1.0
        return cash_ratio

    def average_momentum_score(self, start_date, comp_type):
        test = self.pr.DB_LOAD_Price_Data()
        if comp_type == '소형주' : rebal_date = test[['KOSDAQ']]
        else : rebal_date = test[['KOSPI']]
        pos = 0
        neg = 0
        for num in range(1, 13):
            if rebal_date.astype('float').pct_change(num*22).loc[start_date].iloc[0][0] >= 0 :
                if num > 7 : pos = pos + 0.5
                else : pos = pos + 1.5
            else :
                if num > 7 : neg = neg + 0.5
                else: neg = neg + 1.5
        cash_ratio = float(neg / 12)
        return cash_ratio

    def average_momentum_score2(self, start_date, comp_type):
        test = self.pr.DB_LOAD_Price_Data()
        if comp_type == '소형주' : rebal_date = test[['KOSDAQ']]
        else : rebal_date = test[['KOSPI']]
        pos = 0
        neg = 0
        range = [1,3,6,9,12]
        for num in range:
            if rebal_date.astype('float').pct_change(num*22).loc[start_date].iloc[0][0] >= 0 : pos = pos + 1
            else : neg = neg + 1
        cash_ratio = float(neg / 5)
        return cash_ratio

    def rebal_peri_calc(self, start_date, end_date, rebal_P):
        temp_S_year = start_date.split('-')[0]
        temp_S_month = start_date.split('-')[1]
        temp_E_year = end_date.split('-')[0]
        temp_E_month = end_date.split('-')[1]
        period = 12 * (int(temp_E_year) - int(temp_S_year)) + int(temp_E_month) - int(temp_S_month) + 1
        period_repeat = int(period / rebal_P)
        rebal_peri_list = []
        start_month = temp_S_month
        start_year = temp_S_year
        for i in range(period_repeat):
            if i == period_repeat - 1:
                if start_year == temp_E_year and start_month == temp_E_month:
                    if rebal_P == 1 :
                        end_month = temp_E_month
                        end_year = temp_E_year
                        start = start_year + '-' + start_month
                        end = end_year + '-' + end_month
                        rebal_peri_list.append([start, end, '매수'])
                        rebal_peri_df = pd.DataFrame(data=rebal_peri_list, columns=['start_time', 'end_date', 'strategy'])
                    else :
                        rebal_peri_df = pd.DataFrame(data=rebal_peri_list, columns=['start_time', 'end_date', 'strategy'])
                else:
                    end_month = temp_E_month
                    end_year = temp_E_year
                    start = start_year + '-' + start_month
                    end = end_year + '-' + end_month
                    rebal_peri_list.append([start, end, '매수'])
                    rebal_peri_df = pd.DataFrame(data=rebal_peri_list, columns=['start_time', 'end_date','strategy'])
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

    def get_mdd_cagr(self, back_test_df, start_date, end_date):
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
        num_of_year = int(end_date.split('-')[0]) - int(start_date.split('-')[0])
        CAGR = (back_test_df.iloc[-1]['종합포트폴리오'] / back_test_df.iloc[0]['종합포트폴리오']) ** (1 / num_of_year) - 1
        return back_test_df, CAGR

    def get_backtest_log(self, start_date, end_date, value_type, quality_type, jongmok_status_df, export_log=True):
        start_date= pd.to_datetime(start_date)
        end_date = pd.to_datetime(end_date)
        self.plus_jongmok = self.plus_jongmok + jongmok_status_df['수익종목'].astype('int').sum()
        self.minus_jongmok = self.minus_jongmok + jongmok_status_df['손실종목'].astype('int').sum()
        if export_log:
            if (value_type == 'KOSPI') or (value_type == 'KOSDAQ'):
                log_name = str(value_type.replace("/", "_")) + '_' + '_' + str(start_date.year) + str(start_date.month) + '_' + str(end_date.year) + str(end_date.month) + '.xlsx'
            else:
                log_name = str(value_type.replace("/","_")) + '_' + str(quality_type.replace("/","_")) + '_' + str(start_date.year) + str(start_date.month)+'_' + str(end_date.year) + str(end_date.month) + '.xlsx'
            cols = jongmok_status_df.columns.tolist()
            cols = cols[-1:] + cols[:-1]
            jongmok_status_df = jongmok_status_df[cols]
            jongmok_status_df.to_excel(self.fs.Backtest_Log_Path + log_name)
        return
    
    def make_invest_from_year(self, index_date, start_date):
        total_df = SQLITE_control.DB_LOAD_Table(index_date, self.fs.DB_FS_YEAR_PATH, True)
        total_df = total_df[index_date]
        #total_df['ROE'] = total_df['지배지분 순이익'].astype("float") / total_df['지배주주지분'].replace(0, 1).astype("float")
        total_df['주식수'] = total_df['시가총액'].astype("float") * 100000000 / total_df['주가'].replace(0, 1).astype("float")
        total_df['수정BPS'] = (total_df['지배주주지분'].astype("float") - total_df['무형자산'].astype("float")) * 100000000 / \
                            total_df['주식수'].replace(0, 1).astype("float")
        total_df['재고회전율(%)'] = (total_df['매출액'].astype("float") / total_df['재고자산'].replace(0, 1).astype(
            "float")) * 100
        total_df['부채비율(%)'] = (total_df['부채총계'].astype("float") / total_df['지배주주지분'].replace(0, 1).astype(
            "float")) * 100
        total_df['유동비율(%)'] = (total_df['유동자산'].astype("float") / total_df['유동부채'].replace(0, 1).astype("float")) * 100
        total_df['유보율(%)'] = ((total_df['자본잉여금'].astype("float") + total_df['이익잉여금'].astype("float")) / total_df[
            '자본금'].replace(0, 1).astype("float")) * 100
        total_df['현금성자산'] = total_df['유동자산'].astype("float") - total_df['매출채권'].astype("float") - total_df[
            '재고자산'].astype("float")
        total_df['단기금융부채'] = total_df['단기사채'].astype("float") + total_df['단기차입금'].astype("float") + total_df[
            '유동성장기부채'].astype("float")
        total_df['장기금융부채'] = total_df['사채'].astype("float") + total_df['장기차입금'].astype("float") + total_df[
            '장기금융부채'].astype("float")
        total_df['순현금'] = total_df['현금성자산'].astype("float") - (
                    total_df['단기금융부채'].astype("float") + total_df['장기금융부채'].astype("float"))
        # 할인율 LOAD
        expect_profit_df = SQLITE_control.DB_LOAD_Table(self.fs.EXPECT_PROFIT_TABLE, self.fs.DB_EXPECT_PROFIT_PATH, False)
        expect_profit_df.index = pd.to_datetime(expect_profit_df.index)
        try:
            expect_profit_mean = expect_profit_df.loc[str(start_date)].mean()
            total_df['할인율'] = expect_profit_mean['수익률(%)'] * 100
        except:
            total_df['할인율'] = 8.0
        total_df['RIM'] = total_df['수정BPS'] + (
                    total_df['BPS'].astype('float') * (total_df['RIM_ROE'].astype('float') - total_df['할인율']) / total_df['할인율'])
        total_df['RIM_L1'] = total_df['수정BPS'] + (
                    total_df['BPS'].astype('float') * (total_df['RIM_ROE'].astype('float') * self.fs.rim_L1 - total_df['할인율']) / (
                        1 + total_df['할인율'] - self.fs.rim_L1))
        total_df['RIM_L2'] = total_df['수정BPS'] + (
                    total_df['BPS'].astype('float') * (total_df['RIM_ROE'].astype('float') * self.fs.rim_L2 - total_df['할인율']) / (
                        1 + total_df['할인율'] - self.fs.rim_L2))
        total_df.columns = [[index_date]*len(total_df.columns), total_df.columns]
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
            profitability.append(str(((data[index_month]['종합포트폴리오'].iloc[-1] / data[index_month]['종합포트폴리오'].iloc[0])-1)*100)+'%')
            if start_month == 12:
                start_month = 1
                start_year = start_year + 1
            else:
                start_month = start_month + 1
        result = {'년월' : period, '수익률': profitability}
        result_backtest = pd.DataFrame(result)
        result_backtest = result_backtest.set_index('년월')
        result_backtest['수익종목'] = self.plus_jongmok
        result_backtest['손실종목'] = self.minus_jongmok
        result_backtest['승률'] = str(self.plus_jongmok*100 / (self.plus_jongmok + self.minus_jongmok)) + '%'
        result_backtest['수익종목평균수익률'] = str(self.per_profitSum / self.plus_jongmok) + '%'
        result_backtest['손실종목평균손실률'] = str(self.per_lossSum / self.minus_jongmok) + '%'
        result_backtest['총 매매횟수'] = self.total_trade_num
        temp = np.array(list(map(lambda x : float(x.replace("%","")), result_backtest['수익률'])))
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

    def rebal_backtest_excel(self, start_date, end_date, initial_money, strategy_sel, rebal_P, comp_size ='TOTAL', rim_on=True,
                             comp_del=True, BJ_Filter=True, money_ratio=0.0, money_ratio_method ='buy_increase', tax_on=True, portpolio = None):
        #리밸런싱 결과 변수 초기화
        self.plus_jongmok = 0
        self.minus_jongmok = 0
        self.total_trade_num = 0
        self.per_profitSum = 0
        self.per_lossSum = 0
        price_in_df = self.pr.DB_LOAD_Price_Data()
        if portpolio == '스토캐스틱':
            Rebalance_selections = self.rebal_peri_stochastics(start_date, end_date, comp_size)
        else:
            Rebalance_selections = self.rebal_peri_calc(start_date, end_date, rebal_P)
        Rebalance_selections.to_excel('f:\\'+strategy_sel+'.xlsx')
        REBALANCE_DF = pd.DataFrame(data=None)
        KOSPI_flag = False
        KOSDAQ_flag = False
        for i in range(len(Rebalance_selections)):
            start = Rebalance_selections.iloc[i][0]
            end = Rebalance_selections.iloc[i][1]
            if portpolio == '스토캐스틱':
                money_ratio = self.cash_ratio_adjust_algorithm(money_ratio, Rebalance_selections.iloc[i][2], money_ratio_method)
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
                invest_in_df = self.make_invest_from_year(strategy_date, start)
                #price_in_df = self.pr.DB_LOAD_Price_Data()
                (invest_df, price_df) = self.select_code_by_price_excel(price_in_df, invest_in_df, start, end, strategy_date, comp_size)
                low_per = self.quant.get_value_rank_year(invest_df, price_df, start, end, strategy_date, 'PER', None, stock_num,
                                                          rim_on, comp_del, BJ_Filter, 2).dropna()
                temp_df = self.back_test_Beta(price_df, low_per, start, end, initial_money, money_ratio, tax_on)
            elif strategy_sel == '저PBR':
                invest_in_df = self.make_invest_from_year(strategy_date, start)
                #price_in_df = self.pr.DB_LOAD_Price_Data()
                (invest_df, price_df) = self.select_code_by_price_excel(price_in_df, invest_in_df, start, end, strategy_date, comp_size)
                low_pbr = self.quant.get_value_rank_year(invest_df, price_df, start, end, strategy_date, 'PBR', None, stock_num,
                                                          rim_on, comp_del, BJ_Filter, 2).dropna()
                temp_df = self.back_test_Beta(price_df, low_pbr, start, end, initial_money, money_ratio, tax_on)
            elif strategy_sel == 'F스코어':
                fs_in_df = self.make_invest_from_year(strategy_date, start)
                #price_in_df = self.pr.DB_LOAD_Price_Data()
                (fs_df, price_df) = self.select_code_by_price_excel(price_in_df, fs_in_df, start, end, strategy_date, comp_size)
                fs_score = self.quant.get_fscore(fs_df, price_df, strategy_date, stock_num, start, 'past')
                temp_df = self.back_test_Beta(price_df, fs_score, start, end, initial_money, money_ratio, tax_on)
            elif strategy_sel == '모멘텀':
                temp = list(self.price_df.T.dropna().index)
                momentum_price = self.price_df[temp]
                momentum = self.quant.get_momentum_rank(momentum_price, self.price_df[start_date].index[0], 3,
                                                        stock_num).dropna()
                temp_df = self.back_test_Beta(self.price_df, momentum, start, end, initial_money, money_ratio, tax_on)
            elif strategy_sel == '마법공식':

                invest_in_df = self.make_invest_from_year(strategy_date, start)
                #price_in_df = self.pr.DB_LOAD_Price_Data()
                (invest_df, price_df) = self.select_code_by_price_excel(price_in_df, invest_in_df, start, end, strategy_date, comp_size)
                magic = self.quant.get_value_rank_year(invest_df, price_df, start, end, strategy_date, '자본수익률', '이익수익률', stock_num,
                                                        rim_on, comp_del, BJ_Filter, 2).dropna()
                temp_df = self.back_test_Beta(price_df, magic, start, end, initial_money, money_ratio, tax_on)
            elif strategy_sel == 'PER_ROA':
                invest_in_df = self.make_invest_from_year(strategy_date, start)
                #price_in_df = self.pr.DB_LOAD_Price_Data()
                (invest_df, price_df) = self.select_code_by_price_excel(price_in_df, invest_in_df, start, end, strategy_date, comp_size)
                magic = self.quant.get_value_rank_year(invest_df, price_df, start, end, strategy_date, 'PER', 'ROA', stock_num,
                                                        rim_on, comp_del, BJ_Filter, 2).dropna()
                temp_df = self.back_test_Beta(price_df, magic, start, end, initial_money, money_ratio, tax_on)

            elif strategy_sel == '마법공식2':
                start_time = time.time()
                invest_in_df = self.make_invest_from_year(strategy_date, start)
                print('make_invest_from_year : %f 초' % (time.time() - start_time))
                start_time = time.time()
                #price_in_df = self.pr.DB_LOAD_Price_Data()
                print('DB_LOAD_Price_Data : %f 초' % (time.time() - start_time))
                start_time = time.time()
                (invest_df, price_df) = self.select_code_by_price_excel(price_in_df, invest_in_df, start, end, strategy_date, comp_size)
                print('select_code_by_price_excel : %f 초' % (time.time() - start_time))
                if self.test_log_on == True:
                    invest_df.to_excel('F:\\test_log\\invest_df_rebal.xlsx')
                    price_df.to_excel('F:\\test_log\\price_df_rebal.xlsx')
                start_time = time.time()
                magic = self.quant.get_value_rank_year(invest_df, price_df, start, end, strategy_date, 'PBR', 'GP/A', stock_num,
                                                        rim_on, comp_del, BJ_Filter, 2).dropna()
                print('get_value_rank : %f 초' % (time.time() - start_time))
                if self.test_log_on == True:
                    magic.to_excel('F:\\test_log\\magic.xlsx')
                start_time = time.time()
                temp_df = self.back_test_Beta(price_df, magic, start, end, initial_money, money_ratio, tax_on)
                print('back_test_Beta : %f 초' % (time.time() - start_time))
            elif strategy_sel == 'SJ_LOGIC':
                invest_in_df = self.make_invest_from_year(strategy_date, start)
                #price_in_df = self.pr.DB_LOAD_Price_Data()
                (invest_df, price_df) = self.select_code_by_price_excel(price_in_df, invest_in_df, start, end, strategy_date, comp_size)
                self.quant.MAX_PBR = 1.8
                self.quant.MIN_ROE = 0.15
                low_per = self.quant.get_value_rank(invest_df, price_df, start, end, strategy_date, 'PBR', 'ROE', stock_num,
                                                          rim_on, comp_del, BJ_Filter, 2).dropna()
                temp_df = self.back_test_Beta(price_df, low_per, start, end, initial_money, money_ratio, tax_on)
            elif strategy_sel == '정량모멘텀':
                invest_in_df = self.make_invest_from_year(strategy_date, start)
                (invest_df, price_df) = self.select_code_by_price_excel(price_in_df, invest_in_df, start, end, strategy_date,
                                                                        comp_size)
                fixed_df = self.quant.get_Fixed_Quantity_Momentum(price_df, start_date, 12)
                temp_df = self.back_test_Beta(price_df, fixed_df, start, end, initial_money, money_ratio, tax_on)
            elif strategy_sel == 'KOSPI':
                if KOSPI_flag == False:
                    code_list = SQLITE_control.DB_LOAD_Table(self.fs.TOTAL_JONGMOK_NAME_TABLE, self.fs.DB_TOTAL_JONGMOK_PATH)
                    #price_in_df = self.pr.DB_LOAD_Price_Data()
                    KOSPI =code_list.loc[['KOSPI']]
                    temp_df = self.back_test_Beta(price_in_df, KOSPI, start_date, end_date, initial_money, 0.0, tax_on)
                    KOSPI_flag = True  # flag처리하여 리벨런싱 안하도록 처리...

            elif strategy_sel == 'KOSDAQ':
                if KOSDAQ_flag == False:
                    code_list = SQLITE_control.DB_LOAD_Table(self.fs.TOTAL_JONGMOK_NAME_TABLE, self.fs.DB_TOTAL_JONGMOK_PATH)
                    #price_in_df = self.pr.DB_LOAD_Price_Data()
                    KOSDAQ = code_list.loc[['KOSDAQ']]
                    temp_df = self.back_test_Beta(price_in_df, KOSDAQ, start_date, end_date, initial_money, 0.0, tax_on)
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
        #test = test.set_index('년월')
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
        plt.show()

if __name__ == "__main__":
    
    test = BACK_TEST()
    quant = Quant_Strategy()
    strategy_date = '2015/12'
    start_date = '2002-2'
    end_date = '2020-5'
    initial_money = 100000000
    rebal_P = 3
    # 저PER, F스코어, 마법공식, 밸류콤보, 모멘텀 중 택1
    strategy = '정량모멘텀'
    plt.figure(figsize=(16, 9))
    plt.subplot(2, 1, 1)
    # 리밸런스 백테스트
    (test.KOSPI, result_KOSPI) = test.rebal_backtest_excel(start_date, end_date, initial_money, 'KOSPI', rebal_P, BJ_Filter=True, comp_size='TOTAL',
                                         rim_on=True, comp_del=False, money_ratio = 0.0, tax_on=True, portpolio=None)
    test.KOSPI.to_excel('F:\\OneDrive - Moedog, Inc\\EXCEL\\BACKTEST_RESULT\\REF_KOSPI.xlsx')

    (test.KOSDAQ, result_KOSPI) = test.rebal_backtest_excel(start_date, end_date, initial_money, 'KOSDAQ', rebal_P, BJ_Filter=True, comp_size='TOTAL',
                                         rim_on=True, comp_del=False, money_ratio = 0.0, tax_on=True, portpolio=None)
    test.KOSDAQ.to_excel('f:\\OneDrive - Moedog, Inc\\EXCEL\\BACKTEST_RESULT\\REF_KOSDAQ.xlsx')

    (TEST_DF1, RESULT_DF1) = test.rebal_backtest_excel(start_date, end_date, initial_money, strategy, rebal_P, BJ_Filter=True, comp_size='소형주',
                                         rim_on=True, comp_del=True, money_ratio = 0.0, money_ratio_method = 'buy_increase', tax_on=True, portpolio=None)
    TEST_DF1.to_excel('f:\\OneDrive - Moedog, Inc\\EXCEL\\BACKTEST_RESULT\\TEST_DF1.xlsx')
    RESULT_DF1.to_excel('f:\\OneDrive - Moedog, Inc\\EXCEL\\BACKTEST_RESULT\\RESULT_DF1.xlsx')

    (TEST_DF2, RESULT_DF2) = test.rebal_backtest_excel(start_date, end_date, initial_money, strategy, rebal_P, BJ_Filter=True, comp_size='대형주',
                                         rim_on=True, comp_del=True, money_ratio = 0.0, money_ratio_method = 'buy_increase', tax_on=True, portpolio=None)
    TEST_DF2.to_excel('f:\\OneDrive - Moedog, Inc\\EXCEL\\BACKTEST_RESULT\\TEST_DF2.xlsx')
    RESULT_DF2.to_excel('f:\\OneDrive - Moedog, Inc\\EXCEL\\BACKTEST_RESULT\\RESULT_DF2.xlsx')
    '''
    (TEST_DF3, RESULT_DF3) = test.rebal_backtest_excel(start_date, end_date, initial_money, strategy, rebal_P, BJ_Filter=True, comp_size='대형주',
                                         rim_on=True, comp_del=True, money_ratio = 0.0, money_ratio_method = 'buy_increase', tax_on=True, portpolio=None)
    TEST_DF3.to_excel('f:\\OneDrive - Moedog, Inc\\EXCEL\\BACKTEST_RESULT\\TEST_DF3.xlsx')
    RESULT_DF3.to_excel('f:\\OneDrive - Moedog, Inc\\EXCEL\\BACKTEST_RESULT\\RESULT_DF3.xlsx')
    
    (TEST_DF4, RESULT_DF4) = test.rebal_backtest_excel(start_date, end_date, initial_money, '마법공식2', 9, BJ_Filter=True, comp_size='소형주',
                                         rim_on=True, comp_del=True, money_ratio = 0.0, money_ratio_method = 'buy_decrease', tax_on=True, portpolio=None)
    TEST_DF4.to_excel('f:\\OneDrive - Moedog, Inc\\EXCEL\\BACKTEST_RESULT\\TEST_DF4.xlsx')
    RESULT_DF4.to_excel('f:\\OneDrive - Moedog, Inc\\EXCEL\\BACKTEST_RESULT\\RESULT_DF4.xlsx')

    (TEST_DF5, RESULT_DF5) = test.rebal_backtest_excel(start_date, end_date, initial_money, '마법공식2', 12, BJ_Filter=True, comp_size='소형주',
                                         rim_on=True, comp_del=True, money_ratio=0.0, money_ratio_method = 'buy_increase', tax_on=True, portpolio=None)
    TEST_DF5.to_excel('f:\\OneDrive - Moedog, Inc\\EXCEL\\BACKTEST_RESULT\\TEST_DF5.xlsx')
    RESULT_DF5.to_excel('f:\\OneDrive - Moedog, Inc\\EXCEL\\BACKTEST_RESULT\\RESULT_DF5.xlsx')
    
    TEST_DF6 = test.rebal_backtest_excel(start_date, end_date, initial_money, '마법공식2', 6, BJ_Filter=True, comp_size='대형주',
                                         rim_on=True, comp_del=True, money_ratio=0.0, money_ratio_method = 'buy_decrease', tax_on=True, portpolio='스토캐스틱')
    RESULT_DF6 = test.get_backtest_result(TEST_DF6, REF_KOSPI, REF_KOSDAQ)
    TEST_DF6.to_excel('f:\\OneDrive - Moedog, Inc\\EXCEL\\BACKTEST_RESULT\\TEST_DF6.xlsx')
    '''
    (test.KOSPI, CAGR_KOSPI) = test.get_mdd_cagr(test.KOSPI, start_date, end_date)
    (test.KOSDAQ, CAGR_KOSDAQ) = test.get_mdd_cagr(test.KOSDAQ, start_date, end_date)
    (TEST_DF1, CAGR1) = test.get_mdd_cagr(TEST_DF1, start_date, end_date)
    (TEST_DF2, CAGR2) = test.get_mdd_cagr(TEST_DF2, start_date, end_date)
    '''
    (TEST_DF3, CAGR3) = test.get_mdd_cagr(TEST_DF3, start_date, end_date)    
    (TEST_DF4, CAGR4) = test.get_mdd_cagr(TEST_DF4, start_date, end_date)
    (TEST_DF5, CAGR5) = test.get_mdd_cagr(TEST_DF5, start_date, end_date)
#    (TEST_DF6, CAGR6) = test.get_mdd_cagr(TEST_DF6, start_date, end_date)
    '''
    test.KOSPI['총변화율'].plot(label='KOSPI' + ' = ' + str(CAGR_KOSPI * 100) + '%')
    test.KOSDAQ['총변화율'].plot(label='KOSDAQ' + ' = ' + str(CAGR_KOSDAQ * 100) + '%')
    TEST_DF1['총변화율'].plot(label='소형주' + ' = ' + str(CAGR1 * 100) + '%')
    TEST_DF2['총변화율'].plot(label='대형주' + ' = ' + str(CAGR2 * 100) + '%')
    '''
    TEST_DF3['총변화율'].plot(label='average_momentum2' + ' = ' + str(CAGR3 * 100) + '%')    
    TEST_DF4['총변화율'].plot(label='마법공식2_소형_9' + ' = ' + str(CAGR4 * 100) + '%')
    TEST_DF5['총변화율'].plot(label='마법공식2_소형_12' + ' = ' + str(CAGR5 * 100) + '%')
#    TEST_DF6['총변화율'].plot(label='마법공식2_소형_buy_decrease_6' + ' = ' + str(CAGR6 * 100) + '%')
    '''
    plt.legend()
    plt.subplot(2, 1, 2)
    test.KOSPI['MDD'].plot(label='KOSPI')
    test.KOSDAQ['MDD'].plot(label='KOSDAQ')
    TEST_DF1['MDD'].plot(label='소형주')
    TEST_DF2['MDD'].plot(label='대형주')
    '''
    TEST_DF3['MDD'].plot(label='average_momentum2')    
    TEST_DF4['MDD'].plot(label='마법공식2_소형_9')
    TEST_DF5['MDD'].plot(label='마법공식2_소형_12')
#    TEST_DF6['MDD'].plot(label='마법공식2_소형_buy_decrease_6')
    '''
    plt.legend()
    test.make_result_visualize(RESULT_DF1, 'DF1')
    test.make_result_visualize(RESULT_DF2, 'DF2')
    plt.show()
    '''
    test.make_result_visualize(RESULT_DF3, 'DF3')
    test.make_result_visualize(RESULT_DF3, 'DF3')
    test.make_result_visualize(RESULT_DF4, 'DF4')
    test.make_result_visualize(RESULT_DF5, 'DF5')
    plt.show()
    '''
    '''
        fs_path = r'C:\STOCK_TEST\재무제표데이터.xlsx'
        fs_df = quant.get_finance_data(fs_path)
        fr_path = r'C:\STOCK_TEST\재무비율데이터.xlsx'
        fr_df = quant.get_finance_data(fr_path)
        invest_path = r'C:\STOCK_TEST\투자지표데이터.xlsx'
        invest_df = quant.get_finance_data(invest_path)
        price_path = r'C:\STOCK_TEST\가격데이터.xlsx'
        price_df = pd.read_excel(price_path)      
        TEST_DF3 = test.rebal_backtest_excel(start_date, end_date, initial_money, '마법공식', rebal_P)
        (TEST_DF3, CAGR3) = test.get_mdd_cagr(TEST_DF3, start_date, end_date)
        #    TEST_DF2 = test.rebal_backtest(start_date, end_date, initial_money, 'F스코어', rebal_P)
        TEST_DF4 = test.rebal_backtest_excel(start_date, end_date, initial_money, '밸류콤보', rebal_P)
        #    TEST_DF5 = test.rebal_backtest(start_date, end_date, initial_money, '모멘텀', rebal_P)
        (TEST_DF4, CAGR4) = test.get_mdd_cagr(TEST_DF4, start_date, end_date)
        #    (TEST_DF5, CAGR5) = test.get_mdd_cagr(TEST_DF5, start_date, end_date)
        TEST_DF['총변화율'].plot(label='low_PER' + ' = ' + str(CAGR1 * 100) + '%')
        TEST_DF3['총변화율'].plot(label='magic' + ' = ' + str(CAGR3 * 100) + '%')
        TEST_DF4['총변화율'].plot(label='value_combo' + ' = ' + str(CAGR4 * 100) + '%')
        #    TEST_DF5['총변화율'].plot(label='momentum' + ' = ' + str(CAGR5 * 100) + '%')
        #    TEST_DF5['MDD'].plot(label='momentum')
        #    (TEST_DF2, CAGR2) = test.get_mdd_cagr(TEST_DF2, start_date, end_date)
        #
        plt.legend()
        plt.subplot(3, 1, 3)
        TEST_DF['MDD'].plot(label='low_PER')
        TEST_DF3['MDD'].plot(label='magic')
        TEST_DF4['MDD'].plot(label='value_combo')
        plt.legend()
        plt.show()
        #   TEST_DF2['총변화율'].plot(label='Fscore' + ' - ' + str(CAGR2*100) + '%')
        #
        #   TEST_DF2['MDD'].plot(label='Fscore')
        #
  
    
    #    low_pbr = python_quant.get_value_rank(test.select_code_by_price(price_df, invest_df, start_date), 'PBR', strategy_date, 20).dropna()
    #    per_backtest = test.back_test_Beta(price_df, low_per, start_date, end_date, initial_money)
    #    pbr_backtest = test.back_test_Beta(price_df, low_pbr, start_date, end_date, initial_money)
    # PBR 5구간 비교
    
    
        low_per = python_quant.get_value_rank(test.select_code_by_price(price_df, invest_df, start_date), 'PER', strategy_date, 20).dropna()
        low_per = python_quant.get_value_rank(test.select_code_by_price(price_df, invest_df, start_date), 'PER',
                                              strategy_date, 20).dropna()
        TEST_DF2 = test.back_test_Beta(price_df, low_per, start_date, end_date, initial_money)
        pbr_all = python_quant.get_value_rank(test.select_code_by_price(price_df, invest_df, start_date), 'PBR', strategy_date, None).dropna()
        length_pbr = int(len(pbr_all)/ 5)
        pbr1_backtest = test.back_test_Beta(price_df, pbr_all[:length_pbr], start_date, end_date, initial_money)
        pbr2_backtest = test.back_test_Beta(price_df, pbr_all[length_pbr:length_pbr*2], start_date, end_date, initial_money)
        pbr3_backtest = test.back_test_Beta(price_df, pbr_all[length_pbr*2:length_pbr*3], start_date, end_date, initial_money)
        pbr4_backtest = test.back_test_Beta(price_df, pbr_all[length_pbr*3:length_pbr*4], start_date, end_date, initial_money)
        pbr5_backtest = test.back_test_Beta(price_df, pbr_all[length_pbr*4:length_pbr*5], start_date, end_date, initial_money)
        pbr1_backtest['총변화율'].plot(label='PBR1')
        pbr2_backtest['총변화율'].plot(label='PBR2')
        pbr3_backtest['총변화율'].plot(label='PBR3')
        pbr4_backtest['총변화율'].plot(label='PBR4')
        pbr5_backtest['총변화율'].plot(label='PBR5')
        def rebal_backtest(self, start_date, end_date, initial_money, strategy_sel, rebal_P):
        Rebalance_selections = self.rebal_peri_calc(start_date, end_date, rebal_P)
        REBALANCE_DF = pd.DataFrame(data=None)
        for i in range(len(Rebalance_selections)):
            start = Rebalance_selections.iloc[i][0]
            end = Rebalance_selections.iloc[i][1]
            strategy_date = self.decision_strategy_date(start)
            num = 20
            if strategy_sel == '저PER':
                price_df = SQLITE_control.DB_LOAD_Price_Data()
                invest_df = SQLITE_control.DB_LOAD_Finance_Data(self.fs.DB_INVEST_WEB_YEAR_PATH)
                low_per = self.quant.get_value_rank(self.select_code_by_price(price_df, invest_df, start), 'PER',
                                                    strategy_date, num).dropna()
                temp_df = self.back_test_Beta(price_df, low_per, start, end, initial_money)
            elif strategy_sel == '저PBR':
                price_df = SQLITE_control.DB_LOAD_Price_Data()
                invest_df = SQLITE_control.DB_LOAD_Finance_Data(self.fs.DB_INVEST_WEB_YEAR_PATH)
                low_pbr = self.quant.get_value_rank(self.select_code_by_price(price_df, invest_df, start), 'PBR',
                                                    strategy_date, num).dropna()
                temp_df = self.back_test_Beta(price_df, low_pbr, start, end, initial_money)
            elif strategy_sel == 'F스코어':
                price_df = SQLITE_control.DB_LOAD_Price_Data()
                fs_df = SQLITE_control.DB_LOAD_Finance_Data(self.fs.DB_FS_WEB_YEAR_PATH)
                fs_score = self.quant.get_fscore(self.select_code_by_price(price_df, fs_df, start),
                                                 strategy_date, num)
                temp_df = self.back_test_Beta(price_df, fs_score, start, end, initial_money)
            elif strategy_sel == '모멘텀':
                price_df = SQLITE_control.DB_LOAD_Price_Data()
                temp = list(price_df.T.dropna().index)
                momentum_price = price_df[temp]
                momentum = self.quant.get_momentum_rank(momentum_price, price_df[start_date].index[0], 3,
                                                        num)
                temp_df = self.back_test_Beta(price_df, momentum, start, end, initial_money)
            elif strategy_sel == '마법공식':
                price_df = SQLITE_control.DB_LOAD_Price_Data()
                invest_df = SQLITE_control.DB_LOAD_Finance_Data(self.fs.DB_INVEST_WEB_YEAR_PATH)
                fr_df = SQLITE_control.DB_LOAD_Finance_Data(self.fs.DB_FR_WEB_YEAR_PATH)
                magic = self.quant.magic_formula(self.select_code_by_price(price_df, fr_df, start),
                                                 self.select_code_by_price(price_df, invest_df, start),
                                                 strategy_date, num)
                temp_df = self.back_test_Beta(price_df, magic, start, end, initial_money)

            elif strategy_sel == '밸류콤보':
                price_df = SQLITE_control.DB_LOAD_Price_Data()
                invest_df = SQLITE_control.DB_LOAD_Finance_Data(self.fs.DB_INVEST_WEB_YEAR_PATH)
                value_list = ['PER', 'PBR']
                combo = self.quant.make_value_combo(value_list, self.select_code_by_price(price_df, invest_df,
                                                                                          start), strategy_date, num)
                temp_df = self.back_test_Beta(price_df, combo, start, end, initial_money)
            else:
                pass
            REBALANCE_DF = pd.concat([REBALANCE_DF[:-1], temp_df])
            initial_money = temp_df['종합포트폴리오'][-1]
        REBALANCE_DF['일변화율'] = REBALANCE_DF['종합포트폴리오'].pct_change()
        REBALANCE_DF['총변화율'] = REBALANCE_DF['종합포트폴리오'] / REBALANCE_DF['종합포트폴리오'][0] - 1
        return REBALANCE_DF   
    '''
