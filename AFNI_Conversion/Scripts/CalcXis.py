# Name: Christopher Villongco
# Date: September 5, 2012
# Date: February 18, 2016
# Updated by Eric Carruth
# Date: March 21, 2017
# This script will compute xi coordinates of loaded data points within the volume of a 3D FE mesh
import sys
import pdb

# USER INPUT=============================================================================
mDir = sys.argv[5] # if set up like this: ./continuity --full --no-threads --batch $script $mDir $modelFile
outDir = mDir + 'ContinuityFiles/'

# directory where .cont6 model is located
#mdir = '/Users/dayakern/Desktop/continuity/pcty/examples/_dayatest/eric_files/'
mdir = mDir

# directory where data file is located
datadir = outDir #mdir

# base continuity model
modelFile = sys.argv[6]

# /Users/dayakern/Desktop/4801_Testing/AFNI_Conversion/ucsd_mri_2/14-3_tac
# Continuity data form
data_file = 'cont_DT_coords_mask_aligned.txt'

case = 'DT_maskcoords'

output = datadir + 'XiTable_' + modelFile + '_' + case + '.txt'

# xi calculation subdivisions
subdiv = '10'

# list of elements to calculate xis in
ellist = 'all'

# USER INPUT=============================================================================
# for this one mdir -> datadir
print 'Loading model %s'%(datadir + modelFile + '.cont6')
self.Load_File(datadir + modelFile + '.cont6', log=0)

# for this one datadir -> mDir
self.LoadContModule(('fitting',));
print 'Loading fitting data file %s'%(mDir+data_file)
self.LoadFittingData(mDir + data_file, log=0)

self.auto_update_dimensions()
self.Send(None, log=0)

self.CalcMeshFast([('Calculate', None), ('Do not Calculate', None), ('Calculate', None), ('Angle change scale factors (for nodal derivs wrt angle change)', None)], log=1)

# 3D volume fit to output Xi coordinates of data file
self.FitData({'preapplyConstraints':0,'calcErrorStr':'error = (data-x)*weight\n','geomDataIsCart':1,'err':'1.00e-006','selections':{'Coordinate 2': 'coord2', 'Coordinate 3': 'coord3', 'Coordinate 1': 'coord1'},'initializeFields':0,'iterationLimit':'10','fit_selections':(),'xi_options':{'dpError': '50.0', 'errorType': 'sd', 'datalist': 'all', 'sdError': '50.0', 'optimizeVars': 1, 'filterData': True, 'calcType': 'in 3D volume', 'showTable': True, 'subdivisions': subdiv, 'itmax': '50', 'vmax': '1.5', 'elemlist': ellist, 'ignorePoints': 1, 'tolerance': '1e-006', 'dpErrorType': 'sd', 'newtonUpdate': 1, 'outputPath':output},'output_type':'Update nodal variable'}, log=0)

##################################################################################
# ERROR HERE IN BATCH MODE, MIGHT NOT NEED THIS
# Output element Xi coordinates
#self.ListElementPoints({'opfile':0,'degree':0,'deformed':0,'viewAsTable':0,'rgrid':0,'gauss':1,'xilist':[[0.0], [0.0], [0.0]],'nxipt':[1, 1, 1],'grid':0,'nelist':[0],'fname':'elem_xis.txt','ppoint':0,'output':'LISTING','global_':0,'type':'CUBE','infile':'NoInputFile','rect':0,'rfile':0}, log=0)


# 3D volume fit with labels
#~ self.FitData({'preapplyConstraints':0,'calcErrorStr':'error = (data-x)*weight\n','geomDataIsCart':1,'err':'1.00e-006','selections':{'Coordinate 2': 'coord_2', 'Coordinate 3': 'coord_3', 'Coordinate 1': 'coord_1'},'initializeFields':0,'iterationLimit':'10','fit_selections':(),'xi_options':{'dpError': '50.0', 'errorType': 'sd', 'datalist': 'LV;default;ST', 'sdError': '50.0', 'optimizeVars': 1, 'filterData': True, 'calcType': 'in 3D volume', 'showTable': True, 'subdivisions': subdiv, 'itmax': '50', 'vmax': '1.5', 'elemlist': 'LV;default;ST', 'ignorePoints': 1, 'tolerance': '1e-006', 'dpErrorType': 'sd', 'newtonUpdate': 1, 'outputPath':output},'output_type':'Update nodal variable'}, log=0)

print "That's all, folks!"
