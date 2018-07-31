from qplot import nvline,line
from matplotlib import pyplot as plt
from qpython import qconnection
conn = qconnection.QConnection('locahost')
conn.open()
conn(r'''
func_cgr:{[Category]
a:select symbol:first symbol@idesc sum_volume, sum_volume: first sum_volume@idesc sum_volume by date 
        from select sum_volume:sum volume by date,symbol from Category;
b:select date,time,Instrument,symbol,open,close,high,low,volume from Category;
c:ej[`date`symbol;a;b]
};

''',pandas=True)
conn(r'''f_par:{[n;k1;k2;b1;b2]
stg_DT_v1:table_j;
stg_DT_par:select open:first open,close:last close,
                  HH:max[high],LC:min[close],HC:max[close],LL:min[low]
            by date from stg_DT_v1;
stg_DT_par:update TR:max((HH-LL),abs[HH-prev close],abs[LL-prev close]) by date from stg_DT_par;
stg_DT_par:select date,open,close,m20_HH:prev[n mmax HH],
                                  m20_LC:prev[n mmin LC],
                                  m20_HC:prev[n mmax HC],
                                  m20_LL:prev[n mmin LL],
                                  ATR:prev[n mavg TR]
           from stg_DT_par;
stg_DT_par:update Range:?[((m20_HH-m20_LC)>=(m20_HC-m20_LL));(m20_HH-m20_LC);(m20_HC-m20_LL)] from stg_DT_par;
stg_DT_par:update BuyLine:open+k1*Range from stg_DT_par;
stg_DT_par:update SellLine:open-k2*Range from stg_DT_par;
stg_DT_par:update ATR_rate:ATR%(prev close) from stg_DT_par;

stg_DT_range:select date,Range,BuyLine,SellLine,ATR_rate from stg_DT_par;
stg_DT_v2:ej[`date;stg_DT_range;stg_DT_v1];

stg_DT_v2:select date,time,Instrument,symbol,open,close,high,low,volume,Range,BuyLine,SellLine,ATR_rate from stg_DT_v2 where date>(first date)+n;

ud_position:stg_DT_v2;

ud_position:update sig:1 from ud_position where (prev open)<open;
ud_position:update sig:-1 from ud_position where (prev open)>open;
ud_position:update sig:fills sig from ud_position;
ud_position:update sig:0^sig from ud_position;
ud_position:update position:-1 from ud_position where (sig=-1) and (open>BuyLine);
ud_position:update position:1 from ud_position where (sig=1) and (open<SellLine);

ud_position:update position:0 from ud_position where ATR_rate>b1;
ud_position:update position:0 from ud_position where ATR_rate<b2;

ud_position:update position:fills position from ud_position;
ud_position:update position:0^position from ud_position;

ud_position:update N:n from ud_position;
ud_position:update k1:k1 from ud_position;
ud_position:update k2:k2 from ud_position;
ud_position:update b1:b1 from ud_position;
ud_position:update b2:b2 from ud_position
};

''',pandas=True)
# 画 ATR_rate 分布图
ATR_rate=conn(r'''f_par:{[n;k1;k2]
stg_DT_v1:table_j;
stg_DT_par:select open:first open,close:last close,
                  HH:max[high],LC:min[close],HC:max[close],LL:min[low]
            by date from stg_DT_v1;
stg_DT_par:update TR:max((HH-LL),abs[HH-prev close],abs[LL-prev close]) by date from stg_DT_par;
stg_DT_par:select date,open,close,m20_HH:prev[n mmax HH],
                                  m20_LC:prev[n mmin LC],
                                  m20_HC:prev[n mmax HC],
                                  m20_LL:prev[n mmin LL],
                                  ATR:prev[n mavg TR]
           from stg_DT_par;
stg_DT_par:update Range:?[((m20_HH-m20_LC)>=(m20_HC-m20_LL));(m20_HH-m20_LC);(m20_HC-m20_LL)] from stg_DT_par;
stg_DT_par:update BuyLine:open+k1*Range from stg_DT_par;
stg_DT_par:update SellLine:open-k2*Range from stg_DT_par;
stg_DT_par:update ATR_rate:ATR%(prev close) from stg_DT_par;

stg_DT_ATR:select date,ATR_rate from stg_DT_par

};
stg_DT_ATR:f_par[20;0.51;0.51];
select first ATR_rate by date from stg_DT_ATR
''',pandas=True)

plt.plot(ATR_rate)
conn(r'''

func_DT:{[begdate;enddate;data]

trade_indicator:select date,time,symbol,open,close,volume,position,N,k1,k2,b1,b2
                    from data where date within(begdate,enddate);

hdq_CmRet: select 
        DailyRet:sum minRet,
        cm_ret:last cm_ret,
        turnover:sum diat_k,
        N:first N,
        k1:first k1,
        k2:first k2,
        b1:first b1,
        b2:first b2
by date
from (
        update cm_ret:sums minRet  
        from (min_ret:select date,diat_k:abs[position-prev position],N,k1,k2,b1,b2,
                                minRet:0^((position*(log (close%open)))-(0.0002*abs deltas position))
                        from trade_indicator));      

hdq_test_result:select  
        sharpe:(250*(avg DailyRet)) % ((sqrt 250)*(dev DailyRet)),
        annual_ret:250*(avg DailyRet), 
        annual_vol :(sqrt 250)*(dev DailyRet),
        turnover: avg turnover,
        cum_ret: last cm_ret, 
        maxdd: 1-exp neg max (maxs sums DailyRet)-(sums DailyRet), 
        win_pro: (sum DailyRet>0) % ((sum DailyRet>0)+(sum DailyRet <0)),
        N:first N,
        k1:first k1,
        k2:first k2,
        b1:first b1,
        b2:first b2
         from hdq_CmRet
};


''', pandas=True)
conn(r'''
table_j:select date,time,Instrument,symbol,open,close,high,low,volume from func_cgr[`j];
''',pandas=True)
# k1,k2非对称
conn(r'''
k1:0;
result:();
do[100;k1:k1+0.01;k2:0;do[100;k2:k2+0.01;ud_position:f_par[20;k1;k2];result:result uj func_DT[2015.04.15;2018.05.31;ud_position]]];
select from result where sharpe=max[sharpe]
''',pandas=True)
# k1,k2对称
# 回测区间：2011.04.15-2018.05.31
conn(r'''
k1:0;
result:();
do[50;k1:k1+0.02;k2:k1;b1:0.04;do[5;b1:b1+0.002;b2:0.01;do[5;b2:b2+0.002;ud_position:f_par[20;k1;k2;b1;b2];result:result uj func_DT[2011.04.15;2018.06.30;ud_position]]]];
select from result where sharpe=max[sharpe]
''',pandas=True)
# k1,k2对称
# 回测区间：2016.01.31-2018.05.31
conn(r'''
k1:0;
result:();
do[50;k1:k1+0.02;k2:k1;b1:0.04;do[5;b1:b1+0.002;b2:0.01;do[5;b2:b2+0.002;ud_position:f_par[20;k1;k2;b1;b2];result:result uj func_DT[2016.01.31;2018.06.30;ud_position]]]];
select from result where sharpe=max[sharpe]
''',pandas=True)
conn(r'''
ud_position:f_par[20;0.4;0.4;0.46;0.014];
''',pandas=True)