import numpy as np
import statsmodels.api as sm
from statsmodels.tsa.stattools import adfuller
import pandas as pd
from scipy import stats
from numpy import concatenate
from pandas import DataFrame
from qpython import qconnection
conn = qconnection.QConnection('localhost')
conn.open()
day1=conn(r'''
string date where date>2018.05.31
''',pandas=True)
number=conn(r'''
count date where date>2018.05.31
''',pandas=True)
print(day1[18].decode('utf-8'))
print(number)
df=DataFrame(np.ones((1,4),float,1),columns=['up','mean','down','res'])
def sca(day,sym1,sym2):
    conn(r'''
    getData: {[day;sym1;sym2]
        data1:select date,time:?[time>17:00;time-24:00;time],price1:price from futtick where date=day, symbol=sym1;
        data2:select date,time:?[time>17:00;time-24:00;time],price2:price from futtick where date=day, symbol=sym2;
        aj[`time;data2;data1]
        };
    ''')
    data=conn('getData[%s;%s;%s]'%(day,sym1,sym2),pandas=True)
    return data

for i in range(1,number,1):
    data1=sca(day1[i-1].decode('utf-8'),'`AP810','`AP812')
    datanext=sca(day1[i].decode('utf-8'),'`AP810','`AP812')
    data1=data1.values
    price1=data1[:,3]
    price2=data1[:,2]
    price1=np.array(price1,dtype='float')
    price2=np.array(price2,dtype='float')
    #线性回归增加常数项 y=kx+b
    price11=sm.add_constant(price1)
    # 进行最小二乘回归
    result = (sm.OLS(price2,price11)).fit()
    # 回归函数的常数项
    a=result.params[0]
    # 取得回归函数的参数项
    b=result.params[1]
    one=np.ones(((len(price1)),1),float)
    # 检验在时间窗口的长度下合约序列是否为协整
    result1 = sm.tsa.stattools.coint(price2, price1)
    # 取出并记录p值
    pvalue = result1[1]
    up=np.zeros(((len(price1)),1),float)
    down=np.zeros(((len(price1)),1),float)
    mean=np.zeros(((len(price1)),1),float)
    res1=np.zeros(((len(price1)),1),float)
    res0=price2 - b*price1 - a*one
    #res0=np.array(res0)
    if pvalue<0.05:
        backtest=True
        datanext=datanext.values
        price11=datanext[:,3]
        price22=datanext[:,2]
        price=np.ones((len(price11)),float,1)
        res1 = price22 -  b*price11-a*price
        std = np.std(res0)
        mean = np.mean(res0)
        interval=stats.t.interval(0.95,len(res1)-1,mean,std)
        up_limit = interval[1]
        down_limit=interval[0]
        up=(price*up_limit).reshape(len(price),1)
        down=(price*down_limit).reshape(len(price),1)
        print(backtest)
#以下为手动设置上下限以及止损线
#up_limit=mean + entry * std
#down_limit = mean - entry *std
#up_out_limt=mean+out*std
#down_out_limt=mean-out*std
        mean=(price*mean).reshape(len(price),1)
        res1=res1.reshape(len(price),1)
    data1=concatenate((up,mean),axis=1)
    data2= concatenate((data1,down),axis=1)
    data3= concatenate((data2,res1),axis=1)
    data3=DataFrame(data3,columns=['up','mean','down','res'])
    df=pd.concat([df,data3],axis=0)
conn('{`data_m set x}', df)
conn(r'''
data1:select datetime:date+time,date,time,price1:price,buy1,sell1 from futtick where date>2018.06.01,symbol=`AP810;
data2:select datetime:date+time,date,time,price2:price,bid1:buy1,ask1:sell1 from futtick where date>2018.06.01,symbol=`AP812;
data22:aj[`datetime;data2;data1];
data_m:1_data_m;
data_m1:data22 ^ data_m;
data_ming:update sig:-1 from data_m1 where res>up;
data_ming:update sig:1 from data_ming where res<down;
data_ming:update sig:0 from data_ming where 0>=res*prev res;
data_ming:update 0^fills sig from data_ming;
data_ming:update dif:price2-price1 from data_ming;
data_ming:update Ret:(prev sig)*(dif-(prev dif)) from data_ming; 
data_ming:update k:1 from data_ming;
data_ming:update turnover:abs deltas sig from data_ming;
data_ming:update cost:((ask1-price2)+(price1-buy1)) from data_ming where (((prev sig)=0) and (sig=1));
data_ming:update cost:((price2-bid1)+(sell1-price1)) from data_ming where (((prev sig)=0) and (sig=-1));
data_ming:update cost:((price2-bid1)+(sell1-price1)) from data_ming where (((prev sig)=1) and (sig=0));
data_ming:update cost:((ask1-price2)+(price1-buy1)) from data_ming where (((prev sig)=-1) and (sig=0));
data_ming:update cost:0^cost from data_ming;
''',pandas=True)
conn(r'''
funct:{[begdate;enddate]
trade_indicator:select date,time,price1,price2,sig,dif,k,Ret,cost,turnover from data_ming where date within(begdate,enddate);
hdq_CmRet1::select 
        DailyRet:sum minRet , 
        cm_ret:last cm_ret, 
        number:sum k,
        turnover:sum turnover
by date
from (
        update cm_ret:sums minRet  
        from (min_ret:select date,time,sig,turnover,k,
        minRet:0^log(1+((Ret-cost)%(price1+price2))) 
        from (select date,time,sig,price1,price2,Ret,cost,k,turnover from trade_indicator)));
hdq_test_result:select  
        sharpe:(250*(avg DailyRet)) % ((sqrt 250)*(dev DailyRet)),
        annual_ret:250*(avg DailyRet), 
        annual_vol :(sqrt 250)*(dev DailyRet),
        cum_ret: last cm_ret, 
        maxdd: 1-exp neg max (maxs sums DailyRet)-(sums DailyRet), 
        win_pro: (sum DailyRet>0) % ((sum DailyRet>0)+(sum DailyRet <0)),
        turnover_rate:(sum turnover)% (sum number)
         from hdq_CmRet1
};
''', pandas=True)
result=conn(r'''
funct[2018.06.01;2018.06.29]
''',pandas=True)
print(result)