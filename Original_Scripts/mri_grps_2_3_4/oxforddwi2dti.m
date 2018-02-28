% oxforddwi2dti.m

% This script generates commands to convert diffusion weighted images
% acquired at Oxford University by Irvin Teh and Jurgen Schneider to
% diffusion tensor data in AFNI. To do this, run the script, then copy and 
% paste each string printed in the Command Window into a Unix terminal.
% Make sure each command finishes before running the next one.

% There are six total commands:
% 1. Average the b0 images (4) into one b0 image
% 2. Average the DW images (15*4 = 60) into one high SNR image for creating
%    a mask
% 3. Look at the averaged DW image to choose a threshold for the mask
% 4. Create the mask with the chosen threshold
% 5. Compile the averaged b0 image and DW images into one dataset
% 6. Calculate the diffusion tensors from the DW images, the mask, and the
%    gradient direction file
    
% Written by: Eric Carruth
% Created: 7/7/2016
% Last modified: 7/7/2016

%% Clean slate
clearvars; close all; clc;

%% Define things

r = 3; % Rat number

ratfls = {'24-2_tac'; '24-3_tac'; '24-5_sham'; '24-6_sham'};
dwfl = sprintf('%s.nii',ratfls{r});
b0mgfl = 'image_b0_mag_avg';
dwavgfl = 'image_dw_mag_avg';
mskfl = 'msk';
gradfl = '/Users/ecarruth/Documents/Research/MRI/Gradient_Direction_Files/Oxford-60directions_v4.1D';
dtfl = 'DT_gradfile_msk';
imfl = 'image_b0_dw';
b0ims = [0 16 32 48];

%% Make it clear what should be pasted into Unix terminal
fprintf('### Copy and paste each line below one at a time into a Unix terminal:\n\n');

%% Create a b0 averaged image
fprintf('3dMean -prefix %s %s[%d] %s[%d] %s[%d] %s[%d]\n\n', ...
    b0mgfl,dwfl,b0ims(1),dwfl,b0ims(2),dwfl,b0ims(3),dwfl,b0ims(4));

%% Create an averaged image over all gradient directions (for creating the mask)
fprintf('3dMean -prefix %s %s[%d-%d] %s[%d-%d] %s[%d-%d] %s[%d-%d]\n\n', ...
    dwavgfl,dwfl,b0ims(1)+1,b0ims(2)-1,dwfl,b0ims(2)+1, ...
    b0ims(3)-1,dwfl,b0ims(3)+1,b0ims(4)-1,dwfl,b0ims(4)+1,63);

%% Create a mask
fprintf('### At this point, you should open the image %s, and determine a good threshold value for the mask.\n',dwavgfl);
fprintf('### To do this, copy and paste\n\n');
fprintf('afni %s+orig\n\n',dwavgfl);
fprintf(['### in the terminal window. In AFNI, open the "Define OverLay" window. \n### ' ...
    'Then click on different parts of the image(s) to see the value to the right of "ULay = ".\n']);
fprintf('### Finally, run the following command, inserting the value you choose in place of the *.\n');
fprintf('### \t(For 16-* scans, a threshold value of ~6000 was pretty good.)\n\n');

fprintf('3dcalc -a %s+orig -expr ''ispositive(a-*)'' -prefix %s\n\n',dwavgfl,mskfl);

%% Create a combined image data set of the averaged b0 image followed by all gradient directions
fprintf('3dTcat -prefix %s %s+orig %s[%d-%d] %s[%d-%d] %s[%d-%d] %s[%d-%d]\n\n', ...
    imfl,b0mgfl,dwfl,b0ims(1)+1,b0ims(2)-1,dwfl,b0ims(2)+1, ...
    b0ims(3)-1,dwfl,b0ims(3)+1,b0ims(4)-1,dwfl,b0ims(4)+1,63);


%% Run the final command to generate DTs
fprintf('3dDWItoDT -mask %s+orig -prefix %s -eigs %s %s+orig\n\n', ...
    mskfl,dtfl,gradfl,imfl);

fprintf('### That''s it!\n\n');

% End of script