
import os
import sys
ROOT_DIR = os.path.dirname(os.path.abspath(os.path.dirname(__file__)))
sys.path.append(ROOT_DIR)
import xlwings as xw
from multiprocessing import Pool
import pandas as pd
import DataBase.MySQL_control
import re
import numpy as np
thread_num = 4

import xlwings as xw
from multiprocessing import Pool
import pandas as pd
import DataBase.MySQL_control
import re
import numpy as np
import tqdm
from pathlib import Path
import re
thread_num = 4

class GET_RIM_DATA():
    def __init__(self, path):
        self.app = xw.App(visible=False)
        self.path = path
        # 파일 상장법인목록
        #self.wb = xw.Book(path)
        self.DB = DataBase.MySQL_control.DB_control()
        sort_val = "가치평가"
        self.eval_file_list = [file for file in os.listdir(path) if ((file.endswith(".xlsb")) & (sort_val in file))]
        
                
    def get_eval_info(self):
        for file in tqdm.tqdm(self.eval_file_list):
            real_path=os.path.join(self.path, file)
            table_name = re.findall("\d+", file)
            if len(table_name)==1 : table_name=table_name[0]
            else: table_name=table_name[1]
            try:
                self.get_eval_file(real_path,table_name)
            except:
                print(file)
        #self.app.kill()

    # 가치평가 & Rim file DB SAVE
    def get_eval_file(self, path, table_name):
        self.wb = xw.Book(path)
        self.종합 = self.wb.sheets['종합']
        self.rim = self.wb.sheets['RIM']
        temp_val=self.종합.range('A5:AC2300').value
        temp_val2 = self.rim.range('A4:R2300').value
        temp_df=pd.DataFrame(temp_val)
        temp_df.iloc[0] = temp_df.iloc[0].map(lambda x : str(x).replace(" ",""))
        temp_df.columns = temp_df.iloc[0]
        temp_df = temp_df.set_index("CODE")
        temp_df=temp_df.iloc[1:]
        sort_index=[x for x in temp_df.index if x!=None ]
        temp_df=temp_df.loc[sort_index]
        temp_df.columns = [x.replace("%", "퍼센트") for x in temp_df.columns]
        self.DB.DB_SAVE("stocks_가치평가", table_name, temp_df)
        temp_df = pd.DataFrame(temp_val2)
        temp_df.iloc[0] = temp_df.iloc[0].map(lambda x: str(x).replace(" ", ""))
        temp_df.columns = temp_df.iloc[0]
        temp_df = temp_df.set_index("CODE")
        temp_df = temp_df.iloc[1:]
        sort_index = [x for x in temp_df.index if x != None]
        temp_df = temp_df.loc[sort_index]
        self.DB.DB_SAVE("stocks_rim",table_name, temp_df)        
        self.wb.close()


class GET_EXCEL_DATA():
    def __init__(self, path):
        self.app = xw.App(visible=False)
        # 파일 상장법인목록
        self.excel_path = self.get_latest_file(path, 'value')
        self.path_value = path
        self.wb = xw.Book(self.excel_path)
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
        self.DB_Finance = "stocks_finance"
        self.DB_ROE = "system_parameter"
        self.title = re.findall('\d+', self.excel_path)[-1]
        
        self.DB = DataBase.MySQL_control.DB_control()
        self.DB_Finance = "stocks_finance"
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
    
    def Save_Value_Info(self):
        sort_val = "value"
        file_list = [file for file in os.listdir(self.path_value) if ((file.endswith(".xlsb")) & (sort_val in file))]
        #app = xw.App(visible=False)
        for file in tqdm.tqdm(file_list):
            real_path = os.path.join(self.path_value, file)
            table_name = re.findall("\d+", file)
            if len(table_name) == 1:
                table_name = table_name[0]
            else:
                table_name = table_name[1]
            try:
                self.wb = xw.Book(real_path)
                self.종합 = self.wb.sheets['종합']
                df = self.Get_Total_Info()

                self.wb.close()
                self.DB.DB_SAVE(self.DB_Value, table_name, df)
            except:
                print(file)

    def Get_Total_Info(self, start_cell="A5", end_cell="BJ2500"):
        temp = self.종합.range(start_cell + ":" + end_cell).value
        df = pd.DataFrame(temp)
        df.iloc[0]=df.iloc[0].replace(" ","")
        df.columns = df.iloc[0]
        df = df.iloc[1:].set_index(df.columns[0]).dropna().drop_duplicates(keep='first')
        df.columns = [x.replace(" ","").replace("/","_").replace("%", "퍼센트") for x in df.columns]
        #df = df.drop(["OCF/A "],axis=1)
        # df.dropna().reset_index().set_index("종목")
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
        
        #total=total.reset_index()
        self.DB.DB_SAVE(self.DB_Value, self.title, total)
        return total

    def Get_Stock_Finance_Year_Info(self, name):
        # .wb.sheets.add(name)
        # temp_sheet = self.wb.sheets[name]
        # Value company 입력
        self.Value["B2"].value = name
        # 재무상태표
        temp = self.재무제표.range("B6:K42").value
        finance_state = pd.DataFrame(temp)
        finance_state.columns = finance_state.iloc[0]
        finance_state = finance_state.set_index("10년").iloc[1:]
        finance_state.index = finance_state.index.map(lambda x: str(x).lstrip())
        #finance_state.columns = ["20" + x.split(".")[0] + "/" + str(3 * int(x.split(".")[1].replace("Q", ""))).zfill(2)
        #                         for x in finance_state.columns]
        finance_state = finance_state.T.iloc[-1:].T
        # 손익계산서 (손익계산서는 총 5개의 Quarter가 표시 되므로 재무상태표,현금흐름표와 column일치화를 위해 마지막2개열만 취한다)
        temp = self.재무제표.range("R6:AA29").value
        income_state = pd.DataFrame(temp)
        income_state.columns = income_state.iloc[0]
        income_state = income_state.set_index("10년").iloc[1:]
        income_state.index = income_state.index.map(lambda x: str(x).lstrip())
        income_state = income_state.T.iloc[-1:].T

        # 현금흐름표
        temp = self.재무제표.range("R32:AA41").value
        Cash_flow = pd.DataFrame(temp)
        Cash_flow.columns = Cash_flow.iloc[0]
        Cash_flow = Cash_flow.set_index("10년").iloc[1:]
        Cash_flow.index = Cash_flow.index.map(lambda x: str(x).lstrip())
        Cash_flow = Cash_flow.T.iloc[-1:].T

        total = pd.concat([finance_state, income_state, Cash_flow])

        # 기존 아이투자 재무제표와 이름 맞추기...후...
        total = total.rename(index={"지배주주순이익": "지배지분순이익", "영업활동현금흐름": "영업활동으로인한현금흐름", "재무활동현금흐름": "재무활동으로인한현금흐름",
                                    "투자활동현금흐름": "투자활동으로인한현금흐름", "총자산": "자산총계", "총부채": "부채총계"})
        total.replace("-", np.nan)
        try:
            total.loc['ROE'] = int(self.재무제표["AB28"].value) / int(total.loc['지배주주지분'])
        except:
            prev = int(total.loc['지배주주지분'][0])
            # Cur = total.loc['ROE'][1]
            if prev == 0:
                total.loc['ROE'] = 0
            else:
                # 최신분기 재무제표가 없는 기업들이 종종 있음... 이경우 전년도의 ROE를 써야할듯
                total.loc['ROE'] = int(self.재무제표["AA28"].value) / int(total.loc['지배주주지분'][0])
        # self.wb.sheets[name].delete()

        return total[[total.columns[0]]], total[[total.columns[1]]]

    def Get_Stock_Finance_Quarter_Info(self, name):
        # .wb.sheets.add(name)
        # temp_sheet = self.wb.sheets[name]
        # Value company 입력
        self.Value["B2"].value = name
        # 재무상태표
        temp = self.재무제표.range("N6:P41").value
        finance_state = pd.DataFrame(temp)
        finance_state.columns = finance_state.iloc[0]
        finance_state = finance_state.set_index("분기").iloc[1:]
        finance_state.index = finance_state.index.map(lambda x: str(x).lstrip())
        try:
            #total.loc['ROE'] = [int(self.재무제표["AA28"].value) / int(total.loc['지배주주지분'][0]),int(self.재무제표["AB28"].value) / int(total.loc['지배주주지분'][1])]
            finance_state.loc['ROE'] = int(self.재무제표["AB28"].value) / int(finance_state.loc['지배주주지분'].astype("int"))
        except:
            try:
                prev = int(finance_state.loc['지배주주지분'][0])
                #prev = int(finance_state.loc['지배주주지분'])
                # Cur = total.loc['ROE'][1]
                if prev == 0:
                    finance_state.loc['ROE'] = 0
                else:
                    # 최신분기 재무제표가 없는 기업들이 종종 있음... 이경우 전년도의 ROE를 써야할듯
                    finance_state.loc['ROE'] = int(self.재무제표["AA28"].value) / int(finance_state.loc['지배주주지분'][0])
            except:
                print(name)
                finance_state.loc['ROE'] = 0
                pass

        finance_state.columns = ["20" + x.split(".")[0] + "/" + str(3 * int(x.split(".")[1].replace("Q", ""))).zfill(2)
                                 for x in finance_state.columns]
        #finance_state = finance_state.T.iloc[-2:].T
        # 손익계산서 (손익계산서는 총 5개의 Quarter가 표시 되므로 재무상태표,현금흐름표와 column일치화를 위해 마지막2개열만 취한다)
        temp = self.재무제표.range("AD6:AI28").value
        income_state = pd.DataFrame(temp)
        income_state.columns = income_state.iloc[0]
        income_state = income_state.set_index("분기").iloc[1:]
        income_state.columns = ["20" + x.split(".")[0] + "/" + str(3 * int(x.split(".")[1].replace("Q", ""))).zfill(2)
                                for x in income_state.columns]
        income_state.index = income_state.index.map(lambda x: str(x).lstrip())
        income_state = income_state.T.drop("감가상각비",axis=1).iloc[-2:].T
        #income_state = income_state.T.iloc[-1:].T
        # 현금흐름표
        temp = self.재무제표.range("AD32:AI40").value
        Cash_flow = pd.DataFrame(temp)
        Cash_flow.columns = Cash_flow.iloc[0]
        Cash_flow = Cash_flow.set_index("분기").iloc[1:]
        Cash_flow.columns = ["20" + x.split(".")[0] + "/" + str(3 * int(x.split(".")[1].replace("Q", ""))).zfill(2) for
                             x in Cash_flow.columns]
        Cash_flow.index = Cash_flow.index.map(lambda x: str(x).lstrip())
        Cash_flow = Cash_flow.T.iloc[-2:].T
        #Cash_flow = Cash_flow.T.iloc[-1:].T
        # ETC
        # 주식수, 주가, 시총
        temp = self.가치평가.range("I4:J6").value
        Etc = pd.DataFrame(temp)
        Etc = Etc.set_index(Etc.columns[0])
        Etc=Etc.replace('-',0)
        Etc=Etc/100000000
        Etc.loc['주식수'] =(Etc.loc['발행주식수']+Etc.loc['우선주']-Etc.loc['자기주식수'])
        Etc=pd.concat([Etc,Etc],axis=1)
        Etc.columns = finance_state.columns
        total = pd.concat([finance_state, income_state, Cash_flow, Etc])

        # 기존 아이투자 재무제표와 이름 맞추기...후...
        total = total.rename(index={"지배주주순이익": "지배지분순이익", "영업활동현금흐름": "영업활동으로인한현금흐름", "재무활동현금흐름": "재무활동으로인한현금흐름",
                                    "투자활동현금흐름": "투자활동으로인한현금흐름", "총자산": "자산총계", "총부채": "부채총계"})
        total.replace("-", np.nan)
        # 추가사항
        total.loc['BPS'] = total.loc['지배주주지분'].astype('float') / total.loc['주식수'].astype('float')

        total.loc['ROE'] = total.loc['지배지분순이익'].astype('float') / total.loc['지배주주지분'].astype('float')
        total.loc['부채비율(%)'] = (total.loc['부채총계'].astype("float") / total.loc['지배주주지분'].replace(0, 1).astype(
            "float")) * 100
        total.loc['유동비율(%)'] = (total.loc['유동자산'].astype("float") / total.loc['유동부채'].replace(0, 1).astype(
            "float")) * 100
        total.loc['유보율(%)'] = ((total.loc['자본잉여금'].astype("float") + total.loc['이익잉여금'].astype("float")) / total.loc[
            '자본금'].replace(0, 1).astype("float")) * 100
        # total.loc['현금성자산'] = total.loc['유동자산'].astype("float") - total.loc['매출채권'].astype("float") - table[
        #    '재고자산'].astype("float")
        total.loc['순현금'] = total.loc['현금성자산'].astype("float") - (
                total.loc['단기금융부채'].astype("float") + total.loc['장기금융부채'].astype("float"))
        total = total.replace([np.inf, -np.inf], np.nan)
        # self.wb.sheets[name].delete()

        return total[[total.columns[0]]], total[[total.columns[1]]]
    # Quarter finance
    def Get_Stocks_Finance_Quarter(self):
        jongmok_list = self.Get_Total_List()
        for num, name in enumerate(tqdm.tqdm(jongmok_list.index)):
            Prev_Q, Current_Q = self.Get_Stock_Finance_Quarter_Info(jongmok_list.loc[name]['종목'])
            #Current_Q = self.Get_Stock_Finance_Quarter_Info(jongmok_list.loc[name]['종목'])
            if num == 0:
                Current_Q_name = Current_Q.columns[0]
                Prev_Q_name = Prev_Q.columns[0]
                Current_Q.columns = [name]
                Prev_Q.columns = [name]
                total_P_df = Prev_Q.T
                total_C_df = Current_Q.T
            else:
                if Current_Q.columns[0] == Current_Q_name:
                    Prev_Q.columns = [name]
                    Current_Q.columns = [name]
                    total_P_df = pd.concat([total_P_df, Prev_Q.T])
                    total_C_df = pd.concat([total_C_df, Current_Q.T])
                    #print(num)
                else:
                    continue
        total_C_df.columns = [[Current_Q_name] * len(total_C_df.columns), total_C_df.columns]
        total_P_df.columns = [[Prev_Q_name] * len(total_P_df.columns), total_P_df.columns]
        self.app.kill()
        self.DB.DB_SAVE(self.DB_Finance, Current_Q_name, total_C_df, multi_index=True)
        self.DB.DB_SAVE(self.DB_Finance, Prev_Q_name, total_P_df, multi_index=True)
        return total_C_df

    # Year finance
    def Get_Stocks_Finance_Year(self):
        jongmok_list = self.Get_Total_List()
        for num, name in enumerate(tqdm.tqdm(jongmok_list.index)):
            Prev_Q, Current_Q = self.Get_Stock_Finance_Year_Info(jongmok_list.loc[name]['종목'])
            if num == 0:
                Current_Q_name = Current_Q.columns[0]
                Prev_Q_name = Prev_Q.columns[0]
                Current_Q.columns = [name]
                Prev_Q.columns = [name]
                total_P_df = Prev_Q.T
                total_C_df = Current_Q.T
            else:
                if Current_Q.columns[0] == Current_Q_name:
                    Prev_Q.columns = [name]
                    Current_Q.columns = [name]
                    total_P_df = pd.concat([total_P_df, Prev_Q.T])
                    total_C_df = pd.concat([total_C_df, Current_Q.T])
                    # print(num)
                else:
                    continue
        total_C_df.columns = [[Current_Q_name] * len(total_C_df.columns), total_C_df.columns]
        total_P_df.columns = [[Prev_Q_name] * len(total_P_df.columns), total_P_df.columns]
        #self.DB.DB_SAVE(self.DB_Finance, Current_Q_name, total_C_df, multi_index=True)
        self.DB.DB_SAVE(self.DB_Finance, Prev_Q_name, total_P_df, multi_index=True)

        return total_P_df, total_C_df

    # ROE Table Make
    def Make_ROE_Table(self):
        temp = self.DB.DB_LOAD_TABLE_LIST("stocks_finance")
        total_df = pd.DataFrame(data=None)
        for num, data in enumerate(tqdm.tqdm(temp)):
            temp = self.DB.DB_LOAD_Table("stocks_finance", data, multi_index=True)
            table = temp[data]
            table['ROE'] = table['지배지분순이익'].astype('float') / table['지배주주지분'].astype('float')
            table['ROE'] = table['ROE'].replace([np.inf, -np.inf], np.nan)
            table = table[['ROE']]
            table.columns = [data]
            if num == 0:
                total_df = table.copy()
            else:
                total_df = pd.merge(total_df, table, how='outer', left_index=True, right_index=True)
        for index in total_df.index:
            total_df.loc[index] = total_df.loc[index].rolling(4).sum()
        self.DB.DB_SAVE(self.DB_ROE, "roe_quarter", total_df, multi_index=False)
        return total_df

    def Modify_Stocks_Valuelist(self):
        temp = self.DB.DB_LOAD_TABLE_LIST("stocks_value_list")
        for num, data in enumerate(tqdm.tqdm(temp)):
            #if data == "2020/03" : value_tool_flag =True
            temp = self.DB.DB_LOAD_Table("stocks_value_list", data, multi_index=False)
            temp.columns=[str(x).replace(" ","") for x in temp.columns]
            self.DB.DB_SAVE("stocks_value_list",data,temp)
    # Finance DB 내용 수정시 사용
    def Modify_Stocks_Finance(self):
        temp = self.DB.DB_LOAD_TABLE_LIST("stocks_finance")
        value_tool_flag = False
        for num, data in enumerate(tqdm.tqdm(temp)):
            # 이시점을 기준으로 Value sheet에서 뽑은 정보임... date>2020/03
            if data == "2020/03" : value_tool_flag =True
            temp = self.DB.DB_LOAD_Table("stocks_finance", data, multi_index=True)
            # 2011년 IFRS국제회계기준 적용으로 인한 "지배지분순이익" "지배주주지분"
            table = temp[data]
            if value_tool_flag:
                pass
            else:
                table['주식수'] = table['주식수'].map(lambda x: x if ((x == None) or (x == np.nan)) else float(x)/100000000)

            '''
            #table['지배지분순이익']=table.apply(lambda x: x['당기순이익'] if ((x['지배지분순이익']==0) or (x['지배지분순이익']==np.nan) or (x['지배지분순이익']==None)) else x['지배지분순이익'], axis=1)
            if int(data.split("/")[0]) >= 2020 :
                table['BPS'] = table['지배주주지분'].astype('float') / table['주식수'].astype('float')
            else:                
                table['단기금융부채'] = table['단기사채'].astype("float") + table['단기차입금'].astype("float") + table[
                    '유동성장기부채'].astype("float")
            table['지배지분순이익'] = table.apply(lambda x: x['당기순이익'] if ((str(x['지배지분순이익']) == '0.0')or(str(x['지배지분순이익']) == 'None')) else x['지배지분순이익'], axis=1)
            table['ROE'] = table['지배지분순이익'].astype('float') / table['지배주주지분'].astype('float')
            table['부채비율(%)'] = (table['부채총계'].astype("float") / table['지배주주지분'].replace(0, 1).astype(
                "float")) * 100
            table['유동비율(%)'] = (table['유동자산'].astype("float") / table['유동부채'].replace(0, 1).astype(
                "float")) * 100
            table['유보율(%)'] = ((table['자본잉여금'].astype("float") + table['이익잉여금'].astype("float")) / table[
                '자본금'].replace(0, 1).astype("float")) * 100
            table['현금성자산'] = table['유동자산'].astype("float") - table['매출채권'].astype("float") - table[
                '재고자산'].astype("float")
            table['순현금'] = table['현금성자산'].astype("float") - (
                    table['단기금융부채'].astype("float") + table['장기금융부채'].astype("float"))
            
            temp = table['감가상각비'].T.iloc[-1:]
            table = table.drop(['감가상각비'],axis=1)
            table = pd.concat([table, temp.T.iloc[-1:].T], axis=1)
            #table = table.T.drop_duplicates(keep="last").T
            '''
            table.columns = [[data] * len(table.columns), table.columns]
            table=table.replace([np.inf,-np.inf],np.nan)
            self.DB.DB_SAVE(self.DB_Finance, data, table, multi_index=True)

    def shift_back(self, lst):
        lst_new = lst.copy()
        for i in range(len(lst)):
            if i == 0:
                lst_new[i + 1] = np.nan
            elif i == len(lst) - 1:
                pass
            else:
                lst_new[i + 1] = lst[i]
        return lst_new
    #Series data
    def Make_RIM_ROE_Table(self):
        ROE_TABLE = self.DB.DB_LOAD_Table("system_parameter","roe_quarter")
        for code in tqdm.tqdm(ROE_TABLE.index):
            ROE_TABLE.loc[code] = self.Make_RIM_ROE(ROE_TABLE.loc[code])
        self.DB.DB_SAVE(self.DB_ROE, "rim_roe_quarter", ROE_TABLE, multi_index=False)

    def Make_RIM_ROE(self, data):
        name = data.name
        ROE_data = data
        ROE_data_pct = pd.to_numeric(ROE_data, errors='coerce').pct_change()
        ROE_data_pct_shift = self.shift_back(ROE_data_pct)
        ROE_data_pct_shift2 = self.shift_back(ROE_data_pct_shift)
        ROE_data.name='ROE'
        ROE_data_pct.name = 'ROE_PCT'
        ROE_data_pct_shift.name = 'ROE_PCT_shift'
        ROE_data_pct_shift2.name = 'ROE_PCT_shift2'
        ROE_data = pd.concat([ROE_data, ROE_data_pct, ROE_data_pct_shift,ROE_data_pct_shift2], axis=1)
        ROE_data['ROE'] = ROE_data['ROE'].replace("-", 0).astype('float')
        ROE_data['ROE평균'] = ROE_data['ROE'].rolling(3).sum() / 3
        ROE_data['ROE평균_shift'] = self.shift_back(ROE_data['ROE평균'])
        ROE_data['ROE추세'] = self.shift_back(ROE_data['ROE'])
        RIM_ROE = []
        for num, index in enumerate(ROE_data.index):
            try:
                if ROE_data.iloc[num][2] * ROE_data.iloc[num][3] < 0:
                    RIM_ROE.append(ROE_data.iloc[num][5])
                else:
                    RIM_ROE.append(ROE_data.iloc[num][6])
            except:
                RIM_ROE.append(ROE_data.iloc[num][0])
                pass
        ROE_data = pd.Series(RIM_ROE, index=ROE_data.index)
        ROE_data.name=name

        return ROE_data

    def get_latest_file(self, path, type_val='value'):
        make_time_max=0
        prev_ctime=0
        for num,file in enumerate(os.listdir(path)):
            if type_val in file:
                if ".xlsb" in file:
                    ctime = os.path.getctime(os.path.join(path,file))
                    if num==0:
                        latest_file=file
                        prev_ctime=ctime
                    elif ctime>prev_ctime:
                        latest_file=file
                        prev_ctime=ctime
                    else:
                        continue
        return os.path.join(path,latest_file)
if __name__ == "__main__":
    current_path = Path(os.getcwd())
    v_path = 'ValueTool\Valuetool'
    path = os.path.join(current_path.parent.parent.parent, v_path)

    #exel_path=r'ValueTool\차단해제및재무분기데이터 수집\20_4Q_21_1Q\value tool 20210723.xlsb'
    rim_path = r'F:\OneDrive - Office 365\ValueTool\Valuetool'

    # 분기데이터 추출 엑셀매크로 실행
    #test=GET_RIM_DATA(path)
    test=GET_EXCEL_DATA(path)
    #test.Get_Stocks_Finance_Quarter()

    # rim, 가치평가 sheet table 업데이트 시.,,..,
    #test = GET_RIM_DATA(rim_path)



'''
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
        for num, name in enumerate(jongmok_list.index):
            print(num)
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
    a.b=test.Get_Stocks_Finance_List()
    print(a.head())
'''
