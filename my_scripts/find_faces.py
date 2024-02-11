import collections
import math

import FreeCAD
import Part

doc = App.getDocument("first_example")
obj = doc.getObject("Slice006_child001")

def is_equals_with_tolerance(value, target, tolerance=0.001):
    return abs(target - value) <= tolerance


faces_with_angle = []
for f in obj.Shape.Faces:

    normal = f.normalAt(0, 0)
    ref_vector = FreeCAD.Vector(normal.x, normal.y, 0)
    if ref_vector.Length > 1e-6:
        ref_vector.normalize()
    else:
        ref_vector = FreeCAD.Vector(1, 0, 0)
    angle = math.degrees(normal.getAngle(ref_vector))
    if angle <= 1:
        Part.show(f, 'dropped_face_{}_angle_{}'.format(f, angle))
        continue
    faces_with_angle.append(f)

# Dict[Face,List[Face]]
face_with_collinear_normals = collections.defaultdict(list)

# Group faces by collinear normals
for f in faces_with_angle:
    face_with_collinear_normals[f].append(f)

    for f2 in faces_with_angle:
        cross_product = f.normalAt(0, 0) * f2.normalAt(0, 0)
        if is_equals_with_tolerance(abs(cross_product), 1):
            face_with_collinear_normals[f].append(f2)

# Find bottom faces
group_id = 0
result_faces = []
for _grp_face, faces_in_group in face_with_collinear_normals.items():
    if len(faces_in_group) > 1:
        faces_in_group.sort(key=lambda x: x.BoundBox.ZMin)

    grp_face = faces_in_group[0]
    group_id += 1
    Part.show(grp_face, 'face_{}'.format(grp_face))
