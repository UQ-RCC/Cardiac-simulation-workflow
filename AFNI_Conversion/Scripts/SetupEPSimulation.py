#************************************************************
# Description: Modifies the parameters of the material coordinates from the
# outputted file from the FieldFit3D.py script in preparation for the
# fibre fitting/EP simulation. The simulation setup follows the tutorial from:
# https://www.youtube.com/watch?v=nL7Sv0QEyoU&list=PLiW2csqywnmjAwqrSlxjZy0CKe9w3iSjA&index=15
#************************************************************

import sys
import shutil
import os
from client.PrefsManager import * # Get existing working dir where vsolns are saved

################################################################################
# MODIFIED FROM ParaViewInterface.py [convertToLists() function, line 285] &   #
# ******cont6_template.py.txt [modified structure and code]                    #
################################################################################

## PARAMETERS ******************************************************************

# [5] if set up like this: ./continuity --full --no-threads --batch $script $mDir
fDir = sys.argv[5]
mDir = fDir + 'ContinuityFiles/'

workDir = allPrefs['workDir']['defVal']
vSolnDir = mDir + 'Vsolns/'
modelDir = mDir

inputFileName = 'EDC_fitted_trilinear_DTfit_3_mat_mod.cont6'
modelOutputName = 'EDC_mod_EP.cont6'

### PART ZERO *******************************************************************
# Saves out element information (zero-indexed global node numbers)
# Arguments:
# mesh -> instance of Mesh class
# dir -> output file directory
# file -> output filename
def elementOutput( mesh, dir=vSolnDir, file='_ELEMFILE.csv'):
    output = ''
    
    ## Header
    output = 'Global_Node_1,Global_Node_2,Global_Node_3,Global_Node_4,Global_Node_5,Global_Node_6,Global_Node_7,Global_Node_8\n'
    
    ## Zero-indexed elements data (for Paraview)
    elements_array = mesh.obj.elements - 1

    ## Elements
    for i in range(len(elements_array)):
        
        # Global node numbers
        elements = elements_array[i]
        output = output + '%i,%i,%i,%i,%i,%i,%i,%i\n' % (elements[0], elements[1], elements[2], elements[3], elements[4], elements[5], elements[6], elements[7])

    print output  # Output to console
            
    ## Write output to file
    f = dir + file
    of = open( f , 'w' )
    of.write( output )
#end def elementOutput

# Saves out nodes information (x,y,z coordinates)
# Arguments:
# mesh -> instance of Mesh class
# dir -> output file directory
# file -> output filename
def nodeOutput( mesh, dir=vSolnDir, file='_NODEFILE.csv' ):
    output = ''
        
    ## Header
    output = 'Coordinate_X,Coordinate_Y,Coordinate_Z\n'
    
    ## Nodes (x,y,z coordinates of nodes)
    for i in range(len(mesh.obj)):
        
        # x, y, z stored in field variable 1, 2, 3 which is stored at
        # index 0-2, and the value is the first index of the field
        # variable's array
        nodeDerivs = mesh.obj.nodes[i].derivs
        output = output + '%.9f,%.9f,%.9f\n' % (nodeDerivs[0][0], nodeDerivs[1][0], nodeDerivs[2][0])

    print output  # Output to console
    # Write output to file
    f = dir + file
    of = open( f, 'w' )
    of.write( output )
#end def nodeOuput function

## PART ONE ********************************************************************

# Load latest fitted file from the FieldFit3D.py script.
self.Load_File(modelDir + inputFileName, log=0)

# Refine mesh
self.RefineMesh({'customXi3s':[],'autostoreBM':0,'newScaleFactor':'Arc lengths','autostore':1,'useCustoms':0,'customXi1s':[],'preserveNodeNumbers':0,'subdivide':False,'customXi2s':[],'nodesPerElem':[2, 2, 2],'intermediate':0,'doAveraging':1,'elemlist':[0],'elemsPerElem':[6, 6, 3],'convertToDegree':0,'gen_labels':[1, 1, 1, 1],'computeDerivatives':1}, log=0)

# Send/Calc
self.auto_update_dimensions()
self.Send(None, log=0)
self.CalcMesh([('Calculate', None), ('Do not Calculate', None), ('Calculate', None), ('Global arc length scale factors (for nodal derivs wrt arc lengths)', None)], log=0)

## PART TWO ********************************************************************

# Add Ionic Model
self.Load_File({'model_id':'1392', 'username':'guest', 'password':'tests', 'keep_existing_data':True }, log=0)

# Edit ionic model parameters
epEqs = self.stored_data.epEquations.obj
epEqs['variables'].setIcByName('stim_amplitude', [['Field 8', '']])
epEqs['variables'].setIcByName('u', [['Field 7', '']])
self.stored_data.store(epEqs, modified = True)
self.Send(None, log=0)

# Compile the ionic model, initialize the electrophysiology solve
self.CompileEPIonic(compileType = "C Single Precision")

self.Send(None, log=0)
self.CalcMesh([('Calculate', None), ('Do not Calculate', None), ('Calculate', None), ('Global arc length scale factors (for nodal derivs wrt arc lengths)', None)], log=0)


## PART THREE ******************************************************************

# Change the basis function
lderv = [1,0,0,0,0,0,0,0] # only the first deriv
hderv = [1,1,1,1,1,1,1,1] # all of the derivs
nderv = [0,0,0,0,0,0,0,0] # none of the derivs
nd = self.stored_data.nodes.obj # nodes object

nd.setGeomBasisValues([1, 1, 1, 3, 3, 3, 3, 3, 3, 3, 3, 3, 1, 3, 3, 0, 0, 0])
nd.setEnabledDerivs([hderv, hderv, hderv, lderv, lderv, lderv,
                        lderv, lderv, lderv, lderv, lderv, lderv,
                        hderv, lderv, nderv, nderv, nderv, nderv])

# Set the 495, 496, 501, 502 nodes to pace the LV from one spot
# [13] = Field Vector 3, Field Variable 8
# [0] = 'Value' deriv
nd.nodes[494].derivs[13][0] = 10.0
nd.nodes[495].derivs[13][0] = 10.0
nd.nodes[500].derivs[13][0] = 10.0
nd.nodes[501].derivs[13][0] = 10.0

self.stored_data.store(nd, modified = True)

# Set-up Conductivity
self.Load_File({'model_id':'1277', 'username':'guest', 'password':'tests', 'keep_existing_data':True }, log=0)

f11Value = 0.009
f22Value = 0.001

mat = self.stored_data.conductivityEquations.obj
mat['variables'].setIcByName("f11",[['value', f11Value]])
mat['variables'].setIcByName("f22",[['value', f22Value]])
mat['variables'].setIcByName("f33",[['value', f22Value]])
self.stored_data.store(mat, modified = True)
self.Send(None, log=0)
self.CompileEPConductivity(log=0, vf=None)

# Update model
self.auto_update_dimensions()
self.Send(None, log=0)
self.CalcMesh([('Calculate', None), ('Do not Calculate', None), ('Calculate', None), ('Global arc length scale factors (for nodal derivs wrt arc lengths)', None)], log=0)

# Save model out with material coords
self.Save(modelDir + modelOutputName, log=0)

# Save out refined mesh nodes/elems as separate files, to be used in visualisation
elementOutput(self.stored_data.elem)
nodeOutput(self.stored_data.nodes)

## PART FOUR *******************************************************************
# Initialise EP Simulation
self.SinitElectrophys(log=0)

# Run Simulation, save out solutions
# Note: TO RUN IN BATCH MODE -> renderResult = 0;
isRendered = 0
outputFileName = 'testrun'
self.SintElectrophys({'numGpuThreads':64,'odeStepSize':0.01,'plicitType':'Implicit','parallelLinearSolver':False,'solutions':{'tableResult': 0, 'counter': 10, 'writeFile': 1, 'saveSolutionFrequency': '1', 'saveRestartFrequency': '100', 'restartFile': 0, 'renderResult': isRendered},'stateVarInputSelections':[],'stateVarDoTable':0,'stateVarElemList':'all','parallelODESolver':False,'tstart':0.0,'useCuda':0,'stateVarOutputSelections':[],'serverKeyname':'electromech_exchange','useMultigpus':0,'stateVarList':'1','fileName': outputFileName,'useTrilinos':0,'aps':{'tableResult': 0, 'counter': 10, 'node_list': 'all', 'writeFile': 0, 'restartFile': 0, 'renderResult': 0},'stateVarListType':'collocation points','stateVarFrequency':1,'stateVarSelections':[],'dtout':0.1,'tlen':30.0,'reassemble_lhs':1,'ecgs':{'restartFile': 0, 'writeFile': 0, 'counter': 10, 'tableResult': 0, 'renderResult': 0}}, log=0)

# Move voltage solution files to the rat data specific directory
# Modified from http://www.pythonforbeginners.com/os/python-the-shutil-module
print workDir
print vSolnDir
for file in os.listdir(workDir):
    if file.startswith('Vsoln') or file.startswith('restart'):
        shutil.move(workDir + file, vSolnDir)

print "All Done!"
