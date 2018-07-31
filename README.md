# Quantitive-Finance
## Created by Soulkey Liu (Ming Liu)
For CTA quant who invest in stock and futures and work in hedge fund;  
If you want to run these codes, what you will need are Python 3.6, Pycharm (or other notebook),Matlab (version 2008-2017) Kdb+ 3.31(Q language, download at https://code.kx.com/q/).
### Thanks to 
S. Wei at Peking University;  
M. Tang at Peking University & London Business School;  
Prof. Bob at University of California, Berkeley;  
Henry. Yu at Southwestern University of Finance and Economics & Xiamen University.  
Without their help, I can't make these code by my own.
## Current Work
Traditional CTA quant trading strategy (include turtle trading, Dual thrust, Open Range Breaker and others)and some machine learning trading strategy (LSTM, Xgboost and others)
## Future work
About Futures:Statistical arbitrage based on deep machine learning (Reinforcement Learning:Sarsa,Q learning and others, Xgboost, DQN, light gbm(Microsoft), GBDT, LSTM (RNN), SVM). I expect that through deep machine learning, we can find a stable nonlinear correlation exist in volatility(variance), return, or other related data between two futures or stocks, then we can get a higher sharpe ratio based on statistical arbitrage.  Solving the covariance matrix is to use PCA method to select major features and reduce the matrix dimension.  
About Stocks:To use deep machine learning to get the value of weight in Multi-factor stock model. However, evidence is found that linear model is more suitable for China's stock market, compared to machine learning, because linear model is really helpful to reduce the noise in stock data. Moreover, China's stock data include too much noise, the ratio of signal to noise is lower, in this case, the effect of machine learning will be worse compared with linear regression. 
