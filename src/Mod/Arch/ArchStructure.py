#***************************************************************************
#*                                                                         *
#*   Copyright (c) 2011                                                    *  
#*   Yorik van Havre <yorik@uncreated.net>                                 *  
#*                                                                         *
#*   This program is free software; you can redistribute it and/or modify  *
#*   it under the terms of the GNU Lesser General Public License (LGPL)    *
#*   as published by the Free Software Foundation; either version 2 of     *
#*   the License, or (at your option) any later version.                   *
#*   for detail see the LICENCE text file.                                 *
#*                                                                         *
#*   This program is distributed in the hope that it will be useful,       *
#*   but WITHOUT ANY WARRANTY; without even the implied warranty of        *
#*   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the         *
#*   GNU Library General Public License for more details.                  *
#*                                                                         *
#*   You should have received a copy of the GNU Library General Public     *
#*   License along with this program; if not, write to the Free Software   *
#*   Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  *
#*   USA                                                                   *
#*                                                                         *
#***************************************************************************

import FreeCAD,FreeCADGui,Draft,ArchComponent,DraftVecUtils,ArchCommands
from FreeCAD import Vector
from PyQt4 import QtCore
from DraftTools import translate

__title__="FreeCAD Structure"
__author__ = "Yorik van Havre"
__url__ = "http://free-cad.sourceforge.net"

def makeStructure(baseobj=None,length=1,width=1,height=1,name=str(translate("Arch","Structure"))):
    '''makeStructure([obj],[length],[width],[heigth],[swap]): creates a
    structure element based on the given profile object and the given
    extrusion height. If no base object is given, you can also specify
    length and width for a cubic object.'''
    obj = FreeCAD.ActiveDocument.addObject("Part::FeaturePython",name)
    _Structure(obj)
    _ViewProviderStructure(obj.ViewObject)
    if baseobj:
        obj.Base = baseobj
        obj.Base.ViewObject.hide()
    obj.Width = width
    obj.Height = height
    obj.Length = length
    obj.ViewObject.ShapeColor = ArchCommands.getDefaultColor("Structure")
    return obj

def makeStructuralSystem(objects,axes):
    '''makeStructuralSystem(objects,axes): makes a structural system
    based on the given objects and axes'''
    result = []
    if objects and axes:
        for o in objects:
            s = makeStructure(o)
            s.Axes = axes
            result.append(s)
        FreeCAD.ActiveDocument.recompute()
    return result

class _CommandStructure:
    "the Arch Structure command definition"
    def GetResources(self):
        return {'Pixmap'  : 'Arch_Structure',
                'MenuText': QtCore.QT_TRANSLATE_NOOP("Arch_Structure","Structure"),
                'Accel': "S, T",
                'ToolTip': QtCore.QT_TRANSLATE_NOOP("Arch_Structure","Creates a structure object from scratch or from a selected object (sketch, wire, face or solid)")}
        
    def Activated(self):
        
        global QtGui, QtCore
        from PyQt4 import QtGui, QtCore
        
        self.Length = 0.5
        self.Width = 0.2
        self.Height = 1
        self.continueCmd = False
        sel = FreeCADGui.Selection.getSelection()
        if sel:
            # direct creation
            FreeCAD.ActiveDocument.openTransaction(str(translate("Arch","Create Structure")))
            FreeCADGui.doCommand("import Arch")
            # if selection contains structs and axes, make a system
            st = Draft.getObjectsOfType(sel,"Structure")
            ax = Draft.getObjectsOfType(sel,"Axis")
            if st and ax:
                FreeCADGui.doCommand("Arch.makeStructuralSystem(" + ArchCommands.getStringList(st) + "," + ArchCommands.getStringList(ax) + ")")
            else:
                # else, do normal structs
                for obj in sel:
                    FreeCADGui.doCommand("Arch.makeStructure(FreeCAD.ActiveDocument." + obj.Name + ")")
            FreeCAD.ActiveDocument.commitTransaction()
            FreeCAD.ActiveDocument.recompute()
        else:
            # interactive mode
            if hasattr(FreeCAD,"DraftWorkingPlane"):
                FreeCAD.DraftWorkingPlane.setup()
            import DraftTrackers
            self.points = []
            self.tracker = DraftTrackers.boxTracker()
            self.tracker.width(self.Width)
            self.tracker.height(self.Height)
            self.tracker.length(self.Length)
            self.tracker.on()
            FreeCADGui.Snapper.getPoint(callback=self.getPoint,movecallback=self.update,extradlg=self.taskbox())
            
    def getPoint(self,point=None,obj=None):
        "this function is called by the snapper when it has a 3D point"
        self.tracker.finalize()
        if point == None:
            return
        FreeCAD.ActiveDocument.openTransaction(str(translate("Arch","Create Structure")))
        FreeCADGui.doCommand('import Arch')
        FreeCADGui.doCommand('s = Arch.makeStructure(length='+str(self.Length)+',width='+str(self.Width)+',height='+str(self.Height)+')')
        FreeCADGui.doCommand('s.Placement.Base = '+DraftVecUtils.toString(point))
        FreeCAD.ActiveDocument.commitTransaction()
        FreeCAD.ActiveDocument.recompute()
        if self.continueCmd:
            self.Activated()

    def taskbox(self):
        "sets up a taskbox widget"
        w = QtGui.QWidget()
        w.setWindowTitle(str(translate("Arch","Structure options")))
        lay0 = QtGui.QVBoxLayout(w)
        
        lay1 = QtGui.QHBoxLayout()
        lay0.addLayout(lay1)
        label1 = QtGui.QLabel(str(translate("Arch","Length")))
        lay1.addWidget(label1)
        value1 = QtGui.QDoubleSpinBox()
        value1.setDecimals(2)
        value1.setValue(self.Length)
        lay1.addWidget(value1)
        
        lay2 = QtGui.QHBoxLayout()
        lay0.addLayout(lay2)
        label2 = QtGui.QLabel(str(translate("Arch","Width")))
        lay2.addWidget(label2)
        value2 = QtGui.QDoubleSpinBox()
        value2.setDecimals(2)
        value2.setValue(self.Width)
        lay2.addWidget(value2)

        lay3 = QtGui.QHBoxLayout()
        lay0.addLayout(lay3)
        label3 = QtGui.QLabel(str(translate("Arch","Height")))
        lay3.addWidget(label3)
        value3 = QtGui.QDoubleSpinBox()
        value3.setDecimals(2)
        value3.setValue(self.Height)
        lay3.addWidget(value3)

        value4 = QtGui.QCheckBox(str(translate("Arch","Continue")))
        lay0.addWidget(value4)
        
        QtCore.QObject.connect(value1,QtCore.SIGNAL("valueChanged(double)"),self.setLength)
        QtCore.QObject.connect(value2,QtCore.SIGNAL("valueChanged(double)"),self.setWidth)
        QtCore.QObject.connect(value3,QtCore.SIGNAL("valueChanged(double)"),self.setHeight)
        QtCore.QObject.connect(value4,QtCore.SIGNAL("stateChanged(int)"),self.setContinue)
        return w
        
    def update(self,point):
        "this function is called by the Snapper when the mouse is moved"
        self.tracker.pos(point)
        
    def setWidth(self,d):
        self.Width = d
        self.tracker.width(d)

    def setHeight(self,d):
        self.Height = d
        self.tracker.height(d)

    def setLength(self,d):
        self.Length = d
        self.tracker.length(d)

    def setContinue(self,i):
        self.continueCmd = bool(i)
       
class _Structure(ArchComponent.Component):
    "The Structure object"
    def __init__(self,obj):
        ArchComponent.Component.__init__(self,obj)
        obj.addProperty("App::PropertyLength","Length","Base",
                        str(translate("Arch","The length of this element, if not based on a profile")))
        obj.addProperty("App::PropertyLength","Width","Base",
                        str(translate("Arch","The width of this element, if not based on a profile")))
        obj.addProperty("App::PropertyLength","Height","Base",
                        str(translate("Arch","The height or extrusion depth of this element. Keep 0 for automatic")))
        obj.addProperty("App::PropertyLinkList","Axes","Base",
                        str(translate("Arch","Axes systems this structure is built on")))
        obj.addProperty("App::PropertyVector","Normal","Base",
                        str(translate("Arch","The normal extrusion direction of this object (keep (0,0,0) for automatic normal)")))
        obj.addProperty("App::PropertyIntegerList","Exclude","Base",
                        str(translate("Arch","The element numbers to exclude when this structure is based on axes")))
        self.Type = "Structure"
        
    def execute(self,obj):
        self.createGeometry(obj)
        
    def onChanged(self,obj,prop):
        self.hideSubobjects(obj,prop)
        if prop in ["Base","Length","Width","Height","Normal","Additions","Subtractions","Axes"]:
            self.createGeometry(obj)

    def getAxisPoints(self,obj):
        "returns the gridpoints of linked axes"
        import DraftGeomUtils
        pts = []
        if len(obj.Axes) == 1:
            for e in obj.Axes[0].Shape.Edges:
                pts.append(e.Vertexes[0].Point)
        elif len(obj.Axes) >= 2:
            set1 = obj.Axes[0].Shape.Edges
            set2 = obj.Axes[1].Shape.Edges
            for e1 in set1:
                for e2 in set2: 
                    pts.extend(DraftGeomUtils.findIntersection(e1,e2))
        return pts

    def getAxisPlacement(self,obj):
        "returns an axis placement"
        if obj.Axes:
            return obj.Axes[0].Placement
        return None

    def createGeometry(self,obj):
        import Part, DraftGeomUtils
        
        # getting default values
        height = width = length = 1
        if hasattr(obj,"Length"):
            if obj.Length:
                length = obj.Length
        if hasattr(obj,"Width"):
            if obj.Width:
                width = obj.Width
        if hasattr(obj,"Height"):
            if obj.Height:
                height = obj.Height

        # creating base shape
        pl = obj.Placement
        base = None
        if obj.Base:
            if obj.Base.isDerivedFrom("Part::Feature"):
                if obj.Normal == Vector(0,0,0):
                    p = FreeCAD.Placement(obj.Base.Placement)
                    normal = p.Rotation.multVec(Vector(0,0,1))
                else:
                    normal = Vector(obj.Normal)
                normal = normal.multiply(height)
                base = obj.Base.Shape.copy()
                if base.Solids:
                    pass
                elif base.Faces:
                    base = base.extrude(normal)
                elif (len(base.Wires) == 1):
                    if base.Wires[0].isClosed():
                        base = Part.Face(base.Wires[0])
                        base = base.extrude(normal)
            elif obj.Base.isDerivedFrom("Mesh::Feature"):
                if obj.Base.Mesh.isSolid():
                    if obj.Base.Mesh.countComponents() == 1:
                        sh = ArchCommands.getShapeFromMesh(obj.Base.Mesh)
                        if sh.isClosed() and sh.isValid() and sh.Solids:
                            base = sh
        else:
            if obj.Normal == Vector(0,0,0):
                normal = Vector(0,0,1)
            else:
                normal = Vector(obj.Normal)
            normal = normal.multiply(height)
            l2 = length/2 or 0.5
            w2 = width/2 or 0.5
            v1 = Vector(-l2,-w2,0)
            v2 = Vector(l2,-w2,0)
            v3 = Vector(l2,w2,0)
            v4 = Vector(-l2,w2,0)
            base = Part.makePolygon([v1,v2,v3,v4,v1])
            base = Part.Face(base)
            base = base.extrude(normal)
            
        base = self.processSubShapes(obj,base)
            
        if base:
            # applying axes
            pts = self.getAxisPoints(obj)
            apl = self.getAxisPlacement(obj)
            if pts:
                fsh = []
                for i in range(len(pts)):
                    if hasattr(obj,"Exclude"):
                        if i in obj.Exclude:
                            continue
                    sh = base.copy()
                    if apl:
                        sh.Placement.Rotation = apl.Rotation
                    sh.translate(pts[i])
                    fsh.append(sh)
                    obj.Shape = Part.makeCompound(fsh)

            # finalizing
            
            else:
                if base:
                    if not base.isNull():
                        if base.isValid() and base.Solids:
                            if base.Volume < 0:
                                base.reverse()
                            if base.Volume < 0:
                                FreeCAD.Console.PrintError(str(translate("Arch","Couldn't compute the wall shape")))
                                return
                            base = base.removeSplitter()
                            obj.Shape = base
                if not DraftGeomUtils.isNull(pl):
                    obj.Placement = pl
    
class _ViewProviderStructure(ArchComponent.ViewProviderComponent):
    "A View Provider for the Structure object"

    def __init__(self,vobj):
        ArchComponent.ViewProviderComponent.__init__(self,vobj)

    def getIcon(self):
        import Arch_rc
        return ":/icons/Arch_Structure_Tree.svg"

FreeCADGui.addCommand('Arch_Structure',_CommandStructure())
