#************************************************************
#
# Date: 
# Description: Adds material coordinates to the existing
# fitted_tricubic file from Eric and saves it out as a new model.
#
#************************************************************
import sys

# [5] if set up like this: ./continuity --full --no-threads --batch $script $mDir $modelFile
outDir = sys.argv[5] + 'ContinuityFiles/'

# Parameters
modelDir = outDir
modelName = sys.argv[6]
modelOutputName = modelName + '_mat.cont6'

# Load/Send/Calc the model
self.Load_File(modelDir + modelName + '.cont6', log=0)
self.Send(None, log=0)
self.CalcMesh([('Calculate', None), ('Do not Calculate', None), ('Calculate', None), ('Global arc length scale factors (for nodal derivs wrt arc lengths)', None)], log=0)

# Load in DTI material model
self.Load_File({'model_id':'1389', 'username':'guest', 'password':'tests', 'keep_existing_data':True }, log=0)

self.auto_update_dimensions()
self.Send(None, log=0)
self.CalcMesh([('Calculate', None), ('Do not Calculate', None), ('Calculate', None), ('Global arc length scale factors (for nodal derivs wrt arc lengths)', None)], log=0)

# Save model out with material coords
self.Save(modelDir + modelOutputName, log=0)

print "That's All!"
