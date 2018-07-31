from qplot import nvline
from qpython import qconnection
conn = qconnection.QConnection('localhost')
conn.open()
conn(r'''\v''',pandas=True)
# 找出18年焦炭每天的主力合约及其对应的各个量
conn(r'''
a:select symbol:first symbol@idesc sum_volume, sum_volume: first sum_volume@idesc sum_volume by date 
        from select sum_volume:sum volume by date,symbol from `zn;
b:select date,time,symbol,open,close,volume from `zn;
c:ej[`date`symbol;a;b];
trade:c;
trade:update position:-1 from trade where (time=-03:00) and (open>prev close);
trade:update position:1 from trade where (time=-03:00) and (open<prev close);
trade:update position:0^position from trade;
select from trade where (time=-03:00);
''',pandas=True)
conn(r'''
func:{[begdate;enddate;data]
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
         from hdq_CmRet};
''', pandas=True)
#回测
conn(r'''
func[2016.01.01;2018.05.31;trade]
''',pandas=True)
line_mRet_wc=conn(r'''
func_mRet_wc:{[begdate;enddate;data]
trade_indicator:select date,time,symbol,open,close,volume,position
                    from data where date within(begdate,enddate);
min_ret:select date,sums minRet 
            from (select date,minRet:0^(position*log close%open)-(0.00006*abs deltas position) from trade_indicator)
            where minRet<>0};
func_mRet[2011.04.15;2018.05.31;trade]
''', pandas=True)
nvline(line_mRet_wc)