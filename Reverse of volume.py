\l /db/future1
\c 1000 1000
instru:`RB
begdate:2010.01.01
enddate:2015.01.01
k1:1
m:4
t1:3
t2:9

trade_indicator:select from (ungroup select time,symbol,date,instrument:instru,volume,close,high,low,
                    pclose:prev close,phigh:prev high,plow:prev low,pvolume:prev volume
                    by date from bar1[instru]) where date within(begdate,enddate);

/标记放量
//找出放量的点Q1
trade_indicator:update Q1:1 by date from trade_indicator where (volume>(60 mavg volume)) and ((volume%pvolume)>m) and (close>pclose);
//找出前一分钟放量，当前缩量的点Q
trade_indicator:update Q:1 by date from trade_indicator where ((prev Q1)=1) and ((volume%pvolume)<0.5);
//以Q点为起始点，设定其后t1分钟为判断区间
trade_indicator:update qq:t1 msum Q by date from trade_indicator;
instru:`RB
begdate:2015.01.01
enddate:2017.01.01
k1:0.5
m:4
t1:5
t2:5

trade_indicator:select from (ungroup select time,symbol,date,instrument:instru,volume,close:(high+low)%2,high,low,
                    pclose:prev close,phigh:prev high,plow:prev low,pvolume:prev volume
                    by date from bar1[instru]) where date within(begdate,enddate);

/标记放量
//找出放量的点Q1
trade_indicator:update Q1:1 by date from trade_indicator where (volume>(60 mavg volume)) and ((volume%pvolume)>m) and (close>pclose);
//找出前一分钟放量，当前缩量的点Q
trade_indicator:update Q:1 by date from trade_indicator where ((prev Q1)=1) and ((volume%pvolume)<0.5);
//以Q点为起始点，设定其后t1分钟为判断区间
trade_indicator:update qq:t1 msum Q by date from trade_indicator;

/设定轨道
//在Q点计算pivot和line1
trade_indicator:update pivot:((high+low)%2) from trade_indicator where (Q=1) and ((prev qq)=0);
trade_indicator:update line1:(pivot+(k1*(high-low)))  from trade_indicator where (Q=1) and ((prev qq)=0);
//在判断区间内填充line1
trade_indicator:update line1:fills line1 from trade_indicator where qq>0;

/判断是否跌破下界
//在判断区间的第二个点处开始对是否开仓进行判断，若开仓，则持仓t2分钟
trade_indicator:update position:-1 from trade_indicator where (close<line1) and (qq>0) and ((prev qq)>0);
//设置止损线
trade_indicator:update line2:line1*1.0025 from trade_indicator where (position=-1);
trade_indicator:update line2:t2 mavg line2 from trade_indicator;
trade_indicator:update position:0 from trade_indicator where (close>line2);
//设置止盈线
trade_indicator:update line3:line1*0.9975 from trade_indicator where (position=-1);
trade_indicator:update line3:t2 mavg line3 from trade_indicator;
trade_indicator:update position:0 from trade_indicator where (close<line3);

trade_indicator:update position:0 by date from trade_indicator where ((t2 xprev position)=-1);
trade_indicator:update position:0^fills position by date from trade_indicator;

getret: {[begdate; enddate;instru; k1; m; t1;t2]
trade_indicator: select from (ungroup select time, symbol, date, instrument:instru, volume, close:(high+low) % 2, high, low,
pclose: prev close, phigh: prev high,plow: prev low, pvolume: prev volume by date from bar1 [instru]) where date within(begdate, enddate);
/ 标记放量
  // 找出放量的点Q1
trade_indicator: update Q1: 1 by date from trade_indicator where (volume > (60 mavg volume)) and ((volume % pvolume) > m) and (close > pclose);
// 找出前一分钟放量，当前缩量的点Q
trade_indicator: update Q: 1 by date from trade_indicator where ((prev Q1)=1) and ((volume % pvolume) < 0.5);
// 以Q点为起始点，设定其后t1分钟为判断区间
trade_indicator: update qq: t1 msum Q by date from trade_indicator;
/ 设定轨道
  // 在Q点计算pivot和line1
trade_indicator: update pivot: ((high + low) % 2)from trade_indicator where (Q=1) and ((prev qq)=0);
trade_indicator: update line1: (pivot + (k1 * (high - low))) from trade_indicator where (Q=1) and ((prev qq)=0);
// 在判断区间内填充line1
trade_indicator: update line1: fills line1 from trade_indicator where qq > 0;
/ 判断是否跌破下界
  // 在判断区间的第二个点处开始对是否开仓进行判断，若开仓，则持仓t2分钟
trade_indicator: update position: -1 from trade_indicator where (close < line1) and (qq > 0) and ((prev qq) > 0);
trade_indicator: update line2: line1 * 1.002 from trade_indicator where (position=-1);
trade_indicator: update line2: t2 mavg line2 from trade_indicator;

trade_indicator: update position: 0 from trade_indicator where (close > line2);
trade_indicator: update position: 0 by date from trade_indicator where ((t2 xprev position)=-1);
trade_indicator: update position: 0 ^ fills position by date from trade_indicator;
// 设置止盈线
trade_indicator: update line3: line1 * 0.998 from trade_indicator where (position=-1);
trade_indicator: update line3: t2 mavg line3 from trade_indicator;
trade_indicator: update position: 0 from trade_indicator where (close < line3);
trade_indicator: update turn: abs(position - prev position) from trade_indicator;
retdata: () xkey select instrument: first instrument, k1: k1, m: m, t1: t1, t2: t2, sum turn,
DailyRet: 0 ^ log((exp(sum MinRet)) - (sum turn * 0.0002)),
day_win: 0 ^ (sum MinRet > 0) % sum ?[position <> 0; 1; 0] by date from
(select date, instrument, close, position, turn, MinRet:0 ^ ((prev position) * (log(close % prev close)))
from trade_indicator)};
getperf: {[begdate;enddate;instru;k1;m;t1;t2]
retdata: getret[begdate;enddate;instru;k1;m;t1;t2];
result: () xkey select instrument: first instrument,k1: first k1,m: first m,t1: first
t1, t2: first t2,
cum_ret: exp sum DailyRet,
annual_ret: 365 * (sum DailyRet) % ((max date) - (min date)),
annual_vol: (sqrt 365) * (dev DailyRet),
sharpe: (365 * (sum DailyRet) % ((max date) - (min date))) % ((sqrt 365) * (dev DailyRet)),
maxdd: 1 - exp neg max(maxs sums DailyRet)-(sums DailyRet),
win_pro: (sum(DailyRet > 0)) % (sum(day_win > 0)),
trade_num: avg turn from retdata where not null date};
/t1:判断时间
/t2:持仓时间
/k1:波动系数
/m:放量倍数

dayret:
    raze{[m]
    raze{[t1;m]
    raze{[t1;t2;m]
        raze{[k1;t1;t2;m]
            raze getperf[2015.01.01;2017.01.01;;k1;m;t1;t2] each key bar1
            } '[(-2)+(til 10)%2;t1;t2;m]
        }'[t1;(3+til 5);m]
    }'[3+(2*(til 2));m]
    }'[3+til 3]
getperf[2010.01.01;2017.01.01;`RB;-2;4;5;10]
dayret:select from dayret where not null instrument;
/dayret
bestperf:`sharpe xdesc select max sharpe,cum_ret:cum_ret@first idesc sharpe,annual_ret:annual_ret@first idesc sharpe,k1:k1@first idesc sharpe,m:m@first idesc sharpe,t1:t1@first idesc sharpe,t2:t2@first idesc sharpe,win_pro:win_pro@first idesc sharpe by instrument from dayret;
bestperf