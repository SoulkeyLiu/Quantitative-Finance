# Quantitative-Finance
## Author:Soulkey Liu （Ming Liu, Ph.D. candidate in Finance(SWUFE), Bsc in Finance (SWUFE), visiting students(UC Berkeley))
These codes are targeted for CTA quant who invest in stock and futures and work in hedge fund;  
If you want to run these codes, what you will need are Python 3.6, Pycharm (or other notebook),Matlab (version 2008-2017) Kdb+ 3.31(Q language, download at https://code.kx.com/q/).
### Thanks to
S. Wei (Peking University);  
M. Tang (Peking University & London Business School);  
Prof. Anderson (University of California, Berkeley);  
Henry. Yu (Xiamen University).  
## Current Work
Traditional CTA quant trading strategy (include turtle trading, Dual thrust, Open Range Breaker and others)and some machine learning trading strategy (LSTM, Xgboost and others)
## Future work
About Futures:Statistical arbitrage based on deep machine learning (Reinforcement Learning:Sarsa,Q learning and others, Xgboost, DQN, light gbm(Microsoft), GBDT, LSTM (RNN), SVM). I expect that through deep machine learning, we can find a stable nonlinear correlation exist in volatility(variance), return, or other related data between two futures or stocks, then we can get a higher sharpe ratio based on statistical arbitrage.  Solving the covariance matrix is to use PCA method to select major features and reduce the matrix dimension.  
About Stocks:To use deep machine learning to get the value of weight in Multi-factor stock model. However, evidence is found that linear model is more suitable for China's stock market, compared to machine learning, because linear model is really helpful to reduce the noise in stock data. Moreover, China's stock data include too much noise, the ratio of signal to noise is lower, in this case, the effect of machine learning will be worse compared with linear regression. 
If you have any questions, please contact by email to 463629841@qq.com.
