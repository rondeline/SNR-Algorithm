function [chunk_number, chunk_start_time, chunk_end_time, included] = get_chunk_stats(chunk)
% function [chunk_number, chunk_start_time, chunk_end_time, included] = get_chunk_stats(chunk)
% function to extract the ordinal number of the chunk (conversation or
% pause), and its start and end times

k = findstr(chunk, '"');

chunk_number = str2double(chunk(k(1)+1:k(2)-1));   % value should be between the first two quote marks

% get the first and last speaker utterances
i1 = findstr(chunk, 'spkr=');
i2 = findstr(chunk, '/>');
chunk_start_time = process_line2(chunk(i1(1):i2(1)));
[~, chunk_end_time] = process_line2(chunk(i1(end):i2(end)));

included = check_inclusion(chunk_start_time, chunk_end_time); 





