# main.py (Final Version)

try:
	from PySide6 import QtCore, QtGui, QtWidgets
	from shiboken6 import wrapInstance
except:
	from PySide2 import QtCore, QtGui, QtWidgets
	from shiboken2 import wrapInstance

import maya.OpenMayaUI as omui
import maya.cmds as cmds
import os
import json
import sys
import importlib

SCRIPT_DIRECTORY = os.path.dirname(__file__)
if SCRIPT_DIRECTORY not in sys.path:
	sys.path.append(SCRIPT_DIRECTORY)

import util_joint as utj
import util_curves as utc
importlib.reload(utj)
importlib.reload(utc)

import util_iconreload as uir
importlib.reload(uir)
from util_iconreload import get_maya_icon


#Library
LIBRARY_DIRECTORY = os.path.join(SCRIPT_DIRECTORY, 'LIBRARY')
os.makedirs(LIBRARY_DIRECTORY, exist_ok=True)

DEFAULT_JOINT_LIBRARY_PATH = os.path.join(LIBRARY_DIRECTORY, 'default_joints_library.json')
JOINT_LIBRARY_PATH = os.path.join(LIBRARY_DIRECTORY, 'joints_library.json')
CURVE_LIBRARY_PATH = os.path.join(LIBRARY_DIRECTORY, 'curves_library.json')
DEFAULT_CURVE_LIBRARY_PATH = os.path.join(LIBRARY_DIRECTORY, 'default_curves_library.json')

#########################################   FRAME   ###################################################
class FramLayout(QtWidgets.QWidget):
	def __init__(self, title="", parent=None):
		super().__init__(parent)
		self.namehead = QtWidgets.QToolButton(text=title, checkable=True, checked=True)
		self.namehead.setToolButtonStyle(QtCore.Qt.ToolButtonTextBesideIcon)
		self.namehead.setArrowType(QtCore.Qt.DownArrow)
		self.namehead.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
		self.namehead.toggled.connect(self.checkedToggled)
		self.frame = QtWidgets.QFrame()
		self.frame.setFrameShape(QtWidgets.QFrame.StyledPanel)
		self.frame.setFrameShadow(QtWidgets.QFrame.Raised)
		self.frameLayout = QtWidgets.QVBoxLayout(self.frame)
		self.mainLayout = QtWidgets.QVBoxLayout(self)
		self.mainLayout.setSpacing(0)
		self.mainLayout.setContentsMargins(0,0,0,0)
		self.mainLayout.addWidget(self.namehead)
		self.mainLayout.addWidget(self.frame)
	def checkedToggled(self, checked):
		self.namehead.setArrowType(QtCore.Qt.DownArrow if checked else QtCore.Qt.RightArrow)
		self.frame.setVisible(checked)
	def addWidget(self, widget):
		self.frameLayout.addWidget(widget)

#########################################   COLOR   ###################################################

# main.py

#########################################   COLOR   ###################################################

class ColorSliderWidget(QtWidgets.QWidget):
	def __init__(self, parent=None):
		super().__init__(parent)
		self.color_layout = QtWidgets.QHBoxLayout(self)
		self.color_layout.setContentsMargins(0, 0, 0, 0)
		self.color_layout.setSpacing(8)

		# <<< เราจะเก็บสีพื้นฐาน และสีสุดท้ายที่ปรับความสว่างแล้ว แยกกัน >>>
		self.base_color = QtGui.QColor(255, 255, 255) # สี default ขาว
		self.final_color = QtGui.QColor(255, 255, 255)

		self.color_show = QtWidgets.QPushButton()
		self.color_show.setFixedSize(50, 18)
		self.color_show.clicked.connect(self.pickColor)

		self.color_slider = QtWidgets.QSlider(QtCore.Qt.Horizontal)
		self.color_slider.setRange(0, 255) # Slider มีค่า 0 (มืด) ถึง 255 (สว่าง)
		self.color_slider.setValue(255) # เริ่มต้นที่สว่างสุด
		self.color_slider.valueChanged.connect(self.updateColor)

		self.color_layout.addWidget(QtWidgets.QLabel("Color"))
		self.color_layout.addWidget(self.color_show)
		self.color_layout.addWidget(self.color_slider)

		# <<< เรียกใช้ updateColor ตอนเริ่มเพื่อให้สีแสดงผลถูกต้อง >>>
		self.updateColor(self.color_slider.value())

	def updateColor(self, value):
		# <<< นี่คือส่วนที่แก้ไขหลัก >>>
		# เราจะใช้ระบบสี HSV (Hue, Saturation, Value)
		# โดย H, S จะมาจากสีที่เราเลือก (base_color)
		# และ V (ความสว่าง) จะมาจากค่าของ slider
		h, s, _, a = self.base_color.getHsv()
		
		# สร้างสีใหม่จากค่า H, S ของสีเดิม และ V จาก slider
		self.final_color = QtGui.QColor()
		self.final_color.setHsv(h, s, value, a)

		# อัปเดตสีที่ปุ่มแสดงผล
		r, g, b, _ = self.final_color.getRgb()
		self.color_show.setStyleSheet(f"background-color: rgb({r},{g},{b}); border: 1px solid #555;")

	def pickColor(self):
		self.selected_color = QtWidgets.QColorDialog.getColor(self.base_color, self, "Select Color")
		if self.selected_color.isValid():
			self.base_color = self.selected_color
			# <<< เมื่อเลือกสีใหม่ ให้เรียก updateColor เพื่อคำนวณความสว่างใหม่ทันที >>>
			self.updateColor(self.color_slider.value())

#########################################   MAIN   ###################################################
class JoinCurvesLibaryDialog(QtWidgets.QDialog):
	def __init__(self,parent=None):
		super().__init__(parent)
		self.setWindowTitle('Join&Curves Libary')
		self.resize(300,600)
		
		self.library_data = {}
		self.curve_library_data = {}
		self.default_presets = ["body", "arm", "leg", "hand"]
		
		#Layout หลัก
		self.mainLayout = QtWidgets.QVBoxLayout(self)
		self.setLayout(self.mainLayout)
		
		#2แม่ใหญ่
		self.setup_joint_ui()
		self.setup_curves_ui()
		
		self.mainLayout.addWidget(self.joint_frameLayout)
		self.mainLayout.addWidget(self.curves_frameLayout)
		self.mainLayout.addStretch()
		
		#โหลดข้อมูลทั้งหมด
		self.reload_all_libraries()

	def setup_joint_ui(self):
		self.joint_frameLayout = FramLayout("Joint Create")

		self.joint_listWidget = QtWidgets.QListWidget()
		self.joint_listWidget.setIconSize(QtCore.QSize(60,60))
		self.joint_listWidget.setViewMode(QtWidgets.QListView.IconMode)
		self.joint_listWidget.setMovement(QtWidgets.QListView.Static)
		self.joint_frameLayout.addWidget(self.joint_listWidget)
		
		self.buttonAddDel_LayoutJJ = QtWidgets.QHBoxLayout()
		self.buttonAddDel_LayoutJJ.addStretch()
		self.buttonAddJJ = QtWidgets.QPushButton('ADD')
		self.buttonDelJJ = QtWidgets.QPushButton('DEL')
		self.buttonAddDel_LayoutJJ.addWidget(self.buttonAddJJ)
		self.buttonAddDel_LayoutJJ.addWidget(self.buttonDelJJ)
		self.joint_frameLayout.frameLayout.addLayout(self.buttonAddDel_LayoutJJ)

		self.CheckboxGroup_LayoutJJ = QtWidgets.QHBoxLayout()
		self.Label_CreateCurvesJJ = QtWidgets.QLabel('Create Curves With Joint')
		self.Checkbox_CreateCurvesJJ = QtWidgets.QCheckBox()
		self.CheckboxGroup_LayoutJJ.addWidget(self.Label_CreateCurvesJJ)
		self.CheckboxGroup_LayoutJJ.addWidget(self.Checkbox_CreateCurvesJJ)
		self.CheckboxGroup_LayoutJJ.addStretch()
		self.joint_frameLayout.frameLayout.addLayout(self.CheckboxGroup_LayoutJJ)
		
		self.childJJ = QtWidgets.QWidget()
		self.childJJ_frameLayout = QtWidgets.QVBoxLayout(self.childJJ)
		self.childJJ_frameLayout.setContentsMargins(25,0,0,0)
		
		self.Checkbox_CreateGroupJJ = QtWidgets.QCheckBox('Group Curves')
		self.childJJ_frameLayout.addWidget(self.Checkbox_CreateGroupJJ)

		self.rotate_LayoutJJ = QtWidgets.QHBoxLayout()
		self.rotate_LayoutJJ.addWidget(QtWidgets.QLabel('Rotate'))
		self.rotate_LayoutJJX, self.rotate_LayoutJJY, self.rotate_LayoutJJZ = [QtWidgets.QDoubleSpinBox() for _ in range(3)]
		for w in [self.rotate_LayoutJJX, self.rotate_LayoutJJY, self.rotate_LayoutJJZ]: self.rotate_LayoutJJ.addWidget(w)
		self.childJJ_frameLayout.addLayout(self.rotate_LayoutJJ)

		self.scale_LayoutJJ = QtWidgets.QHBoxLayout()
		self.scale_LayoutJJ.addWidget(QtWidgets.QLabel('Scale'))
		self.scale_LayoutJJX, self.scale_LayoutJJY, self.scale_LayoutJJZ = [QtWidgets.QDoubleSpinBox() for _ in range(3)]
		for w in [self.scale_LayoutJJX, self.scale_LayoutJJY, self.scale_LayoutJJZ]: self.scale_LayoutJJ.addWidget(w)
		self.childJJ_frameLayout.addLayout(self.scale_LayoutJJ)

		self.color_LayoutJJ = QtWidgets.QHBoxLayout()
		self.colorSliderJJ = ColorSliderWidget()
		self.color_LayoutJJ.addWidget(self.colorSliderJJ)
		self.childJJ_frameLayout.addLayout(self.color_LayoutJJ)
		
		self.joint_frameLayout.frameLayout.addWidget(self.childJJ)
		self.childJJ.setEnabled(False)

		self.button_LayoutJJ = QtWidgets.QHBoxLayout()
		self.createButtonJJ = QtWidgets.QPushButton('Create')
		self.button_LayoutJJ.addWidget(self.createButtonJJ)
		self.joint_frameLayout.frameLayout.addLayout(self.button_LayoutJJ)

		self.buttonAddJJ.clicked.connect(self.add_joint_item)
		self.buttonDelJJ.clicked.connect(self.del_joint_item)
		self.createButtonJJ.clicked.connect(self.create_preset_item)
		self.Checkbox_CreateCurvesJJ.toggled.connect(self.toggle_createCurves)

	def setup_curves_ui(self):
		self.curves_frameLayout = FramLayout("Curves Create")

		self.curves_listWidget = QtWidgets.QListWidget()
		self.curves_listWidget.setIconSize(QtCore.QSize(60,60))
		self.curves_listWidget.setViewMode(QtWidgets.QListView.IconMode)
		self.curves_listWidget.setMovement(QtWidgets.QListView.Static)
		self.curves_frameLayout.addWidget(self.curves_listWidget)
		
		self.buttonAddDel_LayoutCC = QtWidgets.QHBoxLayout()
		self.buttonAddDel_LayoutCC.addStretch()
		self.buttonAddCC = QtWidgets.QPushButton('ADD')
		self.buttonDelCC = QtWidgets.QPushButton('DEL')
		self.buttonAddDel_LayoutCC.addWidget(self.buttonAddCC)
		self.buttonAddDel_LayoutCC.addWidget(self.buttonDelCC)
		self.curves_frameLayout.frameLayout.addLayout(self.buttonAddDel_LayoutCC)

		self.namesuffix_layout = QtWidgets.QHBoxLayout()
		self.name_label = QtWidgets.QLabel('NAME :')
		self.name_lineEdit = QtWidgets.QLineEdit()
		self.namesuffix_layout.addWidget(self.name_label)
		self.namesuffix_layout.addWidget(self.name_lineEdit)
		self.suffix_label = QtWidgets.QLabel('Suffix :')
		self.suffix_lineEdit = QtWidgets.QLineEdit()
		self.namesuffix_layout.addWidget(self.suffix_label)
		self.namesuffix_layout.addWidget(self.suffix_lineEdit)
		self.curves_frameLayout.frameLayout.addLayout(self.namesuffix_layout)
		
		self.CheckboxGroup_LayoutCC = QtWidgets.QHBoxLayout()
		self.Label_CreateCurvesCC = QtWidgets.QLabel('Group Curves')
		self.Checkbox_CreateCurvesCC = QtWidgets.QCheckBox()
		self.CheckboxGroup_LayoutCC.addWidget(self.Label_CreateCurvesCC)
		self.CheckboxGroup_LayoutCC.addWidget(self.Checkbox_CreateCurvesCC)
		self.CheckboxGroup_LayoutCC.addStretch()
		self.curves_frameLayout.frameLayout.addLayout(self.CheckboxGroup_LayoutCC)
		
		self.childCC = QtWidgets.QWidget()
		self.childCC_frameLayout = QtWidgets.QVBoxLayout(self.childCC)
		self.childCC_frameLayout.setContentsMargins(25,0,0,0)

		self.suffixNameGroup_layout = QtWidgets.QHBoxLayout()
		self.suffixNameGroup_layout_label = QtWidgets.QLabel('Suffix Name Group:')
		self.suffixNameGroup_layout_lineEdit = QtWidgets.QLineEdit()
		self.suffixNameGroup_layout.addWidget(self.suffixNameGroup_layout_label)
		self.suffixNameGroup_layout.addWidget(self.suffixNameGroup_layout_lineEdit)
		self.childCC_frameLayout.addLayout(self.suffixNameGroup_layout)
		
		self.curves_frameLayout.frameLayout.addWidget(self.childCC)
		self.childCC.setEnabled(False)

		self.rotate_LayoutCC = QtWidgets.QHBoxLayout()
		self.rotate_LayoutCC.addWidget(QtWidgets.QLabel('Rotate'))
		self.rotate_LayoutCCX, self.rotate_LayoutCCY, self.rotate_LayoutCCZ = [QtWidgets.QDoubleSpinBox() for _ in range(3)]
		for w in [self.rotate_LayoutCCX, self.rotate_LayoutCCY, self.rotate_LayoutCCZ]: self.rotate_LayoutCC.addWidget(w)
		self.curves_frameLayout.frameLayout.addLayout(self.rotate_LayoutCC)

		self.scale_LayoutCC = QtWidgets.QHBoxLayout()
		self.scale_LayoutCC.addWidget(QtWidgets.QLabel('Scale'))
		self.scale_LayoutCCX, self.scale_LayoutCCY, self.scale_LayoutCCZ = [QtWidgets.QDoubleSpinBox() for _ in range(3)]
		for w in [self.scale_LayoutCCX, self.scale_LayoutCCY, self.scale_LayoutCCZ]: self.scale_LayoutCC.addWidget(w)
		self.curves_frameLayout.frameLayout.addLayout(self.scale_LayoutCC)

		self.color_LayoutCC = QtWidgets.QHBoxLayout()
		self.colorSliderCC = ColorSliderWidget()
		self.color_LayoutCC.addWidget(self.colorSliderCC)
		self.curves_frameLayout.frameLayout.addLayout(self.color_LayoutCC)

		self.button_LayoutCC = QtWidgets.QHBoxLayout()
		self.createButtonCC = QtWidgets.QPushButton('Create')
		self.button_LayoutCC.addWidget(self.createButtonCC)
		self.curves_frameLayout.frameLayout.addLayout(self.button_LayoutCC)

		self.buttonAddCC.clicked.connect(self.add_curve_item)
		self.buttonDelCC.clicked.connect(self.del_curve_item)
		self.createButtonCC.clicked.connect(self.create_curve_item)
		self.Checkbox_CreateCurvesCC.toggled.connect(self.toggle_GroupCurves)

	def reload_all_libraries(self):
		#โหลดข้อมูลจากไฟล์ JSON 
		print("\n--- Reloading all libraries ---")
		self.joint_listWidget.clear()
		self.curves_listWidget.clear()

		default_data = utj.load_default_library(self, DEFAULT_JOINT_LIBRARY_PATH)
		user_data = utj.load_library(self, JOINT_LIBRARY_PATH)
		self.library_data = {**default_data, **user_data}
		
		default_curve_data = utc.load_default_curve_library(self, DEFAULT_CURVE_LIBRARY_PATH)
		user_curve_data = utc.load_curve_library(self, CURVE_LIBRARY_PATH)
		self.curve_library_data = {**default_curve_data, **user_curve_data}
		print("--- Reload complete ---")

	def add_joint_item(self):
		utj.add_Joint_WidgetsItem(self)
		utj.save_Library(self, JOINT_LIBRARY_PATH)

	def del_joint_item(self):
		utj.del_Joint_WidgetsItem(self)
		utj.save_Library(self, JOINT_LIBRARY_PATH)

	def create_preset_item(self):
		utj.create_from_preset(self)

	def add_curve_item(self):
		selection = cmds.ls(sl=True)
		if not selection: return cmds.warning("Please select a curve to add.")
		for sel in selection:
			shape = cmds.listRelatives(sel, s=True, type='nurbsCurve')
			if shape and not self.curves_listWidget.findItems(sel, QtCore.Qt.MatchExactly):
				item = QtWidgets.QListWidgetItem(sel)
				item.setIcon(get_maya_icon("out_curve.png"))
				self.curves_listWidget.addItem(item)
		utc.save_curve_library(self, CURVE_LIBRARY_PATH)
		self.reload_all_libraries()

	def del_curve_item(self):
		selected_items = self.curves_listWidget.selectedItems()
		if not selected_items: return
		for item in selected_items:
			self.curves_listWidget.takeItem(self.curves_listWidget.row(item))
		utc.save_curve_library(self, CURVE_LIBRARY_PATH)
		self.reload_all_libraries()

	def create_curve_item(self):
		utc.create_curve_from_preset(self)
	
	def toggle_createCurves(self, checked):
		self.childJJ.setEnabled(checked)

	def toggle_GroupCurves(self, checked):
		self.childCC.setEnabled(checked)

#########################################   RUN UI   ###################################################
def run():
	global ui
	try:
		ui.close()
	except:
		pass
	ptr = wrapInstance(int(omui.MQtUtil.mainWindow()),QtWidgets.QWidget)
	ui = JoinCurvesLibaryDialog(parent=ptr)
	ui.show()