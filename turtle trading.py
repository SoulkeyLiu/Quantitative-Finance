from qpython import qconnection
conn = qconnection.QConnection('localhost')
conn.open()
data=conn(r'''
table1:60_select date,time,close,mavg20:20 mavg close,mavg60:60 mavg close from rb; 
table1:update position:1 from table1 where mavg20>mavg60;
table1:update position:-1 from table1 where mavg20<mavg60; 
table1:update position:0^position from table1;
table1:update return:sums 0^position*((next close)-close) from table1;
table1
''',pandas=True)
from qplot import *
from qpython import qconnection
conn = qconnection.QConnection('localhost')
conn.open()
data = conn(r'''
       f1:{[cost;x;y] $[y>x+cost;y-cost;y<x-cost;y+cost;x]};
       f2:{[cost; series] 
       t0: f1[cost] scan series;
       fills reverse fills reverse?[(t0>prev t0)&(not null prev t0);1;?[t0<prev t0;-1;0N]]
       };
       data: bar[`j]
       data1:update sig: f2[10;p] from data
       data1:update k: (fills reverse fills reverse?[((-1 xprev sig)*sig)=-1;p;0n]) - p from data1
       data2:update lable:fills reverse fills reverse?[((-1 xprev sig)*sig)=-1;p;0n] from data1
       data3:update lable1:abs(p - ?[((-1 xprev sig)*sig)=-1;-1 xprev lable;lable]) from data2
    ''',pandas=True)
conn.close()
nvline(data)