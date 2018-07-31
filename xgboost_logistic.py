import pandas as pd
import numpy as np
import xgboost as xgb
from xgboost.sklearn import XGBClassifier
from sklearn import cross_validation, metrics
from sklearn.grid_search import GridSearchCV
from sklearn.cross_validation import train_test_split
import matplotlib.pylab as plt
from sklearn.preprocessing import LabelEncoder
from numpy import concatenate
from pandas import DataFrame
from math import sqrt
from sklearn.metrics import mean_squared_error
import time
from qpython import qconnection
conn = qconnection.QConnection('localhost')
conn.open()
# load data
conn(r'''
f1:{[cost;x;y] $[y>x+cost;y-cost;y<x-cost;y+cost;x]};
f2:{[cost; series] 
    t0: f1[cost] scan series;
    fills reverse fills reverse?[(t0>prev t0)&(not null prev t0);1;?[t0<prev t0;-1;0N]]
    };
data:select from basis where (not null close) & (not null amount) & (not null volume)&(volume>=0)&(close>=0);
data1:update sig1:f2[3;close] from data;
data1:update sig:?[(sig1*(-1 xprev sig1))=-1;neg sig1;sig1] from data1;
data1:update mavgc5:5 mavg close from data1;
data1:update mavgv10:10 mavg volume from data1;
data1:update mavgv30:30 mavg volume from data1;
data1:update cost:0^?[((prev sig)*sig)=-1;close*0.00015;0] from data1;
data1:update minRet:0^log(1+((prev sig)*((close%prev close)-1))-cost%prev close) from data1;
data1:update sig:?[sig=1;1;0] from data1;
data1
''', pandas=True)

dataset = conn(r'''
select `$ string each date,sig,symbol,close,mavgc5,dif,stock,minRet,volume,mavgv10,mavgv30 from data1 
''', pandas=True)
values_full =dataset.values
values = values_full[:,1:]
encoder = LabelEncoder()
values[:,1] = encoder.fit_transform(values[:,1])
# ensure all data is float
#values = values.astype('float32')
start_time = time.time()
# 读入数据
n_train_hours = 365 * 1403
train = values[332911:n_train_hours,:]
tests = values[n_train_hours:,1:]
#print(train[:1,:])
#print(tests[:1,:])

params = {
    'booster': 'gbtree',
    'objective': 'binary:logistic',  # 多分类的问题
    #'num_class': 2,  # 类别数，与 multisoftmax 并用
    'gamma': 0.1,  # 用于控制是否后剪枝的参数,越大越保守，一般0.1、0.2这样子。
    'max_depth': 10,  # 构建树的深度，越大越容易过拟合
    'lambda': 2,  # 控制模型复杂度的权重值的L2正则化项参数，参数越大，模型越不容易过拟合。
    'subsample': 0.7,  # 随机采样训练样本
    'colsample_bytree': 0.7,  # 生成树时进行的列采样
    'min_child_weight': 2,
    'scale_pos_weight':1,
    # 这个参数默认是 1，是每个叶子里面 h 的和至少是多少，对正负样本不均衡时的 0-1 分类而言
    # ，假设 h 在 0.01 附近，min_child_weight 为 1 意味着叶子节点中最少需要包含 100 个样本。
    # 这个参数非常影响结果，控制叶子节点中二阶导的和的最小值，该参数值越小，越容易 overfitting。
    'silent': 0,  # 设置成1则没有运行信息输出，最好是设置为0.
    'eta': 0.2,  # 如同学习率
    'seed': 100,
    'nthread': 6,  # cpu 线程数
     #'eval_metric': 'rmse'
}
plst = list(params.items())
num_rounds = 500  # 迭代次数
train_xy, val = train_test_split(train, test_size=0.3, random_state=1)
# random_state is of big influence for val-auc
y = train_xy[:,0]
X = train_xy[:,1:]
val_y = val[:,0]
val_X = val[:,1:]
xgb_val = xgb.DMatrix(val_X, label=val_y)
xgb_train = xgb.DMatrix(X, label=y)
xgb_test = xgb.DMatrix(tests)
watchlist = [(xgb_train, 'train'), (xgb_val, 'val')]
# training model
# early_stopping_rounds 当设置的迭代次数较大时，early_stopping_rounds 可在一定的迭代次数内准确率没有提升就停止训练
model = xgb.train(plst, xgb_train, num_rounds, watchlist, early_stopping_rounds=100)
#model.save_model('./model/xgb.model')  # 用于存储训练出的模型
print ("best best_ntree_limit:", model.best_ntree_limit)
preds = model.predict(xgb_test, ntree_limit=model.best_ntree_limit)
# 输出运行时长
cost_time = time.time() - start_time
print ("xgboost success!", '\n', "cost time:", cost_time, "(s)")
y_test = values[n_train_hours:,0]
test_rmse = sqrt(mean_squared_error(y_test, preds))
print('Test RMSE: %.3f' % test_rmse)
preds=preds.reshape(len(preds),1)
date = values_full[n_train_hours:,0].reshape((len(preds), 1))
test_s = concatenate((date,preds),axis=1)
#test_ss = concatenate((date,values[n_train_hours:,:]),axis=1)
test_ss = concatenate((test_s,values[n_train_hours:,1:]),axis=1)
df = DataFrame(test_ss,columns=dataset.columns)
conn('{`data_lstm_s set x}', df)
conn(r'''
data_lstm_s:update date: "D"$ string each date from data_lstm_s;
data_lstm_s:update sig:?[sig<0.5;-1;1] from data_lstm_s;
data_lstm_s:update cost:0^?[((prev sig)*sig)=-1;close*0.00012;0] from data_lstm_s;
data_lstm_s:update minRet:0^log(1+((prev sig)*((close%prev close)-1))-cost%prev close) from data_lstm_s;
data_lstm_s:update turnover:0^?[cost=0;0;1] from data_lstm_s;
5#select from data_lstm_s where cost<>0
''',pandas=True)
conn(r'''
funct:{[begdate;enddate]
trade_indicator:select date,symbol,sig,close,cost,turnover from data_lstm_s where date within(begdate,enddate);
hdq_CmRet1::select 
        DailyRet:sum minRet , 
        cm_ret:last cm_ret, 
        number:sum abs(sig),
        turnover:sum turnover
by date
from (
        update cm_ret:sums minRet  
        from (min_ret:select date,symbol,sig,turnover,
        minRet:0^log(1+((prev sig)*((close%prev close)-1))-cost%prev close) 
        from (select date,symbol,sig,close,cost,turnover from trade_indicator)));
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
funct[2017.12.27;2018.01.31]
''',pandas=True)
print(result)