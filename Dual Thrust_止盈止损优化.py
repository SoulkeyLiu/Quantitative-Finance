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
c:select date,time,Instrument,symbol,open,close,high,low,volume from ej[`date`symbol;a;b]
};
''',pandas=True)
conn(r'''
f_par:{[cgr_data;n;k1;k2;b1;b2]
stg_DT_v1:cgr_data;
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

stg_DT_range:select date,Range,BuyLine,SellLine,ATR_rate,hf_ATR_rate:max[ATR_rate]%2 from stg_DT_par;
stg_DT_v2:ej[`date;stg_DT_range;stg_DT_v1];

stg_DT_v2:select date,time,Instrument,symbol,open,close,high,low,volume,Range,BuyLine,SellLine,ATR_rate,hf_ATR_rate from stg_DT_v2 where date>(first date)+n;

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
ATR_rate=conn(r'''f_ATR_rate:{[Category;n;k1;k2]
stg_DT_v1:func_cgr[Category];
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
stg_DT_ATR:f_ATR_rate[`j;20;0.36;0.36];
select first ATR_rate by date from stg_DT_ATR
''',pandas=True)

plt.plot(ATR_rate)
conn(r'''

func_DT:{[begdate;enddate;data]

trade_indicator:select date,time,symbol,open,close,volume,position,N,k1,k2,b1,b2,hf_ATR_rate
                    from data where date within(begdate,enddate);

hdq_CmRet: select 
        DailyRet:sum minRet,
        cm_ret:last cm_ret,
        turnover:sum diat_k,
        N:first N,
        k1:first k1,
        k2:first k2,
        b1:first b1,
        b2:first b2,
        hf_ATR_rate:first hf_ATR_rate
by date
from (
        update cm_ret:sums minRet  
        from (min_ret:select date,diat_k:abs[position-prev position],N,k1,k2,b1,b2,hf_ATR_rate,
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
        b2:first b2,
        hf_ATR_rate:first hf_ATR_rate
         from hdq_CmRet
};


''', pandas=True)
# k1,k2对称
# 不包含止盈止损优化
conn(r'''
main:{[Category;n;begdate;enddate]
cgr_data:func_cgr[Category];
k1:-0.02;
k2:-0.02;
result:();
b0:exec last hf_ATR_rate from func_DT[begdate;enddate;f_par[cgr_data;n;k1;k2;0;0]];
kc:50;
bc:10;
b10:0.9*b0;
b20:1.1*b0;

do[kc;k1:k1+0.02;k2:k1;b1:b10;do[bc;b1:b1+0.1*b0;b2:b20;do[bc;b2:b2-0.1*b0;result:result uj func_DT[begdate;enddate;f_par[cgr_data;n;k1;k2;b1;b2]]]]];
select from result where sharpe=max[sharpe]
};
''',pandas=True)
#以下包含止盈止损优化
conn(r'''tp_sl:{[tp_sl_data;p;q]

tp_sl_data:update tp_sl_pst:-1 from tp_sl_data where (sig=-1) and (open>BuyLine);
tp_sl_data:update tp_sl_pst:1 from tp_sl_data where (sig=1) and (open<SellLine);

tp_sl_data:update tp_sl_pst:0 from tp_sl_data where ATR_rate>b1;
tp_sl_data:update tp_sl_pst:0 from tp_sl_data where ATR_rate<b2;

tp_sl_data:update mRet:0^((position*(log (close%open)))-(0.0002*abs deltas position)) from tp_sl_data;
tp_sl_data:update mMaxdd:1-exp neg (maxs sums mRet)-(sums mRet) from tp_sl_data;

tp_sl_data:update tp_maxdd:mMaxdd%(sums mRet) from tp_sl_data;

tp_sl_data:update sl_maxdd:open from tp_sl_data where prev[position]=0 and position<>0;
tp_sl_data:update sl_maxdd:fills sl_maxdd from tp_sl_data;
tp_sl_data:update sl_maxdd:((position*(log (sl_maxdd%open)))-(0.0002*abs deltas position)) from tp_sl_data;

tp_sl_data:update tp_sl_pst:0 from tp_sl_data where tp_maxdd>p;
tp_sl_data:update tp_sl_pst:0 from tp_sl_data where sl_maxdd<q;


tp_sl_data:update tp_sl_pst:fills tp_sl_pst from tp_sl_data;
tp_sl_data:update tp_sl_pst:0^tp_sl_pst from tp_sl_data;

tp_sl_data:update position:tp_sl_pst from tp_sl_data;

tp_sl_data:update p:p from tp_sl_data;
tp_sl_data:update q:q from tp_sl_data

};
cgr_data:func_cgr[`rb];
tp_sl_data:f_par[cgr_data;20;0.44;0.44;0.028;0.0028];

count select from tp_sl[tp_sl_data;0.1;0.1] where tp_sl_pst<>0 
''',pandas=True)
# 包含止盈止损优化
conn(r'''main_tp_sl:{[Category;n;begdate;enddate;p_max;q_max]

opt_para:main[Category;n;begdate;enddate];
k1:exec first k1 from opt_para;
k2:exec first k2 from opt_para;
b1:exec first b1 from opt_para;
b2:exec first b2 from opt_para;

cgr_data:func_cgr[Category];
tp_sl_data:f_par[cgr_data;n;k1;k2;b1;b2];

pb:0;
qb:0;
pc:10;
qc:10;
p:0;

result_tp_sl:();

do[10;q:0;p:p+0.01;do[10;q:q+0.01;result_tp_sl:result_tp_sl uj func_DT_tp_sl[begdate;enddate;tp_sl[tp_sl_data;p;q]]]];

select from result_tp_sl where sharpe=max[sharpe]

};

''',pandas=True)
# 不包含止盈止损优化
# main_tp_sl[Category;n;begdate;enddate;q_max;p_max]
conn(r'''
main_tp_sl[`rb;20;2016.01.31;2018.06.30;0.2;-0.2]
''',pandas=True)
line_mRet_wc=conn(r'''

func_mRet_wc:{[begdate;enddate;data]

trade_indicator:select date,time,symbol,open,close,volume,position
                    from data where date within(begdate,enddate);

min_ret:select date,cm_mRet:sums minRet 
            from (select date,minRet:0^((position*(log (close%open)))-(0.0002*abs deltas position)) from trade_indicator)
            where minRet<>0;
cum_mRet:select date:last date,cm_mRet:last cm_mRet by date from min_ret
};

func_mRet_wc[2011.04.15;2018.06.30;ud_position]
''', pandas=True)
# nvline(line_mRet_wc)
plt.plot(line_mRet_wc)