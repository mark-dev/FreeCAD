from math import degrees
import FreeCAD as App
import FreeCADGui as Gui
import Part

selection = Gui.Selection.getSelectionEx()[0]
face = selection.SubObjects[0]

u_min, u_max, v_min, v_max = face.ParameterRange
u = (u_min + u_max) / 2
v = (v_min + v_max) / 2
face_pt = face.valueAt(u, v)
face_normal = face.normalAt(u, v)
line = Part.makeLine(face_pt, face_pt + face_normal * 10)
Part.show(line)

ref_vector = App.Vector(face_normal.x, face_normal.y, 0) # Projection of face_normal.
if ref_vector.Length > 1e-6:
    ref_vector.normalize()
else:
    ref_vector = App.Vector(1, 0, 0)

line = Part.makeLine(face_pt, face_pt + ref_vector * 10)
Part.show(line)

print(degrees(face_normal.getAngle(ref_vector)))