function datax = compute_weighted_averages_Power
%  Modified 6/19/2019
%  Now weighted averages are based on Power, not dB
%  Called from compute_snr_power.m
% Compute weighted averages over the entire day

global statSTR dB_Correction

% returns day averages as a cell array

Noise_Power = sum(statSTR.Noise_Power_Sum)/sum(statSTR.Noise_Duration);
Noise = 10*log10(Noise_Power) + dB_Correction;

OLN_conv_Power = sum(statSTR.OLN_conv_Power_Sum)/sum(statSTR.OLN_conv_Duration);
OLN_conv = 10*log10(OLN_conv_Power) + dB_Correction;
OLF_conv_Power = sum(statSTR.OLF_conv_Power_Sum)/sum(statSTR.OLF_conv_Duration);
OLF_conv = 10*log10(OLF_conv_Power) + dB_Correction;
OLN_pause_Power = sum(statSTR.OLN_pause_Power_Sum)/sum(statSTR.OLN_pause_Duration);
OLN_pause = 10*log10(OLN_pause_Power) + dB_Correction;
OLF_pause_Power = sum(statSTR.OLF_pause_Power_Sum)/sum(statSTR.OLF_pause_Duration);
OLF_pause = 10*log10(OLF_pause_Power) + dB_Correction;

FAN_Power = sum(statSTR.FAN_Power_Sum)/sum(statSTR.FAN_Duration);
FAN = 10*log10(FAN_Power) + dB_Correction;
FAF_Power = sum(statSTR.FAF_Power_Sum)/sum(statSTR.FAF_Duration);
FAF = 10*log10(FAF_Power) + dB_Correction;
Female_Power = (sum(statSTR.FAN_Power_Sum) + sum(statSTR.FAF_Power_Sum)) / (sum(statSTR.FAN_Duration)+sum(statSTR.FAF_Duration));
Female = 10*log10(Female_Power) + dB_Correction;

MAN_Power = sum(statSTR.MAN_Power_Sum)/sum(statSTR.MAN_Duration);
MAN = 10*log10(MAN_Power) + dB_Correction;
MAF_Power = sum(statSTR.MAF_Power_Sum)/sum(statSTR.MAF_Duration);
MAF = 10*log10(MAF_Power) + dB_Correction;
Male_Power = (sum(statSTR.MAN_Power_Sum) + sum(statSTR.MAF_Power_Sum)) / (sum(statSTR.MAN_Duration)+sum(statSTR.MAF_Duration));
Male = 10*log10(Male_Power) + dB_Correction;

CXN_Power = sum(statSTR.CXN_Power_Sum)/sum(statSTR.CXN_Duration);
CXN = 10*log10(CXN_Power) + dB_Correction;
CXF_Power = sum(statSTR.CXF_Power_Sum)/sum(statSTR.CXF_Duration);
CXF = 10*log10(CXF_Power) + dB_Correction;
Other_Ch_Power = (sum(statSTR.CXN_Power_Sum) + sum(statSTR.CXF_Power_Sum)) / (sum(statSTR.CXN_Duration)+sum(statSTR.CXF_Duration));
Other_Ch = 10*log10(Other_Ch_Power) + dB_Correction;

ComboN_Power = sum(statSTR.ComboN_Power_Sum)/sum(statSTR.ComboN_Duration);
ComboN = 10*log10(ComboN_Power) + dB_Correction;
ComboF_Power = sum(statSTR.ComboF_Power_Sum)/sum(statSTR.ComboF_Duration);
ComboF = 10*log10(ComboF_Power) + dB_Correction;
ComboAll_Power = (sum(statSTR.ComboN_Power_Sum) + sum(statSTR.ComboF_Power_Sum)) / (sum(statSTR.ComboN_Duration)+sum(statSTR.ComboF_Duration));
ComboAll = 10*log10(ComboAll_Power) + dB_Correction;

CHN_Power = sum(statSTR.CHN_Power_Sum)/sum(statSTR.CHN_Duration);
CHN = 10*log10(CHN_Power) + dB_Correction;
CHF_Power = sum(statSTR.CHF_Power_Sum)/sum(statSTR.CHF_Duration);
CHF = 10*log10(CHF_Power) + dB_Correction;

SNR_FAN = FAN - Noise;
SNR_FAF = FAF - Noise;
SNR_Female = Female - Noise;

SNR_MAN = MAN - Noise;
SNR_MAF = MAF - Noise;
SNR_Male = Male - Noise;

SNR_CXN = CXN - Noise;
SNR_CXF = CXF - Noise;
SNR_Other_Ch = Other_Ch - Noise;

SNR_ComboN = ComboN - Noise;
SNR_ComboF = ComboF - Noise;
SNR_ComboAll = ComboAll - Noise;


SNR_CHN = CHN - Noise;
SNR_CHF = CHF - Noise;

datax = [OLN_conv, OLF_conv, OLN_pause, OLF_pause, Noise, NaN, NaN, NaN...
    Female, FAN, FAF, Male, MAN, MAF, Other_Ch, CXN, CXF, ComboAll, ComboN,  ComboF, NaN, CHN, CHF,...
    NaN, NaN, SNR_Female, SNR_FAN, SNR_FAF, SNR_Male, SNR_MAN, SNR_MAF, SNR_Other_Ch, SNR_CXN, SNR_CXF, SNR_ComboAll, SNR_ComboN, SNR_ComboF, NaN, SNR_CHN, SNR_CHF];
datax = round(datax * 100)/100;   % keep two decimal places
datax = num2cell(datax);

