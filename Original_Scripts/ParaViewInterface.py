import xml.etree.cElementTree as XML
import os
import numpy


class ParaViewOutput:
    """
        Examples of vtk can be found here [http://public.kitware.com/pipermail/vtkusers/2003-May/017988.html]
        and here [http://www.vtk.org/wp-content/uploads/2015/04/file-formats.pdf]
    """
    fibers = None
    path = "ParaView/vtkFiles/"
    filename = path + "out"

    __elements = None
    __vertices = None

    @classmethod
    def outputVTK(cls):

        print("Removing existing VTK files")
        cls.removeExistingVTKFiles()

        print("Refining mesh for output.")
        cls.getMesh(refinement=3)

        print("Outputting mesh data.")
        cls.outputMeshVTU()
        if(cls.fibers != None):
            print("Outputting fiber data.")
            cls.outputFiberVTU()
    @classmethod
    def removeExistingVTKFiles(cls):
        # remove any existing vtk files
        for file in os.listdir(cls.path):
            if file.endswith(".vtu"):
                filepath = os.path.join(cls.path, file)
                os.remove(filepath)

    @classmethod
    def getMesh(cls, refinement=1):
        refineArgs = {
            'elemsPerElem': [refinement, refinement, refinement],
            'nodesPerElem': [2, 2, 2],
            'customXi1s': [],
            'customXi2s': [],
            'customXi3s': [],
            'autostore': 0,
            'newScaleFactor': 'Arc lengths',
            'elemlist': [0],
            'gen_labels': [0, 0, 0, 0],
            'computeDerivatives': 1,
            'subdivide': False,
            'autostoreBM': 0,
            'intermediate': 0,
            'useCustoms': 0,
            'convertToDegree': 0,
            'doAveraging': 0,
            'preserveNodeNumbers': 0
        }
        from blenderScripts.Continuity.continuityShellAccess import getContVF
        if(not getContVF().calculatedMesh):
            getContVF().calc_mesh()
        # get elements and nodes (nodes are in xi(relative to element) form)
        elements, nodes, a = getContVF().send_cmd(
            ['mesh.RefineMesh', refineArgs])
        # get actual coordinates from relative positions
        nodes, b, c, d = getContVF().send_cmd(['mesh.GetXjsAtXis', [nodes, refineArgs['elemsPerElem'], refineArgs['newScaleFactor'], refineArgs['computeDerivatives']]])
        del a, b, c, d

        # get only the first 8 (or 4) indices (which is the element data), cast to int, then subtract 1 to normalise to 0 based indexing
        try:
            cls.__elements = numpy.array(elements)[:, list(range(8))].astype(numpy.int32) - 1
        except IndexError:
            cls.__elements = numpy.array(elements)[:, list(range(4))].astype(numpy.int32) - 1
        # from 0 to the last multiple of 8 that is in the node list
        fieldVarIndexList = list(range(0, len(nodes[0]), 8))
        cls.__vertices = numpy.array(nodes)[:, fieldVarIndexList]

    """
    @classmethod
    def refineMesh(cls, refinement=2):
        from blenderScripts.hexblender.hex_interp_subdiv_no_priorities import hex_interp_subdiv_no_priorities
        from pcty.client.meshCommands import swap_elem_columns
        try:
            elements = swap_elem_columns(cls.__elements)
            vertices = cls.__vertices
            for i in range(refinement):
                elements, vertices = hex_interp_subdiv_no_priorities(
                    elements, vertices)
            elements = swap_elem_columns(elements)
            cls.__elements = elements
            cls.__vertices = vertices
        except Exception as e:
            print("Failed to refine mesh.")
            print(repr(e))
    """
    @classmethod
    def outputMeshVTU(cls):
        #from blenderScripts.Continuity.continuityShellAccess import getContVF
        #contVF = getContVF()

        # determine if elements are 2D
        elements2D = False
        try:
            cls.__elements[0][7]
        except IndexError as e:
            elements2D = True

        # top level header
        vtkFile = XML.Element("VTKFile", type="UnstructuredGrid",
                              version="0.1", byte_order="LittleEndian")
        # UnstructuredGrid top level
        unstructuredGrid = XML.SubElement(vtkFile, "UnstructuredGrid")

        # made of multiple independent pieces, this is the base geometry
        pieceBase = XML.SubElement(unstructuredGrid, "Piece", NumberOfPoints=str(
            len(cls.__vertices)), NumberOfCells=str(len(cls.__elements)))

        # contains points, cells, pointData(optional), cellData(optional)

        # points level, NumberOfComponents = length of a vertex definition
        points = XML.SubElement(pieceBase, "Points")
        pointString = []
        # all rows, columns 0, 1, 2
        for x, y, z in cls.__vertices[:, list(range(3))]:
            pointString.append("" + str(x) + " " +
                               str(y) + " " + str(z) + "\n")
        pointString = ''.join(pointString)
        dataArrayPoints = XML.SubElement(
            points, "DataArray", type="Float32", NumberOfComponents="3", format="ascii").text = pointString

        # cells level
        cells = XML.SubElement(pieceBase, "Cells")

        # connectivity of points to make the cells, all appended
        connectivityString = []
        for element in cls.__elements:
            cellString = None
            if(not elements2D):
                cellString = str(element[0]) + " " + str(element[2]) + " " + str(element[3]) + " " + str(element[1]) + " " + str(
                    element[4]) + " " + str(element[6]) + " " + str(element[7]) + " " + str(element[5]) + "\n"
            else:
                cellString = str(element[0]) + " " + str(element[2]) + \
                    " " + str(element[3]) + " " + str(element[1]) + "\n"
            connectivityString.append(cellString)
        connectivityString = ''.join(connectivityString)
        dataArrayCellsConnectivity = XML.SubElement(
            cells, "DataArray", type="Int32", Name="connectivity", format="ascii").text = connectivityString

        # delimiters of where each cell definition ends, ex for a cell def of 4
        # points the first offset would be 4, then 8, then 12 and so on.
        offsetsString = []
        # 4 for quad, 8 for hexahedron
        elementOffsetIncrement = 4 if elements2D else 8
        elementOffsetNumber = elementOffsetIncrement
        while(elementOffsetNumber <= elementOffsetIncrement * len(cls.__elements)):
            offsetsString.append(str(elementOffsetNumber) + "\n")
            elementOffsetNumber += elementOffsetIncrement
        offsetsString = ''.join(offsetsString)
        dataArrayCellsOffsets = XML.SubElement(
            cells, "DataArray", type="Int32", Name="offsets", format="ascii").text = offsetsString

        # cell type of each cell in order 9 for quad, 12 for hexahedron
        cellType = "9\n" if elements2D else "12\n"
        cellTypesString = [cellType] * len(cls.__elements)
        cellTypesString = ''.join(cellTypesString)
        dataArrayCellsOffsets = XML.SubElement(
            cells, "DataArray", type="UInt8", Name="types", format="ascii").text = cellTypesString

        # pointData level, skip if no data fields
        if(len(cls.__vertices[0]) > 3):
            pointData = XML.SubElement(pieceBase, "PointData")
            for fieldVar in range(3, len(cls.__vertices[0])):  # these are the field variables that are not coordinates
                fieldString = []
                for i in range(len(cls.__vertices)):
                    fieldString.append(str(cls.__vertices[i, fieldVar]) + "\n")
                fieldString = ''.join(fieldString)
                field = XML.SubElement(pointData, "DataArray", type="Float32", Name="FieldVariable " + str(fieldVar-2), format="ascii").text = fieldString # -2 in order to start numbering at 1 (for variable index 3)

        # get the tree starting at the root of the vtkFile level, then write to
        # file
        vtuFile = XML.ElementTree(vtkFile)
        vtuFile.write(cls.filename + ".vtu", xml_declaration=True)

    @classmethod
    def outputFiberVTU(cls):
        # top level header
        vtkFile = XML.Element("VTKFile", type="UnstructuredGrid",
                              version="0.1", byte_order="LittleEndian")
        # UnstructuredGrid top level
        unstructuredGrid = XML.SubElement(vtkFile, "UnstructuredGrid")

        # made of multiple independent pieces, this is the fibers section
        pieceFibers = XML.SubElement(unstructuredGrid, "Piece", NumberOfPoints=str(len(
            cls.fibers['coordinates'])), NumberOfCells=str(len(cls.fibers['coordinates'])))

        # contains points, cells, pointData(optional), cellData(optional)

        # points level, NumberOfComponents = length of a vertex definition
        points = XML.SubElement(pieceFibers, "Points")
        pointString = []
        for vertex in cls.fibers['coordinates']:
            pointString.append(
                "" + str(vertex[0]) + " " + str(vertex[1]) + " " + str(vertex[2]) + "\n")
        pointString = ''.join(pointString)
        dataArrayPoints = XML.SubElement(
            points, "DataArray", type="Float32", NumberOfComponents="3", format="ascii").text = pointString

        # cells level
        cells = XML.SubElement(pieceFibers, "Cells")

        # connectivity of points to make the cells, all appended
        connectivityString = []
        for i in range(len(cls.fibers['coordinates'])):
            connectivityString.append(str(i) + "\n")
        connectivityString = ''.join(connectivityString)
        dataArrayCellsConnectivity = XML.SubElement(
            cells, "DataArray", type="Int32", Name="connectivity", format="ascii").text = connectivityString

        # delimiters of where each cell definition ends, ex for a cell def of 4
        # points the first offset would be 4, then 8, then 12 and so on.
        offsetsString = []
        for i in range(1, len(cls.fibers['coordinates']) + 1):
            offsetsString.append(str(i) + "\n")
        offsetsString = ''.join(offsetsString)
        dataArrayCellsOffsets = XML.SubElement(
            cells, "DataArray", type="Int32", Name="offsets", format="ascii").text = offsetsString

        # cell type of each cell in order 1 vertex
        cellTypesString = ["1\n"] * len(cls.fibers['coordinates'])
        cellTypesString = ''.join(cellTypesString)
        dataArrayCellsOffsets = XML.SubElement(
            cells, "DataArray", type="UInt8", Name="types", format="ascii").text = cellTypesString

        # pointData level
        pointData = XML.SubElement(pieceFibers, "PointData", Vectors="Vector")

        tensorData = ([], [], [])
        tensorName = ("FibersX", "FibersY", "FibersZ")
        for tensor in cls.fibers['tensors']:
            for i in range(3):
                tensorLine = ""
                for j in range(3):
                    value = str(tensor[i][j])
                    if value == "nan":
                        value = "0"
                    tensorLine = tensorLine + value + " "
                tensorLine += "\n"
                tensorData[i].append(tensorLine)

        for i in range(3):
            XML.SubElement(pointData, "DataArray", type="Float32",
                           Name=tensorName[i], format="ascii", NumberOfComponents="3").text = ''.join(tensorData[i])

        # get the tree starting at the root of the vtkFile level, then write to
        # file
        vtuFile = XML.ElementTree(vtkFile)
        vtuFile.write(cls.filename + "Fiber.vtu", xml_declaration=True)

    @classmethod
    def openParaview(cls):
        # TODO this will only work after paraview updates to use python 3.5
        # subprocess calls an executable
        #import subprocess
        #subprocess.run(["ParaView/bin/paraview", "--data=" + cls.filename + ".vtu;" + cls.filename + "Fiber.vtu;"])
        #subprocess.run(["ParaView/bin/paraview", "--script=ParaView/vtkFiles/load.py"])
        print("\n\nParaView scripting not currently working. Please run:",
              "\n./ParaView/bin/paraview --script=ParaView/vtkFiles/load.py\n",
              "from the Continuity root directory to start ParaView.\n\n")

    @classmethod
    def showInParaview(cls, refreshVTK=True):
        # rebuilds vtk file by default
        if(refreshVTK):
            cls.outputVTK()

        # spawn new thread for paraview
        from threading import Thread
        thread = Thread(target=cls.openParaview)
        thread.start()
        print("Started ParaView")

    @classmethod
    def convertToLists(cls, vf):
        '''
        This will convert the currently loaded model into lists for output to
        VTK files
        '''
        # Elements
        # The node numbers need to be zero based
        elem_array = vf.stored_data.elem.obj.elements - 1

        # Nodes
        node_list = []
        for i in range(len(vf.stored_data.nodes.obj)):
            # x, y, z stored in field variable 1, 2, 3 which is stored at
            # index 0-2, and the value is the first index of the field
            # variable's array
            nodeDerivs = vf.stored_data.nodes.obj.nodes[i].derivs
            node_list.append(
                (nodeDerivs[0][0], nodeDerivs[1][0], nodeDerivs[2][0]))
        return numpy.array(node_list), elem_array
