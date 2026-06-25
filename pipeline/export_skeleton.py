"""Export a rigged GLB's armature to JSON for the sprite-motion editor: every bone's name, parent,
head/tail in bone-space (world coords) + use_deform, plus the body-mesh bbox for sprite calibration.
Exact numbers, no transcription. Run: blender -b --python _export_skeleton.py -- <rigged>.glb <out>.json
"""
import bpy, sys, json, os
argv=sys.argv[sys.argv.index("--")+1:]
GLB=argv[0]; OUT=argv[1]
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=GLB)
arm=[o for o in bpy.context.scene.objects if o.type=="ARMATURE"][0]
M=arm.matrix_world
meshes=[o for o in bpy.context.scene.objects if o.type=="MESH" and len(o.data.vertices)>300]
mesh=max(meshes,key=lambda m:len(m.data.vertices))
vs=[mesh.matrix_world@v.co for v in mesh.data.vertices]
xs=[v.x for v in vs]; ys=[v.y for v in vs]; zs=[v.z for v in vs]
def r(v): return [round(v.x,4),round(v.y,4),round(v.z,4)]
bones=[]
for b in arm.data.bones:
    bones.append({"name":b.name,"parent":(b.parent.name if b.parent else None),
                  "head":r(M@b.head_local),"tail":r(M@b.tail_local),"deform":bool(b.use_deform)})
data={"name":os.path.splitext(os.path.basename(GLB))[0],"facing":"-Y",
      "bbox":{"x":[round(min(xs),4),round(max(xs),4)],"y":[round(min(ys),4),round(max(ys),4)],"z":[round(min(zs),4),round(max(zs),4)]},
      "bones":bones}
open(OUT,"w",encoding="utf-8").write(json.dumps(data,indent=1))
print(f"SKEL EXPORT {len(bones)} bones -> {OUT}", flush=True)
