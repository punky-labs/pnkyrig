import importlib

import maya.cmds as cmds
from . import rigshapes
importlib.reload(rigshapes)

class Limb():
    def __init__(self, locators, 
                 names, 
                 name='limb', 
                 side='R',
                 orient='hor',
                 bind_color = (0,1,0), 
                 ik_color = (1,0,0), 
                 fk_color = (0,0,1)
                 ):

        self.locators = locators
        self.names = names
        self.side = side+'_'
        self.name = name
        self.bind_color = bind_color
        self.ik_color = ik_color
        self.fk_color = fk_color

        print(f'Side {self.side}')


    def build_limb(self):
        self.master_ctl = self.create_master_ctl()
        
        self.fk_chain = self.build_chain(suffix='FK', orient=True, color=self.fk_color)
        self.ik_chain = self.build_chain(suffix='IK', orient=True, color=self.ik_color)
        self.bind_chain = self.build_chain(suffix='bind', orient=True, color=self.bind_color)
        self.build_FK()
        self.build_IK()
        self.heirachy()
        self.cleanup()
        self.create_blend()



    def build_chain(self, suffix, orient=True, color=(1,0,0)):
        print('Building Limb section - {}'.format(suffix))
        chain = []
        
        root_name = self.side+self.names['root']+"_"+suffix+"_JNT"
        positions = {loc: cmds.xform(self.locators[loc], q=1, t=1) for loc in ['root', 'mid', 'end']}
        root_p = positions['root']
        mid_name = self.side+self.names['mid']+"_"+suffix+"_JNT"
        mid_p = positions['mid']
        end_name = self.side+self.names['end']+"_"+suffix+"_JNT"
        end_p = positions['end']
        cmds.select(d=True)  # Deselect all to ensure joints are created independently
        cmds.select( d=True )
        chain.append(cmds.joint( p=root_p, n=root_name ))
        chain.append(cmds.joint( p=mid_p, n=mid_name ))
        chain.append(cmds.joint( p=end_p, n=end_name ))

        joints_to_color = [(jnt, color) for jnt in chain]
        rigshapes.setRGBColor(joints_to_color)

        if orient:
            cmds.joint( root_name, e=True, zso=True, oj='xyz' , sao='yup')
            cmds.joint( mid_name, e=True, zso=True, oj='xyz' , sao='yup')
            cmds.joint( end_name, e=True, zso=True, oj='none')
        
        return chain


    def locate(self, to_name, from_name, rot=False, trans=True, freeze=False):
        if trans:
            cmds.delete(cmds.pointConstraint(to_name, from_name))
        if rot:
            cmds.delete(cmds.orientConstraint(to_name, from_name))
        if freeze:
            cmds.makeIdentity(from_name, apply=True, translate=True, rotate=True,
                              scale=True, normal=False)

    def parent_chain(self, chain):
        parent = None
        for i, obj in enumerate(chain):
            if i== 0:
                parent = obj
            else:
                print(f"Parenting {obj[0]} to {parent}")
                cmds.parent(obj, parent)
                parent = obj

    def build_FK(self):
        self.FK_ctls = []

        # Create FK rig
        for joint in self.fk_chain:
            ctl_name = joint.replace('_JNT', '_CTL')
            ctl = cmds.circle(name = ctl_name, nr=(1, 0, 0), c=(0, 0, 0))
            self.locate(joint, ctl, rot=True, trans=True, freeze=False)
            self.FK_ctls.append(ctl[0])
            cmds.orientConstraint(ctl, joint)
            rigshapes.setRGBColor(ctl[0], color=self.fk_color)

        self.parent_chain(self.FK_ctls)
    
    def build_IK(self):
        
        # create IKH
        self.ikh = cmds.ikHandle(name='_IKH',
                            startJoint=self.ik_chain[0],
                            endEffector=self.ik_chain[-1], sticky='sticky',
                            solver='ikRPsolver', setupForRPsolver=True)[0]
        self.ik_end = cmds.circle(name = self.ik_chain[-1].replace('_JNT', '_CTL'), nr=(1, 0, 0), 
                            c=(0, 0, 0), d=1, s=4)
        self.locate(self.ik_chain[-1], self.ik_end, rot=False, trans=True, freeze=True)
        cmds.parentConstraint(self.ik_end, self.ikh, mo=True)
        rigshapes.setRGBColor(self.ik_end[0], color=self.ik_color)

        pv_name = self.side+self.names['pv']+"_IK_CTL"
        self.pv = cmds.circle(name = pv_name, nr=(1, 0, 0), 
                            c=(0, 0, 0), d=1, s=3)
        cmds.rotate( '90deg', 0, 0, self.pv, r=True )
        self.locate(self.locators['pv'], self.pv, rot=False, trans=True, freeze=True)
        cmds.poleVectorConstraint(self.pv, self.ikh)
        rigshapes.setRGBColor(self.pv[0], color=self.ik_color)

        cmds.orientConstraint(self.ik_chain[-1], self.ik_end)

    def heirachy(self):
        root_grp = cmds.group( em=True, name=self.side+self.name.upper() )

        cmds.parent(self.master_ctl, root_grp)

        fk_ctls_grp = cmds.group( em=True, name=self.side+self.name+"_FK_CTL_GRP" )
        cmds.parent(self.FK_ctls[0], fk_ctls_grp)
        
        ik_ctls_grp = cmds.group( em=True, name=self.side+self.name+"_IK_CTL_GRP" )
        cmds.parent(self.ik_end[0], ik_ctls_grp)
        cmds.parent(self.pv[0], ik_ctls_grp)
        
        skeleton_grp = cmds.group( em=True, name=self.side+self.name+"_JNT_GRP" )
        cmds.parent(self.fk_chain[0], skeleton_grp)
        cmds.parent(self.ik_chain[0], skeleton_grp)
        cmds.parent(self.bind_chain[0], skeleton_grp)
        cmds.parent(self.ikh, skeleton_grp)

        cmds.parent(fk_ctls_grp, root_grp)
        cmds.parent(ik_ctls_grp, root_grp)
        cmds.parent(skeleton_grp, root_grp)


    def cleanup(self):
        self.lock_and_hide(self.FK_ctls, attribute_list=['translate', 'scale', 'visibility'])
        self.lock_and_hide(self.ik_end[0], attribute_list=['rotate', 'scale', 'visibility'])
        self.lock_and_hide(self.pv[0], attribute_list=['rotate', 'scale', 'visibility'])

    def lock_and_hide(self, nodes, attribute_list=None):
        if not attribute_list:
            attribute_list = ['translate', 'rotate', 'scale', 'visibility']

        if not isinstance(nodes, list):
            nodes = [nodes]

        for node in nodes:
            for attr in attribute_list:
                if any(t == attr for t in ['translate', 'rotate', 'scale']):
                    [cmds.setAttr(node + '.' + attr + axis, lock=True, keyable=False) for axis in 'XYZ']
                else:
                    cmds.setAttr(node + '.' + attr, lock=True, keyable=False)

    def create_master_ctl(self, color=(1,1,0)):
        master_ctl = rigshapes.makeCross(self.side+'MASTER_CTL')
        self.locate(self.locators['mid'], master_ctl)
        cmds.move(0, 2, 0, master_ctl, relative=True)
        cmds.addAttr(master_ctl, keyable = True, shortName='ikblend', longName='Blend', defaultValue=1.0, minValue=0, maxValue=1 )
        self.lock_and_hide(master_ctl, attribute_list=['translate', 'rotate', 'scale', 'visibility'])
        rigshapes.setRGBColor(master_ctl, color=color)
        
        return master_ctl


    def create_blend(self):

        for ik, fk, bind in zip(self.ik_chain, self.fk_chain, self.bind_chain):
            for attr in ['translate', 'rotate', 'scale']:
                blend_node = cmds.createNode('blendColors',
                                      n=bind.replace('bind_JNT', attr + '_BCN'))
                cmds.connectAttr(ik + '.' + attr, blend_node + '.color1')
                cmds.connectAttr(fk + '.' + attr, blend_node + '.color2')
                cmds.connectAttr(self.master_ctl + '.ikblend', blend_node + '.blender')
                cmds.connectAttr(blend_node + '.output', bind + '.' + attr)
        

