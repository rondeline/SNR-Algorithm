function xlswrite_summary
% function xlswrite_summary
% Function to  write the summary data to the excel file

global LENA_labels
global statSTR
global xlsfileSTR

Summary_Sheet = xlsfileSTR.SheetNames{3};

% get information for each label in turn

start_col = xlsfileSTR.start_col3;
start_row = xlsfileSTR.start_row3 + 1;
number_of_stats = xlsfileSTR.number_of_stats;   % items stored
data = NaN*ones(number_of_stats,1);
for klab = 1:length(LENA_labels)
    for seg_type = 1:3    % conversations, pauses, and accumulated
        rowx = (seg_type-1)*(number_of_stats+2) + start_row;  %allow two blank rows between
        rng = [xlcolumnletter(start_col + klab - 1) int2str(rowx)];
        if seg_type < 3
            data(1) = statSTR.Number_Accepted(klab,seg_type);
            data(2) = statSTR.Number_Rejected(klab,seg_type);
            Duration_Sum = statSTR.Duration_Sum(klab,seg_type);
            data(3) = Duration_Sum/data(1);        % mean duration
            data(4) = statSTR.dB_Sum(klab,seg_type)/Duration_Sum;
            wt_ave_power = statSTR.Power_Sum(klab,seg_type)/Duration_Sum;
            data(5) = 10 * log10(wt_ave_power);
            
        else
            data(1) = statSTR.Number_Accepted(klab,1) + statSTR.Number_Accepted(klab,2);
            data(2) = statSTR.Number_Rejected(klab,1) + statSTR.Number_Rejected(klab,2);
            Total_Duration = statSTR.Duration_Sum(klab,1) + statSTR.Duration_Sum(klab,2);
            data(3) = Total_Duration/data(1);
            data(4) = (statSTR.dB_Sum(klab,1) + statSTR.dB_Sum(klab,2))/Total_Duration;
            wt_ave_power = (statSTR.Power_Sum(klab,1) + statSTR.Power_Sum(klab,2))/Total_Duration;
            data(5) = 10 * log10(wt_ave_power);
        end
        
        xlswrite(xlsfileSTR.out_file, data(1:5), Summary_Sheet, rng);
    end
end
