from pandas import read_csv
from datetime import datetime
from math import sqrt
from numpy import concatenate
from matplotlib import pyplot
from pandas import DataFrame
from pandas import concat
from sklearn.preprocessing import MinMaxScaler
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import mean_squared_error
from keras.models import Sequential
from keras.layers.core import Dense, Activation, Dropout
from keras.layers import LSTM
import numpy as np
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
data1
''', pandas=True)

dataset = conn(r'''
select `$ string each date,symbol,close,mavgc5,dif,stock,minRet,volume,mavgv10,mavgv30,sig from data1 
''', pandas=True)
values_full =dataset.values
values = values_full[:,1:]
# specify columns to plot
groups = [1, 2, 3, 4, 5, 6, 7, 8]
i = 1
# plot each column
pyplot.figure()
for group in groups:
	pyplot.subplot(len(groups), 1, i)
	pyplot.plot(values[:, group])
	pyplot.title(dataset.columns[group], y=0.5, loc='right')
	i += 1
pyplot.show()
#以下为自定义LSTM神经网络模型程序
def build_model(layers):
    model = Sequential()
    model.add(LSTM(
        input_shape=(layers[1], layers[0]),
        output_dim=layers[1],
        return_sequences=True))
    model.add(Dropout(0.2))
    model.add(LSTM(
        layers[2],
        return_sequences=False))
    model.add(Dropout(0.2))
    model.add(Dense(
        output_dim=layers[3]))
    model.add(Activation("linear"))
    model.compile(loss="mse", optimizer="rmsprop")
    return model
encoder = LabelEncoder()
values[:,0] = encoder.fit_transform(values[:,0])
# ensure all data is float
values = values.astype('float32')
# print(values[0, :])
# normalize features
scaler = MinMaxScaler(feature_range=(0, 1))
scaled = scaler.fit_transform(values)
# split into train and test sets
n_train_hours = 365 * 1200
train = scaled[:n_train_hours, :]
test = scaled[n_train_hours:, :]
#print(train[:,0])
#print(test)
# split into input and outputs
train_X, train_y = train[:, :-1], train[:, -1]
test_X, test_y = test[:, :-1], test[:, -1]
# reshape input to be 3D [samples, timesteps, features]
train_X = train_X.reshape((train_X.shape[0], 1, train_X.shape[1]))
test_X = test_X.reshape((test_X.shape[0], 1, test_X.shape[1]))
# design network
model = Sequential()
model.add(LSTM(50, input_shape=(train_X.shape[1], train_X.shape[2])))
model.add(Dropout(0.1))
model.add(Dense(1))
model.compile(loss='mse', optimizer='rmsprop')
# fit network
history = model.fit(train_X, train_y, epochs=6, batch_size=365*5, validation_data=(test_X, test_y), verbose=2, shuffle=False)
# plot history
pyplot.plot(history.history['loss'], label='train')
pyplot.plot(history.history['val_loss'], label='test')
pyplot.legend()
pyplot.show()
# make a prediction
# print(train_X.shape, train_y.shape, test_X.shape, test_y.shape)
# make a prediction
yhat = model.predict_classes(test_X).astype('int')
test_X = test_X.reshape((test_X.shape[0], test_X.shape[2]))
# invert normalization of forecasted values
yhat = yhat.reshape((len(yhat), 1))
date = values_full[n_train_hours:,0].reshape((len(yhat), 1))
print(train_X.shape, train_y.shape, test_X.shape, test_y.shape)
inv_yhat = concatenate((test_X, yhat), axis=1)
test_k = concatenate((date, inv_yhat), axis=1)
# calculate RMSE
test_rmse = sqrt(mean_squared_error(test_y, yhat))
print('Test RMSE: %.3f' % rmse)
test_s = concatenate((date,values[n_train_hours:,:-1]),axis=1)
#test_ss = concatenate((date,values[n_train_hours:,:]),axis=1)
inv=inv_yhat[:,-1].reshape(len(inv_yhat[:,-1]),1)
test_ss = concatenate((test_s,inv),axis=1)
print(test_ss[0:1,:])
# df = DataFrame(test_k,columns=dataset.columns)
df = DataFrame(test_ss,columns=dataset.columns)
conn('{`data_lstm_s set x}', df)
conn(r'''
data_lstm_s:update date: "D"$ string each date from data_lstm_s;
data_lstm_s:update sig:?[sig=0;-1;1] from data_lstm_s;
data_lstm_s:update cost:0^?[((prev sig)*sig)=-1;close*0.00012;0] from data_lstm_s;
data_lstm_s:update minRet:0^log(1+((prev sig)*((close%prev close)-1))-cost%prev close) from data_lstm_s;
data_lstm_s:update turnover:0^?[cost=0;0;1] from data_lstm_s;
10#select from data_lstm_s where cost<>0
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
funct[2017.03.07;2017.11.30]
''',pandas=True)
print(result)