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

r = 1; % Rat number

ratfls = {'5-3_tac'; '5-4_sham'; '6-1_tac'; '6-4_sham'};
dwfl = sprintf('%s.nii',ratfls{r});
b0mgfl = 'image_b0_mag.nii';
dwmgfl = 'image_dw_mag.nii';
b0avgfl = 'image_b0_mag_avg';
dwavgfl = 'image_dw_mag_avg';
mskfl = 'msk';
gradfl = '/Users/ecarruth/Documents/Research/MRI/Gradient_Direction_Files/Oxford-30directions.1D';
dtfl = 'DT_gradfile_msk';
imfl = 'image_b0_dw';
b0ims = [0 1 2 3];

%% Make it clear what should be pasted into Unix terminal
fprintf('### Copy and paste each line below one at a time into a Unix terminal:\n\n');

%% Create a b0 averaged image
fprintf('3dMean -prefix %s %s[%d] %s[%d] %s[%d] %s[%d]\n\n',b0avgfl, ...
    b0mgfl,b0ims(1),b0mgfl,b0ims(2),b0mgfl,b0ims(3),b0mgfl,b0ims(4));

%% Create an averaged image over all gradient directions (for creating the mask)
% % Using 3dTstat:
% fprintf('3dTstat -mean -prefix %s %s\n\n',dwavgfl,dwmgfl);
% % Using 3dTstat *should* work, but it generates data that is flipped 180
% % degrees around the z-axis when imported into Seg3D! Instead, use 3dMean
% % and list out all dw images...
% % Unfortunately, 3dMean does this too!!! (Not sure why or how to fix it)
% Using 3dMean:
cmd = sprintf('3dMean -prefix %s',dwavgfl);
for m = 1:30
    pcmd = sprintf(' %s[%d]',dwmgfl,m-1);
    cmd = [cmd pcmd];
end

cmd = [cmd '\n\n'];

fprintf(cmd);

% NOTE:
% So, what I ended up doing was keeping the 3dMean command. When imported
% into Seg3D, the image_b0_mag.nii file is oriented the same way as later
% versions (13-*, 14-*, 16-*, and 24-*), with the positive x-axis going
% from base to apex. Similarly, the image_b0_dw, image_dw_mag, and 
% DT_gradfile_msk images are oriented in this way, so the DT data are 
% oriented that way (I presume). Conversely, image_dw_mag_avg.nii,
% image_b0_mag_avg.nii, image_dw_mag_avg.nii, and of course the masks
% created from those images, are flipped 180 degrees around the z-axis.
% So my plan is to segment the flipped images, then if they are imported
% flipped into Blender, flip them back there and carry on.
% EDC 5/12/2017

%% Create a mask
fprintf('### At this point, you should open the image %s, and determine a good threshold value for the mask.\n',dwavgfl);
fprintf('### To do this, copy and paste\n\n');
fprintf('afni %s+orig\n\n',dwavgfl);
fprintf(['### in the terminal window. In AFNI, open the "Define OverLay" window. \n### ' ...
    'Then click on different parts of the image(s) to see the value to the right of "ULay = ".\n']);
fprintf('### Finally, run the following command, inserting the value you choose in place of the *.\n');
fprintf('### \t(For 16-* scans, a threshold value of ~6000 was pretty good.)\n\n');

fprintf('3dcalc -a %s+orig -expr ''ispositive(a-*)'' -prefix %s\n\n',dwavgfl,mskfl);

%% Copy mask to a .nii file for Seg3D
fprintf('3dcopy msk+orig. msk.nii\n\n');

%% Create a combined image data set of the averaged b0 image followed by all gradient directions
fprintf('3dTcat -prefix %s %s+orig %s\n\n',imfl,b0avgfl,dwmgfl);

%% Copy averaged DW file to .nii for Seg3D
fprintf('3dcopy image_dw_mag_avg+orig. image_dw_mag_avg.nii\n\n');

%% Run the final command to generate DTs
fprintf('3dDWItoDT -mask %s+orig -prefix %s -eigs %s %s+orig\n\n', ...
    mskfl,dtfl,gradfl,imfl);

fprintf('### That''s it!\n\n');

% End of script