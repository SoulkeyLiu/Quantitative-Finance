from qplot import nvline,line
from matplotlib import pyplot as plt
from qpython import qconnection
conn = qconnection.QConnection('localhost')
conn.open()
conn(r'''
func_cgr:{[Category]
a:select symbol:first symbol@idesc sum_volume, sum_volume: first sum_volume@idesc sum_volume by date 
        from select sum_volume:sum volume by date,symbol from Category;
b:select date,time,Instrument,symbol,open,close,high,low,volume from Category;
c:ej[`date`symbol;a;b]
};
''',pandas=True)
conn(r'''f_par:{[n;k1;k2]
stg_DT_v1:table_j;
stg_DT_par:select open:first open,HH:max[high],LC:min[close],HC:max[close],LL:min[low] 
            by date from stg_DT_v1;
stg_DT_par:select date,open,m20_HH:prev[n mmax HH],
                          m20_LC:prev[n mmin LC],
                          m20_HC:prev[n mmax HC],
                          m20_LL:prev[n mmin LL]
           from stg_DT_par;
stg_DT_par:update Range:?[((m20_HH-m20_LC)>=(m20_HC-m20_LL));(m20_HH-m20_LC);(m20_HC-m20_LL)] from stg_DT_par;
stg_DT_par:update BuyLine:open+k1*Range from stg_DT_par;
stg_DT_par:update SellLine:open-k2*Range from stg_DT_par;
stg_DT_range:select date,Range,BuyLine,SellLine from stg_DT_par;
stg_DT_v2:ej[`date;stg_DT_range;stg_DT_v1];
stg_DT_v2:select date,time,Instrument,symbol,open,close,high,low,volume,BuyLine,SellLine from stg_DT_v2 where date>first date;
ud_position:stg_DT_v2;
ud_position:update sig:1 from ud_position where (prev open)<open;
ud_position:update sig:-1 from ud_position where (prev open)>open;
ud_position:update sig:fills sig from ud_position;
ud_position:update sig:0^sig from ud_position;
ud_position:update position:-1 from ud_position where (sig=-1) and (open>BuyLine);
ud_position:update position:1 from ud_position where (sig=1) and (open<SellLine);
ud_position:update position:fills position from ud_position;
ud_position:update position:0^position from ud_position;
ud_position:update N:n from ud_position;
ud_position:update k1:k1 from ud_position;
ud_position:update k2:k2 from ud_position
};
ud_position:f_par[20;0.75;0.2];
select from 5#ud_position
''',pandas=True)
conn(r'''
func_DT:{[begdate;enddate;data]
trade_indicator:select date,time,symbol,open,close,volume,position,N,k1,k2
                    from data where date within(begdate,enddate);
hdq_CmRet: select 
        DailyRet:sum minRet,
        cm_ret:last cm_ret,
        turnover:sum diat_k,
        N:first N,
        k1:first k1,
        k2:first k2
by date
from (
        update cm_ret:sums minRet  
        from (min_ret:select date,diat_k:abs[position-prev position],N,k1,k2,
                                minRet:0^((position*(log (close%open)))-(0.00015*abs deltas position))
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
        k2:first k2
         from hdq_CmRet
};
''', pandas=True)
conn(r'''
table_j:select date,time,Instrument,symbol,open,close,high,low,volume from func_cgr[`rb];
''',pandas=True)
# k1,k2非对称
conn(r'''
k1:0;
result:();
do[100;k1:k1+0.01;k2:0;do[100;k2:k2+0.01;ud_position:f_par[20;k1;k2];result:result uj func_DT[2016.01.01;2018.05.31;ud_position]]];
select from result where sharpe=max[sharpe]
''',pandas=True)
# k1,k2对称
conn(r'''
k1:0;
result:();
do[200;k1:k1+0.005;k2:k1;do[1;ud_position:f_par[20;k1;k2];result:result uj func_DT[2011.04.15;2018.05.31;ud_position]]];
select from result where sharpe=max[sharpe]
''',pandas=True)
conn(r'''
ud_position:f_par[20;0.74;0.74];
''',pandas=True)
line_mRet=conn(r'''

func_mRet:{[begdate;enddate;data]

trade_indicator:select date,time,open,close,position
                    from data where date within(begdate,enddate);

min_ret:select date,cm_minRet:sums minRet 
            from (select date,minRet:0^(position*(log (close%open))) from trade_indicator)
            where minRet<>0;
cum_mRet:select date:last date,cm_minRet:last cm_minRet by date from min_ret
};

func_mRet[2011.04.15;2018.05.31;ud_position]
''', pandas=True)
# nvline(line_mRet)
plt.plot(line_mRet)
line_mRet_wc=conn(r'''

func_mRet_wc:{[begdate;enddate;data]

trade_indicator:select date,time,symbol,open,close,volume,position
                    from data where date within(begdate,enddate);

min_ret:select date,cm_mRet:sums minRet 
            from (select date,minRet:0^((position*(log (close%open)))-(0.00015*abs deltas position)) from trade_indicator)
            where minRet<>0;
cum_mRet:select date:last date,cm_mRet:last cm_mRet by date from min_ret
};

func_mRet_wc[2011.04.15;2018.05.31;ud_position]
''', pandas=True)
# nvline(line_mRet_wc)
plt.plot(line_mRet_wc)