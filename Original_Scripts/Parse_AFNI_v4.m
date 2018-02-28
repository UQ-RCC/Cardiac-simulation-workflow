% Written by: Christopher Villongco
% Date: April 30, 2012
% -------------------------------------------------------------------------
% This script will take AFNI output (imported to Matlab and saved as a .txt
% file) and render the diffusion data. The AFNI output can be pre-filtered
% in Excel or elsewhere if needed. The AFNI output is generated by running
% the 3dmaskdump function, like so:
% 3dmaskdump -index -noijk -xyz -o DT_grfl_msk_dump.txt DT_gradfile_msk+orig.
% There are now four output files to this script. Each contains the full
% diffusion tensor (DT), the unique tensor components (D), the coordinates
% (coords), eigenvectors (vs), and eigenvalues (es) for the following four
% cases:
% 1. The full volume
% 2. All masked data points (where MD~=0)
% 3. Half of the data % (might remove this one)
% 4. The (masked) central slice
% Each of these data sets can be rotated as needed using the function
% rotate_DT_data
% -------------------------------------------------------------------------
% Modified by: Eric Carruth
% Last Edited: March 16, 2017

%% Set up, then load the data

clearvars; close all; clc;

% Options for user parameters
rtns = {'5-3_tac' '5-4_sham' '6-1_tac' '6-4_sham'; ...
    '13-1_sham' '13-2_tac' '14-3_tac' '14-6_sham'; ...
    '16-1_sham' '16-3_tac' '16-4_sham' '16-5_tac'; ...
    '24-2_tac' '24-3_tac' '24-5_sham' '24-6_sham'};

%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% ####################################################################### %
% ########## USER PARAMETERS - edit for each scan as necessary ########## %

% Group #
grp = 4; % 1, 2, 3, or 4
% Rat #
rtn = rtns{grp,4}; % Second value should be 1, 2, 3, or 4

% Choose scan directory and dump file to use
maindir = sprintf('/Volumes/Data/ecarruth/MRI/Oxford_DTI/%d/',grp);
scandir = sprintf('%s/',rtn);
file = 'DT_grfl_msk_dump.txt'; % should be same for all Oxford_DTI data

% ####################################################################### %
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

% Set up image sizes for the 2 cases (group 1 had different size than
% others)
% Group 1
sx1 = 192;
sy1 = 192;
sz1 = 192;
% Group 2
sx2 = 216;
sy2 = 144;
sz2 = 144;

% Size of image in voxels
if grp == 1
    size_x = sx1;
    size_y = sy1;
    size_z = sz1;
else
    size_x = sx2;
    size_y = sy2;
    size_z = sz2;
end

% Useful parameters
ld = size_x*size_y*size_z;  % Number of voxels (rows in d)
wd = 24;                    % Number of columns in d, as described below

% Set path
path = [maindir scandir];
cd(path)

% Load the file
fprintf('Loading file... ');
tic;
opwd = pwd;
cd(path)
fid = fopen(file);
d = textscan(fid,'%n',ld*wd);
d = reshape(d{1},wd,ld)';
cd(opwd)
fprintf('Done.\n');
toc;

% Mask out data with MD == 0 and FA == 1;
ind_nzs = d(:,24)~=0 & d(:,23)~=1;

% 3dmaskdump exports coordinates in the RAI reference frame, I think.
% Converting to LPI appears to result in the correct dimensions and
% ordering of the tensors.
d(:,2) = -d(:,2); % Switch (R) to (L) [mm]
d(:,3) = -d(:,3); % Switch (A) to (P) [mm]
% d(:,4) = -d(:,4); % Switch (I) to (S) [mm]

% Get image resolution from first voxel's (x,y,z) coordinates
dx = d(1,2); % [mm]
dy = d(1,3); % [mm]
dz = d(1,4); % [mm]

% Mask data
d_nz = d(ind_nzs,:);
ldnz = length(d_nz);
pvxnz = ldnz/ld*100;
fprintf('Mask included ~%.f%% of voxels.\n',pvxnz);

fprintf('Processing file %s...\n', [path file]);

% Columns in .mat file (variable d)
%   1   2   3   4   5   6   7   8   9   10  11      12      13      14
%   n	x	y	z	Dxx	Dxy	Dyy	Dxz	Dyz	Dzz	lambda1	lambda2	lambda3	evec1x
%   15      16      17      18      19      20      21      22      23  24
%   evec1y	evec1z	evec2x	evec2y	evec2z	evec3x	evec3y	evec3z	FA	MD

% (AFNI uses lambda1 > lambda2 > lambda3)
% (Continuity uses lambda1 < lambda2 < lambda3)

%% BUILD COORDINATES AND DIFFUSION TENSORS (Full)

% Initialize variables
    D = zeros(size(d,1),6);
    DT = zeros(3,3,size(d,1));
    coords = zeros(size(d,1),3);
    es = zeros(size(d,1),3);
    vs = zeros(3,3,size(d,1));

% --- Assemble unique diffusion tensor components D and full tensor DT ----
    D(:,1) = d(:,5); D(:,2) = d(:,7); D(:,3) = d(:,10); 
    D(:,4) = d(:,6); D(:,5) = d(:,8); D(:,6) = d(:,9);
    DT(1,1,:) = d(:,5); DT(1,2,:) = d(:,6); DT(1,3,:) = d(:,8); 
    DT(2,1,:) = d(:,6); DT(2,2,:) = d(:,7); DT(2,3,:) = d(:,9);
    DT(3,1,:) = d(:,8); DT(3,2,:) = d(:,9); DT(3,3,:) = d(:,10);
     
% ------------------------- Assemble coordinates --------------------------
    coords(:,1) = d(:,2); % [mm]
    coords(:,2) = d(:,3); % [mm]
    coords(:,3) = d(:,4); % [mm]

% ------------------------- Assemble eigenvalues --------------------------
% The convention used is es(:,3) = primary eigenvalue - Continuity style
    es(:,1) = d(:,13); es(:,2) = d(:,12); es(:,3) = d(:,11);

% ------------------------- Assemble eigenvectors -------------------------
% The convention here is as follows:
% vs(1,3,:) is the x-component of the primary eigenvector
% vs(2,1,:) is the y-component of the tertiary eigenvector
    vs(1,3,:) = d(:,14); vs(2,3,:) = d(:,15); vs(3,3,:) = d(:,16);
    vs(1,2,:) = d(:,17); vs(2,2,:) = d(:,18); vs(3,2,:) = d(:,19);
    vs(1,1,:) = d(:,20); vs(2,1,:) = d(:,21); vs(3,1,:) = d(:,22);

% Save full data set
ofile = file(1:end-4);
save([ofile '_out_full.mat'],'D','DT','coords','es','vs');

%% BUILD COORDINATES AND DIFFUSION TENSORS (Masked)

% Initialize variables
    D = zeros(size(d_nz,1),6);
    DT = zeros(3,3,size(d_nz,1));
    coords = zeros(size(d_nz,1),3);
    es = zeros(size(d_nz,1),3);
    vs = zeros(3,3,size(d_nz,1));

% --- Assemble unique diffusion tensor components D and full tensor DT ----
    D(:,1) = d_nz(:,5); D(:,2) = d_nz(:,7); D(:,3) = d_nz(:,10); 
    D(:,4) = d_nz(:,6); D(:,5) = d_nz(:,8); D(:,6) = d_nz(:,9);
    DT(1,1,:) = d_nz(:,5); DT(1,2,:) = d_nz(:,6); DT(1,3,:) = d_nz(:,8); 
    DT(2,1,:) = d_nz(:,6); DT(2,2,:) = d_nz(:,7); DT(2,3,:) = d_nz(:,9);
    DT(3,1,:) = d_nz(:,8); DT(3,2,:) = d_nz(:,9); DT(3,3,:) = d_nz(:,10);
     
% ------------------------- Assemble coordinates --------------------------
    coords(:,1) = d_nz(:,2);
    coords(:,2) = d_nz(:,3);
    coords(:,3) = d_nz(:,4);
    x = coords(:,1); y = coords(:,2); z = coords(:,3);

% ------------------------- Assemble eigenvalues --------------------------
% The convention used is es(:,3) = primary eigenvalue - Continuity style
    es(:,1) = d_nz(:,13); es(:,2) = d_nz(:,12); es(:,3) = d_nz(:,11);

% ------------------------- Assemble eigenvectors -------------------------
% The convention here is as follows:
% vs(1,3,:) is the x-component of the primary eigenvector
% vs(2,1,:) is the y-component of the third (smallest) eigenvector
    vs(1,3,:) = d_nz(:,14); vs(2,3,:) = d_nz(:,15); vs(3,3,:) = d_nz(:,16);
    vs(1,2,:) = d_nz(:,17); vs(2,2,:) = d_nz(:,18); vs(3,2,:) = d_nz(:,19);
    vs(1,1,:) = d_nz(:,20); vs(2,1,:) = d_nz(:,21); vs(3,1,:) = d_nz(:,22);

% Save masked data set
savefile = [ofile '_out_mask.mat'];
save(savefile, 'D', 'DT', 'coords', 'es', 'vs','d_nz');
    
    
%% Plot masked data

% Determine number of voxels
fprintf('Total masked data points:\n%d\n',ldnz);

% Plot 1/10th of all included voxel locations from DT data set
fprintf('Plotting voxel coordinates...\n');
figure;
plot3(x(1:10:end),y(1:10:end),z(1:10:end),'bo','Markersize',5, ...
'MarkerFaceColor',[0 0 0.3]);
hold on;
xlabel('x'); ylabel('y'); zlabel('z');
axis equal;
grid on;

%% Half
% % Save half of data set to get nice cutaway view of all DTs
% ind_half = find(d_nz(:,4)>round(size_z/2) & boolean(mod(d_nz(:,4),2)) ...
%     & boolean(mod(d_nz(:,2),2)) & boolean(mod(d_nz(:,3),2)));
% D_half = D(ind_half,:);
% DT_half = DT(:,:,ind_half);
% coords_half = coords(ind_half,:);
% es_half = es(ind_half,:);
% vs_half = vs(:,:,ind_half);
% savefile = [ofile '_outmask_half.mat'];
% save(savefile,'D_half','DT_half','coords_half','es_half','vs_half');

%% Slice
% Select slice
mes = sprintf('Rendering center slice...');
disp(mes);
x_r = round(d_nz(:,2),4);
slice = size_x/2.*dx;
ind_slice = find(x_r>=slice-dx/2 & x_r<=slice+dx/2); % Oxford ax
mes = sprintf('Number of points in slice %d:\n%d',slice,length(ind_slice));
disp(mes);

% Assemble slice data
D = D(ind_slice,:);
DT = DT(:,:,ind_slice);
coords = coords(ind_slice,:);
es = es(ind_slice,:);
vs = vs(:,:,ind_slice);

% Plot voxel locations of selected slice
plot3(x(ind_slice),y(ind_slice),z(ind_slice),'go','Markersize',5, ...
    'MarkerFaceColor',[0 0.3 0]);

% Plot all data points from DT data set for selected slice
figure;
plotDTI_ne(es(1:4:end,:),vs(:,:,1:4:end),coords(1:4:end,1), ...
    coords(1:4:end,2),coords(1:4:end,3),0.1,1.2);
% plotDTI_ne(es,vs,coords(:,1),coords(:,2),coords(:,3),0.07,1.2);
xlabel('x');
ylabel('y');
zlabel('z');
axis equal;
grid on;
colorbar;

% Save data
savefile = [ofile '_outmask_slice.mat'];
save(savefile,'D','DT','coords','es','vs');

% Create a file for rendering the DTs in Continuity
renderDTform('cont_DTs_slice.txt',coords,es,vs);

% End of script