import pandas as pd
import DataBase.MySQL_control
import requests


def make_quarter_db_data():
    path = 'F:\\OneDrive - Office 365\\ValueTool\\차단해제및재무분기데이터 수집\\'
    db = DataBase.MySQL_control.DB_control()
    code_list = db.DB_LOAD_Table('stocks_lists', 'stocks_lists_all')
    #temp_df = pd.DataFrame(data=None)
    new_col = []
    for num, name in enumerate(code_list['Name']):
        print(num)
        '''
        if num == 30:
            break
        '''
        try:
            temp_df = pd.read_excel(path+name+'.xlsx')

        except:
            print("No")
            continue
        temp_df = temp_df.set_index(temp_df.columns[0])
        jongmok_시총, jongmok_주가 = Crolling_Jongmok_stock_quantity('A' + code_list.iloc[num].name)
        temp_df.loc['시가총액'] = jongmok_시총
        temp_df.loc['주가'] = jongmok_주가
        temp_df.index = list(map(lambda x: x.strip(), temp_df.index))
        temp_df = temp_df.loc[['유동자산', '현금성자산', '매출채권', '재고자산', '비유동자산', '유형자산',
                               '무형자산', '영업권', '총자산', '유동부채', '매입채무', '비유동부채', '총부채',
                               '자본금', '자본잉여금', '이익잉여금', '지배주주지분',  '매출액', '매출원가', '매출총이익',
                                '감가상각비', '연구개발비', '영업이익',  '지배주주순이익', '영업활동현금흐름', '당기순이익',
                                '투자활동현금흐름', '재무활동현금흐름', '장기금융부채', '단기금융부채', '시가총액', '주가']]
        #print(temp_df.reset_index().head())
        temp_df = temp_df.reset_index().drop_duplicates("index").set_index("index")
        #print(len(temp_df))
        temp_df.index = ['유동자산', '현금및현금성자산', '매출채권', '재고자산', '비유동자산', '유형자산',
                         '무형자산', '영업권', '자산총계', '유동부채', '매입채무', '비유동부채', '부채총계',
                         '자본금', '자본잉여금', '이익잉여금', '지배주주지분',  '매출액', '매출원가', '매출총이익',
                         '감가상각비', '연구개발비', '영업이익',  '지배지분순이익', '영업활동으로인한현금흐름', '당기순이익',
                         '투자활동으로인한현금흐름', '재무활동으로인한현금흐름', '장기금융부채', '단기금융부채', '시가총액', '주가']
        for col in temp_df.columns:
            new_col.append('20'+col.replace(".1Q","/03").replace(".2Q","/06").replace(".3Q","/09").replace(".4Q","/12"))
        temp_df.columns = new_col
        new_col = []
        temp_df.columns = [['A'+str(code_list[code_list['Name'] == name].index[0])]*len(temp_df.columns), temp_df.columns]
        temp_df = temp_df.stack(level=0)
        temp_df = temp_df.swaplevel(0,1)
        temp_df = temp_df.unstack(level=1)
        #temp_df.columns = ['A'+str(code_list[code_list['Name'] == name].index[0])]
        if num == 0:
            total_df = temp_df.copy()
        else :
            #total_df = pd.merge(total_df, temp_df, how='outer', left_index=True, right_index=True)
            total_df = pd.concat([total_df, temp_df], axis=0)
    Save_quarter_finance_to_DB(total_df)
    return total_df

def Save_quarter_finance_to_DB(df):
    db = DataBase.MySQL_control.DB_control()
    for col in df.columns.levels[0]:
        db.DB_SAVE('stocks_finance', col, df[[col]], multi_index=True)
    return

def Crolling_Jongmok_stock_quantity(code):
    snap_shot_url = "http://comp.fnguide.com/SVO2/ASP/SVD_Main.asp?pGB=1&cID=&MenuYn=Y&ReportGB=&NewMenuID=101&stkGb=701&gicode="
    total_url = snap_shot_url + code
    fs_page_total = requests.get(total_url)
    fs_tables_total = pd.read_html(fs_page_total.text)
    test = fs_tables_total[0]
    try:
        jongmok_시총 = int(test[1][4])
        jongmok_주가 = int(test[1][0].split("/")[0].replace(",",""))
    except :
        jongmok_시총 = 0
        jongmok_주가 = 0
    return (jongmok_시총, jongmok_주가)

if __name__ == '__main__':
    total = make_quarter_db_data()

    print(total)