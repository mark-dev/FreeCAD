import collections

import BOPTools.SplitFeatures
import CompoundTools.Explode
import FreeCAD
import Part


# obj = None  # your roof solid

def roof_magic(obj):
    bbox = obj.Shape.BoundBox
    box = doc.addObject("Part::Box", "myBox")
    box.Length = bbox.XLength
    box.Width = bbox.YLength
    box.Height = bbox.ZLength
    box.Placement = FreeCAD.Placement(bbox.Center, FreeCAD.Rotation(0, 0, 0))
    box.Placement = FreeCAD.Placement(FreeCAD.Vector(bbox.XMin, bbox.YMin, bbox.ZMin), FreeCAD.Rotation(0, 0, 0))

    Part.show(box.Shape, 'solid_bounding_box')

    j = BOPTools.SplitFeatures.makeSlice(name='Slice')
    j.Base = box
    j.Tools = [obj]
    j.Proxy.execute(j)
    j.purgeTouched()

    parts = CompoundTools.Explode.explodeCompound(j)[1]
    FreeCAD.ActiveDocument.recompute()
    parts.sort(key=lambda x: x.Shape.Area, reverse=True)

    print('Parts: {}'.format(parts))

    below_roof_part = parts[0]
    Part.show(below_roof_part.Shape, 'below_roof_part')

    # interest_faces = []
    # z_complanar = []
    # for f in below_roof_part.Shape.Faces:
    #     normal_vector = f.normalAt(0, 0)
    #     complanar_coords = [c for c in normal_vector if abs(c) in (0, 1)]
    #     is_plane_complanar = (len(complanar_coords) == 3)
    #
    #     z_part = normal_vector[2]
    #
    #     if abs(z_part) == 1:
    #         z_complanar.append(f)
    #
    #     if is_plane_complanar:
    #         continue
    #
    #     interest_faces.append(f)
    #
    # if len(z_complanar) > 1:
    #     z_complanar.sort(key=lambda x: x.BoundBox.ZMin)
    #     interest_faces.extend(z_complanar[1:])
    #
    # for idx, f in enumerate(interest_faces):
    #     Part.show(f, 'result_face_{}'.format(idx))


def is_equals_with_tolerance(value, target, tolerance=0.001):
    return abs(target - value) <= tolerance


def is_face_complanar_some_plane(f):
    normal_vector = f.normalAt(0, 0)
    complanar_coords = [
        c for c in normal_vector if
        is_equals_with_tolerance(abs(c), 0) or is_equals_with_tolerance(abs(c), 1)
    ]
    return (len(complanar_coords) == 3)


def roof_subvolume_generate(obj):
    # Dict[Face,List[Face]]
    face_with_collinear_normals = collections.defaultdict(list)

    # Group faces by collinear normals
    for f in obj.Shape.Faces:
        face_with_collinear_normals[f].append(f)

        for f2 in obj.Shape.Faces:
            cross_product = f.normalAt(0, 0) * f2.normalAt(0, 0)
            if is_equals_with_tolerance(abs(cross_product), 1):
                face_with_collinear_normals[f].append(f2)

    # Find bottom faces
    group_id = 0
    result_faces = []
    for _grp_face, faces_in_group in face_with_collinear_normals.items():
        filtered_candidates = [f for f in faces_in_group if not is_face_complanar_some_plane(f)]

        if not filtered_candidates:
            continue

        # If parallel faces found -> remain one (lowest by Z coordinate)
        if len(filtered_candidates) > 1:
            filtered_candidates.sort(key=lambda x: x.BoundBox.ZMin)

        f = filtered_candidates[0]
        Part.show(f, 'face_group_id_{}_{}'.format(group_id, hash(f)))

        result_faces.append(f)
        group_id += 1

    # Extrude each face & make solid compound
    solids = []
    for f in result_faces:
        sh = f.extrude(FreeCAD.Vector(0, 0, 10000000))
        solids.append(sh)

    r = Part.makeCompound(solids)
    Part.show(r, 'Result - compound for substract')

    return r, face_with_collinear_normals


# obj = doc.getObject("Fusion")
roof_subvolume_generate(obj)
