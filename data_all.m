clc, clear
cd = 'F:\Betalpha\�ڻ��շ���ģ��\�ھ�~ʮ��\DATA\';
type = cell(4,1);
type{1,1} = ['cu';'zn';'ni';'au';'al';'pb';'sn';'ag';'rb';'hc';'bu';'ru'];
type{2,1} = ['m1';'a1';'p1';'cs';'y1';'c1';'jd';'l1';'pp';'jm';'v1';'j1';'i1'];
type{3,1} = ['sr';'zc';'ta';'wh';'cf';'fg';'ma';'oi';'rm'];
type{4,1} = ['nmfi';'nffi';'jjri';'nmbm';'enfi';'cifi';'crfi';'oofi';'sofi';'apfi'];
cu = xlsread(strcat(cd, '1_������.xlsx'),'cu'); %��ͭ�������翪�̣�1995-04-17��
alldate = cu(:,1); %��������
startdate = '2012/01/01';
enddate = '2016/11/15';
[data_sh, clpr_sh] = data_processing(cd, '1_������.xlsx', type{1,1}, alldate, startdate, enddate);
[data_dl, clpr_dl] = data_processing(cd, '2_������.xlsx', type{2,1}, alldate, startdate, enddate);
[data_zz, clpr_zz] = data_processing(cd, '3_֣����.xlsx', type{3,1}, alldate, startdate, enddate);
[data_ind, clpr_ind] = data_processing(cd, '4_����ָ��.xlsx', type{4,1}, alldate, startdate, enddate);
