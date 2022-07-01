class PORT_PARAMETER():

    WantConditionList = ['단테시초가1번', '단테시초가2번', '단테떡상이1', '단테단타1번','종가베팅_박범진', '단테떡상이2',]

    SwingConditionList = ['단테단타1번', '단테떡상이1', '단테떡상이2', "단테_하이힐_스윙", "단테_하이힐_일봉"]

    MorningList = ['단테시초가1번', '단테시초가2번']

    AfternoonList = ['종가베팅_박범진']

    port_parameter = {
        "강환국_울트라_소형주":{"Buy_Upper_limit": 2, "Buy_Cancel_limit":5, "Sell_Upper_Limit":10, "Sell_Lower_Limit":-5,"Stock_Quantity":20},
        "마법공식2": {"Buy_Upper_limit": 3, "Buy_Cancel_limit": 5, "Sell_Upper_Limit": 20, "Sell_Lower_Limit": -8,"Stock_Quantity":20},
        "etc":{"Buy_Upper_limit": 3, "Buy_Cancel_limit":5, "Sell_Upper_Limit":5, "Sell_Lower_Limit":-5,"Stock_Quantity":100},
        "단테_하이힐_일봉": {"Buy_Upper_limit": 3, "Buy_Cancel_limit": 5, "Sell_Upper_Limit": 5, "Sell_Lower_Limit": -5,"Stock_Quantity":10},
        "단테_하이힐_스윙": {"Buy_Upper_limit": 3, "Buy_Cancel_limit": 5, "Sell_Upper_Limit": 5, "Sell_Lower_Limit": -5,"Stock_Quantity":10},
        "단테하이힐_단타": {"Buy_Upper_limit": 3, "Buy_Cancel_limit": 5, "Sell_Upper_Limit": 5, "Sell_Lower_Limit": -5,"Stock_Quantity":10},
        "단테시초가1번": {"Buy_Upper_limit": 3, "Buy_Cancel_limit": 5, "Sell_Upper_Limit": 7, "Sell_Lower_Limit": -5,"Stock_Quantity":10},
        "단테시초가2번": {"Buy_Upper_limit": 3, "Buy_Cancel_limit": 5, "Sell_Upper_Limit": 7, "Sell_Lower_Limit": -5,"Stock_Quantity":10},
        "단테떡상이1": {"Buy_Upper_limit": 3, "Buy_Cancel_limit": 5, "Sell_Upper_Limit": 7, "Sell_Lower_Limit": -5,"Stock_Quantity":10},
        "단테떡상이2": {"Buy_Upper_limit": 3, "Buy_Cancel_limit": 5, "Sell_Upper_Limit": 7, "Sell_Lower_Limit": -5,
                    "Stock_Quantity": 10},
        "단테단타1번": {"Buy_Upper_limit": 3, "Buy_Cancel_limit": 5, "Sell_Upper_Limit": 5, "Sell_Lower_Limit": -5,"Stock_Quantity":10},
        "종가베팅_박범진": {"Buy_Upper_limit": 3, "Buy_Cancel_limit": 5, "Sell_Upper_Limit": 7, "Sell_Lower_Limit": -5,
                  "Stock_Quantity": 5},
    }

