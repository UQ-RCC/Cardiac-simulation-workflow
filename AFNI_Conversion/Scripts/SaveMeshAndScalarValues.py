# Script parts Modified from:
# Answer on this page
# https://stackoverflow.com/questions/45665130/create-mesh-from-cells-and-points-in-paraview, 
# Vtk API documentation and https://www.vtk.org/gitweb?p=VTK.git;a=blob;f=Examples/Annotation/Python/labeledMesh.py, 
# https://stackoverflow.com/questions/3770348/how-to-safely-open-close-files-in-python-2-4
#
# Script restructured into functions + rewritten to be run from command line by Hoang

import vtk
import sys
import numpy as np
import os
import glob

""" Recreates a 3D mesh from data captured from the output of the Continuity EP 
simulation. In this particular case, the mesh is a reconstruction from nodes/elements 
information from a left ventricle heart model that was saved out.
nodesFile -> the file where the nodes information of the heart mesh were saved
elemsFile -> the file where the elems information of the heart mesh were saved
Returns -> the reconstructed mesh (polyData)
"""
def Load(nodesFile, elemsFile):
	polyData = vtk.vtkPolyData() # Mesh to be constructed
	pDPoints = vtk.vtkPoints() # Points of the mesh 
	pDCells = vtk.vtkCellArray() # Cells of the mesh
	LVMeshPoints = None # Nodes information for LV mesh
	LVMeshElems = None # Elements information for LV mesh
	
	## Insert Coords 
	try:
		# Import nodes file
		LVMeshPoints = open(nodesFile)
		id = 0 # ID # for points
		line = LVMeshPoints.readline() # Read the header
			
		for coords in LVMeshPoints:

			# Get coord values by row
			coordValues = coords.strip().split(',')

			# Insert coords into points
			pDPoints.InsertPoint(id, (float(coordValues[0]),
																float(coordValues[1]),
																float(coordValues[2])))
			
			id = id + 1 # Increment Id
	
	finally:
		if LVMeshPoints is not None:

			# Close opened file
			LVMeshPoints.close()

	# print 'Added nodes info to points'

	## Insert Elems
	try:
		# Import elems file
		LVMeshElems = open(elemsFile)

		# Number of points per cell
		numPoints = 4
		line = LVMeshElems.readline() # Reading the header
			
		for elems in LVMeshElems:

			# Get elems values by row
			elemsValues = elems.strip().split(',')
					
			## Insert elems into cells   
			# Elems need to be reordered from the Continuity format
			# -> [hex[0],hex[1],hex[3],hex[2],hex[4],hex[5],hex[7],hex[6]]
			# From: HEXBLENDER_OT_import_pickle(bpy.types.Operator) function
			
			# Inner Plane
			pDCells.InsertNextCell(numPoints, (int(elemsValues[0]),
																				int(elemsValues[1]),
																				int(elemsValues[3]),
																				int(elemsValues[2])))
			# Outer Plane
			pDCells.InsertNextCell(numPoints, (int(elemsValues[4]),
																				int(elemsValues[5]),
																				int(elemsValues[7]),
																				int(elemsValues[6])))

			# Horizontal Planes
			pDCells.InsertNextCell(numPoints, (int(elemsValues[6]),
																				int(elemsValues[7]),
																				int(elemsValues[3]),
																				int(elemsValues[2])))
	finally:
		if LVMeshElems is not None:

			# Close opened file
			LVMeshElems.close()
	
	# print 'Added elems info to cells'
	
	# Add points and cells to polydata
	polyData.SetPoints(pDPoints)
	polyData.SetPolys(pDCells)
	
	# print 'Recreation of LV Mesh completed'
	return polyData

""" Formats the voltage solution results that were outputted from the Continuity 
EP simulation. In this particular case, the data is cleaned up to be used as the
scalar information to determine the colour mapping of the mesh.
filePath -> the location to the specific voltage solution data 
Returns -> Properly formatted scalar values (scalarData)  
"""  
def GetVoltageSoln(filePath):
	vSolns = np.load(filePath) # Location of the voltage solutions
	vSoln = vSolns[0] # The voltage solution data
	cleaner_data = [] # Holds the cleaned up voltage solution data

	# Clean up the shape of the data [Modified from Roy's heart_reader code]
	for i in vSoln:
		cleaner_data.append(i[0])
		
	# Convert back into numpy array [From Roy's heart_reader code]         
	cleaner_data = np.array(cleaner_data) 

	## Format scalar information
	scalarData = vtk.vtkDoubleArray() # Scalar object
	scalarData.SetName("Voltage Solution")

	id = 0; # Position of data
	minValue = 0;
	maxValue = 0;

	# Insert voltage solution values into scalar object
	for i in cleaner_data[0]:
		if i < minValue:
			minValue = i
		if i > maxValue:
			maxValue = i

		scalarData.InsertValue(id, i)
		id = id + 1

	#  print minValue, maxValue
	return scalarData

## there are probs better ways to do this, but oh well.
def SaveFrames(fileDir, scalarInformation, mesh, pDWriter):
	frameNum = 0

	relevantFiles = glob.glob(fileDir + 'Vsoln_testrun_*')

	## Save out scalar value for 0
	mesh.GetPointData().SetScalars(scalarInformation)
	pDWriter.SetInputData(mesh)
	fileName = "Vsoln_testrun_0"
	pDWriter.SetFileName('/Users/dayakern/Desktop/_PARAVIEW_THINGS/Vsolns/%s.vtp' % fileName)
	pDWriter.SetDataModeToBinary()
	pDWriter.Write()
	
	for file in relevantFiles:
		scalarInformation = GetVoltageSoln(file)

		# # Update scalar values here
		mesh.GetPointData().SetScalars(scalarInformation)

		## Save out files
		pDWriter.SetInputData(mesh)
		baseFileName = os.path.basename(file) # get filename without the file path
		fileName = baseFileName[:-4] # get filename without the extension
		pDWriter.SetFileName('/Users/dayakern/Desktop/_PARAVIEW_THINGS/Vsolns/%s.vtp' % fileName)
		pDWriter.SetDataModeToBinary()
		pDWriter.Write()

	print('All States Saved')

def init(nodesFile, elemsFile, fileDir):
	pDWriter = vtk.vtkXMLPolyDataWriter()
		
	# Load mesh information
	polyData = Load(nodesFile, elemsFile)
		
	# Set initial scalar information
	scalarInformation = None
	polyData.GetPointData().SetScalars(scalarInformation)

	# Save out all scalar information
	SaveFrames(fileDir, scalarInformation, polyData, pDWriter)

# pypython script fileDir
fileDir = sys.argv[1]
# fileName = sys.argv[2] - no longer required
init(fileDir + '_NODEFILE.csv', fileDir + '_ELEMFILE.csv', fileDir)
