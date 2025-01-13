import maya.cmds as cmds

def makeCross(name, size=1, plane='z'):
    points = [(-1.0, 3.0, 0.0), (1.0, 3.0, 0.0), (1.0, 1.0, 0.0), 
              (3.0, 1.0, 0.0), (3.0, -1.0, 0.0), (1.0, -1.0, 0.0), 
              (1.0, -3.0, 0.0), (-1.0, -3.0, 0.0), (-1.0, -1.0, 0.0), 
              (-3.0, -1.0, 0.0), (-3.0, 1.0, 0.0), (-1.0, 1.0, 0.0), 
              (-1.0, 3.0, 0.0)]
    thisCurve = cmds.curve(n=name, d=1, p=points)
    bounding = cmds.xform(thisCurve, q=True, bb=True)
    scale = size/(bounding[3]-bounding[0])
    cmds.scale((scale), (scale), (scale), thisCurve, absolute=True )
    if plane == 'x':
        cmds.rotate(0, '90deg', 0, thisCurve)
    elif plane == 'y':
        cmds.rotate('90deg', 0, 0, thisCurve)
    cmds.makeIdentity(thisCurve, apply=True, t=True, r=True, s=True)

    return thisCurve

def makeCross3D(name, size=1):
    crosses = []
    crosses.append(makeCross('crossz', size=size))
    crosses.append(makeCross('crossx', size=size, plane = 'x'))
    crosses.append(makeCross('crossy', size=size, plane = 'y'))
    parentShapes(crosses, name=name)


# Groups multiple shape nodes under a single node 
def parentShapes(selected=None, name=None):
    if selected is None:
        selected = cmds.ls(sl=True)

    shapeNodes = cmds.listRelatives(selected, s=True)
    if shapeNodes is not None:
        new_group = cmds.group(empty=True, n=name)
        for shapeNode in shapeNodes:
            cmds.parent(shapeNode, new_group, relative=True,  shape=True)
        for shapeObject in selected:
            cmds.delete(shapeObject)
    else:
        cmds.error('Please select only shape nodes')

def setRGBColor(ctrl, color = (1,1,1)):
    
    rgb = ("R","G","B")
    
    cmds.setAttr(ctrl + ".overrideEnabled",1)
    cmds.setAttr(ctrl + ".overrideRGBColors",1)
    
    for channel, color in zip(rgb, color):
        cmds.setAttr(ctrl + ".overrideColor%s" %channel, color)