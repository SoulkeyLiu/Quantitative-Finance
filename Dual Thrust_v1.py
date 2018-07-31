from qplot import nvline
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
table_j:select date,time,Instrument,symbol,open,close,high,low,volume from func_cgr[`j];
5#select from table_j
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
stg_DT_par:update BuyLine:prev[open]+k1*Range from stg_DT_par;
stg_DT_par:update SellLine:prev[open]-k2*Range from stg_DT_par;

stg_DT_range:select date,Range,BuyLine,SellLine from stg_DT_par;
stg_DT_v2:ej[`date;stg_DT_range;stg_DT_v1];

stg_DT_v2:select date,time,Instrument,symbol,open,close,high,low,volume,BuyLine,SellLine from stg_DT_v2 where date>first date
};
stg_DT_v2:f_par[20;0.6;0.6];
5#select from stg_DT_v2

''',pandas=True)
#更新头寸
conn(r'''
ud_position:stg_DT_v2;
ud_position:update position:1 from ud_position where open>BuyLine;
ud_position:update position:-1 from ud_position where open<SellLine;
ud_position:update position:0^position from ud_position;
''',pandas=True)
conn(r'''
func_DT:{[begdate;enddate;data]
trade_indicator:select date,time,symbol,open,close,volume,position
                    from data where date within(begdate,enddate);
hdq_CmRet: select 
        DailyRet:sum minRet,
        cm_ret:last cm_ret,
        turnover:sum diat_k
by date
from (
        update cm_ret:sums minRet  
        from (min_ret:select date,diat_k:abs[position-prev position],
                                minRet:0^((position*log close%open)-(0.00015*abs deltas position))
                        from trade_indicator));      
hdq_test_result:select  
        sharpe:(250*(avg DailyRet)) % ((sqrt 250)*(dev DailyRet)),
        annual_ret:250*(avg DailyRet), 
        annual_vol :(sqrt 250)*(dev DailyRet),
        turnover: avg turnover,
        cum_ret: last cm_ret, 
        maxdd: 1-exp neg max (maxs sums DailyRet)-(sums DailyRet), 
        win_pro: (sum DailyRet>0) % ((sum DailyRet>0)+(sum DailyRet <0))
         from hdq_CmRet
};
func_DT[2011.04.15;2018.05.31;ud_position]
''', pandas=True)
line_mRet=conn(r'''
func_mRet:{[begdate;enddate;data]
trade_indicator:select date,time,symbol,open,close,volume,position
                    from data where date within(begdate,enddate);
min_ret:select date,sums minRet 
            from (select date,minRet:0^((prev position)*log (open%prev close)-(0.00006*abs deltas position)) from trade_indicator)
            where minRet<>0
};
func_mRet[2011.04.15;2018.05.31;ud_position]
''', pandas=True)
nvline(line_mRet)