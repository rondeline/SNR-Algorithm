function process_SNR_Power_2(convers_segment, pause_segment, ipair, pause_number, conv_start_time, conv_end_time, pause_start_time, pause_end_time, line2rite)
% function process_SNR_Power_2(convers_segment, pause_segment, ipair, conv_start_time, conv_end_time, pause_start_time, pause_end_time, line2rite)
% Part of new package, with weighted averages based on Power, not dB.
% function to process a conversation-pause pair (called from compute_SNR_Power.m now - 6/18/2019)
% Based on program process_chunk.m
% 25-May-2018

% 15-Sep-2019
% New version, to use pause following each conversation

% 24-Sep-2019
% Modified to include different set of labels for Noise/Speech in
% Conversation and Pause blocks

% Invoked from compute_snr.m

global LENA_labels
global statSTR
global dB_Correction
global grand_data_block

minimum_time = statSTR.minimum_time;

number_labels = length(LENA_labels);

% First analyze conversation segment

% Get each utterance
utter_start = findstr(convers_segment, 'spkr=');
utter_stop = findstr(convers_segment, '/>');
if length(utter_start) ~= length(utter_stop)
    disp ('Problem with conversation utterance delimiters!')
    return
end

for k = 1:length(utter_start)
    utterance = convers_segment(utter_start(k):utter_stop(k));
    [start_time, stop_time, level_dB] = process_line3(utterance);  % these lines are new, for process_SNR_Power
    level = 10.^(level_dB/10);   % convert to power
    if check_inclusion(start_time, stop_time)  % process only if times are in range
        dur = stop_time - start_time;
        label = utterance(7:9);   % here's the label
        indx = find(ismember(LENA_labels, label));
        if isempty(indx)
            fprintf('Conversation #%d, Utterance #%d: Label %s not in list!\n', ipair, k, label)
        else
            statSTR.Label_Count(indx, 1) = statSTR.Label_Count(indx, 1) + 1;
            statSTR.Label_Duration(indx, 1) = statSTR.Label_Duration(indx, 1) + dur;
        end
        switch label
            case 'FAN'
                statSTR.FAN_Duration(ipair) = statSTR.FAN_Duration(ipair) + dur;
                statSTR.ComboN_Duration(ipair) = statSTR.ComboN_Duration(ipair) + dur;
                statSTR.FAN_Power_Sum(ipair) = statSTR.FAN_Power_Sum(ipair) + level * dur;
                statSTR.ComboN_Power_Sum(ipair) = statSTR.ComboN_Power_Sum(ipair) + level * dur;
            case 'FAF'
                statSTR.FAF_Duration(ipair) = statSTR.FAF_Duration(ipair) + dur;
                statSTR.ComboF_Duration(ipair) = statSTR.ComboF_Duration(ipair) + dur;
                statSTR.FAF_Power_Sum(ipair) = statSTR.FAF_Power_Sum(ipair) + level * dur;
                statSTR.ComboF_Power_Sum(ipair) = statSTR.ComboF_Power_Sum(ipair) + level * dur;
            case 'MAN'
                statSTR.MAN_Duration(ipair) = statSTR.MAN_Duration(ipair) + dur;
                statSTR.ComboN_Duration(ipair) = statSTR.ComboN_Duration(ipair) + dur;
                statSTR.MAN_Power_Sum(ipair) = statSTR.MAN_Power_Sum(ipair) + level * dur;
                statSTR.ComboN_Power_Sum(ipair) = statSTR.ComboN_Power_Sum(ipair) + level * dur;
            case 'MAF'
                statSTR.MAF_Duration(ipair) = statSTR.MAF_Duration(ipair) + dur;
                statSTR.ComboF_Duration(ipair) = statSTR.ComboF_Duration(ipair) + dur;
                statSTR.MAF_Power_Sum(ipair) = statSTR.MAF_Power_Sum(ipair) + level * dur;
                statSTR.ComboF_Power_Sum(ipair) = statSTR.ComboF_Power_Sum(ipair) + level * dur;
            case 'CXN'
                statSTR.CXN_Duration(ipair) = statSTR.CXN_Duration(ipair) + dur;
                statSTR.ComboN_Duration(ipair) = statSTR.ComboN_Duration(ipair) + dur;
                statSTR.CXN_Power_Sum(ipair) = statSTR.CXN_Power_Sum(ipair) + level * dur;
                statSTR.ComboN_Power_Sum(ipair) = statSTR.ComboN_Power_Sum(ipair) + level * dur;
            case 'CXF'
                statSTR.CXF_Duration(ipair) = statSTR.CXF_Duration(ipair) + dur;
                statSTR.ComboF_Duration(ipair) = statSTR.ComboF_Duration(ipair) + dur;
                statSTR.CXF_Power_Sum(ipair) = statSTR.CXF_Power_Sum(ipair) + level * dur;
                statSTR.ComboF_Power_Sum(ipair) = statSTR.ComboF_Power_Sum(ipair) + level * dur;
            case 'CHN'
                statSTR.CHN_Duration(ipair) = statSTR.CHN_Duration(ipair) + dur;
                statSTR.CHN_Power_Sum(ipair) = statSTR.CHN_Power_Sum(ipair) + level * dur;
            case 'CHF'
                statSTR.CHF_Duration(ipair) = statSTR.CHF_Duration(ipair) + dur;
                statSTR.CHF_Power_Sum(ipair) = statSTR.CHF_Power_Sum(ipair) + level * dur;
            case 'OLN'  % overlap categories - keep separate level calculations
                statSTR.OLN_conv_Duration(ipair) = statSTR.OLN_conv_Duration(ipair) + dur;
                statSTR.OLN_conv_Power_Sum(ipair) = statSTR.OLN_conv_Power_Sum(ipair) + level * dur;
                % fprintf('\n%s: Conversation %d, Utterance %d\n', label, ipair, k);
            case 'OLF'  % overlap categories - keep separate level calculations
                statSTR.OLF_conv_Duration(ipair) = statSTR.OLF_conv_Duration(ipair) + dur;
                statSTR.OLF_conv_Power_Sum(ipair) = statSTR.OLF_conv_Power_Sum(ipair) + level * dur;
                % fprintf('\n%s: Conversation %d, Utterance %d\n', label, ipair, k);
            otherwise
                statSTR.Noise_Duration(ipair) = statSTR.Noise_Duration(ipair) + dur;
                statSTR.Noise_Power_Sum(ipair) = statSTR.Noise_Power_Sum(ipair) + level * dur;
        end
    end
end

% now process pause - ALL segments are considered noise (except OLN, OLF -
% 29-Jun-2018)

% Get each utterance
utter_start = findstr(pause_segment, 'spkr=');
utter_stop = findstr(pause_segment, '/>');
if length(utter_start) ~= length(utter_stop)
    disp ('Problem with pause utterance delimiters!')
    return
end

for k = 1:length(utter_start)
    utterance = pause_segment(utter_start(k):utter_stop(k));
    [start_time, stop_time, level_dB] = process_line3(utterance);  % these lines are new, for process_SNR_Power
    level = 10.^(level_dB/10);   % convert to power

    if check_inclusion(start_time, stop_time)  % process only if times are in range
        dur = stop_time - start_time;
        label = utterance(7:9);
        indx = find(ismember(LENA_labels, label));
        if isempty(indx)
            fprintf('Pause #%d, Utterance #%d: Label %s not in list!\n', pause_number, k, label)
        else
            statSTR.Label_Count(indx, 2) = statSTR.Label_Count(indx, 2) + 1;
            statSTR.Label_Duration(indx, 2) = statSTR.Label_Duration(indx, 2) + dur;
        end
        
% 24-Sep-2019
% New method to compute speech and noise, using same rules for pause block as for conversation block
% Note that the accumulations use the index for the CONVERSATION BLOCK
% (ipair) rather than the index for the PAUSE BLOCK (pause_number) so the
% accumulations for this conversation-pause pair are counted appropriately
% together.
%

%         if strcmpi(label, 'OLN')  % overlap categories - keep separate level calculations
%             statSTR.OLN_pause_Duration(ipair) = statSTR.OLN_pause_Duration(ipair) + dur;
%             statSTR.OLN_pause_Power_Sum(ipair) = statSTR.OLN_pause_Power_Sum(ipair) + level * dur;
%             % fprintf('\n%s: Pause %d, Utterance %d\n', label, ipair, k);
%         elseif strcmpi(label, 'OLF')
%             statSTR.OLF_pause_Duration(ipair) = statSTR.OLF_pause_Duration(ipair) + dur;
%             statSTR.OLF_pause_Power_Sum(ipair) = statSTR.OLF_pause_Power_Sum(ipair) + level * dur;
%             % fprintf('\n%s: Pause %d, Utterance %d\n', label, ipair, k);
%         else
%             statSTR.Noise_Duration(ipair) = statSTR.Noise_Duration(ipair) + dur;
%             statSTR.Noise_Power_Sum(ipair) = statSTR.Noise_Power_Sum(ipair) + level * dur;
%         end
        switch label
            case 'FAN'
                statSTR.FAN_Duration(ipair) = statSTR.FAN_Duration(ipair) + dur;
                statSTR.ComboN_Duration(ipair) = statSTR.ComboN_Duration(ipair) + dur;
                statSTR.FAN_Power_Sum(ipair) = statSTR.FAN_Power_Sum(ipair) + level * dur;
                statSTR.ComboN_Power_Sum(ipair) = statSTR.ComboN_Power_Sum(ipair) + level * dur;
            case 'FAF'
                statSTR.FAF_Duration(ipair) = statSTR.FAF_Duration(ipair) + dur;
                statSTR.ComboF_Duration(ipair) = statSTR.ComboF_Duration(ipair) + dur;
                statSTR.FAF_Power_Sum(ipair) = statSTR.FAF_Power_Sum(ipair) + level * dur;
                statSTR.ComboF_Power_Sum(ipair) = statSTR.ComboF_Power_Sum(ipair) + level * dur;
            case 'MAN'
                statSTR.MAN_Duration(ipair) = statSTR.MAN_Duration(ipair) + dur;
                statSTR.ComboN_Duration(ipair) = statSTR.ComboN_Duration(ipair) + dur;
                statSTR.MAN_Power_Sum(ipair) = statSTR.MAN_Power_Sum(ipair) + level * dur;
                statSTR.ComboN_Power_Sum(ipair) = statSTR.ComboN_Power_Sum(ipair) + level * dur;
            case 'MAF'
                statSTR.MAF_Duration(ipair) = statSTR.MAF_Duration(ipair) + dur;
                statSTR.ComboF_Duration(ipair) = statSTR.ComboF_Duration(ipair) + dur;
                statSTR.MAF_Power_Sum(ipair) = statSTR.MAF_Power_Sum(ipair) + level * dur;
                statSTR.ComboF_Power_Sum(ipair) = statSTR.ComboF_Power_Sum(ipair) + level * dur;
            case 'CXN'
                statSTR.CXN_Duration(ipair) = statSTR.CXN_Duration(ipair) + dur;
                statSTR.ComboN_Duration(ipair) = statSTR.ComboN_Duration(ipair) + dur;
                statSTR.CXN_Power_Sum(ipair) = statSTR.CXN_Power_Sum(ipair) + level * dur;
                statSTR.ComboN_Power_Sum(ipair) = statSTR.ComboN_Power_Sum(ipair) + level * dur;
            case 'CXF'
                statSTR.CXF_Duration(ipair) = statSTR.CXF_Duration(ipair) + dur;
                statSTR.ComboF_Duration(ipair) = statSTR.ComboF_Duration(ipair) + dur;
                statSTR.CXF_Power_Sum(ipair) = statSTR.CXF_Power_Sum(ipair) + level * dur;
                statSTR.ComboF_Power_Sum(ipair) = statSTR.ComboF_Power_Sum(ipair) + level * dur;
            case 'CHN'
                statSTR.CHN_Duration(ipair) = statSTR.CHN_Duration(ipair) + dur;
                statSTR.CHN_Power_Sum(ipair) = statSTR.CHN_Power_Sum(ipair) + level * dur;
            case 'CHF'
                statSTR.CHF_Duration(ipair) = statSTR.CHF_Duration(ipair) + dur;
                statSTR.CHF_Power_Sum(ipair) = statSTR.CHF_Power_Sum(ipair) + level * dur;
            case 'OLN'  % overlap categories - keep separate level calculations
                statSTR.OLN_pause_Duration(ipair) = statSTR.OLN_conv_Duration(ipair) + dur;
                statSTR.OLN_pause_Power_Sum(ipair) = statSTR.OLN_conv_Power_Sum(ipair) + level * dur;
            case 'OLF'  % overlap categories - keep separate level calculations
                statSTR.OLF_pause_Duration(ipair) = statSTR.OLF_conv_Duration(ipair) + dur;
                statSTR.OLF_pause_Power_Sum(ipair) = statSTR.OLF_conv_Power_Sum(ipair) + level * dur;
            otherwise
                statSTR.Noise_Duration(ipair) = statSTR.Noise_Duration(ipair) + dur;
                statSTR.Noise_Power_Sum(ipair) = statSTR.Noise_Power_Sum(ipair) + level * dur;
        end
    end
end

% compute the stats

conv_dur = conv_end_time - conv_start_time;
pause_dur = pause_end_time - pause_start_time;
WT_Noise_Power = statSTR.Noise_Power_Sum(ipair)/statSTR.Noise_Duration(ipair);
WT_Noise = 10*log10(WT_Noise_Power) + dB_Correction;

WT_FAN_Power = statSTR.FAN_Power_Sum(ipair)/statSTR.FAN_Duration(ipair);
WT_FAN = 10*log10(WT_FAN_Power) + dB_Correction;
WT_FAF_Power = statSTR.FAF_Power_Sum(ipair)/statSTR.FAF_Duration(ipair);
WT_FAF = 10*log10(WT_FAF_Power) + dB_Correction;
WT_Female_Power = (statSTR.FAN_Power_Sum(ipair)+statSTR.FAF_Power_Sum(ipair))/(statSTR.FAN_Duration(ipair)+statSTR.FAF_Duration(ipair));
WT_Female = 10*log10(WT_Female_Power) + dB_Correction;

WT_MAN_Power = statSTR.MAN_Power_Sum(ipair)/statSTR.MAN_Duration(ipair);
WT_MAN = 10*log10(WT_MAN_Power) + dB_Correction;
WT_MAF_Power = statSTR.MAF_Power_Sum(ipair)/statSTR.MAF_Duration(ipair);
WT_MAF = 10*log10(WT_MAF_Power) + dB_Correction;
WT_Male_Power = (statSTR.MAN_Power_Sum(ipair)+statSTR.MAF_Power_Sum(ipair))/(statSTR.MAN_Duration(ipair)+statSTR.MAF_Duration(ipair));
WT_Male = 10*log10(WT_Male_Power) + dB_Correction;

WT_CXN_Power = statSTR.CXN_Power_Sum(ipair)/statSTR.CXN_Duration(ipair);
WT_CXN = 10*log10(WT_CXN_Power) + dB_Correction;
WT_CXF_Power = statSTR.CXF_Power_Sum(ipair)/statSTR.CXF_Duration(ipair);
WT_CXF = 10*log10(WT_CXF_Power) + dB_Correction;
WT_Other_Ch_Power = (statSTR.CXN_Power_Sum(ipair)+statSTR.CXF_Power_Sum(ipair))/(statSTR.CXN_Duration(ipair)+statSTR.CXF_Duration(ipair));
WT_Other_Ch = 10*log10(WT_Other_Ch_Power) + dB_Correction;

WT_ComboN_Power = statSTR.ComboN_Power_Sum(ipair)/statSTR.ComboN_Duration(ipair);
WT_ComboN = 10*log10(WT_ComboN_Power) + dB_Correction;
WT_ComboF_Power = statSTR.ComboF_Power_Sum(ipair)/statSTR.ComboF_Duration(ipair);
WT_ComboF = 10*log10(WT_ComboF_Power) + dB_Correction;
WT_ComboAll_Power = (statSTR.ComboN_Power_Sum(ipair)+statSTR.ComboF_Power_Sum(ipair))/(statSTR.ComboN_Duration(ipair)+statSTR.ComboF_Duration(ipair));
WT_ComboAll = 10*log10(WT_ComboAll_Power) + dB_Correction;


WT_CHN_Power = statSTR.CHN_Power_Sum(ipair)/statSTR.CHN_Duration(ipair);
WT_CHN = 10*log10(WT_CHN_Power) + dB_Correction;
WT_CHF_Power = statSTR.CHF_Power_Sum(ipair)/statSTR.CHF_Duration(ipair);
WT_CHF = 10*log10(WT_CHF_Power) + dB_Correction;

WT_OLN_conv_Power = statSTR.OLN_conv_Power_Sum(ipair)/statSTR.OLN_conv_Duration(ipair);
WT_OLN_conv = 10*log10(WT_OLN_conv_Power) + dB_Correction;
WT_OLF_conv_Power = statSTR.OLF_conv_Power_Sum(ipair)/statSTR.OLF_conv_Duration(ipair);
WT_OLF_conv = 10*log10(WT_OLF_conv_Power) + dB_Correction;
WT_OLN_pause_Power = statSTR.OLN_pause_Power_Sum(ipair)/statSTR.OLN_pause_Duration(ipair);
WT_OLN_pause = 10*log10(WT_OLN_pause_Power) + dB_Correction;
WT_OLF_pause_Power = statSTR.OLF_pause_Power_Sum(ipair)/statSTR.OLF_pause_Duration(ipair);
WT_OLF_pause = 10*log10(WT_OLF_pause_Power) + dB_Correction;

SNR_FAN = WT_FAN - WT_Noise;
SNR_FAF = WT_FAF - WT_Noise;
SNR_Female = WT_Female - WT_Noise;

SNR_MAN  = WT_MAN - WT_Noise;
SNR_MAF  = WT_MAF - WT_Noise;
SNR_Male = WT_Male - WT_Noise;

SNR_CXN  = WT_CXN - WT_Noise;
SNR_CXF  = WT_CXF - WT_Noise;
SNR_Other_Ch = WT_Other_Ch - WT_Noise;

SNR_ComboN  = WT_ComboN - WT_Noise;
SNR_ComboF  = WT_ComboF - WT_Noise;
SNR_ComboAll = WT_ComboAll - WT_Noise;

SNR_CHN  = WT_CHN - WT_Noise;
SNR_CHF  = WT_CHF - WT_Noise;

% string the data values together

dataw = [ipair, pause_number, conv_start_time, conv_end_time, conv_dur, pause_start_time, pause_end_time, pause_dur,...
    WT_OLN_conv, WT_OLF_conv, WT_OLN_pause, WT_OLF_pause, WT_Noise,...
    NaN, WT_Female, WT_FAN, WT_FAF, WT_Male, WT_MAN, WT_MAF, WT_Other_Ch, WT_CXN, WT_CXF, WT_ComboAll, WT_ComboN,  WT_ComboF, NaN, WT_CHN, WT_CHF,...
    NaN, NaN, SNR_Female, SNR_FAN, SNR_FAF, SNR_Male, SNR_MAN, SNR_MAF, SNR_Other_Ch, SNR_CXN, SNR_CXF, SNR_ComboAll, SNR_ComboN, SNR_ComboF, NaN, SNR_CHN, SNR_CHF];
dataw = round(dataw * 100)/100;   % keep two decimal places
dataw = num2cell(dataw);
row = line2rite;

col_1 = 1;
col_2 = col_1 + length(dataw) - 1;


grand_data_block(row, col_1:col_2) = dataw;

