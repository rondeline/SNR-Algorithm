function datax = compute_weighted_averages_Power
% Weighted day-long averages (based on **Power**) with safe zero-checks.
% 15-May-2025  JARVIS
% -------------------------------------------------------------------------
global statSTR dB_Correction

safe_db = @(num,den) ...
    (den>0 && num>0) * (10*log10(num/den)+dB_Correction) + ...
    (den==0 || num==0) * NaN;                 % returns NaN when undefined

% ----- conversation & pause power levels --------------------------------
Noise      = safe_db(sum(statSTR.Noise_Power_Sum),      sum(statSTR.Noise_Duration));
OLN_conv   = safe_db(sum(statSTR.OLN_conv_Power_Sum),   sum(statSTR.OLN_conv_Duration));
OLF_conv   = safe_db(sum(statSTR.OLF_conv_Power_Sum),   sum(statSTR.OLF_conv_Duration));
OLN_pause  = safe_db(sum(statSTR.OLN_pause_Power_Sum),  sum(statSTR.OLN_pause_Duration));
OLF_pause  = safe_db(sum(statSTR.OLF_pause_Power_Sum),  sum(statSTR.OLF_pause_Duration));

FAN        = safe_db(sum(statSTR.FAN_Power_Sum),        sum(statSTR.FAN_Duration));
FAF        = safe_db(sum(statSTR.FAF_Power_Sum),        sum(statSTR.FAF_Duration));
Female     = safe_db(sum(statSTR.FAN_Power_Sum)+sum(statSTR.FAF_Power_Sum), ...
                     sum(statSTR.FAN_Duration)+sum(statSTR.FAF_Duration));

MAN        = safe_db(sum(statSTR.MAN_Power_Sum),        sum(statSTR.MAN_Duration));
MAF        = safe_db(sum(statSTR.MAF_Power_Sum),        sum(statSTR.MAF_Duration));
Male       = safe_db(sum(statSTR.MAN_Power_Sum)+sum(statSTR.MAF_Power_Sum), ...
                     sum(statSTR.MAN_Duration)+sum(statSTR.MAF_Duration));

CXN        = safe_db(sum(statSTR.CXN_Power_Sum),        sum(statSTR.CXN_Duration));
CXF        = safe_db(sum(statSTR.CXF_Power_Sum),        sum(statSTR.CXF_Duration));
Other_Ch   = safe_db(sum(statSTR.CXN_Power_Sum)+sum(statSTR.CXF_Power_Sum), ...
                     sum(statSTR.CXN_Duration)+sum(statSTR.CXF_Duration));

ComboN     = safe_db(sum(statSTR.ComboN_Power_Sum),     sum(statSTR.ComboN_Duration));
ComboF     = safe_db(sum(statSTR.ComboF_Power_Sum),     sum(statSTR.ComboF_Duration));
ComboAll   = safe_db(sum(statSTR.ComboN_Power_Sum)+sum(statSTR.ComboF_Power_Sum), ...
                     sum(statSTR.ComboN_Duration)+sum(statSTR.ComboF_Duration));

CHN        = safe_db(sum(statSTR.CHN_Power_Sum),        sum(statSTR.CHN_Duration));
CHF        = safe_db(sum(statSTR.CHF_Power_Sum),        sum(statSTR.CHF_Duration));

% ----- SNRs --------------------------------------------------------------
snr = @(x) x - Noise;
SNR_FAN      = snr(FAN);   SNR_FAF      = snr(FAF);   SNR_Female   = snr(Female);
SNR_MAN      = snr(MAN);   SNR_MAF      = snr(MAF);   SNR_Male     = snr(Male);
SNR_CXN      = snr(CXN);   SNR_CXF      = snr(CXF);   SNR_Other_Ch = snr(Other_Ch);
SNR_ComboN   = snr(ComboN);SNR_ComboF   = snr(ComboF);SNR_ComboAll = snr(ComboAll);
SNR_CHN      = snr(CHN);   SNR_CHF      = snr(CHF);

% ----- assemble row (same order as original RunME) -----------------------
datax = [ ...
    OLN_conv, OLF_conv, OLN_pause, OLF_pause, Noise, NaN, ...
    Female, FAN, FAF, Male, MAN, MAF, Other_Ch, CXN, CXF, ...
    ComboAll, ComboN, ComboF, NaN, CHN, CHF, ...
    NaN, NaN, SNR_Female, SNR_FAN, SNR_FAF, SNR_Male, SNR_MAN, SNR_MAF, ...
    SNR_Other_Ch, SNR_CXN, SNR_CXF, SNR_ComboAll, SNR_ComboN, SNR_ComboF, ...
    NaN, SNR_CHN, SNR_CHF ];

datax = round(datax*100)/100;
datax = num2cell(datax);
end
