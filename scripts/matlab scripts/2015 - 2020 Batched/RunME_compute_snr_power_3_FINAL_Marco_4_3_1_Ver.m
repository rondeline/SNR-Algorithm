clear all
% compute_snr_power_2.m
% Modified from compute_snr.m, so that weighted averages are now based on
% power, not dB.
%  18-Jun-2019
%
% 15-Sep-2019
% New version, to use pause following each conversation
%
% November-2021
% New version to compile data across days, and batch execute.
% Data output to Compiled_BatchRun_UConn.xlsx

compileddataoutput = [pwd filesep 'Compiled_BatchRun_Marco2_trial.xlsx'];
%datafolder = ['Z:\Programs, Materials, and Tasks\Matlab - LENA Noise Program\OLD ITS files from Nairan (2008 - 2015) -- Need to figure out'];  % data folder
datafolder = 'Z:\Research Projects\NIH CI study\LENA\RunningCode + Protocol\noEMA_project\itsVer_4.3.1';  % data folder

%% Added 011723

%{
All_Files = dir(datafolder);
All_Files = struct2cell(All_Files)';
All_Files = All_Files(3:end,1);

TXT_Files = find(contains(All_Files,'.its')==1);
Excel_Files = find(contains(All_Files,'.xlsx')==1);

ID_TXT = erase (All_Files(TXT_Files,1),'.its');
ID_Excel = erase (All_Files(Excel_Files,1),'.xlsx');

ID_Same = intersect(ID_TXT,ID_Excel);

if length(ID_Same) < max(length(ID_TXT),length(ID_Excel))
    
    ID_Diff_TXT = setdiff(ID_Excel,ID_TXT);
    ID_Diff_Xlsx = setdiff(ID_TXT,ID_Excel);
    
    if size(ID_Diff_TXT,1) > 0 || size(ID_Diff_Xlsx,1) > 0
        
        Missing_Xlsx = strcat(ID_Diff_Xlsx,'.xlsx');
        Missing_Txt = strcat(ID_Diff_TXT,'.txt');
        disp(['The following files are missing:'])
        Missing_Xlsx = Missing_Xlsx'
        Missing_Txt = Missing_Txt'
        
        yn = input('Do you want to comnntinue without these recordings? [y or n]: ', 's');
        
        if isempty(yn)  || upper(yn) ~= 'Y'
            error('OK, exiting...')
        end

    end
end
    
clear All_Files Excel_Files ID_Diff_TXT ID_Diff_Xlsx ID_Excel ID_TXT Missing_Txt Missing_Xlsx TXT_Files yn
%}

%% Changed
%% Getting the ID automatically from the participant folder
 ID = {
         'S52'  
%         'S2_EG'
%         %'S3_SR'
%         %'S4_JS'
%         %'S5_LA'
%         %'S6_OR'
%         %'S7_AM'
%         %'S8_BM'
%         %'S9_JM'
%         %'S10_MR'
%         %'S11_EQ'
%         %'S12_EA'
%         %'S13_FR'
%         %'S14_RR'
%         %'S15_LR'
%         %'S16_AR'
         };
%{
ID_Marker =cell2mat(strfind(ID,'_'));

for Subject = 1:length(ID)
    Current_ID = ID{Subject,1};
    ID{Subject,1} = Current_ID(1:ID_Marker(Subject,2)-1);
    Recordings{Subject,1} = strcat(Current_ID(ID_Marker(Subject,2):end),'.its');
    
    clear Current_ID
end

clear ID_Marker ID Subject

Unique_Subjects = unique(ID);
MAX_Recording = 0;
for Subject = 1:length(Unique_Subjects)
    
    Current_Subject = Unique_Subjects (Subject);
    Current_Subject = strcmp(ID,Current_Subject);
    Rec{Subject,:} =  Recordings(Current_Subject)';
    MAX_Recording = max(sum(Current_Subject),MAX_Recording);
    clear Current_Subject
end

ID = Unique_Subjects;
Rec;

clear Unique_Subjects 
%}
% ID = {
%         'P41_LITM'  
%     };

Rec = {{'_XX_Day1.its', '_XX_Day2.its'}};

%
% Script file to compute SNR for Female, Male, Other Child, Combined over Male, Female, Other Child, and for Child
% Based on program analyze_its_file.m
% 25-May-2018
% 14-Jun-2018
% 22-Jun-2018 - Updated to compute SNR separately for "Near" and "Far" for
%      each speaker.
% Tharpe, Hornsby, Benitez Project



global statSTR
global grand_data_block
global Inclusion_Boundaries
global dB_Correction
global LENA_labels

global h1_row h2_row
global h2a_col h2b1_col h2b2_col
global h3_col h3_row
global headings2a

% for counting labels and computing proportional durations

LENA_labels = {'FAN', 'FAF', 'MAN', 'MAF', 'CXN', 'CXF', 'CHN', 'CHF', 'NON', 'NOF', 'TVN', 'TVF', 'OLN', 'OLF', 'SIL'};
number_labels = length(LENA_labels);
statSTR.Label_Count = zeros(number_labels, 2);    % allocate space for counts
statSTR.Label_Duration = zeros(number_labels, 2);  % and for durations

SNR_output_file = [pwd filesep 'Individual_SNR_Power.xlsx'];



day = {'_XX_Day1.txt', '_XX_Day2.txt', '_XX_Day3.txt'};  % if more than two days, then add to this list (e.g. {'_Day3.its'})

for f = 1:length(ID)
    
    %for each ID, run two days, d = day
    
    day = Rec{f};
    for d = 1:length(day) % days
        
        filen = horzcat([char(ID{f}), char(day(d))]);
        fullname = [datafolder filesep filen];
        fid = fopen(fullname, 'rt');
        if fid <= 0
            disp('Sorry, could not open the file.')
            return
        end
        
        display(['Running ', filen])
        
        [~, sheetname] = fileparts(fullname);  % get just filename, without extension, which will become sheet name
        
     % Now, see if output file exists. If not, user may create it
     if ~exist(SNR_output_file)
            disp(['Output file ' SNR_output_file ' does not exist.'])
            yn = input('Do you want to create it? [y or n]: ', 's');
            if isempty(yn)  || upper(yn) ~= 'Y'
                disp('OK, exiting...')
                return
            end
            xlswrite(SNR_output_file, NaN);  % create blank file
            
        % delete sheets 2 and 3 from this blank file if they exist, and name
        % remaining sheet according to subject and session
        [~, B] = xlsfinfo(SNR_output_file); % get sheet names
        nsheets = length(B);
        if nsheets > 1
                e = actxserver('Excel.Application'); % delete Sheets 2 & 3
                ewb = e.Workbooks.Open(SNR_output_file);
                for k = 2:nsheets
                    ewb.Worksheets.Item(['Sheet' int2str(k)]).Delete;
                end
                ewb.Save
                ewb.Close(false)
            end
            rename_sheet(SNR_output_file, 1, sheetname)
            write_SNR_headings_2(SNR_output_file, 1)
            xlswrite(SNR_output_file, {sheetname}, sheetname, 'A1')  % id at upper left
            bolden(SNR_output_file, 1, {'A1'})   % bolden it
            sheet_no = 1;
        else
            sheet_no = new_worksheet_deleteallcontent_4_3_1(SNR_output_file, sheetname);    % create new worksheet (overwrites any existing data, updated november 21 to delete existing content for easier batching)
        end
        
        dB_Correction = 97;   % to convert LINA levels to dBA (?)
        
        number_of_rows_grand = 1000;  % pick a big number
        number_of_columns_grand = 60; % pick a large enough number
        
        grand_data_block = num2cell(NaN * ones(number_of_rows_grand, number_of_columns_grand));  % for storage of detailed data
        
        % Get inclusion times associated with this file
        Inclusion_Boundaries = get_inclusion_times(fullname);  %updated to include pathname
        if isscalar(Inclusion_Boundaries)
            disp('Inclusion file read problem! Exiting...')
            return   % problem encountered
        end
        
        whole_text = fscanf(fid, '%c');   % read in the whole file as text
        
        % now find the beginning and ending phrases
        start_place = strfind(whole_text,'Flow of the Recordings');
        if length(start_place) ~= 1
            disp('Could not find opening phrase in file')
            return
        end
        % 4.6 files include the literal string "the Bars", 4.3.1 do not.
        stop_place = strfind(whole_text, 'the Bars');
        if isempty(stop_place)                 % <-- 4.3.1 fallback
            stop_place = strfind(whole_text,'</Recording>');    % use last </Recording>
            stop_place = stop_place(end);       % pick the final closing tag
        end
        
        whole_text = whole_text(start_place:stop_place);  % keep only relevant part
        
        % Get boundaries of conversations
        conversation_start = findstr(whole_text, 'Conversation num');
        conversation_stop = findstr(whole_text, 'Conversation>');
        if length(conversation_start) ~= length(conversation_stop)
            disp('Problem with conversation markers!')
            return
        end
        
        pause_start = findstr(whole_text, 'Pause num');
        pause_stop = findstr(whole_text, 'Pause>');
        if length(pause_start) ~= length(pause_stop)
            disp('Problem with pause markers!')
            return
        end
        
        %         unequal_lengths = false;
        %         if length(conversation_start) ~= length(pause_start)
        %             fprintf('\nWarning! Different number of conversations (%d) and pauses (%d)\n\n', length(conversation_start), length(pause_start));
        %             yn = input('Enter Y to continue anyway: ', 's');
        %             if upper(yn) ~= 'Y'
        %                 disp('Exiting...')
        %                 return
        %             end
        %             unequal_lengths = true;
        %         end
        
        % allocate space for chunk stats
        number_chunks = length(conversation_start);
        
        statSTR.minimum_time = 0;
        statSTR.Noise_Power_Sum = zeros(number_chunks,1);
        statSTR.OLN_conv_Power_Sum = zeros(number_chunks,1);  % overlap near and far (conversations)
        statSTR.OLF_conv_Power_Sum = zeros(number_chunks,1);
        statSTR.OLN_pause_Power_Sum = zeros(number_chunks,1);  % overlap near and far (pausess)
        statSTR.OLF_pause_Power_Sum = zeros(number_chunks,1);
        statSTR.FAN_Power_Sum = zeros(number_chunks,1);
        statSTR.FAF_Power_Sum = zeros(number_chunks,1);
        statSTR.MAN_Power_Sum = zeros(number_chunks,1);
        statSTR.MAF_Power_Sum = zeros(number_chunks,1);
        statSTR.CXN_Power_Sum = zeros(number_chunks,1);
        statSTR.CXF_Power_Sum = zeros(number_chunks,1);
        statSTR.CHN_Power_Sum = zeros(number_chunks,1);
        statSTR.CHF_Power_Sum = zeros(number_chunks,1);
        statSTR.ComboN_Power_Sum = zeros(number_chunks,1); % combination of Male, Female, and OtherChild
        statSTR.ComboF_Power_Sum = zeros(number_chunks,1); % combination of Male, Female, and OtherChild
        
        statSTR.Noise_Duration = zeros(number_chunks,1);
        statSTR.OLN_conv_Duration = zeros(number_chunks,1);  % overlap near and far (conversations)
        statSTR.OLF_conv_Duration = zeros(number_chunks,1);
        statSTR.OLN_pause_Duration = zeros(number_chunks,1);  % overlap near and far (pausess)
        statSTR.OLF_pause_Duration = zeros(number_chunks,1);
        statSTR.FAN_Duration = zeros(number_chunks,1);
        statSTR.FAF_Duration = zeros(number_chunks,1);
        statSTR.MAN_Duration = zeros(number_chunks,1);
        statSTR.MAF_Duration = zeros(number_chunks,1);
        statSTR.CXN_Duration = zeros(number_chunks,1);
        statSTR.CXF_Duration = zeros(number_chunks,1);
        statSTR.CHN_Duration = zeros(number_chunks,1);
        statSTR.CHF_Duration = zeros(number_chunks,1);
        statSTR.ComboN_Duration = zeros(number_chunks,1);
        statSTR.ComboF_Duration = zeros(number_chunks,1);
        
        statSTR.Conversation_Start = zeros(number_chunks,1);
        statSTR.Conversation_End = zeros(number_chunks,1);
        % statSTR.Pause_Start = zeros(number_chunks,1);
        % statSTR.Pause_End = zeros(number_chunks,1);
        
        line2rite = 0;
        for ipair = 1:number_chunks
            convers_segment = whole_text(conversation_start(ipair):conversation_stop(ipair));  % conversation
            [pause_segment, pause_number] = get_following_pause(whole_text(conversation_stop(ipair):end));                   % pause
            if pause_number == 0   % means a pause was not found
                fprintf('Warning - No pause found for Conversation #%d -- Omitting...\n', ipair);
                continue
            end
            [conv_start_time, conv_end_time, pause_start_time, pause_end_time] = get_chunk_times(convers_segment, pause_segment);
            if conv_end_time ~= pause_start_time
                fprintf('Warning - Pause start time not equal to Conversation end time for Conversation #%d -- Omiting...\n', ipair);
                continue
            end
            if check_inclusion(conv_start_time, conv_end_time)
                line2rite = line2rite + 1;
                process_SNR_Power_2_4_3_1(convers_segment, pause_segment, ipair, pause_number, conv_start_time, conv_end_time, pause_start_time, pause_end_time, line2rite)
            end
        end
        
        
        
        
        
        % compute weighted average levels over all conversations/pauses (for the
        % entire day)
        datax = compute_weighted_averages_Power_4_3_1; % function to compute weighted averages for day
        col_x = h2a_col + length(headings2a) - 5;
        rngx = [xlcolumnletter(col_x) int2str(h2_row+1)];
        xlswrite(SNR_output_file, datax, sheet_no, rngx)
        
        rng = [xlcolumnletter(h2a_col) int2str(h2_row+3)];
        xlswrite(SNR_output_file, grand_data_block, sheet_no, rng)
        
        % write the table of number, actual durations, and proportional durations
        % first the numbers
        conv_numb = num2cell([statSTR.Label_Count(:,1); NaN; sum(statSTR.Label_Count(:,1))]);
        xlswrite(SNR_output_file, conv_numb, sheet_no, [xlcolumnletter(h3_col+1) int2str(h3_row+3)])
        pause_numb = num2cell([statSTR.Label_Count(:,2); NaN; sum(statSTR.Label_Count(:,2))]);
        xlswrite(SNR_output_file, pause_numb, sheet_no, [xlcolumnletter(h3_col+5) int2str(h3_row+3)])
        
        % next the actual durations
        dur_conv = statSTR.Label_Duration(:,1);
        dur_conv = round(dur_conv*100)/100;
        conv_dur_total = sum(dur_conv);
        dur_conv = num2cell([dur_conv; NaN; round(conv_dur_total*100)/100]);
        xlswrite(SNR_output_file, dur_conv, sheet_no, [xlcolumnletter(h3_col+2) int2str(h3_row+3)])
        
        dur_pause = statSTR.Label_Duration(:,2);
        dur_pause = round(dur_pause*100)/100;
        pause_dur_total = sum(dur_pause);
        dur_pause = num2cell([dur_pause; NaN; round(pause_dur_total*100)/100]);
        xlswrite(SNR_output_file, dur_pause, sheet_no, [xlcolumnletter(h3_col+6) int2str(h3_row+3)])
        
        % next the duration proportions
        
        conv_proportions = statSTR.Label_Duration(:,1)/conv_dur_total;
        conv_proportions = round(conv_proportions * 100)/100;   % two decimal places
        conv_proportions = num2cell([conv_proportions; NaN; sum(conv_proportions)]);
        xlswrite(SNR_output_file, conv_proportions, sheet_no, [xlcolumnletter(h3_col+3) int2str(h3_row+3)])
        
        pause_proportions = statSTR.Label_Duration(:,2)/pause_dur_total;
        pause_proportions = round(pause_proportions * 100)/100;   % two decimal places
        pause_proportions = num2cell([pause_proportions; NaN; sum(pause_proportions)]);
        xlswrite(SNR_output_file, pause_proportions, sheet_no, [xlcolumnletter(h3_col+7) int2str(h3_row+3)])
%         
        %% NEW CODE FROM ERIKA
        % The data to compile are in datax, specifically the 5, 16, 17, 18 values,
        % these correspond to
        % Noise
        % Speech Comb
        % Speech Near
        % Speech Far
        
        header = {'Noise', 'Speech Comb', 'Speech Near', 'Speech Far', 'Speech Comb Adjusted', };
        index = [5, 16, 17, 18];
        
        for x = 1:length(index)
         
            datacompile{d}(f,x)= datax{index(x)};
        end
        
    end
    
end


% MORE CODE FROM ERIKA, CALCULATE THE CALCULATED VARIABLES, and THEN
% ULTIMATELY SAVE DATA TO A NEW EXCEL FILE.

% datacompile{1} = real(datacompile{1});
% datacompile{2} = real(datacompile{2});

% MORE CODE FROM ERIKA, CALCULATE THE CALCULATED VARIABLES, and THEN
% ULTIMATELY SAVE DATA TO A NEW EXCEL FILE.
day = length (datacompile);

for d=1:day

    datacompile{d} = real(datacompile{d});
    
end


% now calculate the "calculated values
for f = 1:length(ID)
    for d = 1:day
        
        % now compute 'Speech Comb Adjusted');
        datacompile{d}(f,5) =  10.*log10((10.^(datacompile{d}(f,2)./10))-(10.^(datacompile{d}(f,1)./10)));
        
        %compute 'Speech Near Adjusted'
        datacompile{d}(f,6) =  10.*log10((10.^(datacompile{d}(f,3)./10))-(10.^(datacompile{d}(f,1)./10)));
        
        %compute 'Speech Far Adjusted'
        datacompile{d}(f,7) =  10.*log10((10.^(datacompile{d}(f,4)./10))-(10.^(datacompile{d}(f,1)./10)));
        
        
        %compute 'SNR Comb'
        datacompile{d}(f, 8) = datacompile{d}(f,2)-datacompile{d}(f,1);
        
        
        %compute 'SNR Near'
        datacompile{d}(f, 9) = datacompile{d}(f,3)-datacompile{d}(f,1);
        
        %compute 'SNR Far'
        datacompile{d}(f, 10) = datacompile{d}(f,4)-datacompile{d}(f,1);
        
        % compute  'SNR Comb Adjusted'
        datacompile{d}(f, 11) = datacompile{d}(f,5)-datacompile{d}(f,1);
        
        
        % compute SNR Near Adjusted
        
        datacompile{d}(f, 12) = datacompile{d}(f,6)-datacompile{d}(f,1);
        
        % Compute SNR Far Adjusted
        
        datacompile{d}(f, 13) = datacompile{d}(f,7)-datacompile{d}(f,1);
        
    end

end
% datacompile{1} = real(datacompile{1});
% datacompile{2} = real(datacompile{2});

for d=1:day
    datacompile{d}(isnan(datacompile{d})) = 0;
    datacompile{d}(isinf(abs(datacompile{d}))) = 0;
    datacompile{d} = real(datacompile{d});
    
end

% now combine across the two days. 
% start by taking the simple linear average across the two days, and then
% make some corrections to select columns

% datacompile{3} = (datacompile{1}+datacompile{2})./2;
% 
% for f = 1:length(ID)
% datacompile{3}(f,5) = 10.*log10((10.^(datacompile{3}(f,2)/10)-10.^(datacompile{3}(f,1)/10)));
% datacompile{3}(f,8) = datacompile{3}(f,2)-datacompile{3}(f,1);
% datacompile{3}(f,11)= datacompile{3}(f,5)-datacompile{3}(f,1);
% 
% end

%% Mean Calculation %%
datacompile{day+1} = 0;
for d=1:day

    datacompile{day+1} = (datacompile{day+1}+datacompile{d});
    
end

for f = 1:length(ID)
    
    Current_Subject = length(Rec{f});
    datacompile{day+1}(f,:) = datacompile{day+1}(f,:)./Current_Subject;
    clear Current_Subject
end

for f = 1:length(ID)
datacompile{day+1}(f,5) = 10.*log10((10.^(datacompile{day+1}(f,2)/10)-10.^(datacompile{day+1}(f,1)/10)));
datacompile{day+1}(f,8) = datacompile{day+1}(f,2)-datacompile{day+1}(f,1);
datacompile{day+1}(f,11)= datacompile{day+1}(f,5)-datacompile{day+1}(f,1);

end

%% Added 

%% STD Calculation %%
Data_for_STD = [];
datacompile{day+2} = 0;
for f = 1:length(ID)
  Data_for_STD = [];
    Current_Subject = length(Rec{f});
    for D = 1:Current_Subject
        Temp_Data = datacompile{D}(f,:);
        Data_for_STD = cat(1,Data_for_STD,Temp_Data);
    end
       STD_Matrix(f,:) = std(Data_for_STD,[],1);
    clear Current_Subject Data_for_STD
    
end

datacompile{day+2} = STD_Matrix;
dataccompile = cell2mat(datacompile)'; 

% finally time to start writing all data to an excel file

%% Making Headers
headers = {};
for D = 1:day
    
    Template_Header = Header_Maker(D);
    headers = cat(1,headers,Template_Header)
    
end

clear D Template_Header

Temp ={

'Avg_Noise'
'Avg_Speech Comb'
'Avg_Speech Near'
'Avg_Speech Far'
'Avg_Speech Comb Adjusted'
'Avg_Speech Near Adjusted'
'Avg_Speech Far Adjusted'
'Avg_SNR Comb'
'Avg_SNR Near'
'Avg_SNR Far'
'Avg_SNR Comb Adjusted'
'Avg_SNR Near Adjusted'
'Avg_SNR Far Adjusted'

'STD_Noise'
'STD_Speech Comb'
'STD_Speech Near'
'STD_Speech Far'
'STD_Speech Comb Adjusted'
'STD_Speech Near Adjusted'
'STD_Speech Far Adjusted'
'STD_SNR Comb'
'STD_SNR Near'
'STD_SNR Far'
'STD_SNR Comb Adjusted'
'STD_SNR Near Adjusted'
'STD_SNR Far Adjusted'
};
headers = cat(1,headers,Temp)

clear Temp

xlswrite(compileddataoutput,headers,'Compiled_BatchRun','A2')
xlswrite(compileddataoutput,reshape(ID, 1, length(ID)),'Compiled_BatchRun', 'B1')
xlswrite(compileddataoutput, cell2mat(datacompile)', 'Compiled_BatchRun', 'B2')


