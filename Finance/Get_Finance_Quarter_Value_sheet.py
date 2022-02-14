import xlwings as xw
from multiprocessing import Pool
import pandas as pd
import DataBase.MySQL_control
import re
import numpy as np
import tqdm

thread_num = 4



class GET_EXCEL_DATA():
    def __init__(self, path):
        xw.Book(path).set_mock_caller()
        self.wb = xw.Book.caller()
        self.DB = DataBase.MySQL_control.DB_control()
        self.관심종목 = self.wb.sheets['관심종목']
        self.업종 = self.wb.sheets['업종']
        self.종합 = self.wb.sheets['종합']
        self.Value = self.wb.sheets['Value']
        self.차트 = self.wb.sheets['차트']
        self.재무제표 = self.wb.sheets['재무제표']
        self.가치평가 = self.wb.sheets['가치평가']
        self.total_dict = {}
        self.DB_Industry = "stocks_industry_list"
        self.DB_Thema = "stocks_thema_list"
        self.DB_Value = "stocks_value_list"
        self.DB_Finance="stocks_finance"
        self.title=re.findall('\d+',path)[-1]

    '''
    def main(self):
        wb = xw.Book.caller()
        sheet = wb.sheets['관심종목']
        sheet["A5"].value = "xlwings 모듈 test"
        sheet["A6"].value = "투손플레이스"
    '''
    # =======================================================================
    # 업종 Sheet 정리
    # - 업종리스트
    # - 테마리스트
    # - 업종별 종목리스트
    # - 테마별 종목리스트
    # =======================================================================

    # 업종 리스트 DF 반환
    def Get_Industry_Info(self, start_cell="A3", end_cell="H114"):
        temp = self.업종.range(start_cell + ":" + end_cell).value
        df = pd.DataFrame(temp)
        df.columns = df.iloc[0]
        df = df.iloc[3:].drop("No", axis=1)
        df = df.set_index(df.columns[0])
        return df

    # 테마리스트 DF 반환
    def Get_Thema_Info(self, start_cell="AL3", end_cell="AM37"):
        temp = self.업종.range(start_cell + ":" + end_cell).value
        df = pd.DataFrame(temp)
        df.columns = df.iloc[0]
        df = df.iloc[1:].set_index(df.columns[0])
        return df

    def Get_Total_Info(self, start_cell="A5", end_cell="BJ2500"):
        temp=self.종합.range(start_cell+":"+end_cell).value
        df=pd.DataFrame(temp)
        df.columns=df.iloc[0]
        df=df.iloc[1:].set_index(df.columns[0]).dropna().drop_duplicates(keep='first')
        #df.dropna().reset_index().set_index("종목")
        return df

    # 딕셔너리 반환
    def Get_Industry_Stocks_List(self):
        Industry_list = self.Get_Industry_Info()
        total_dict = {}

        for name in Industry_list.index:
            self.업종["K2"].value = str(name)
            temp = self.업종.range("J3:V33").value
            df = pd.DataFrame(temp)
            df.columns = df.iloc[0]
            df = df.iloc[1:].drop("No", axis=1)
            df = df.set_index(df.columns[0])
            total_dict[name] = df
        for name in total_dict.key():
            self.DB.DB_SAVE(self.DB_Industry, name, total_dict[name])
        return total_dict

    # 딕셔너리 반환
    def Get_Thema_Stocks_List(self):
        Thema_list = self.Get_Thema_Info()
        total_dict = {}

        for name in Thema_list.index:
            self.업종["Y2"].value = str(name)
            temp = self.업종.range("X3:AJ33").value
            df = pd.DataFrame(temp)
            df.columns = df.iloc[0]
            df = df.iloc[1:].drop("No", axis=1)
            df = df.set_index(df.columns[0])
            total_dict[name] = df
        for name in total_dict.key():
            self.DB.DB_SAVE(self.DB_Thema, name, total_dict[name])
        return total_dict

    def Get_Total_List(self):
        total = self.Get_Total_Info()
        self.DB.DB_SAVE(self.DB_Value, self.title, total)
        return total

    def Get_Stock_Finance_Info(self, name):
        #.wb.sheets.add(name)
        #temp_sheet = self.wb.sheets[name]
        # Value company 입력
        self.Value["B2"].value=name
        # 재무상태표
        temp = self.재무제표.range("N6:P41").value
        finance_state = pd.DataFrame(temp)
        finance_state.columns = finance_state.iloc[0]
        finance_state = finance_state.set_index("분기").iloc[1:]
        finance_state.index = finance_state.index.map(lambda x: str(x).lstrip())
        finance_state.columns = ["20" + x.split(".")[0] + "/" + str(3 * int(x.split(".")[1].replace("Q", ""))).zfill(2)
                                 for x in finance_state.columns]

        # 손익계산서 (손익계산서는 총 5개의 Quarter가 표시 되므로 재무상태표,현금흐름표와 column일치화를 위해 마지막2개열만 취한다)
        temp = self.재무제표.range("AD6:AI28").value
        income_state = pd.DataFrame(temp)
        income_state.columns = income_state.iloc[0]
        income_state = income_state.set_index("분기").iloc[1:]
        income_state.columns = ["20" + x.split(".")[0] + "/" + str(3 * int(x.split(".")[1].replace("Q", ""))).zfill(2)
                                for x in income_state.columns]
        income_state.index = income_state.index.map(lambda x: str(x).lstrip())
        income_state = income_state.T.iloc[-2:].T

        # 현금흐름표
        temp = self.재무제표.range("AD32:AI40").value
        Cash_flow = pd.DataFrame(temp)
        Cash_flow.columns = Cash_flow.iloc[0]
        Cash_flow = Cash_flow.set_index("분기").iloc[1:]
        Cash_flow.columns = ["20" + x.split(".")[0] + "/" + str(3 * int(x.split(".")[1].replace("Q", ""))).zfill(2) for
                             x in Cash_flow.columns]
        Cash_flow.index = Cash_flow.index.map(lambda x: str(x).lstrip())
        Cash_flow = Cash_flow.T.iloc[-2:].T

        total = pd.concat([finance_state, income_state, Cash_flow])

        # 기존 아이투자 재무제표와 이름 맞추기...후...
        total=total.rename(index={"지배주주순이익":"지배지분순이익","영업활동현금흐름":"영업활동으로인한현금흐름","재무활동현금흐름":"재무활동으로인한현금흐름","투자활동현금흐름":"투자활동으로인한현금흐름","총자산":"자산총계","총부채":"자산총계"})
        total.replace("-", np.nan)
        try:
            total.loc['ROE'] = int(self.재무제표["AB28"].value) / int(total.loc['지배주주지분'][1])
        except:
            prev=int(total.loc['지배주주지분'][0])
            #Cur = total.loc['ROE'][1]
            if prev == 0:
                total.loc['ROE'] = 0
            else:
                # 최신분기 재무제표가 없는 기업들이 종종 있음... 이경우 전년도의 ROE를 써야할듯
                total.loc['ROE'] = int(self.재무제표["AA28"].value) / int(total.loc['지배주주지분'][0])
        #self.wb.sheets[name].delete()

        return total[[total.columns[1]]]

    def Get_Stocks_Finance_List(self):
        jongmok_list = self.Get_Total_List()
        for num, name in enumerate(tqdm.tqdm(jongmok_list.index)):
            #print(num)
            Current_Q = self.Get_Stock_Finance_Info(jongmok_list.loc[name]['종목'])
            if num == 0:
                Current_Q_name = Current_Q.columns[0]
                Current_Q.columns = [name]
                total_C_df = Current_Q.T
            else:
                if Current_Q.columns[0] == Current_Q_name:
                    Current_Q.columns = [name]
                    total_C_df = pd.concat([total_C_df, Current_Q.T])
                else:
                    continue
        total_C_df.columns=[[Current_Q_name]*len(total_C_df.columns),total_C_df.columns]
        self.DB.DB_SAVE(self.DB_Finance, Current_Q_name, total_C_df, multi_index=True)
        return total_C_df

if __name__ == "__main__":
    path = r'D:\OneDrive - Office 365\ValueTool\차단해제및재무분기데이터 수집\20_4Q_21_1Q\value tool 20210319.xlsb'
    test = GET_EXCEL_DATA(path)
    a=test.Get_Stocks_Finance_List()