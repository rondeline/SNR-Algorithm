function store_line(indx, level, dur, iord, chunk_number)
% function store_line(indx, level, dur, iord, chunk_number)
% Function to store a line of data grand data block
%  in anticipation of writing to the excel file.
% Making sure it's for the right LENA label

global statSTR xlsfileSTR
global grand_data_block
global grand_data_block2

Seg_number = statSTR.Number_Utterances(indx);

columns_per_label = length(xlsfileSTR.sub_labels) + 1;  % number of colums to allocate to each label

% if we were writing each line one at a time (not recommended - SLOW!)
% % rowx = xlsfileSTR.start_row1 + Seg_number - 1;
% % colx = (indx-1)*columns_per_label + xlsfileSTR.start_col1;
% 
% rng = [xlcolumnletter(colx) int2str(rowx)];
% xlswrite(xlsfileSTR.out_file, [level dur iord], xlsfileSTR.SheetNames{1}, rng)

if iord == 1
    ord = 'conv';
else
    ord = 'pause';
end
ord = [ord '-' int2str(chunk_number)];
dataw = {statSTR.Number_Utterances(indx) level dur ord};
rowa = Seg_number;

cola1 = (indx-1)*columns_per_label + 1;
cola2 = cola1 + length(dataw) - 1;

grand_data_block(rowa, cola1:cola2) = dataw;

% number of repeats (accounting for longer durations
dataw{3} = 1;
number_repeats = round(dur);
for k = 1:number_repeats
    statSTR.Number_Utterances_extended(indx) = statSTR.Number_Utterances_extended(indx) + 1;
    rowb = statSTR.Number_Utterances_extended(indx);
    grand_data_block2(rowb, cola1:cola2) = dataw;
end


