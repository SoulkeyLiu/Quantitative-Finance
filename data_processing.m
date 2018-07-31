function [category, clpr, startdate, enddate] = data_processing(cd, file, type, alldate, startdate, enddate)
%路径、文件、品种类型、活跃时间（cu，时间推前至1995年）、开始日期、结束日期
%% 导入文件
num = size(type,1);
category = cell(num,1); %category是大类的意思
for i = 1:num
    category{i,1} = xlsread(strcat(cd,file), type(i,:));
end
%% 输入文件参数（开始日期，结束日期）
d = 693960; %从0000年1月1日算开始，到1899年12月30日算结束一共的天数
startind = [];
endind = [];
count = 0;
while isempty(startind)
    startind = find(datenum(startdate) + count - d == alldate(:,1));
    count = count + 1;
end
count = 0;
while isempty(endind)
    endind = find(datenum(enddate) + count - d == alldate(:,1));
    count = count + 1;
end
startdate = datestr(alldate(startind,1) + d, 26);
enddate = datestr(alldate(endind,1) + d, 26);
%% 录入收盘价：clpr(对于Wind中导入的各品种数据，第5列为收盘价clpr)
clpr = zeros(endind-startind+1, num);
choose_date = alldate(startind:endind);
for count = 1:num
    for i = 1:length(choose_date)
        ind = find(category{count,1}(:,1) == choose_date(i)); %日期的位置是至多唯一的
        if ~isempty(ind)
            clpr(i,count) = category{count,1}(ind,5);
        end
    end
end
