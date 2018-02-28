#************************************************************
#
# Date: Mon Nov 07 17:13:55 2005
# Description: Adds material coordinates to the existing
# fitted_tricubic file from Eric.
# 
# 
#************************************************************
import sys

# [5] if set up like this: ./continuity --full --no-threads --run $script $mDir
fDir = sys.argv[5]
mDir = fDir + 'ContinuityFiles/'


# File Parameters
modelDir = mDir
modelFile = 'EDC_mod_EP.cont6'

# Simulation Parameters
voltageSolnDir = '/Users/dayakern/.continuity//working/'
simulationLength = 30

## Load model file
self.LoadContModule(('electrophysiology',), log=0)
self.Load_File(modelDir + modelFile, log=0)
self.ChangeRenderer({'info': 'gui_renderer', 'renderer': 'OpenMesh'}, log=0) #Make sure mesh is OpenMesh to render EP sim properly

#self.CompileEPIonic(compileType='C Single Precision', log=0, vf=None)
#self.CompileEPConductivity(log=0, vf=None) # Doesn't have compileType.

## Send data to server and calculate
self.Send(None, log=0)
self.CalcMesh([('Calculate', None), ('Do not Calculate', None), ('Calculate', None), ('Global arc length scale factors (for nodal derivs wrt arc lengths)', None)], log=0)

## Render element lines of the model as well as the surface
self.Relem([0, 0, 3, 3, [0.0], ['all']], log=0) # Lines
self.Relem([0, 0, 4, 3, [1.0], ['all']], log=0) # Surfaces

## Render the results from the EP simulation
self.SinitElectrophys(log=0) # Initialise

## Get Voltage Solution
for i in xrange(0,30,1): #steps of 1 from 1 to 30
    if (i == 0):
        file = 'Vsoln_testrun.npy'
    else:
        file = 'Vsoln_testrun_'+str(i)+'.npy'

    self.SanimElectrophys({'vsol_gui':True,'compute_vcg':False,'vcg_output_file':'','vsoln': voltageSolnDir+file},log=0)

# Render voltage solution
self.RenderSolution({'start':'1', 'end':simulationLength  - 1, 'min':'0', 'max':'1', 'autoRerange':0}, log=0)

