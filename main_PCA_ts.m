clc, clear
tic
load('clpr_index_20120104_20161115.mat');
clpr = [clpr_dl clpr_sh clpr_zz]; %2012-01-04~2016-11-15的期货品种收盘价
index = clpr_ind; %2012-01-04~2016-11-15的大类指数收盘价
result = cell(8,16); %预测效果
result_distance = zeros(8,16); %评价指标：解距离的计算
result_contr = cell(8,16); %累积贡献率汇总
result_beta_stats = cell(8,16); %横截面回归统计量汇总（mat文件中没有）
for pca_num = 10  %pca_num是PCA(Principal Component Analysis)的个数
    for period = 50 %period是时序回归的时段长度
       %% 数据预处理
        [m, n] = size(clpr);
        for i = 2:m
            for j = 1:n
                if clpr(i,j) == 0
                    clpr(i,j) = clpr(i-1,j);
                end
            end
        end
        for i = 2:m
            for j = 1:10
                if index(i,j) == 0
                    index(i,j) = index(i-1,j);
                end
            end
        end
        
       %% 1. 涨跌幅计算
        r_clpr = zeros(m, n); %期货品种日收益率
        r_index = zeros(m, 10); %大类指数日收益率
        for i = 2:m
            r_clpr(i,:) = clpr(i,:)./clpr(i-1,:) - 1;
            r_index(i,:) = index(i,:)./index(i-1,:) - 1;
        end
        for i = 1:m
            for j = 1:n
                if isnan(r_clpr(i,j)) || isinf(r_clpr(i,j))
                    r_clpr(i,j) = 0;
                end
            end
        end
        for i = 1:m
            for j = 1:10
                if isnan(r_index(i,j)) || isinf(r_index(i,j))
                    r_index(i,j) = 0;
                end
            end
        end
        
       %% 2. 行业暴露度计算（外加PCA因子）
        factor_matrix = cell(10,3); %横截面回归日期的行业暴露度、时序回归残差、时序回归统计量
        for i = period:m-3
            factor_days = []; 
            factor_stats = [];
            factor_r = [];
            for j = 1:n
                [exposure,~,r,~,stats] = regress(r_clpr(i-period+2:i+1,j), [ones(period,1),r_index(i-period+2:i+1,:)]); %收益率数据用到倒数第三个
                exposure(1,:)=[];
                exposure = exposure';
                r = r';
                factor_days = [factor_days;exposure];
                factor_r = [factor_r;r];
                factor_stats = [factor_stats;stats];
            end
            factor_matrix{i-period+1, 1} = factor_days;
            factor_matrix{i-period+1, 2} = factor_r;
            factor_matrix{i-period+1, 3} = factor_stats;
        end
        
       %% 主成分分析，提取PCA因子 
        r_contr = cell(10,1);
        for i = 1:size(factor_matrix)
            r = factor_matrix{i,2}; %取残差
            r_zscore = zscore(r);
            r_corr = corrcoef(r);
            [vec1, lamda, rate] = pcacov(r);
            f = repmat(sign(sum(vec1)),size(vec1,1),1);
            vec2 = vec1.*f;
            contr = cumsum(rate)/sum(rate);
            df = r_zscore*vec2; %主成分得分
            factor_matrix{i,1} = [factor_matrix{i,1} df(:,1:pca_num)]; %取前pca_num个因子
            r_contr{i,1} = contr;
        end    
        
        pca_contr = zeros(size(r_contr,1),1); %累积贡献率
        for i = 1:size(r_contr,1)
            pca_contr(i) = r_contr{i,1}(pca_num);
        end
        result_contr{pca_num-2,period/10-2} = pca_contr;
        
       %% 3.因子暴露度标准化
        for i = 1:size(factor_matrix)
            temp = factor_matrix{i,1};
            temp = (temp - mean(temp))./std(temp);
            for j = 1:size(temp,1)
                for k = 1:size(temp,2)
                    if isnan(temp(j,k)) || isinf(temp(j,k))
                        temp(j,k) = 0;
                    end
                end
            end
            factor_matrix{i,1} = temp;
        end
        
       %% 4. 因子收益率
        r_resid = zeros(10,n); %横截面残差
        beta = []; %因子收益率
        beta_stats = []; %因子收益率统计量
        for i = period+1:m-2
            [r_factor,~,resid,~,stats] = regress((r_clpr(i+1,:))', [ones(n,1), factor_matrix{i-period,1}]); %收益率数据用到倒数第二个
            r_factor(1,:)=[];
            beta(i - period, :) = r_factor'; 
            r_resid(i - period, :) = resid';
            beta_stats(i - period, :) = stats;
        end
        result_beta_stats{pca_num-2,period/10-2} = beta_stats;
        
       %% 5. 协方差矩阵
        F = cell(10,1); %观测日期的因子协方差矩阵
        for i = 1:size(beta) - period + 1
            beta_period = beta(i:i+period-1, :);
            F{i,1} = cov(beta_period);
        end
        DELTA = cell(10,1); %观测日期的残差协方差矩阵
        for i = 1:size(r_resid) - period + 1
            r_resid_period = r_resid(i:i+period-1,:);
            DELTA{i,1} = cov(r_resid_period);
            for j = 1:size(DELTA{i,1},1)
                for k = 1:size(DELTA{i,1},2)
                    if j~=k || isnan(DELTA{i,1}(j,k))
                        DELTA{i,1}(j,k) = 0;
                    end
                end
            end
        end
       %% 6. 风险预测
        X = cell(10,1); %观测日期的因子暴露度（用来预测第二天风险）
        for i = 1:size(factor_matrix) - period + 1
            X{i,1} = factor_matrix{i+period-1, 1};
        end
        V = cell(10,1); 
        for i = 1:size(X)
            V{i,1} = X{i,1}*F{i,1}*X{i,1}'+DELTA{i,1};
        end
        V_var = cell(10,1); %预测方差
        for i = 1:size(X)
            temp = V{i,1};
            for j = 1:size(temp)
                for k = 1:size(temp)
                    if j~=k
                        temp(j,k) = 0;
                    end
                end
            end
            V_var{i,1} = diag(temp);
        end
       %% 7. 风险评估：对于每一个品种（总的）
        score = zeros(size(X,1),n); %r/estimate_sigma
        for i = 1:n
            r_evaluate = r_clpr(end-size(X,1)+1:end, i);
            for j = 1:size(X,1)
                score(j,i) = r_evaluate(j) / sqrt(V_var{j,1}(i));
            end
        end
        for i = 2:size(score,1)
            for j = 1:size(score,2)
                if score(i,j) == 0
                    score(i,j) = score(i-1,j);
                end
            end
        end
        score_nonzero = cell(n,1); %排除前面的零值
        for i = 1:n
            count = 0;
            for j = 1:size(X,1)
                if score(j,i)~=0
                    count = count + 1;
                    score_nonzero{i,1}(count) = score(j,i);
                end
            end
        end
        s = zeros(n,1); %即各品种的Z值
        for i = 1:n
            s(i) = std(score_nonzero{i,1});
        end
        result{pca_num-2,(period/10)-2} = s; %记录最终预测效果
        distance = 0;
        for i = 1:n
            distance = distance + (s(i) - 1)^2;
        end
        distance = sqrt(distance);
        result_distance(pca_num-2,period/10-2) = distance; %记录解距离
       %% 风险评估：对于每一个品种（分开的） 已算出score
        T = 25;
        std_score = zeros(size(score,1), size(score,2));
        for i = T:size(score,1)
            for j = 1:n
                std_score(i,j) = std(score(i-(T-1):i,j));
                if std_score(i,j) == 0
                    std_score(i,j) = nan;
                end;
            end
        end
        std_score(1:T-1,:) = [];
        p5 = 1 - sqrt(2/T);
        p95 = 1 + sqrt(2/T);
        score_num = zeros(1,n);
        score_num_p5to95 = zeros(1,n);
        for i = 1:size(std_score,1)
            for j = 1:n
                if ~isnan(std_score(i,j))
                    score_num(j) = score_num(j) + 1;
                    if std_score(i,j)>=p5 && std_score(i,j)<=p95
                        score_num_p5to95(j) = score_num_p5to95(j) + 1;
                    end
                end
            end
        end
        p5to95 = score_num_p5to95./score_num;
    end
end
toc