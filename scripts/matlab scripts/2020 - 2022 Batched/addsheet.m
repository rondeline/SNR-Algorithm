SNR_output_file = [pwd filesep 'SNR_soft_speech4 .xlsx'];
% see if file exists

    xlswrite(SNR_output_file, NaN);
    
    e = actxserver('Excel.Application');
    ewb = e.Workbooks.Open(SNR_output_file);
    for k = 2:3
        ewb.Worksheets.Item(['Sheet' int2str(k)]).Delete;
    end
    WS = ewb.Worksheets;
    WS.Add([], WS.Item(WS.Count+2));
    ewb.Save
    ewb.Close(false)

% 
% filen = uigetfile('*.txt', 'Select File to Analyze');
% fid = fopen(filen, 'rt');
% if fid <= 0
%     disp('Sorry, could not open the file.')
%     return
% end
% 
