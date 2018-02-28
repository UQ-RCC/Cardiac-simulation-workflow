#Name: Christopher Villongco
#Date: April 4, 2013
#      August 23, 2011
#      February 18, 2016
#      August 3, 2016
#Script for fitting 3D DT field
#Last modified by Daya (commenting out rendering code lines to run code in batch mode) 7th Oct 2017

import numpy
from time import localtime, strftime
import shutil
import time
import pdb

import sys

# [5] if set up like this: ./continuity --full --no-threads --batch $script $mDir $modelName
fDir = sys.argv[5]
mDir = fDir + 'ContinuityFiles/'
modelName = sys.argv[6]

#########################################################################
############################## USER INPUT ###############################
######################################################################### 

##################### Specify paths and filesnames ######################

########### Fitting working directory containting .cont6 prefit file
md = mDir

########### Continuity model filename
model = modelName + '_mat'
########### Saved Continuity model filename
output = 'EDC_fitted_trilinear_DTfit'

########### Use precalculated Xi table?
xit = 1
########### Precalculated xi table directory
xidir = md
########### Precalculated xi table
xifile = 'XiTable_' + modelName + '_DT_maskcoords.txt' # in ContinuityFiles

xipath = xidir + xifile
modname = xidir + model + '.cont6'

########### Fitting data filename
data_file = 'data_DT_grfl_dump_out_mask_coords20.txt' # down-sampled high-res DT data

################ Specify basis functions for fitted fields ################ 
# Set 'basis' to 'linear' for tri-linear or 'cubic' for tri-Cubic basis functions
# Changes 
#basis = 'cubic'
basis = 'linear'

# list order of linear basis functions (indexed from 1; check Mesh->Basis)
# list order of cubic basis functions in (indexed from 1; check Mesh->Basis)
# Model
nb_linear = 3 # LV_32
nb_Hermite = 1 # LV_32

# List of fields to apply the basis change to (0-2, coordinates; 3-5, angles; 6-8, Fields 1-3; 9-11, Fields 4-6; etc)
fields = [0,1,2, 3,4,5, 6,7,8, 9,10,11, 12,13,14, 15,16,17]

############################ Set Fitting Weights ############################
# list of weights to use for each iteration
# same weights are applied to all terms of penalty function

weights = [100.0, 50.0, 10.0]

# number of fit iterations
its = len(weights)

# Select nodal fields to apply weights to
# fiber fit
selWeight = ['n','n','n','y','y','y','y','y','y','y','y','y','n','n','n','n','n','n']
#             0   1   2   3   4   5   6   7   8   9   10  11  12  13  14  15  16  17

########################## Other Options ########################## 
# Initialize parameters with field(s) mean(s)?
initializeField = 0

# subdivisions if calculating Xis
subdivs = '5'

#########################################################################
########################## FUNCTION DEFINITIONS #########################
#########################################################################

def setFieldBasis(self,derivs,fields,nb):
    nodes = self.stored_data.nodes.obj
    nbs = nodes.getGeomBasisValues()
    for j in fields:
        nbs[j] = nb
    nodes.setGeomBasisValues(nbs)
    eds = nodes.getEnabledDerivs()
    for j in derivs:
        eds[j] = derivs
    nodes.setEnabledDerivs(eds)
    self.stored_data.store(nodes)
    
#########################################################################
########################## DOOOOOOOOOOOOOOOOOOO #########################
#########################################################################
print "\n\nBegin fit (%s)"%(strftime("%a, %d %b %Y %H:%M:%S", localtime()))
t_start = time.clock()

print '\nOpening model', md + model + '.cont6'
self.Load_File(modname, log=0)

# Change basis functions to linear and initialize fields
self.stored_data.nodes.obj.setGeomBasisValues([3,3,3, 3,3,3, 3,3,3, 3,3,3, 0,0,0, 0,0,0])
cdvs = [1,0,0,0,0,0,0,0]
zdvs = [0,0,0,0,0,0,0,0]
self.stored_data.nodes.obj.setEnabledDerivs([cdvs, cdvs, cdvs, cdvs, cdvs, cdvs, cdvs, cdvs, cdvs, cdvs, cdvs, cdvs, zdvs, zdvs, zdvs, zdvs, zdvs, zdvs])
self.Send(None, log=0)
self.CalcMeshFast([('Calculate', None), ('Do not Calculate', None), ('Calculate', None), ('Angle change scale factors (for nodal derivs wrt angle change)', None)], log=0)

## Commenting out the redraw parts for running this script in batch mode
#self.Relem([0, 0, 3, 3, 0.0, [0]], log=0)
#self.om.rolist[-1].setColor([0,0.5,0.5,1])                      # Make refined Cartesian mesh teal
#self.om.renderer.viewer.Redraw()

# Save linear file
self.Save(md + 'testlinear' + '.cont6', log=0)

print 'Select xi table?\n', xit

self.LoadContModule(('fitting',), log=0)

# if basis == 'linear':
#     derivs = [1, 0, 0, 0, 0, 0, 0, 0]
#     setFieldBasis(self,derivs,fields,nb_linear)
# if basis == 'cubic':
#     derivs = [1, 1, 1, 1, 1, 1, 1, 1]
#     setFieldBasis(self,derivs,fields,nb_Hermite)

self.auto_update_dimensions()
self.Send(None, log=0)
self.CalcMeshFast([('Calculate', None), ('Do not Calculate', None), ('Calculate', None), ('Angle change scale factors (for nodal derivs wrt angle change)', None)], log=0)
# Render mesh
#self.Relem([0, 0, 3, 3, 0.0, [0]], log=0)

# pdb.set_trace()

# Load data file
print 'Loading fitting data file %s'%(fDir+data_file)
self.LoadFittingData(fDir + data_file, log=0)

# pdb.set_trace()

print "\n\nDoing %s iterations"%its
print "for weights: ",weights
for j in range(its):
    time_loopstart = time.clock()
    print "\n\n"
    print "##########################################"
    print "######## Fit iteration %s of %s! #########"%(j+1, its)
    print "##########################################"
    print "\n\n"

    weight = weights[j]
    print "Current smoothing weight ", weight
    
    # if j == 0:
    #     initializeField = 1
    # else:
    #     initializeField = 0
    initializeField = 0

# homogenous weights
    self.EWeights({'info':'gui_fit',\
	0 :{'smoothing': selWeight[0],  'smoothing_values': {'default': [[0, 0, 0, 0, 0, 0, 0, 0, 0], [weight, weight, weight, weight, weight, weight, weight, weight, weight]]}},\
	1 :{'smoothing': selWeight[1],  'smoothing_values': {'default': [[0, 0, 0, 0, 0, 0, 0, 0, 0], [weight, weight, weight, weight, weight, weight, weight, weight, weight]]}},\
	2 :{'smoothing': selWeight[2],  'smoothing_values': {'default': [[0, 0, 0, 0, 0, 0, 0, 0, 0], [weight, weight, weight, weight, weight, weight, weight, weight, weight]]}},\
	3 :{'smoothing': selWeight[3],  'smoothing_values': {'default': [[0, 0, 0, 0, 0, 0, 0, 0, 0], [weight, weight, weight, weight, weight, weight, weight, weight, weight]]}},\
	4 :{'smoothing': selWeight[4],  'smoothing_values': {'default': [[0, 0, 0, 0, 0, 0, 0, 0, 0], [weight, weight, weight, weight, weight, weight, weight, weight, weight]]}},\
	5 :{'smoothing': selWeight[5],  'smoothing_values': {'default': [[0, 0, 0, 0, 0, 0, 0, 0, 0], [weight, weight, weight, weight, weight, weight, weight, weight, weight]]}},\
	6 :{'smoothing': selWeight[6],  'smoothing_values': {'default': [[1, 1, 1, 1, 1, 1, 1, 1, 1], [weight, weight, weight, weight, weight, weight, weight, weight, weight]]}},\
	7 :{'smoothing': selWeight[7],  'smoothing_values': {'default': [[1, 1, 1, 1, 1, 1, 1, 1, 1], [weight, weight, weight, weight, weight, weight, weight, weight, weight]]}},\
	8 :{'smoothing': selWeight[8],  'smoothing_values': {'default': [[1, 1, 1, 1, 1, 1, 1, 1, 1], [weight, weight, weight, weight, weight, weight, weight, weight, weight]]}},\
	9 :{'smoothing': selWeight[9],  'smoothing_values': {'default': [[1, 1, 1, 1, 1, 1, 1, 1, 1], [weight, weight, weight, weight, weight, weight, weight, weight, weight]]}},\
	10:{'smoothing': selWeight[10], 'smoothing_values': {'default': [[1, 1, 1, 1, 1, 1, 1, 1, 1], [weight, weight, weight, weight, weight, weight, weight, weight, weight]]}},\
	11:{'smoothing': selWeight[11], 'smoothing_values': {'default': [[1, 1, 1, 1, 1, 1, 1, 1, 1], [weight, weight, weight, weight, weight, weight, weight, weight, weight]]}},\
	12:{'smoothing': selWeight[12], 'smoothing_values': {'default': [[0, 0, 0, 0, 0, 0, 0, 0, 0], [weight, weight, weight, weight, weight, weight, weight, weight, weight]]}},\
	13:{'smoothing': selWeight[13], 'smoothing_values': {'default': [[0, 0, 0, 0, 0, 0, 0, 0, 0], [weight, weight, weight, weight, weight, weight, weight, weight, weight]]}},\
	14:{'smoothing': selWeight[14], 'smoothing_values': {'default': [[0, 0, 0, 0, 0, 0, 0, 0, 0], [weight, weight, weight, weight, weight, weight, weight, weight, weight]]}}}, log=0)
    
    self.auto_update_dimensions()
    self.Send(None, log=0)
	
    if xit:
	# self.FitData({'preapplyConstraints':0,'calcErrorStr':'error = (data-x)*weight\n','geomDataIsCart':1,'err':'1.00e-006',
 #        'selections':{'Field 3': 'dzz', 'Field 2': 'dyy', 'Field 1': 'dxx', 'Field 6': 'dyz', 'Field 5': 'dxz', 'Field 4': 'dxy', 'Coordinate 2': 'coord_2', 'Coordinate 3': 'coord_3', 'Coordinate 1': 'coord_1'},
 #        'fit_selections':('Field 1','Field 2','Field 3','Field 4','Field 5','Field 6',),
 #        'initializeFields':initializeField,'iterationLimit':'10',
 #        'xi_options':{'dpError': '50.0', 'errorType': 'sd', 'datalist': 'all', 'sdError': '50.0', 'optimizeVars': 1,
 #        'filterData': True, 'calcType': 'from table', 'showTable': False, 'subdivisions': '5', 'itmax': '50', 'vmax': '1.5',
 #        'elemlist': 'all', 'ignorePoints': 1, 'tolerance': '1e-006', 'dpErrorType': 'sd',
 #        'newtonUpdate': 1,'output_type':'Update nodal variable', 'xifile':xipath},
 #        'output_type':'Update nodal variable'}, log=0)

        self.FitData({'iterationLimit':'10','calcErrorStr':'error = (data-x)*weight\n',\
            'fit_selections':('Field 1', 'Field 2', 'Field 3', 'Field 4', 'Field 5', 'Field 6'),\
            'xi_options':{'dpError': '50.0', 'errorType': 'sd', 'tol': 1e-06, 'refinement': 5, 'datalist': 'all', 'sdError': '50.0', 'optimizeVars': 0, 'filterData': True, 'autoEnhance': 1, 'calcType': 'from table', 'showTable': False, 'subdivisions': '5', 'itmax': 50, 'doProfile': False, 'autoCorrect': True, 'vmax': 1.5, 'elemlist': 'all', 'ignorePoints': 1, 'tolerance': '1e-6', 'dpErrorType': 'sd', 'newtonUpdate': 1, 'xifile':xipath},\
            'err':'1.00e-006',\
            'selections':{'Field 3': 'dzz', 'Field 2': 'dyy', 'Field 1': 'dxx', 'Field 6': 'dyz', 'Field 5': 'dxz', 'Field 4': 'dxy', 'Coordinate 2': 'coord2', 'Coordinate 3': 'coord3', 'Coordinate 1': 'coord1'},\
            'preapplyConstraints':0,'output_type':'Update nodal variable','initializeFields':0,'geomDataIsCart':1}, log=0) #Modified redraw=0 to log=0, batch mode
        
    self.auto_update_dimensions()
    self.Send(None, log=0)
    
    # save a copy of the model after each fit iteration
    self.Save(md + output + '_%d.cont6'%(j+1), log=0)
    
    # print "Saving result to %s!\n"%(md+output + '_%d.cont6')
    print "Iteration %s completed in %s seconds!!\n"%(j+1,time.clock()-time_loopstart)

print "Saved models %s to %s\n"%(output, md)
print "\n\nEnd Fit (%s)\n"%(strftime("%a, %d %b %Y %H:%M:%S", localtime()))
print "Fitting completed in %s seconds!!\n"%(time.clock()-t_start)

print "All done!"
