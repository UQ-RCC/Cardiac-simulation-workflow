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
from paraview.simple import *

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

  print 'Added nodes info to points'

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
          
          ## insert elems into cells   
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
  
  print 'Added elems info to cells'
  
  # Add points and cells to polydata
  polyData.SetPoints(pDPoints)
  polyData.SetPolys(pDCells)
  
  print 'Recreation of LV Mesh completed'
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

  return scalarData

# Modified from the function: MakeLUTFromCTF() from
# https://www.vtk.org/Wiki/VTK/Examples/Python/Visualization/AssignColorsCellFromLUT
""" Recreates the colour mapping to mirror the results from the EP Continuity simulation.
In this particular case, the colour mapping follows the paraview preset "Cool to Warm";
Scalar values close to 0 will be highlighted in blue, whilst those close to 1 are 
highlighted in red. 
tableSize -> the table size
Returns -> A styled lookup table
"""   
def SetColourMap(tableSize):
  
  # Set the colour scheme of the lookup table. Values all taken from "Cool to Warm" 
  # Colour mapping
  colorTransferFunction = vtk.vtkColorTransferFunction()
  colorTransferFunction.SetNanColor(1.0, 1.0, 0.0)
#  colorTransferFunction.SetColorSpaceToDiverging() # makes colours pass through white

  # Range, r, g, b
  colorTransferFunction.AddRGBPoint(0.0, 0.23137254902000001, 0.298039215686, 0.75294117647100001)
  colorTransferFunction.AddRGBPoint(1.0, 0.70588235294099999, 0.015686274509800001, 0.149019607843)

  lookupTable = vtk.vtkLookupTable()
  lookupTable.Build()
  
  # Update lookup table values  
  for i in range(0, tableSize):

      # Transform to rgba value     
      rgba = list(colorTransferFunction.GetColor(float(i)/ tableSize)) + [1] 
      lookupTable.SetTableValue(i,rgba)

  return lookupTable

# Modified from https://www.paraview.org/Wiki/VTK/Examples/Cxx/Widgets/Slider
""" Sets up the components of the displayed slider
Returns -> modified slider representation
"""
def SetupSliderRep():
    sliderRep = vtk.vtkSliderRepresentation2D()
    
    initialValue = 0 # Initial value of the slider
    
    # 30 frames saved out from the voltage solution
    minValue = 0
    maxValue = 29
    
    sliderTitle = "Voltage Solutions" # Slider title
    sliderLabelFormat = "%.0f" # Slider bar value label format

    x1Coord = 0.2 # Coords of slider position
    y1Coord = 0.1
    x2Coord = 0.8
    y2Coord = y1Coord
    
    # Dimensions of slider components
    sliderLength = 0.02
    sliderWidth = 0.03
    capLength = 0.01
    capWidth = sliderWidth
    tubeWidth = 0.005
    
    # Slider position
    sliderRep.GetPoint1Coordinate().SetCoordinateSystemToNormalizedDisplay()
    sliderRep.GetPoint1Coordinate().SetValue(x1Coord, y1Coord)
    sliderRep.GetPoint2Coordinate().SetCoordinateSystemToNormalizedDisplay()
    sliderRep.GetPoint2Coordinate().SetValue(x2Coord, y2Coord)
    
    # Slider information
    sliderRep.SetValue(initialValue)
    sliderRep.SetMinimumValue(minValue)
    sliderRep.SetMaximumValue(maxValue)
    sliderRep.SetTitleText(sliderTitle)
    sliderRep.SetLabelFormat(sliderLabelFormat)
    sliderRep.SetSliderLength(sliderLength)
    sliderRep.SetSliderWidth(sliderWidth)
    sliderRep.SetEndCapLength(capLength)
    sliderRep.SetEndCapWidth(capWidth)
    sliderRep.SetTubeWidth(tubeWidth)
    
    return sliderRep

# Modified from: https://www.vtk.org/Wiki/VTK/Examples/Python/Animation
""" A callback function which loads in a new set of scalar values every time the slider
is updated; changing what's displayed on the colour map.
"""
class vtkSliderCallback():
   def __init__(self):
       self.val = 0
       self.scalarInformation = ''
       self.vsolFile = fileDir + fileName
   
   def execute(self,obj,event):
       sliderWidget = obj
       
       # Makes sure to only update when slider value changes
       if int(round(sliderWidget.GetRepresentation().GetValue())) > self.val or int(round(sliderWidget.GetRepresentation().GetValue())) < self.val:
	   self.val = int(round(sliderWidget.GetRepresentation().GetValue()))
	   
	   # Update Scalar Values
	   if (self.val == 0):
            self.scalarInformation = None
	   else:
	       self.scalarInformation = GetVoltageSoln(self.vsolFile + "_%d.npy" % self.val)
	       
	   # Update scalar values here
	   self.mesh.GetPointData().SetScalars(self.scalarInformation)
#	   pDWriter = vtk.vtkXMLPolyDataWriter()
#           servermanager.SaveState("/Users/dayakern/Desktop/_PARAVIEW_THINGS/savedstate%d.pvsm" % self.val)
	   ## Save out files (need proper directory)
#	   pDWriter.SetFileName('/Users/dayakern/Desktop/_PARAVIEW_THINGS/mesh %d.vtp' % self.val)
#	   pDWriter.SetInputData(self.mesh)
#	   pDWriter.Write()
#	   print('state saved')

def init(nodesFile, elemsFile, initVsolFile):
    rendBG = (0.51765, 0.50588, 0.54118)
    tableSize = 256
    edgeColour = (0, 0, 0)
    renWinWidth = 625#1200
    renWinHeight = 450#1000
    
    # Load mesh information
    polyData = Load(nodesFile, elemsFile)
    
    # Get voltage solution data
    scalarInformation = None
    
    # Set scalars
    polyData.GetPointData().SetScalars(scalarInformation)
    
    # Setup lookup table
    lookupTable = SetColourMap(tableSize)
    
    # Update mapper
    mapper = vtk.vtkPolyDataMapper()
    mapper.SetInputData(polyData)
    mapper.SetLookupTable(lookupTable)
    
    # Setup slider components
    sliderRep = vtk.vtkSliderRepresentation2D()
    sliderRep = SetupSliderRep()
    
    # Setup how mesh surface will look
    property = vtk.vtkProperty()
    property.EdgeVisibilityOn()
    property.SetEdgeColor(edgeColour)

    actor = vtk.vtkActor()
    actor.SetMapper(mapper)
    actor.SetProperty(property)
    
    ren = vtk.vtkRenderer()
    ren.SetBackground(rendBG) # Modify background colour to grey
    renWin = vtk.vtkRenderWindow()
    renWin.SetSize(renWinWidth, renWinHeight)
    renWin.AddRenderer(ren)
    iren = vtk.vtkRenderWindowInteractor()
    iren.SetRenderWindow(renWin)
    iren.GetInteractorStyle().SetCurrentStyleToTrackballCamera()
    
    # Setup slider behaviours + enable display + interaction
    sliderWidget = vtk.vtkSliderWidget()
    sliderWidget.SetInteractor(iren)
    sliderCallback = vtkSliderCallback()
    sliderCallback.mesh = polyData
    sliderWidget.AddObserver("InteractionEvent", sliderCallback.execute)
    sliderWidget.SetRepresentation(sliderRep)
    sliderWidget.EnabledOn()
    
    ren.AddActor(actor)
    ren.ResetCamera()
    renWin.Render()
    renWin.SetWindowName(fileDir[64:73]) # Title of the window
    iren.Start()

# pypython script fileDir fileName
#fileDir = sys.argv[1]
#fileName = sys.argv[2]
#init(fileDir + '_NODEFILE.csv', fileDir + '_ELEMFILE.csv', fileDir + fileName)

fileName = 'Vsoln_testrun'
directoryList = []

# MRI GROUP 2
directoryList.append("/Users/dayakern/Desktop/4801_Testing/AFNI_Conversion/ucsd_mri_2/13-1_sham/ContinuityFiles/Vsolns/")
directoryList.append("/Users/dayakern/Desktop/4801_Testing/AFNI_Conversion/ucsd_mri_2/13-2_tac/ContinuityFiles/Vsolns/")
directoryList.append("/Users/dayakern/Desktop/4801_Testing/AFNI_Conversion/ucsd_mri_2/14-3_tac/ContinuityFiles/Vsolns/")
directoryList.append("/Users/dayakern/Desktop/4801_Testing/AFNI_Conversion/ucsd_mri_2/14-6_sham/ContinuityFiles/Vsolns/")

# MRI GROUP 3
directoryList.append("/Users/dayakern/Desktop/4801_Testing/AFNI_Conversion/ucsd_mri_3/16-1_sham/ContinuityFiles/Vsolns/")
directoryList.append("/Users/dayakern/Desktop/4801_Testing/AFNI_Conversion/ucsd_mri_3/16-3_tac/ContinuityFiles/Vsolns/")
directoryList.append("/Users/dayakern/Desktop/4801_Testing/AFNI_Conversion/ucsd_mri_3/16-4_sham/ContinuityFiles/Vsolns/")
directoryList.append("/Users/dayakern/Desktop/4801_Testing/AFNI_Conversion/ucsd_mri_3/16-5_tac/ContinuityFiles/Vsolns/")

# MRI GROUP 4
directoryList.append("/Users/dayakern/Desktop/4801_Testing/AFNI_Conversion/ucsd_mri_4/24-2_tac/ContinuityFiles/Vsolns/")
directoryList.append("/Users/dayakern/Desktop/4801_Testing/AFNI_Conversion/ucsd_mri_4/24-3_tac/ContinuityFiles/Vsolns/")
directoryList.append("/Users/dayakern/Desktop/4801_Testing/AFNI_Conversion/ucsd_mri_4/24-5_sham/ContinuityFiles/Vsolns/")
directoryList.append("/Users/dayakern/Desktop/4801_Testing/AFNI_Conversion/ucsd_mri_4/24-6_sham/ContinuityFiles/Vsolns/")

fileDir = directoryList[int(sys.argv[1]) - 1]
init(fileDir + '_NODEFILE.csv', fileDir + '_ELEMFILE.csv', fileDir + fileName)




