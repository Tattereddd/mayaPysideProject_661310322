try:
	from PySide6 import QtCore, QtGui, QtWidgets
	from shiboken6 import wrapInstance
except:
	from PySide2 import QtCore, QtGui, QtWidgets
	from shiboken2 import wrapInstance

import maya.OpenMayaUI as omui
import maya.cmds as cmds
import os

import importlib
from.import util_joint as utj
importlib.reload(utj)

ICON_PATH = os.path.abspath(os.path.join(os.path.dirname('C:/Users/Tran/Documentsmaya/2024/scripts/mayaPysideProject_661310322/)'),'test'))

#########################################   FRAME   ###################################################

class FramLayout(QtWidgets.QWidget):
	def __init__(self, title="", parent=None):
		super().__init__(parent)

		#สร้างตรงหัวชื่อกับลูกศรเปิดปิดแล้วเชื่อมกับdefเช็คtoggleเปิดปิด
		self.namehead = QtWidgets.QToolButton(text=title, checkable=True, checked=True)
		self.namehead.setToolButtonStyle(QtCore.Qt.ToolButtonTextBesideIcon)
		self.namehead.setArrowType(QtCore.Qt.DownArrow)
		self.namehead.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
		self.namehead.toggled.connect(self.checkedToggled)

		#frameใส่ของด้านใน
		self.frame = QtWidgets.QFrame()
		self.frame.setFrameShape(QtWidgets.QFrame.StyledPanel)
		self.frame.setFrameShadow(QtWidgets.QFrame.Raised)
		self.frameLayout = QtWidgets.QVBoxLayout(self.frame)

		#เอาเข้าmainlayout
		self.mainLayout = QtWidgets.QVBoxLayout(self)
		self.mainLayout.setSpacing(0)
		self.mainLayout.setContentsMargins(0,0,0,0) 
		self.mainLayout.addWidget(self.namehead)
		self.mainLayout.addWidget(self.frame)

	#เช็คtoggleเปิดปิด	
	def checkedToggled(self, checked):
		self.namehead.setArrowType(QtCore.Qt.DownArrow if checked else QtCore.Qt.RightArrow)
		self.frame.setVisible(checked)

	def addWidget(self, widget):
		self.frameLayout.addWidget(widget)


#########################################   COLOR   ###################################################

class ColorSliderWidget(QtWidgets.QWidget):
	colorChanged = QtCore.Signal(float)  # ส่งค่า float 0.0-1.0 ออกมา

	####################ตั้งค่าเริ่มต้นสี
	def __init__(self, parent=None):
		super().__init__(parent)

		self.color_layout = QtWidgets.QHBoxLayout(self)
		self.color_layout.setContentsMargins(0, 0, 0, 0)
		self.color_layout.setSpacing(8)

		self.base_color = QtGui.QColor(128, 128, 128)

		#################### Label แสดงสี
		self.color_show = QtWidgets.QPushButton()
		self.color_show.setFixedSize(50, 18)
		self.color_show.setStyleSheet("background-color: rgb(128,128,128); border: 1px solid #555;")
		self.color_show.clicked.connect(self.pickColor)

		#################### Slider ควบคุมค่า 0–255
		self.color_slider = QtWidgets.QSlider(QtCore.Qt.Horizontal)
		self.color_slider.setRange(0, 255)
		self.color_slider.setValue(128)
		self.color_slider.valueChanged.connect(self.updateColor)

		#################### เอาเข้าแม่
		self.color_layout.addWidget(QtWidgets.QLabel("Color"))
		self.color_layout.addWidget(self.color_show)
		self.color_layout.addWidget(self.color_slider)

	#################### updateสี
	def updateColor(self, value):
		self.up_color = value/255.0
		r = int(self.base_color.red() * self.up_color)
		g = int(self.base_color.green() * self.up_color)
		b = int(self.base_color.blue() * self.up_color)

		# ปรับสีใน preview label
		self.color_show.setStyleSheet(f"background-color: rgb({r},{g},{b}); border: 1px solid #555;")
		self.colorChanged.emit(self.up_color)  # ส่งค่า normalized ออกไปถ้าต้องใช้ต่อ

	#################### แสดงสีที่เลือกs
	def pickColor(self):
		self.selected_color = QtWidgets.QColorDialog.getColor(self.base_color, self, "Select Color")
		if self.selected_color.isValid():
			self.base_color = self.selected_color
			self.updateColor(self.color_slider.value())
				


#########################################   MAIN   ###################################################
class JoinCurvesLibaryDialog(QtWidgets.QDialog):
	def __init__(self,parent=None):
		super().__init__(parent)

		self.setWindowTitle('Join&Curves Libary')
		self.resize(300,500)

		self.mainLayout = QtWidgets.QVBoxLayout()
		self.setLayout(self.mainLayout)

		################################################################   JOINT
		self.joint_frameLayout = FramLayout("Joint Create")

		####################ที่เก็บของ
		self.joint_listWidget = QtWidgets.QListWidget()
		self.joint_listWidget.setIconSize(QtCore.QSize(60,60))
		self.joint_listWidget.setSpacing(5)
		self.joint_listWidget.setViewMode(QtWidgets.QListView.IconMode)
		self.joint_listWidget.setMovement(QtWidgets.QListView.Static)
		self.joint_listWidget.setResizeMode(QtWidgets.QListView.Adjust)
		self.joint_frameLayout.addWidget(self.joint_listWidget)

		####################ปุ่มaddกับdel
		self.buttonAddDel_LayoutJJ = QtWidgets.QHBoxLayout()
		self.buttonAddDel_LayoutJJ.addStretch()
		self.buttonAddJJ = QtWidgets.QPushButton('ADD')
		self.buttonAddJJ.clicked.connect(self.add_joint_item)
		self.buttonDelJJ = QtWidgets.QPushButton('DEL')
		self.buttonAddJJ.clicked.connect(self.del_joint_item)
		self.buttonAddDel_LayoutJJ.addWidget(self.buttonAddJJ)
		self.buttonAddDel_LayoutJJ.addWidget(self.buttonDelJJ)
		self.joint_frameLayout.frameLayout.addLayout(self.buttonAddDel_LayoutJJ)

		self.add_default_joint_item("body", "cone.png")
		self.add_default_joint_item("arm", "cone.png")
		self.add_default_joint_item("leg", "cone.png")
		self.add_default_joint_item("hand", "cone.png")

		####################Check boxใหญ่สุด
		self.CheckboxGroup_LayoutJJ = QtWidgets.QHBoxLayout()
		self.Label_CreateCurvesJJ = QtWidgets.QLabel('Create Curves With Joint') #แยกชื่อ
		self.Checkbox_CreateCurvesJJ = QtWidgets.QCheckBox() #แยกcheckbox
		self.CheckboxGroup_LayoutJJ.addWidget(self.Label_CreateCurvesJJ) #จับมารวมกันถ้าไม่แยกcheckboxมันจะไปอยู่หลังข้อความ
		self.CheckboxGroup_LayoutJJ.addWidget(self.Checkbox_CreateCurvesJJ)#จับมารวมกันถ้าไม่แยกcheckboxมันจะไปอยู่หลังข้อความ
		self.CheckboxGroup_LayoutJJ.addStretch()
		self.joint_frameLayout.frameLayout.addLayout(self.CheckboxGroup_LayoutJJ)

		####################ใส่ลูกเข้าด้านใน + จัดlayout
		self.childJJ = QtWidgets.QWidget()
		self.childJJ_frameLayout = QtWidgets.QVBoxLayout(self.childJJ)
		self.childJJ_frameLayout.setContentsMargins(25,0,0,0)
		self.childJJ_frameLayout.setSpacing(4)

		self.Checkbox_CreateGroupJJ = QtWidgets.QCheckBox('Group Curves')
		self.childJJ_frameLayout.addWidget(self.Checkbox_CreateGroupJJ)

		self.rotate_LayoutJJ = QtWidgets.QHBoxLayout()
		self.rotate_LayoutJJ.addWidget(QtWidgets.QLabel('Rotate'))
		self.rotate_LayoutJJX = QtWidgets.QDoubleSpinBox(); self.rotate_LayoutJJX.setRange(0,360)
		self.rotate_LayoutJJY = QtWidgets.QDoubleSpinBox(); self.rotate_LayoutJJY.setRange(0,360)
		self.rotate_LayoutJJZ = QtWidgets.QDoubleSpinBox(); self.rotate_LayoutJJZ.setRange(0,360)
		self.rotate_LayoutJJ.addWidget(self.rotate_LayoutJJX)
		self.rotate_LayoutJJ.addWidget(self.rotate_LayoutJJY)
		self.rotate_LayoutJJ.addWidget(self.rotate_LayoutJJZ)
		self.childJJ_frameLayout.addLayout(self.rotate_LayoutJJ)

		self.scale_LayoutJJ = QtWidgets.QHBoxLayout()
		self.scale_LayoutJJ.addWidget(QtWidgets.QLabel('Scale'))
		self.scale_LayoutJJX = QtWidgets.QDoubleSpinBox(); self.scale_LayoutJJX.setRange(0,999)
		self.scale_LayoutJJY = QtWidgets.QDoubleSpinBox(); self.scale_LayoutJJY.setRange(0,999)
		self.scale_LayoutJJZ = QtWidgets.QDoubleSpinBox(); self.scale_LayoutJJZ.setRange(0,999)
		self.scale_LayoutJJ.addWidget(self.scale_LayoutJJX)
		self.scale_LayoutJJ.addWidget(self.scale_LayoutJJY)
		self.scale_LayoutJJ.addWidget(self.scale_LayoutJJZ)
		self.childJJ_frameLayout.addLayout(self.scale_LayoutJJ)

		####################เรียกใช้color
		self.color_LayoutJJ = QtWidgets.QHBoxLayout()
		self.colorSliderJJ = ColorSliderWidget()
		self.color_LayoutJJ.addWidget(self.colorSliderJJ)
		self.childJJ_frameLayout.addLayout(self.color_LayoutJJ)

		####################เอาลูกมาใส่แม่ใหญ่
		self.joint_frameLayout.frameLayout.addWidget(self.childJJ)
		self.childJJ.setEnabled(False)

		####################เชื่อมเปิดปิด
		self.Checkbox_CreateCurvesJJ.toggled.connect(self.toggle_createCurves)
		####################ปุ่ม
		self.button_LayoutJJ = QtWidgets.QHBoxLayout()
		self.joint_frameLayout.frameLayout.addLayout(self.button_LayoutJJ)
		self.createButtonJJ = QtWidgets.QPushButton('Create')
		self.button_LayoutJJ.addWidget(self.createButtonJJ)


################################################################   CURVES  
		#แม่ใหญ่คนที่ 2 
		self.curves_frameLayout = FramLayout("Curves Create")

		####################ที่เก็บของ
		self.curves_listWidget = QtWidgets.QListWidget()
		self.curves_listWidget.setIconSize(QtCore.QSize(60,60))
		self.curves_listWidget.setSpacing(5)
		self.curves_listWidget.setViewMode(QtWidgets.QListView.IconMode)
		self.curves_listWidget.setMovement(QtWidgets.QListView.Static)
		self.curves_listWidget.setResizeMode(QtWidgets.QListView.Adjust)
		self.curves_frameLayout.addWidget(self.curves_listWidget)

		####################ปุ่มadd del
		self.buttonAddDel_LayoutCC=QtWidgets.QHBoxLayout()
		self.buttonAddDel_LayoutCC.addStretch()
		self.curves_frameLayout.frameLayout.addLayout(self.buttonAddDel_LayoutCC)
		self.buttonAddCC = QtWidgets.QPushButton('ADD')
		self.buttonDelCC = QtWidgets.QPushButton('DEL')
		self.buttonAddDel_LayoutCC.addWidget(self.buttonAddCC)
		self.buttonAddDel_LayoutCC.addWidget(self.buttonDelCC)

		####################กล่องตั้งชื่อ
		self.namesuffix_layout = QtWidgets.QHBoxLayout()
		self.name_label = QtWidgets.QLabel('NAME :')
		self.name_lineEdit = QtWidgets.QLineEdit()
		self.namesuffix_layout.addWidget(self.name_label)
		self.namesuffix_layout.addWidget(self.name_lineEdit)
		#
		self.suffix_label = QtWidgets.QLabel('Suffix :')
		self.suffix_lineEdit = QtWidgets.QLineEdit()
		self.namesuffix_layout.addWidget(self.suffix_label)
		self.namesuffix_layout.addWidget(self.suffix_lineEdit)
		#
		self.curves_frameLayout.frameLayout.addLayout(self.namesuffix_layout)

		####################Checkbox ใหญ่สุด
		self.CheckboxGroup_LayoutCC = QtWidgets.QHBoxLayout()
		self.Label_CreateCurvesCC = QtWidgets.QLabel('Group Curves') #แยกชื่อ
		self.Checkbox_CreateCurvesCC = QtWidgets.QCheckBox() #แยกcheckbox
		self.CheckboxGroup_LayoutCC.addWidget(self.Label_CreateCurvesCC) #จับมารวมกันถ้าไม่แยกcheckboxมันจะไปอยู่หลังข้อความ
		self.CheckboxGroup_LayoutCC.addWidget(self.Checkbox_CreateCurvesCC)#จับมารวมกันถ้าไม่แยกcheckboxมันจะไปอยู่หลังข้อความ
		self.CheckboxGroup_LayoutCC.addStretch()
		self.curves_frameLayout.frameLayout.addLayout(self.CheckboxGroup_LayoutCC)

		####################สร้างที่เก็บลูก + จัดLayout
		self.childCC = QtWidgets.QWidget()
		self.childCC_frameLayout = QtWidgets.QVBoxLayout(self.childCC)
		self.childCC_frameLayout.setContentsMargins(25,0,0,0)
		self.childCC_frameLayout.setSpacing(4)

		####################ที่เก็บของลูก ช่องพิมชื่อgroup
		self.suffixNameGroup_layout = QtWidgets.QHBoxLayout()
		self.suffixNameGroup_layout_label = QtWidgets.QLabel('Suffix Name Group:')
		self.suffixNameGroup_layout_lineEdit = QtWidgets.QLineEdit()		

		self.suffixNameGroup_layout.addWidget(self.suffixNameGroup_layout_label)
		self.suffixNameGroup_layout.addWidget(self.suffixNameGroup_layout_lineEdit)
		self.childCC_frameLayout.addLayout(self.suffixNameGroup_layout)
		
		####################ที่เก็บของเอาลูกใส่แม่ใหญ่
		self.childCC.setLayout(self.childCC_frameLayout) 
		self.curves_frameLayout.frameLayout.addWidget(self.childCC)
		self.childCC.setEnabled(False)

		self.rotate_LayoutCC = QtWidgets.QHBoxLayout()
		self.rotate_LayoutCC.addWidget(QtWidgets.QLabel('Rotate'))
		self.rotate_LayoutCCX = QtWidgets.QDoubleSpinBox(); self.rotate_LayoutCCX.setRange(0,360)
		self.rotate_LayoutCCY = QtWidgets.QDoubleSpinBox(); self.rotate_LayoutCCY.setRange(0,360)
		self.rotate_LayoutCCZ = QtWidgets.QDoubleSpinBox(); self.rotate_LayoutCCZ.setRange(0,360)
		self.rotate_LayoutCC.addWidget(self.rotate_LayoutCCX)
		self.rotate_LayoutCC.addWidget(self.rotate_LayoutCCY)
		self.rotate_LayoutCC.addWidget(self.rotate_LayoutCCZ)
		self.curves_frameLayout.frameLayout.addLayout(self.rotate_LayoutCC)

		self.scale_LayoutCC = QtWidgets.QHBoxLayout()
		self.scale_LayoutCC.addWidget(QtWidgets.QLabel('Scale'))
		self.scale_LayoutCCX = QtWidgets.QDoubleSpinBox(); self.scale_LayoutCCX.setRange(0,999)
		self.scale_LayoutCCY = QtWidgets.QDoubleSpinBox(); self.scale_LayoutCCY.setRange(0,999)
		self.scale_LayoutCCZ = QtWidgets.QDoubleSpinBox(); self.scale_LayoutCCZ.setRange(0,999)
		self.scale_LayoutCC.addWidget(self.scale_LayoutCCX)
		self.scale_LayoutCC.addWidget(self.scale_LayoutCCY)
		self.scale_LayoutCC.addWidget(self.scale_LayoutCCZ)
		self.curves_frameLayout.frameLayout.addLayout(self.scale_LayoutCC)

		####################เรียกใช้color
		self.color_LayoutCC = QtWidgets.QHBoxLayout()
		self.colorSliderCC = ColorSliderWidget()
		self.color_LayoutCC.addWidget(self.colorSliderCC)
		self.curves_frameLayout.frameLayout.addLayout(self.color_LayoutCC)

		####################เชื่อมcheck checkbox
		self.Checkbox_CreateCurvesCC.toggled.connect(self.toggle_GroupCurves)

		####################ปุ่ม
		self.button_LayoutCC = QtWidgets.QHBoxLayout()
		self.curves_frameLayout.frameLayout.addLayout(self.button_LayoutCC)
		self.createButtonCC = QtWidgets.QPushButton('Create')
		self.button_LayoutCC.addWidget(self.createButtonCC)

		##############################   เอา2แม่ใหญ่ใส่พ่อ    

		self.mainLayout.addWidget(self.joint_frameLayout)
		self.mainLayout.addWidget(self.curves_frameLayout)
		self.mainLayout.addStretch()

#################################  check checkbox    
	def toggle_createCurves(self, checked):
		self.childJJ.setEnabled(checked)

	def toggle_GroupCurves(self, checked):
		self.childCC.setEnabled(checked)

	def add_default_joint_item(self, name, icon_name):
		item = QtWidgets.QListWidgetItem(name)
		full_icon_path = os.path.join(ICON_PATH, icon_name)	
		icon = QtGui.QIcon(ICON_PATH if cmds.file(ICON_PATH, q=True, ex=True) else ":/kinJoint.png")
		item.setIcon(icon)
		self.joint_listWidget.addItem(item)

	def add_joint_item(self):
		utj.add_Joint_WidgetsItem(self.joint_listWidget)

	def del_joint_item(self):
		utj.del_Joint_WidgetsItem(self.joint_listWidget)


#################################  RUN UI    #########################################

def run():
	global ui

	try:
		ui.close
	except:
		pass

	ptr = wrapInstance(int(omui.MQtUtil.mainWindow()),QtWidgets.QWidget)
	ui = JoinCurvesLibaryDialog(parent=ptr)
	ui.show()