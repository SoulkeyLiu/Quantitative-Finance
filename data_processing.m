function [category, clpr, startdate, enddate] = data_processing(cd, file, type, alldate, startdate, enddate)
%·�����ļ���Ʒ�����͡���Ծʱ�䣨cu��ʱ����ǰ��1995�꣩����ʼ���ڡ���������
%% �����ļ�
num = size(type,1);
category = cell(num,1); %category�Ǵ������˼
for i = 1:num
    category{i,1} = xlsread(strcat(cd,file), type(i,:));
end
%% �����ļ���������ʼ���ڣ��������ڣ�
d = 693960; %��0000��1��1���㿪ʼ����1899��12��30�������һ��������
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
%% ¼�����̼ۣ�clpr(����Wind�е���ĸ�Ʒ�����ݣ���5��Ϊ���̼�clpr)
clpr = zeros(endind-startind+1, num);
choose_date = alldate(startind:endind);
for count = 1:num
    for i = 1:length(choose_date)
        ind = find(category{count,1}(:,1) == choose_date(i)); %���ڵ�λ��������Ψһ��
        if ~isempty(ind)
            clpr(i,count) = category{count,1}(ind,5);
        end
    end
end
