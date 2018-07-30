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
from keras.layers import Dense
from keras.layers import LSTM
import numpy as np
# load data
dataset = read_csv('j1108.csv', header=0, index_col=0)
values = dataset.values
print(values)
# specify columns to plot
groups = [1, 2, 3, 5, 6, 7]
i = 1
# plot each column
pyplot.figure()
for group in groups:
	pyplot.subplot(len(groups), 1, i)
	pyplot.plot(values[:, group])
	pyplot.title(dataset.columns[group], y=0.5, loc='right')
	i += 1
pyplot.show()
# convert series to supervised learning
def series_to_supervised(data, n_in=1, n_out=1, dropnan=True):
	n_vars = 1 if type(data) is list else data.shape[1]
	df = DataFrame(data)
	cols, names = list(), list()
	# input sequence (t-n, ... t-1)
	for i in range(n_in, 0, -1):
		cols.append(df.shift(i))
		names += [('var%d(t-%d)' % (j+1, i)) for j in range(n_vars)]
	# forecast sequence (t, t+1, ... t+n)
	for i in range(0, n_out):
		cols.append(df.shift(-i))
		if i == 0:
			names += [('var%d(t)' % (j+1)) for j in range(n_vars)]
		else:
			names += [('var%d(t+%d)' % (j+1, i)) for j in range(n_vars)]
	# put it all together
	agg = concat(cols, axis=1)
	agg.columns = names
	# drop rows with NaN values
	if dropnan:
		agg.dropna(inplace=True)
	return agg
encoder = LabelEncoder()
values[:,4] = encoder.fit_transform(values[:,4])
#values[:,0] = encoder.fit_transform(values[:,0])

# ensure all data is float
values = values.astype('float32')
# normalize features
scaler = MinMaxScaler(feature_range=(0, 1))
# scaled = scaler.fit_transform(values)
scaled = scaler.fit_transform(values[:, 1:])
sig = values[:, 0]
print(len(sig))
print(len(scaled))
scaled = np.hstack((sig, scaled))

# frame as supervised learning
reframed = series_to_supervised(scaled, 1, 1)
# drop columns we don't want to predict
reframed.drop(reframed.columns[[8,9,10,11,12,13,14,15]], axis=1, inplace=True)
#print(reframed.head())
# split into train and test sets
values = reframed.values
n_train_hours = 365 * 1300
train = values[:n_train_hours, :]
test = values[n_train_hours:, :]
#print(train[:,0])
#print(test)
# split into input and outputs
train_X, train_y = train[:, 1:], train[:, 0]
test_X, test_y = test[:, 1:], test[:, 0]
#print(train_y)
# reshape input to be 3D [samples, timesteps, features]
train_X = train_X.reshape((train_X.shape[0], 1, train_X.shape[1]))
test_X = test_X.reshape((test_X.shape[0], 1, test_X.shape[1]))
print(train_X.shape, train_y.shape, test_X.shape, test_y.shape)
# design network
model = Sequential()
model.add(LSTM(10, input_shape=(train_X.shape[1], train_X.shape[2])))
model.add(Dense(1))
model.compile(loss='mae', optimizer='adam')
# fit network
history = model.fit(train_X, train_y, epochs=10, batch_size=10240, validation_data=(test_X, test_y), verbose=2, shuffle=False)
# plot history
pyplot.plot(history.history['loss'], label='train')
pyplot.plot(history.history['val_loss'], label='test')
pyplot.legend()
pyplot.show()
# make a prediction
print(train_X.shape, train_y.shape, test_X.shape, test_y.shape)
# make a prediction
yhat = model.predict_classes(test_X).astype('int')
test_X = test_X.reshape((test_X.shape[0], test_X.shape[2]))
print(yhat.shape)
# invert normalization of forecasted values
inv_yhat = concatenate((yhat, test_X), axis=1)
inv_yhat = scaler.inverse_transform(inv_yhat)
inv_yhat = inv_yhat[:,0]
# invert normalization of actual values
test_y = test_y.reshape((len(test_y), 1))
inv_y = concatenate((test_y, test_X), axis=1)
inv_y = scaler.inverse_transform(inv_y)
inv_y = inv_y[:,0]
# calculate RMSE
rmse = sqrt(mean_squared_error(inv_y, inv_yhat))
print(inv_yhat)
print(max(inv_yhat))
print(min(inv_yhat))
print('Test RMSE: %.3f' % rmse)
print(inv_y)
from qpython import qconnection
conn = qconnection.QConnection('192.168.1.106',9911,'sihao','sh123456')
conn.open()
data=conn(r'''
f1:{[cost;x;y] $[y>x+cost;y-cost;y<x-cost;y+cost;x]};
f2:{[cost; series] 
    t0: f1[cost] scan series;
    fills reverse fills reverse?[(t0>prev t0)&(not null prev t0);1;?[t0<prev t0;-1;0N]]
    };
data:dataset
data1:update sig: inv_yhat  from data;
data1:update return:sums sig*((next close)-close) from data1;
data1:update sharpe:return %sdev(return) from data1;
sharpe_ratio: select last(sharpe) from data1;
sharpe_ratio
''',pandas=True)
