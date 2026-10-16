function Template_Header = Header_Maker(Day);

Template_Header = {'_Noise'
'_Speech Comb'
'_Speech Near'
'_Speech Far'
'_Speech Comb Adjusted'
'_Speech Near Adjusted'
'_Speech Far Adjusted'
'_SNR Comb'
'_SNR Near'
'_SNR Far'
'_SNR Comb Adjusted'
'_SNR Near Adjusted'
'_SNR Far Adjusted'};


Template_Header = strcat('Day', num2str(Day), Template_Header)

end