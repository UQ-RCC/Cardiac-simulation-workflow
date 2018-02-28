dir = "/Users/dayakern/Desktop/_PARAVIEW_THINGS/"
fName = "Vsoln_myrun_61.npy"

FILENAME = dir + fName

import numpy as np

# The data has an ugly shape
data = np.load(FILENAME)

heart_data = data[0]

cleaner_data = []

## Clean up the shape of the data
for i in heart_data:
    cleaner_data.append(i[0])

# Convert it back into a numpy array
cleaner_data = np.array(cleaner_data)

# Its now just a 8x6000 array
print(cleaner_data.shape)
