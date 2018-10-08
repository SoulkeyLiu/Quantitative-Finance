from qplot import nvline
import numpy as np
import statsmodels.api as sm
from statsmodels.tsa.stattools import adfuller
import pandas as pd
from scipy import stats
from numpy import concatenate
from pandas import DataFrame
from qpython import qconnection
# 找出18年焦炭每天的主力合约及其对应的各个量
conn(r'''
aaa:select symbol:first symbol@idesc sum_volume, sum_volume: first sum_volume@idesc sum_volume by date 
        from select sum_volume:sum volume by date,symbol from `i;
bbb:select date,time,symbol,high,low,close from `i;
ccc:ej[`date`symbol;aaa;bbb];
''',pandas=True)
data=conn(r'''
select date,time,symbol,high:fills high,low:fills low,close from ccc
''',pandas=True)
number=conn(r'''
count ccc
''',pandas=True)
print(number)
#data=data.decode('utf-8')
df=DataFrame(np.ones((1,1),float,1),columns=['beta'])
data1=data.values
for i in range(0,(number-1200),1):
    min1=data1[i:i+1199,4]
    max1=data1[i:i+1199,3]
    min1=np.array(min1,dtype='float')
    max1=np.array(max1,dtype='float')
    b,intercept, r_value, p_value, slope_std_error = stats.linregress(min1,max1)
#线性回归增加常数项 y=kx+b
# 进行最小二乘回归
# 回归函数的常数项
# 取得回归函数的参数项
    b=b.reshape(1,1)
    b=np.array(b,dtype='float')
    b=DataFrame(b,columns=['beta'])
    df=pd.concat([df,b],axis=0)
    #df=np.concatenate((df,b),axis=1)
    conn('{`data_m3 set x}', df)
    conn(r'''
    data_m3:1_data_m3;
    k3:select date,time,symbol,high,low,close from (ccc);
    k3:1200_k3;
    k3:k3^data_m3;
    k3:120000_update mean1:(120000 mavg beta),std1:(120000 mdev beta) from k3;
    k3:update up:(mean1+0.95*std1),down:(mean1-0.95*std1) from k3;
    k3:update position:1 from k3 where beta>up;
    k3:update position:-1 from k3 where beta<down;
    k3:update position:0^fills position from k3;
    k3:update position:0 from k3 where symbol<>(next symbol);
    k3:update minRet:0^((position*((((next close)-close)%close)))-(0.0002*abs deltas position)) from k3;
    ''', pandas=True)
    conn(r'''

    func:{[begdate;enddate;data]

    trade_indicator:select date,time,symbol,close,position
                        from data where date within(begdate,enddate);

    hdq_CmRet: select 
            DailyRet:sum minRet,
            cm_ret:last cm_ret,
            turnover:sum diat_k
    by date
    from (
            update cm_ret:sums minRet  
            from (min_ret:select date,diat_k:abs[position-prev position],
                                    minRet:0^((position*((((next close)-close)%close)))-(0.0002*abs deltas position))
                            from trade_indicator));      

    hdq_test_result:select  
            sharpe:(230*(avg DailyRet)) % ((sqrt 230)*(dev DailyRet)),
            annual_ret:230*(avg DailyRet), 
            annual_vol :(sqrt 230)*(dev DailyRet),
            turnover: avg turnover,
            cum_ret: last cm_ret, 
            maxdd: 1-exp neg max (maxs sums DailyRet)-(sums DailyRet), 
            win_pro: (sum DailyRet>0) % ((sum DailyRet>0)+(sum DailyRet <0))
             from hdq_CmRet

    };


    ''', pandas=True)
    conn(r'''
    func[2011.01.01;2018.06.30;k3]
    ''', pandas=True)