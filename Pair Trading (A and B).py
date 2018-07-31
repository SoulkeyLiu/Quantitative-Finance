%matplotlib inline
from qpython import qconnection
conn = qconnection.QConnection('localhost')
conn.open()
from qplot import line,lines,kline
import numpy as np
import pandas as pd
import matplotlib.pyplot  as plt
import statsmodels.api as sm
import seaborn as sns
s1=data["rbclose"]
s2=data["hcclose"]
corr=s1.corr(s2)
result = sm.tsa.stattools.coint(s1, s2)
pvalue=result[1]
conn(r'''
nday:1000;
dd:8;
newdata1:(nday)_select from newdata;

    newdata1:update testspread:spread1-(C+(k1*1000)) from newdata1;
    newdata1:select from newdata1 where date within (2016.01.01,2018.03.30);

    newdata1:update deltaspread1:deltaspread from newdata1;
    newdata1:update deltaspread1:0.0 from newdata1 where (deltaspread1>5.0);
    newdata1:update deltaspread1:0.0 from newdata1 where (deltaspread1<-5.0);

    newdata1:update stddeltaspread:10000 mdev deltaspread1 from newdata1;

    newdata1:update ddd:(stddeltaspread*stddeltaspread*dd) from newdata1;

    trade_indicator:update position: -1 from newdata1 where (testspread>ddd);
    trade_indicator:update position:1 from trade_indicator where (testspread<(0-ddd));

    trade_indicator:update position: 0 from trade_indicator where (testspread*(prev testspread))<0;

    trade_indicator:update sig: 1000 from trade_indicator where (rbsymbol=prev rbsymbol) and (rbsymbol<>next rbsymbol);
    trade_indicator:update sig: 1000 from trade_indicator where (hcsymbol=prev hcsymbol) and (hcsymbol<>next hcsymbol);

    trade_indicator: update sig:1000 from trade_indicator where ((nday+50) msum sig)>500;
    trade_indicator: update position:0 from trade_indicator where sig=1000;

    trade_indicator:update position:0^fills position from trade_indicator;
    trade_indicator:update turn:abs(position-prev position) from trade_indicator;

    trade_indicator
''', pandas=True)
import pandas as pd
pd.set_option('display.max_columns', None)
pd.set_option('display.max_rows', None)
a=conn(r'''
select[3000 5000] date,time,aclose:rbclose,asymbol:rbsymbol,bclose:hcclose,bsymbol:hcsymbol,spread1,deltaspread,stddeltaspread,testspread,position from trade_indicator
''',pandas=True)
conn(r'''
get_movmodel:{[nday]
    rbdata:select date,time,rbclose:close,rbsymbol:symbol from bar1[`a] where (date within (2014.01.01,2018.03.30)) and (not null close);
    hcdata:`date`time xkey select date,time,hcclose:close,hcsymbol:symbol from bar1[`b] where (date within (2014.01.01,2018.03.30)) and (not null close);
    newdata:rbdata ij hcdata;
    newdata:update spread1:hcclose-rbclose from newdata;
    newdata:update deltaspread:deltas spread1 from newdata;
    m:nday;
    n:nday;
    do[count((n)_newdata);
        y:newdata[`spread1][(m-nday)+til nday];
        x:til count(y);
        lsfit:{(enlist y) lsq x xexp/: til 1};
        coef:lsfit[x;y];
        newdata:update C:coef[0][0] from newdata where i=m;
        m:m+1];
    newdata
    }
''',pandas=True)
conn(r'''
get_data:{[dd;nday]
    newdata1:(nday)_select from newdata;

    newdata1:update testspread:spread1-(C) from newdata1;
    newdata1:select from newdata1 where date within (2016.01.01,2018.03.30);

    newdata1:update deltaspread1:deltaspread from newdata1;
    newdata1:update deltaspread1:0.0 from newdata1 where (deltaspread1>5.0);
    newdata1:update deltaspread1:0.0 from newdata1 where (deltaspread1<-5.0);

    newdata1:update stddeltaspread:10000 mdev deltaspread1 from newdata1;

    newdata1:update ddd:(stddeltaspread*stddeltaspread*dd) from newdata1;

    trade_indicator:update position: -1 from newdata1 where (testspread>ddd);
    trade_indicator:update position:1 from trade_indicator where (testspread<(0-ddd));

    trade_indicator:update position: 0 from trade_indicator where (testspread*(prev testspread))<0;

    trade_indicator:update sig: 1000 from trade_indicator where (rbsymbol=prev rbsymbol) and (rbsymbol<>next rbsymbol);
    trade_indicator:update sig: 1000 from trade_indicator where (hcsymbol=prev hcsymbol) and (hcsymbol<>next hcsymbol);

    trade_indicator: update sig:1000 from trade_indicator where ((nday+50) msum sig)>500;
    trade_indicator: update position:0 from trade_indicator where sig=1000;

    trade_indicator:update position:0^fills position from trade_indicator;
    trade_indicator:update turn:abs(position-prev position) from trade_indicator;

    trade_indicator
    }

''', pandas=True)
def get_result(dd,nday):
    return conn(r'''get_data[%s;%s]'''%(dd,nday),pandas=True)
conn(r'''
newdata:get_movmodel[1000]
''',pandas=True)
tlist = [2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15]
nday = 500
for dd in tlist:
    a = get_result(dd, nday)
    turn = list(a["turn"])
    position = list(a["position"])
    deltaspread = list(a["deltaspread"])
    accprofit1 = [0]
    accprofit0 = [0]
    for i in range(1, len(a)):
        accprofit1.append(accprofit1[-1] + position[i - 1] * deltaspread[i] - turn[i] * 2)
        accprofit0.append(accprofit0[-1] + position[i - 1] * deltaspread[i] - turn[i] * 0)

    a["accprofit1"] = accprofit1
    a["accprofit0"] = accprofit0
    grouped1 = a['accprofit1'].groupby(a['date']).last()
    grouped0 = a['accprofit0'].groupby(a['date']).last()
    import numpy as np

    x1 = list(grouped1)
    xx1 = [x1[0]]
    for i in range(1, len(x1)):
        xx1.append(x1[i] - x1[i - 1])

    x0 = list(grouped0)
    xx0 = [x0[0]]
    for i in range(1, len(x0)):
        xx0.append(x0[i] - x0[i - 1])

    mean0 = np.mean(xx0)
    mean1 = np.mean(xx1)
    std0 = np.std(xx0)
    std1 = np.std(xx1)
    sharpe0 = mean0 / std0
    sharpe1 = mean1 / std1
    avgnum = sum(turn[1:]) / (2 * 250)

    # line(a.loc[:,["date","accprofit1","accprofit0"]])
    print('\n' + "模型：前500个bar回归" + "   " + "开仓范围：|testspread|>(stddeltaspread*stddeltaspread* %s)" % dd + "   " \
                                                                                                          '\n' + "无手续：" + "mean0:" + str(
        round(mean0, 3)) + "   " + "std0:" + str(round(std0, 3)) + "   " + "sharpe0:" + str(round(sharpe0, 3)) + "   " \
                                                                                                                 '\n' + "手续为1：" + "mean1:" + str(
        round(mean1, 3)) + "   " + "std1:" + str(round(std1, 3)) + "   " + "sharpe1:" + str(round(sharpe1, 3)) + "   " \
                                                                                                                 '\n' + "avgnum:" + str(
        round(avgnum, 3)))
tlist = [2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15]
nday = 1000
for dd in tlist:
    a = get_result(dd, nday)
    turn = list(a["turn"])
    position = list(a["position"])
    deltaspread = list(a["deltaspread"])
    accprofit1 = [0]
    accprofit0 = [0]
    for i in range(1, len(a)):
        accprofit1.append(accprofit1[-1] + position[i - 1] * deltaspread[i] - turn[i] * 2)
        accprofit0.append(accprofit0[-1] + position[i - 1] * deltaspread[i] - turn[i] * 0)
    a["accprofit1"] = accprofit1
    a["accprofit0"] = accprofit0
    grouped1 = a['accprofit1'].groupby(a['date']).last()
    grouped0 = a['accprofit0'].groupby(a['date']).last()
    import numpy as np

    x1 = list(grouped1)
    xx1 = [x1[0]]
    for i in range(1, len(x1)):
        xx1.append(x1[i] - x1[i - 1])

    x0 = list(grouped0)
    xx0 = [x0[0]]
    for i in range(1, len(x0)):
        xx0.append(x0[i] - x0[i - 1])

    mean0 = np.mean(xx0)
    mean1 = np.mean(xx1)
    std0 = np.std(xx0)
    std1 = np.std(xx1)
    sharpe0 = mean0 / std0
    sharpe1 = mean1 / std1
    avgnum = sum(turn[1:]) / (2 * 250)
    # line(a.loc[:,["date","accprofit1","accprofit0"]])
    print('\n' + "模型：前1000个bar回归" + "   " + "开仓范围：|testspread|>(stddeltaspread*stddeltaspread* %s)" % dd + "   " \
                                                                                                           '\n' + "无手续：" + "mean0:" + str(
        round(mean0, 3)) + "   " + "std0:" + str(round(std0, 3)) + "   " + "sharpe0:" + str(round(sharpe0, 3)) + "   " \
                                                                                                                 '\n' + "手续为1：" + "mean1:" + str(
        round(mean1, 3)) + "   " + "std1:" + str(round(std1, 3)) + "   " + "sharpe1:" + str(round(sharpe1, 3)) + "   " \
                                                                                                                 '\n' + "avgnum:" + str(
        round(avgnum, 3)))
tlist = [2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15]
nday = 1500
for dd in tlist:
    a = get_result(dd, nday)
    turn = list(a["turn"])
    position = list(a["position"])
    deltaspread = list(a["deltaspread"])
    accprofit1 = [0]
    accprofit0 = [0]
    for i in range(1, len(a)):
        accprofit1.append(accprofit1[-1] + position[i - 1] * deltaspread[i] - turn[i] * 2)
        accprofit0.append(accprofit0[-1] + position[i - 1] * deltaspread[i] - turn[i] * 0)
    a["accprofit1"] = accprofit1
    a["accprofit0"] = accprofit0
    grouped1 = a['accprofit1'].groupby(a['date']).last()
    grouped0 = a['accprofit0'].groupby(a['date']).last()
    import numpy as np

    x1 = list(grouped1)
    xx1 = [x1[0]]
    for i in range(1, len(x1)):
        xx1.append(x1[i] - x1[i - 1])

    x0 = list(grouped0)
    xx0 = [x0[0]]
    for i in range(1, len(x0)):
        xx0.append(x0[i] - x0[i - 1])

    mean0 = np.mean(xx0)
    mean1 = np.mean(xx1)
    std0 = np.std(xx0)
    std1 = np.std(xx1)
    sharpe0 = mean0 / std0
    sharpe1 = mean1 / std1
    avgnum = sum(turn[1:]) / (2 * 250)
    # line(a.loc[:,["date","accprofit1","accprofit0"]])
    print('\n' + "模型：前1500个bar回归" + "   " + "开仓范围：|testspread|>(stddeltaspread*stddeltaspread* %s)" % dd + "   " \
                                                                                                           '\n' + "无手续：" + "mean0:" + str(
        round(mean0, 3)) + "   " + "std0:" + str(round(std0, 3)) + "   " + "sharpe0:" + str(round(sharpe0, 3)) + "   " \
                                                                                                                 '\n' + "手续为1：" + "mean1:" + str(
        round(mean1, 3)) + "   " + "std1:" + str(round(std1, 3)) + "   " + "sharpe1:" + str(round(sharpe1, 3)) + "   " \
                                                                                                                 '\n' + "avgnum:" + str(
        round(avgnum, 3)))
tlist = [2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15]
nday = 2000
for dd in tlist:
    a = get_result(dd, nday)
    turn = list(a["turn"])
    position = list(a["position"])
    deltaspread = list(a["deltaspread"])
    accprofit1 = [0]
    accprofit0 = [0]
    for i in range(1, len(a)):
        accprofit1.append(accprofit1[-1] + position[i - 1] * deltaspread[i] - turn[i] * 2)
        accprofit0.append(accprofit0[-1] + position[i - 1] * deltaspread[i] - turn[i] * 0)
    a["accprofit1"] = accprofit1
    a["accprofit0"] = accprofit0
    grouped1 = a['accprofit1'].groupby(a['date']).last()
    grouped0 = a['accprofit0'].groupby(a['date']).last()
    import numpy as np

    x1 = list(grouped1)
    xx1 = [x1[0]]
    for i in range(1, len(x1)):
        xx1.append(x1[i] - x1[i - 1])

    x0 = list(grouped0)
    xx0 = [x0[0]]
    for i in range(1, len(x0)):
        xx0.append(x0[i] - x0[i - 1])

    mean0 = np.mean(xx0)
    mean1 = np.mean(xx1)
    std0 = np.std(xx0)
    std1 = np.std(xx1)
    sharpe0 = mean0 / std0
    sharpe1 = mean1 / std1
    avgnum = sum(turn[1:]) / (2 * 250)
    # line(a.loc[:,["date","accprofit1","accprofit0"]])
    print('\n' + "模型：前2000个bar回归" + "   " + "开仓范围：|testspread|>(stddeltaspread*stddeltaspread* %s)" % dd + "   " \
                                                                                                           '\n' + "无手续：" + "mean0:" + str(
        round(mean0, 3)) + "   " + "std0:" + str(round(std0, 3)) + "   " + "sharpe0:" + str(round(sharpe0, 3)) + "   " \
                                                                                                                 '\n' + "手续为1：" + "mean1:" + str(
        round(mean1, 3)) + "   " + "std1:" + str(round(std1, 3)) + "   " + "sharpe1:" + str(round(sharpe1, 3)) + "   " \
                                                                                                                 '\n' + "avgnum:" + str(
        round(avgnum, 3)))
import pandas as pd
pd.set_option('display.max_columns', None)
pd.set_option('display.max_rows', None)
line(a.loc[:,["date","stddeltaspread","spread1","testspread"]])
#HC和RB
#数据预处理：
#deltaspread 的范围:将deltaspread绝对值大于5的视为异常值，将其强行修改为0
#回归模型：
#前1000个bar,只添加一次项；
#计算过程（最优参数）：
#stddeltaspread：前1000个bar
#ddd:stddeltaspread * stddeltaspread * 8
import pandas as pd
pd.set_option('display.max_columns', None)
pd.set_option('display.max_rows', None)