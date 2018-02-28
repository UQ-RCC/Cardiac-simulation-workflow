% Created by: Daya Kern
% Date: 13 October, 2017
% This function contains frankensteined parts from scripts belonging to 
% Christopher Villongco (renderDTform.m, Parse_AFNI) and 
% Eric Carruth (Parse_AFNI_v4.m). The purpose of this script is to save out
% files necessary for the fibre-fitting stage of the heart mesh. Output 1
% is to help compute xi coordinates of loaded data points within the volume
% of a 3D FE mesh. Output 2 is to help with fitting 3D DT field
%
% INPUTS:
% 1. data_group+data_sub_group+main_dir - file path to working directory.
% 2. DTAfname - the aligned DT file from running the scanner2model script
% 3. down_sample_value - the down sampling value for the data (ideal is 10)
%
% OUTPUTS:
% 1. cont_DT_coords_mask_aligned - a file containing the rotated coords
% 2. data_DT_grfl_dump_out_mask_coords.txt - a file containing the rotated
%    coords, as well as the 6 unique log tensor components.

function calc_data_coords(working_dir, DTA_fname, down_sample_value)

    % Working directory
    working_directory = working_dir;
    % Input file
    file = [working_directory DTA_fname];
    
    %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
    % ####################################################################### %
    % ########## USER PARAMETERS ############################################ %
    
    %% Set output files
    % File to contain just the coords for calcXis.py script 
    outputCalcXisFile = [working_directory 'cont_DT_coords_mask_aligned.txt']; 
   
    % File to contain the coords and modified DT_rls for the FieldFit3D.py script
    outputFileAlignedTitle = sprintf('data_DT_grfl_dump_out_mask_coords%i.txt', down_sample_value);
    outputFileAligned = [working_directory outputFileAlignedTitle] 
    
    % ####################################################################### %
    %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%    
  
    %% BUILD COORDINATES (Masked)

    % Load the aligned DT mat file
    fprintf('Loading file... ');
    tic;   
        alignedMatFile = matfile(file); 
        fprintf('Done.\n');
    toc;

    %% Extract only the rotated x,y,z coordinates & tensors from aligned 
    %%  DT mat file
    DT_rl = alignedMatFile.DT_rl; % Gets the rotated log diffusion tensors
    coords_r = alignedMatFile.coords_r; % Gets the rotated coords
    
    size(coords_r)
    size(DT_rl)

    %% Downsample Data
    ds = down_sample_value; % 20 for my computer

    % Downsample the coordinate data
    fprintf('Downsampling file by %i... ', ds);
    tic;  
        % downsample the coordinate data
        ds_coords_r(:,1) = downsample(coords_r(:,1), ds);
        ds_coords_r(:,2) = downsample(coords_r(:,2), ds);
        ds_coords_r(:,3) = downsample(coords_r(:,3), ds);

        % downsample the tensor data
        % only need 6 unique components:
        % dxx:(1,1),dyy:(2,2),dzz:(3,3),dxy:(1,2),dxz:(1,3),dyz:(2,3).
        ds_DT_rl(1,1,:) = downsample(DT_rl(1,1,:), ds);
        ds_DT_rl(2,2,:) = downsample(DT_rl(2,2,:), ds);
        ds_DT_rl(3,3,:) = downsample(DT_rl(3,3,:), ds);
        ds_DT_rl(1,2,:) = downsample(DT_rl(1,2,:), ds);
        ds_DT_rl(1,3,:) = downsample(DT_rl(1,3,:), ds);
        ds_DT_rl(2,3,:) = downsample(DT_rl(2,3,:), ds);
 
        fprintf('Done.\n');
    toc;

    %% Plot masked data
%     x = ds_coords_r(:,1); y = ds_coords_r(:,2); z = ds_coords_r(:,3);
% 
%     % Determine number of voxels
%     fprintf('Total masked data points:\n%d\n',size(ds_coords_r,1));
% 
%     % Plot 1/10th of all included voxel locations from DT data set
%     fprintf('Plotting voxel coordinates...\n');
%     figure;
%     plot3(x(1:10:end),y(1:10:end),z(1:10:end),'bo','Markersize',5, ...
%         'MarkerFaceColor',[0 0 0.3]);
%     hold on;
%     xlabel('x'); ylabel('y'); zlabel('z');
%     axis equal;
%     grid on;

    %% Save downsampled data in the right format  

    %This section of calc_data_coords writes out the coordinates of the 
    %   data from a pre-configured cont_DT_coords_mask file (It has been
    %   re-aligned to suit the continuity mesh).
    sprintf('Saving file in this location: %s', working_directory);
    
    % generate columns of 1's (for coord weights)
    weights = ones(length(ds_coords_r),1);
    
    % generate column of 0's (for label)
    label = zeros(length(ds_coords_r),1);
    
    % generate column of numbers (for data)
    data = (1:length(ds_coords_r))';
        
    %% Saving out calcxi's coord data file
    % assemble data form
    outputDataForm = [ds_coords_r(:,1) weights ds_coords_r(:,2) weights ...
                  ds_coords_r(:,3) weights label data];
    
    % open/create output file
    fid = fopen(outputCalcXisFile,'wt');
    % write headers
    fprintf(fid,'coord1_val\tcoord1_weight\tcoord2_val\tcoord2_weight\tcoord3_val\tcoord3_weight\tLabel\tData\n');
    
    % append data form
    dlmwrite(outputCalcXisFile, outputDataForm, '-append', 'delimiter', '\t');
    % close file
    fclose(fid);
    
    %% Saving out field-fit's coord data file
    % assemble data form
    % dxx:(1,1),dyy:(2,2),dzz:(3,3),dxy:(1,2),dxz:(1,3),dyz:(2,3).
    outputDataFormAligned = [ds_coords_r(:,1) weights ds_coords_r(:,2) weights ...
                  ds_coords_r(:,3) weights squeeze(ds_DT_rl(1,1,:)) ...
                  squeeze(ds_DT_rl(2,2,:)) squeeze(ds_DT_rl(3,3,:)) ...
                  squeeze(ds_DT_rl(1,2,:)) squeeze(ds_DT_rl(1,3,:))...
                  squeeze(ds_DT_rl(2,3,:)) data];
    
    % open/create output file
    fid = fopen(outputFileAligned,'wt');
    % write headers
    fprintf(fid,'coord1_val\tcoord1_weight\tcoord2_val\tcoord2_weight\tcoord3_val\tcoord3_weight\tdxx_val\tdyy_val\tdzz_val\tdxy_val\tdxz_val\tdyz_val\tData\n');
    % append data form
    dlmwrite(outputFileAligned, outputDataFormAligned, '-append', 'delimiter', '\t');
    % close file
    fclose(fid);
    fprintf('Done with saving out files for FieldFit and CalcXis');
end
