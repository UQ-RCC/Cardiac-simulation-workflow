#************************************************************
#
# Date:
# Description: Modifies the parameters of the material coordinates from the
# outputted file from the FieldFit3D.py script in preparation for the
# fibre fitting and saves it out as a new model
#************************************************************
import sys

# [5] if set up like this: ./continuity --full --no-threads --batch $script $mDir
fDir = sys.argv[5]
mDir = fDir + 'ContinuityFiles/'

# Parameters
modelDir = mDir
inputFileName = 'EDC_fitted_trilinear_DTfit_3.cont6'
outputFileName = 'EDC_fitted_trilinear_DTfit_3_mat_mod.cont6'

# Load latest fitted file from the FieldFit3D.py script.
self.Load_File(modelDir + inputFileName, log=0)
self.Send(None, log=0)
self.CalcMesh([('Calculate', None), ('Do not Calculate', None), ('Calculate', None), ('Global arc length scale factors (for nodal derivs wrt arc lengths)', None)], log=0)

# Modify the Material Coordinates For Displaying Fibres
parameters = self.stored_data.matCoordEquations.obj['variables']
parameters.setIcByName('dxx', [['Field 1', '']])
parameters.setIcByName('dxy', [['Field 4', '']])
parameters.setIcByName('dxz', [['Field 5', '']])
parameters.setIcByName('dyy', [['Field 2', '']])
parameters.setIcByName('dyz', [['Field 6', '']])
parameters.setIcByName('dzz', [['Field 3', '']])

self.CompileMatCoord() # not sure if need this

self.Send(None, log=0)
self.CalcMesh([('Calculate', None), ('Do not Calculate', None), ('Calculate', None), ('Global arc length scale factors (for nodal derivs wrt arc lengths)', None)], log=0)

# Save model out with material coords' parameter values updated
self.Save(modelDir + outputFileName, log=0)

print "All done!"

