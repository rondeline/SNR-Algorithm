function process_SNR_Power_2( ...
    convers_segment, pause_segment, ipair, pause_number, ...
    conv_start_time, conv_end_time, pause_start_time, ...
    pause_end_time, line2rite)
% -------------------------------------------------------------------------
% Compatible with ITS versions 4.3.x   (lacks average_dB / peak_dB fields)
% -------------------------------------------------------------------------
% The only behavioural change is that power/snr sums are updated **only**
% when a valid dB figure exists.  Durations and label counts are still
% accumulated for every segment so timing statistics are untouched.
%
% 15-May-2025  JARVIS
% -------------------------------------------------------------------------

global LENA_labels statSTR dB_Correction grand_data_block

% convenience -------------------------------------------------------------
in_range   = @check_inclusion;                % shorter name
label_idx  = @(lab) find(ismember(LENA_labels,lab),1);
valid_db   = @(x) ~(isempty(x) || isnan(x));

% ---------- helper: safely add power ------------------------------------
    function add_pow(field,dur,lev)
        if valid_db(lev)            % only when dB existed in the XML
            statSTR.(field)(ipair) = statSTR.(field)(ipair) + lev*dur;
        end
    end
% -------------------------------------------------------------------------

% ===== 1.  CONVERSATION SEGMENT ==========================================
u_start = strfind(convers_segment,'spkr=');
u_stop  = strfind(convers_segment,'/>');

if numel(u_start) ~= numel(u_stop)
    warning('Conversation block %d has mismatched delimiters – skipped.',ipair);
    return
end

for k = 1:numel(u_start)
    seg = convers_segment(u_start(k):u_stop(k));
    [t0,t1,db] = process_line3_4_3_1(seg);          % db = NaN if field absent
    dur = t1 - t0;

    if in_range(t0,t1) && dur>0
        lab = seg(7:9);
        idx = label_idx(lab);
        if ~isempty(idx)
            statSTR.Label_Count(idx,1)     = statSTR.Label_Count(idx,1)+1;
            statSTR.Label_Duration(idx,1)  = statSTR.Label_Duration(idx,1)+dur;
        end

        % ----------- accumulate -----------------------------------------
        pwr = 10.^(db/10);
        switch lab
            case 'FAN'
                statSTR.FAN_Duration(ipair)   = statSTR.FAN_Duration(ipair)+dur;
                statSTR.ComboN_Duration(ipair)= statSTR.ComboN_Duration(ipair)+dur;
                add_pow('FAN_Power_Sum',dur,pwr);
                add_pow('ComboN_Power_Sum',dur,pwr);
            case 'FAF'
                statSTR.FAF_Duration(ipair)   = statSTR.FAF_Duration(ipair)+dur;
                statSTR.ComboF_Duration(ipair)= statSTR.ComboF_Duration(ipair)+dur;
                add_pow('FAF_Power_Sum',dur,pwr);
                add_pow('ComboF_Power_Sum',dur,pwr);
            case 'MAN'
                statSTR.MAN_Duration(ipair)   = statSTR.MAN_Duration(ipair)+dur;
                statSTR.ComboN_Duration(ipair)= statSTR.ComboN_Duration(ipair)+dur;
                add_pow('MAN_Power_Sum',dur,pwr);
                add_pow('ComboN_Power_Sum',dur,pwr);
            case 'MAF'
                statSTR.MAF_Duration(ipair)   = statSTR.MAF_Duration(ipair)+dur;
                statSTR.ComboF_Duration(ipair)= statSTR.ComboF_Duration(ipair)+dur;
                add_pow('MAF_Power_Sum',dur,pwr);
                add_pow('ComboF_Power_Sum',dur,pwr);
            case 'CXN'
                statSTR.CXN_Duration(ipair)   = statSTR.CXN_Duration(ipair)+dur;
                statSTR.ComboN_Duration(ipair)= statSTR.ComboN_Duration(ipair)+dur;
                add_pow('CXN_Power_Sum',dur,pwr);
                add_pow('ComboN_Power_Sum',dur,pwr);
            case 'CXF'
                statSTR.CXF_Duration(ipair)   = statSTR.CXF_Duration(ipair)+dur;
                statSTR.ComboF_Duration(ipair)= statSTR.ComboF_Duration(ipair)+dur;
                add_pow('CXF_Power_Sum',dur,pwr);
                add_pow('ComboF_Power_Sum',dur,pwr);
            case 'CHN'
                statSTR.CHN_Duration(ipair)   = statSTR.CHN_Duration(ipair)+dur;
                add_pow('CHN_Power_Sum',dur,pwr);
            case 'CHF'
                statSTR.CHF_Duration(ipair)   = statSTR.CHF_Duration(ipair)+dur;
                add_pow('CHF_Power_Sum',dur,pwr);
            case 'OLN'
                statSTR.OLN_conv_Duration(ipair)=statSTR.OLN_conv_Duration(ipair)+dur;
                add_pow('OLN_conv_Power_Sum',dur,pwr);
            case 'OLF'
                statSTR.OLF_conv_Duration(ipair)=statSTR.OLF_conv_Duration(ipair)+dur;
                add_pow('OLF_conv_Power_Sum',dur,pwr);
            otherwise                       % all other labels → noise
                statSTR.Noise_Duration(ipair)=statSTR.Noise_Duration(ipair)+dur;
                add_pow('Noise_Power_Sum',dur,pwr);
        end
    end
end

% ===== 2.  PAUSE SEGMENT  (same strategy) ================================
u_start = strfind(pause_segment,'spkr=');
u_stop  = strfind(pause_segment,'/>');

if numel(u_start) ~= numel(u_stop)
    warning('Pause block %d has mismatched delimiters – skipped.',pause_number);
    return
end

for k = 1:numel(u_start)
    seg = pause_segment(u_start(k):u_stop(k));
    [t0,t1,db] = process_line3_4_3_1(seg);
    dur = t1 - t0;

    if in_range(t0,t1) && dur>0
        lab = seg(7:9);
        idx = label_idx(lab);
        if ~isempty(idx)
            statSTR.Label_Count(idx,2)     = statSTR.Label_Count(idx,2)+1;
            statSTR.Label_Duration(idx,2)  = statSTR.Label_Duration(idx,2)+dur;
        end

        pwr = 10.^(db/10);
        switch lab
            case 'FAN'
                statSTR.FAN_Duration(ipair)=statSTR.FAN_Duration(ipair)+dur;
                add_pow('FAN_Power_Sum',dur,pwr);
                statSTR.ComboN_Duration(ipair)=statSTR.ComboN_Duration(ipair)+dur;
                add_pow('ComboN_Power_Sum',dur,pwr);
            case 'FAF'
                statSTR.FAF_Duration(ipair)=statSTR.FAF_Duration(ipair)+dur;
                add_pow('FAF_Power_Sum',dur,pwr);
                statSTR.ComboF_Duration(ipair)=statSTR.ComboF_Duration(ipair)+dur;
                add_pow('ComboF_Power_Sum',dur,pwr);
            case 'MAN'
                statSTR.MAN_Duration(ipair)=statSTR.MAN_Duration(ipair)+dur;
                add_pow('MAN_Power_Sum',dur,pwr);
                statSTR.ComboN_Duration(ipair)=statSTR.ComboN_Duration(ipair)+dur;
                add_pow('ComboN_Power_Sum',dur,pwr);
            case 'MAF'
                statSTR.MAF_Duration(ipair)=statSTR.MAF_Duration(ipair)+dur;
                add_pow('MAF_Power_Sum',dur,pwr);
                statSTR.ComboF_Duration(ipair)=statSTR.ComboF_Duration(ipair)+dur;
                add_pow('ComboF_Power_Sum',dur,pwr);
            case 'CXN'
                statSTR.CXN_Duration(ipair)=statSTR.CXN_Duration(ipair)+dur;
                add_pow('CXN_Power_Sum',dur,pwr);
                statSTR.ComboN_Duration(ipair)=statSTR.ComboN_Duration(ipair)+dur;
                add_pow('ComboN_Power_Sum',dur,pwr);
            case 'CXF'
                statSTR.CXF_Duration(ipair)=statSTR.CXF_Duration(ipair)+dur;
                add_pow('CXF_Power_Sum',dur,pwr);
                statSTR.ComboF_Duration(ipair)=statSTR.ComboF_Duration(ipair)+dur;
                add_pow('ComboF_Power_Sum',dur,pwr);
            case 'CHN'
                statSTR.CHN_Duration(ipair)=statSTR.CHN_Duration(ipair)+dur;
                add_pow('CHN_Power_Sum',dur,pwr);
            case 'CHF'
                statSTR.CHF_Duration(ipair)=statSTR.CHF_Duration(ipair)+dur;
                add_pow('CHF_Power_Sum',dur,pwr);
            case 'OLN'
                statSTR.OLN_pause_Duration(ipair)=statSTR.OLN_pause_Duration(ipair)+dur;
                add_pow('OLN_pause_Power_Sum',dur,pwr);
            case 'OLF'
                statSTR.OLF_pause_Duration(ipair)=statSTR.OLF_pause_Duration(ipair)+dur;
                add_pow('OLF_pause_Power_Sum',dur,pwr);
            otherwise
                statSTR.Noise_Duration(ipair)=statSTR.Noise_Duration(ipair)+dur;
                add_pow('Noise_Power_Sum',dur,pwr);
        end
    end
end

% ===== 3.  compute weighted metrics (safe divide) ========================
safe_db = @(n,d) (d>0 && n>0) * (10*log10(n/d)+dB_Correction) + ...
                 (d==0 || n==0) * NaN;

conv_dur  = conv_end_time  - conv_start_time;
pause_dur = pause_end_time - pause_start_time;

WT_Noise   = safe_db(statSTR.Noise_Power_Sum(ipair),  statSTR.Noise_Duration(ipair));
WT_FAN     = safe_db(statSTR.FAN_Power_Sum(ipair),    statSTR.FAN_Duration(ipair));
WT_FAF     = safe_db(statSTR.FAF_Power_Sum(ipair),    statSTR.FAF_Duration(ipair));
WT_Female  = safe_db(statSTR.FAN_Power_Sum(ipair)+statSTR.FAF_Power_Sum(ipair), ...
                     statSTR.FAN_Duration(ipair)+statSTR.FAF_Duration(ipair));
WT_MAN     = safe_db(statSTR.MAN_Power_Sum(ipair),    statSTR.MAN_Duration(ipair));
WT_MAF     = safe_db(statSTR.MAF_Power_Sum(ipair),    statSTR.MAF_Duration(ipair));
WT_Male    = safe_db(statSTR.MAN_Power_Sum(ipair)+statSTR.MAF_Power_Sum(ipair), ...
                     statSTR.MAN_Duration(ipair)+statSTR.MAF_Duration(ipair));
WT_CXN     = safe_db(statSTR.CXN_Power_Sum(ipair),    statSTR.CXN_Duration(ipair));
WT_CXF     = safe_db(statSTR.CXF_Power_Sum(ipair),    statSTR.CXF_Duration(ipair));
WT_OtherCh = safe_db(statSTR.CXN_Power_Sum(ipair)+statSTR.CXF_Power_Sum(ipair), ...
                     statSTR.CXN_Duration(ipair)+statSTR.CXF_Duration(ipair));
WT_ComboN  = safe_db(statSTR.ComboN_Power_Sum(ipair), statSTR.ComboN_Duration(ipair));
WT_ComboF  = safe_db(statSTR.ComboF_Power_Sum(ipair), statSTR.ComboF_Duration(ipair));
WT_ComboAll= safe_db(statSTR.ComboN_Power_Sum(ipair)+statSTR.ComboF_Power_Sum(ipair), ...
                     statSTR.ComboN_Duration(ipair)+statSTR.ComboF_Duration(ipair));
WT_CHN     = safe_db(statSTR.CHN_Power_Sum(ipair),    statSTR.CHN_Duration(ipair));
WT_CHF     = safe_db(statSTR.CHF_Power_Sum(ipair),    statSTR.CHF_Duration(ipair));
WT_OLN_c   = safe_db(statSTR.OLN_conv_Power_Sum(ipair), statSTR.OLN_conv_Duration(ipair));
WT_OLF_c   = safe_db(statSTR.OLF_conv_Power_Sum(ipair), statSTR.OLF_conv_Duration(ipair));
WT_OLN_p   = safe_db(statSTR.OLN_pause_Power_Sum(ipair),statSTR.OLN_pause_Duration(ipair));
WT_OLF_p   = safe_db(statSTR.OLF_pause_Power_Sum(ipair),statSTR.OLF_pause_Duration(ipair));

% SNRs (NaN-propagate automatically)
SNR = @(x) x - WT_Noise;
SNR_FAN = SNR(WT_FAN);  SNR_FAF = SNR(WT_FAF);  SNR_Female = SNR(WT_Female);
SNR_MAN = SNR(WT_MAN);  SNR_MAF = SNR(WT_MAF);  SNR_Male   = SNR(WT_Male);
SNR_CXN = SNR(WT_CXN);  SNR_CXF = SNR(WT_CXF);  SNR_OtherCh= SNR(WT_OtherCh);
SNR_CN  = SNR(WT_ComboN); SNR_CF = SNR(WT_ComboF); SNR_CA  = SNR(WT_ComboAll);
SNR_CHN = SNR(WT_CHN);  SNR_CHF = SNR(WT_CHF);

% ---------- assemble row & write out ------------------------------------
row = line2rite;
dataw = [ ...
    ipair, pause_number, conv_start_time, conv_end_time, conv_dur, ...
    pause_start_time, pause_end_time, pause_dur, ...
    WT_OLN_c, WT_OLF_c, WT_OLN_p, WT_OLF_p, WT_Noise, NaN, ...
    WT_Female, WT_FAN, WT_FAF, WT_Male, WT_MAN, WT_MAF, WT_OtherCh, ...
    WT_CXN, WT_CXF, WT_ComboAll, WT_ComboN, WT_ComboF, NaN, WT_CHN, WT_CHF, ...
    NaN, NaN, SNR_Female, SNR_FAN, SNR_FAF, SNR_Male, SNR_MAN, SNR_MAF, ...
    SNR_OtherCh, SNR_CXN, SNR_CXF, SNR_CA, SNR_CN, SNR_CF, NaN, SNR_CHN, SNR_CHF ];
dataw = round(dataw*100)/100;
grand_data_block(row,1:numel(dataw)) = num2cell(dataw);
end
