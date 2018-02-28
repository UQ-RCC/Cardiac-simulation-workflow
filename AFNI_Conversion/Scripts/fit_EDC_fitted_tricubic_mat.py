#************************************************************
#
# Date:
# Description: Modifies the parameters of the material coordinates from the
# outputted file from the FieldFit3D.py script in preparation for the
# fibre fitting and saves it out as a new model
#************************************************************
import sys

# [5] if set up like this: ./continuity --full --no-threads --run $script $mDir
fDir = sys.argv[5]
mDir = fDir + 'ContinuityFiles/'

# Parameters
modelDir = mDir
inputFileName = 'EDC_fitted_trilinear_DTfit_3_mat_mod.cont6'

# Load latest fitted file from the FieldFit3D.py script.
self.Load_File(modelDir + inputFileName, log=0)
self.Send(None, log=0)
self.CalcMesh([('Calculate', None), ('Do not Calculate', None), ('Calculate', None), ('Global arc length scale factors (for nodal derivs wrt arc lengths)', None)], log=0)

# Rendering the heart mesh, with the fibres
self.Relem([0, 0, 3, 3, [0.0], ['all']], log=0)
self.Relem([0, 0, 4, 3, [0.0], ['all']], log=0)
self.Rfibers({'mpsep':0,'xi1':5,'length':0.6,'xi3':'0.0,0.1,0.2,0.3,0.4,0.5,0.6,0.7,0.8,0.9,1','nelist':'all','mp':[0, 0, 0],'mxsep':0,'xi2':5,'color':'by angle','mx':[1, False, False]}, log=0)

print "All done!"
