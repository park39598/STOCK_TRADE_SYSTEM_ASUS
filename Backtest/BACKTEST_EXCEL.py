# coding: utf-8


import matplotlib.pyplot as plt
from Trade_Algrithm.python_quant import *

class BACK_TEST:
    def __init__(self):
        self.fs = Finance_data()
        self.pr = Price_data()
        self.quant = Quant_Strategy()

    def back_test_Beta(self, price_df, strategy_df, start_date, end_date, initial_money):
        # 전략의 상위종목들 DF의 종목코드를 추려내기
        code_list = []
        for code in strategy_df.index:
            code_list.append(code.replace('A', ''))

        strategy_price = price_df[code_list][start_date:end_date]

        # cash 계산
        pf_stock_num = {}
        stock_amount = 0
        stock_pf = 0
        each_money = initial_money / len(code_list)

        for code in strategy_price.columns:
            temp = int(each_money / float(strategy_price[code][0]))
            pf_stock_num[code] = temp
            stock_amount = stock_amount + temp * int(strategy_price[code][0])
            stock_pf = stock_pf + strategy_price[code].astype('int') * pf_stock_num[code]

        cash_amount = initial_money - stock_amount

        backtest_df = pd.DataFrame({'주식포트폴리오': stock_pf})
        backtest_df['현금포트폴리오'] = cash_amount
        backtest_df['종합포트폴리오'] = backtest_df['주식포트폴리오'] + backtest_df['현금포트폴리오']
        backtest_df['일변화율'] = backtest_df['종합포트폴리오'].pct_change()
        backtest_df['총변화율'] = backtest_df['종합포트폴리오'] / initial_money - 1

        return backtest_df

    def select_code_by_price(self, price_df, data_df, start_date):
        new_code_list = []
        for code in price_df[start_date].iloc[0].dropna().index:
            new_code_list.append('A' + code)

        select_df = data_df.loc[new_code_list]
        return select_df

    def decision_strategy_date(self, start_date):
        start_year = start_date.split('-')[0]
        start_month = start_date.split('-')[1]
        if int(start_month) > 3:
            strategy_date = str(int(start_year) - 1) + '/' + '12'
        else:
            strategy_date = str(int(start_year) - 2) + '/' + '12'

        return strategy_date

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
                invest_df = SQLITE_control.DB_LOAD_Latest_Table(self.fs.DB_FS_EXCEL_PATH)
                low_per = self.quant.get_value_rank(self.select_code_by_price(price_df, invest_df, start), 'PER',
                                                      strategy_date, num).dropna()
                temp_df = self.back_test_Beta(price_df, low_per, start, end, initial_money)
            elif strategy_sel == '저PBR':
                price_df = SQLITE_control.DB_LOAD_Price_Data()
                invest_df = SQLITE_control.DB_LOAD_Latest_Table(self.fs.DB_FS_EXCEL_PATH)
                low_pbr = self.quant.get_value_rank(self.select_code_by_price(price_df, invest_df, start), 'PBR',
                                                      strategy_date, num).dropna()
                temp_df = self.back_test_Beta(price_df, low_pbr, start, end, initial_money)
            elif strategy_sel == 'F스코어':
                price_df = SQLITE_control.DB_LOAD_Price_Data()
                fs_df = SQLITE_control.DB_LOAD_Latest_Table(self.fs.DB_FS_EXCEL_PATH)
                fs_score = self.quant.get_fscore(self.select_code_by_price(price_df, fs_df, start),
                                                   strategy_date, num).dropna()
                temp_df = self.back_test_Beta(price_df, fs_score, start, end, initial_money)
            elif strategy_sel == '모멘텀':
                price_df = SQLITE_control.DB_LOAD_Price_Data()
                temp = list(price_df.T.dropna().index)
                momentum_price = price_df[temp]
                momentum = self.quant.get_momentum_rank(momentum_price, price_df[start_date].index[0], 3,
                                                          num).dropna()
                temp_df = self.back_test_Beta(price_df, momentum, start, end, initial_money)
            elif strategy_sel == '마법공식':
                price_df = SQLITE_control.DB_LOAD_Price_Data()
                invest_df = SQLITE_control.DB_LOAD_Latest_Table(self.fs.DB_FS_EXCEL_PATH)
                fr_df = SQLITE_control.DB_LOAD_Finance_Data(self.fs.DB_FR_WEB_YEAR_PATH)
                magic = self.quant.magic_formula(self.select_code_by_price(price_df, fr_df, start),
                                                   self.select_code_by_price(price_df, invest_df, start),
                                                   strategy_date, num).dropna()
                temp_df = self.back_test_Beta(price_df, magic, start, end, initial_money)
            elif strategy_sel == '밸류콤보':
                price_df = SQLITE_control.DB_LOAD_Price_Data()
                invest_df = SQLITE_control.DB_LOAD_Latest_Table(self.fs.DB_FS_EXCEL_PATH)
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

    def rebal_peri_calc(self, start_date, end_date, rebal_P):
        temp_S_year = start_date.split('-')[0]
        temp_S_month = start_date.split('-')[1]
        temp_E_year = end_date.split('-')[0]
        temp_E_month = end_date.split('-')[1]

        period = 12 * (int(temp_E_year) - int(temp_S_year)) + int(temp_E_month) - int(temp_S_month)
        period_repeat = int(period / rebal_P) + 1

        rebal_peri_list = []
        start_month = temp_S_month
        start_year = temp_S_year
        for i in range(period_repeat):
            if i == period_repeat - 1:
                if start_year == temp_E_year and start_month == temp_E_month:
                    rebal_peri_df = pd.DataFrame(data=rebal_peri_list, columns=['start_time', 'end_date'])

                else:
                    end_month = temp_E_month
                    end_year = temp_E_year
                    start = start_year + '-' + start_month
                    end = end_year + '-' + end_month
                    rebal_peri_list.append([start, end])
                    rebal_peri_df = pd.DataFrame(data=rebal_peri_list, columns=['start_time', 'end_date'])

            else:
                if int(start_month) + rebal_P - 1 > 12:
                    end_month = str(int(start_month) + rebal_P - 12 - 1)
                    end_year = str(int(start_year) + 1)
                else:
                    end_month = str(int(start_month) + rebal_P - 1)
                    end_year = str(int(start_year))
                start = start_year + '-' + start_month
                end = end_year + '-' + end_month
                rebal_peri_list.append([start, end])

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


if __name__ == "__main__":
    test = BACK_TEST()
    quant = Quant_Strategy()
    '''
    fs_path = r'C:\STOCK_TEST\재무제표데이터.xlsx'
    fs_df = quant.get_finance_data(fs_path)
    fr_path = r'C:\STOCK_TEST\재무비율데이터.xlsx'
    fr_df = quant.get_finance_data(fr_path)
    invest_path = r'C:\STOCK_TEST\투자지표데이터.xlsx'
    invest_df = quant.get_finance_data(invest_path)
    price_path = r'C:\STOCK_TEST\가격데이터.xlsx'
    price_df = pd.read_excel(price_path)
    '''

    strategy_date = '2015/12'
    start_date = '2016-6'
    end_date = '2018-5'
    initial_money = 100000000
    rebal_P = 6
    # 저PER, F스코어, 마법공식, 밸류콤보, 모멘텀 중 택1
    strategy = '저PER'
    plt.figure(figsize=(10, 7))
    plt.subplot(2, 1, 1)

    # 리밸런스 백테스트
    TEST_DF = test.rebal_backtest(start_date, end_date, initial_money, strategy, rebal_P)
#    TEST_DF2 = test.rebal_backtest(start_date, end_date, initial_money, 'F스코어', rebal_P)
    TEST_DF3 = test.rebal_backtest(start_date, end_date, initial_money, '마법공식', rebal_P)
    TEST_DF4 = test.rebal_backtest(start_date, end_date, initial_money, '밸류콤보', rebal_P)
    TEST_DF5 = test.rebal_backtest(fr_df, start_date, end_date, initial_money, '모멘텀', rebal_P)
    (TEST_DF, CAGR1) = test.get_mdd_cagr(TEST_DF, start_date, end_date)
#    (TEST_DF2, CAGR2) = test.get_mdd_cagr(TEST_DF2, start_date, end_date)
    (TEST_DF3, CAGR3) = test.get_mdd_cagr(TEST_DF3, start_date, end_date)
    (TEST_DF4, CAGR4) = test.get_mdd_cagr(TEST_DF4, start_date, end_date)
    (TEST_DF5, CAGR5) = test.get_mdd_cagr(TEST_DF5, start_date, end_date)

    TEST_DF['총변화율'].plot(label='low_PER' + ' - ' + str(CAGR1*100) + '%')
 #   TEST_DF2['총변화율'].plot(label='Fscore' + ' - ' + str(CAGR2*100) + '%')
    TEST_DF3['총변화율'].plot(label='magic' + ' - ' + str(CAGR3*100) + '%')
    TEST_DF4['총변화율'].plot(label='value_combo' + ' - ' + str(CAGR4*100) + '%')
    TEST_DF5['총변화율'].plot(label='momentum' + ' - ' + str(CAGR5*100) + '%')
    plt.legend()

    plt.subplot(3, 1, 3)
    TEST_DF['MDD'].plot(label='low_PER')
 #   TEST_DF2['MDD'].plot(label='Fscore')
    TEST_DF3['MDD'].plot(label='magic')
    TEST_DF4['MDD'].plot(label='value_combo')
    TEST_DF5['MDD'].plot(label='momentum')


    plt.legend()
    plt.show()
#    low_pbr = python_quant.get_value_rank(test.select_code_by_price(price_df, invest_df, start_date), 'PBR', strategy_date, 20).dropna()

#    per_backtest = test.back_test_Beta(price_df, low_per, start_date, end_date, initial_money)
#    pbr_backtest = test.back_test_Beta(price_df, low_pbr, start_date, end_date, initial_money)

# PBR 5구간 비교
'''
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
'''
