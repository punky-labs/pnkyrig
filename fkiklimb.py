'''
import maya.cmds as cmds
import punky.shelfButtons as shelfButtons
import importlib

importlib.reload(shelfButtons)


'''
import sys
import maya.cmds as cmds
import importlib

from PySide6 import QtCore, QtGui, QtWidgets
from PySide6.QtUiTools import QUiLoader
from maya import OpenMayaUI as omui 
from shiboken6 import wrapInstance
from pathlib import Path

from . import rigshapes
importlib.reload(rigshapes)
from . import rigfunctions
importlib.reload(rigfunctions)


def getMayaWindow():
    mw_ptr = omui.MQtUtil.mainWindow()
    return wrapInstance(int(mw_ptr), QtWidgets.QMainWindow)

class MainWindow(QtWidgets.QMainWindow):
    def __init__(self, parent=None):
        if parent is None:
            parent = getMayaWindow()
        super(MainWindow, self).__init__(parent)
        
        self.limb = { "root":None,
                     "mid": None,
                     "end":None,
                     "pv":None}
        
        self.limb_name = None
        
        self.names = { "root": "shoulder", 
                      "mid": "elbow", 
                      "end" : "wrist", 
                      "pv" : "pv"}
        
        self.side = 'L'
        uiFilePath = Path(__file__).parent / 'ui' / 'fkikui.ui'

        loader = QUiLoader()
        uifile = QtCore.QFile(uiFilePath)
        uifile.open(QtCore.QFile.ReadOnly)
        self.ui = loader.load(uifile, None)
        uifile.close()

        self.ui.fk_color_btn.setStyleSheet("background-color: #ff0000")
        self.ui.ik_color_btn.setStyleSheet("background-color: #00ff00")
        self.ui.bind_color_btn.setStyleSheet("background-color: #0000ff")

        self.ui.btn_1.clicked.connect(self.click_make_locators)
        self.ui.btn_2.clicked.connect(self.click_build)

        self.ui.sel_1.clicked.connect(lambda checked=None, x=1: self.populate_selected(x))
        self.ui.sel_2.clicked.connect(lambda checked=None, x=2: self.populate_selected(x))
        self.ui.sel_3.clicked.connect(lambda checked=None, x=3: self.populate_selected(x))
        self.ui.sel_4.clicked.connect(lambda checked=None, x=4: self.populate_selected(x))

        self.ui.fk_color_btn.clicked.connect(lambda checked=None, x=self.ui.fk_color_btn: self.color_pick(x))
        self.ui.ik_color_btn.clicked.connect(lambda checked=None, x=self.ui.ik_color_btn: self.color_pick(x))
        self.ui.bind_color_btn.clicked.connect(lambda checked=None, x=self.ui.bind_color_btn: self.color_pick(x))

        self.ui.prefix_L.toggled.connect(lambda _ : setattr(self, 'side', 'L'))
        self.ui.prefix_R.toggled.connect(lambda _ : setattr(self, 'side', 'R'))

        self.ui.layout_hor.toggled.connect(lambda _ : setattr(self, 'orient', 'hor'))
        self.ui.layout_vert.toggled.connect(lambda _ : setattr(self, 'orient', 'vert'))

        self.ui_selects = (self.ui.sel_root, self.ui.sel_mid, self.ui.sel_end, self.ui.sel_pv)
        self.setProperty("saveWindowPref", True)



    def click_make_locators(self):
        x = 1
        if self.side == 'R':
            x = -1
        auto_locs = {
                'root' : (0, 0, 0),
                'mid' : (4*x, 0, -2),
                'end' : (8*x, 0, 0),
                'pv' : (4*x, 0, -4)
                }
        for (name, location), selects in zip(auto_locs.items(), self.ui_selects):
            build_name = cmds.spaceLocator( n=name+'_loc')
            if self.orient == 'hor':
                cmds.move(location[0], location[1], location[2], build_name)
            else:
                cmds.move(location[1], location[0]*-1, location[2]*-1, build_name)
            selects.setText(build_name[0])
            self.limb[name] = build_name[0]

    def click_build(self):
        for v in self.limb.values():
            if v == None:
                print("Please select all locators")
                return
        self.names["root"] = self.ui.name_root.text()
        self.names["mid"] = self.ui.name_mid.text()
        self.names["end"] = self.ui.name_end.text()
        self.names["pv"] = self.ui.name_pv.text()

        if self.ui.name_limb.text() == None:
            print("Please add limb name")
        else:
            self.limb_name = self.ui.name_limb.text()

        print(self.ui.bind_color_btn.palette().button().color().red())

        new_arm = rigfunctions.Limb(self.limb, 
                                    self.names, 
                                    name=self.limb_name,
                                    side=self.side,
                                    orient = self.orient,
                                    fk_color=self.RGBtoList(self.ui.fk_color_btn),
                                    ik_color=self.RGBtoList(self.ui.ik_color_btn),
                                    bind_color=self.RGBtoList(self.ui.bind_color_btn))
        new_arm.build_limb()

    def populate_selected(self, destination):
        selected = cmds.ls(sl=True) or []
        if not selected:
            print("No object selected")
            return
        if(destination==1):
            self.ui.sel_root.setText(selected[0])
            self.limb["root"] = selected[0]
        elif(destination==2):
            self.ui.sel_mid.setText(selected[0])
            self.limb["mid"] = selected[0]
        elif(destination==3):
            self.ui.sel_end.setText(selected[0])
            self.limb["end"] = selected[0]
        else:
            self.ui.sel_pv.setText(selected[0])
            self.limb["pv"] = selected[0]

    def color_pick(self, target):
        color = QtWidgets.QColorDialog.getColor()
        target.setStyleSheet("background-color: {}".format(color.name()))

    def RGBtoList(self, element):
        red = element.palette().button().color().red()/255
        green = element.palette().button().color().green()/255
        blue =  element.palette().button().color().blue()/255
        return (red, green, blue)


def launch():
    window = MainWindow()
    window.ui.show()