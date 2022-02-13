import Kiwoom.Kiwoom
# sys : system_specific parameter and functions
# 파이썬 스크립트 관리
import Finance.finance_data


# QtWidget안의 QApplication 클래스는 프로그램을 앱처럼 수행 및 그래픽적요소를 제어하는 기능. 동시성 처리


class Main():
    def __init__(self):
        print("APP_START~!")
        #self.app = QApplication(sys.argv) # Qt5로 실행할 파일명을 자동설정
        self.fs = Finance.finance_data.Finance_data()
        self.kw = Kiwoom.Kiwoom.Kiwoom()
        kosdaq_list_new = []
        kosdaq_list = self.kw.get_code_list_by_market("10")
        kospi_list = self.kw.get_code_list_by_market("0")
        for code in kosdaq_list:
            kosdaq_list_new.append("A"+code)
        a,b,c,d,e = self.fs.Crolling_fs_Total(kosdaq_list_new)
        a.to_excel("f:\\a.xlsx")
        b.to_excel("f:\\b.xlsx")
        c.to_excel("f:\\c.xlsx")
        d.to_excel("f:\\d.xlsx")
        e.to_excel("f:\\e.xlsx")
        #self.app.exec() #event loop start



if __name__ == "__main__":
    Main()