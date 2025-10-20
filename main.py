#########################################   IMPORT   ###################################################

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
import glob
import importlib
import util_joint as utj
import util_curves as utc
import util_addicon as uai
importlib.reload(utj)
importlib.reload(utc)
importlib.reload(uai)
from util_addicon import playblast_icon, sanitize_name

#########################################   LIBRARY   ###################################################

SCRIPT_DIRECTORY = os.path.dirname(__file__)
if SCRIPT_DIRECTORY not in sys.path:
	sys.path.append(SCRIPT_DIRECTORY)

LIBRARY_DIRECTORY = os.path.join(SCRIPT_DIRECTORY, 'LIBRARY')
os.makedirs(LIBRARY_DIRECTORY, exist_ok=True)

CURVE_ICONS_DIRECTORY = os.path.join(SCRIPT_DIRECTORY, 'icons', 'icons_curves')
JOINT_ICONS_DIRECTORY = os.path.join(SCRIPT_DIRECTORY, 'icons', 'icons_joint')

os.makedirs(CURVE_ICONS_DIRECTORY, exist_ok=True)
os.makedirs(JOINT_ICONS_DIRECTORY, exist_ok=True)

DEFAULT_JOINT_LIBRARY_PATH = os.path.join(LIBRARY_DIRECTORY, 'default_joints_library.json')
DEFAULT_CURVE_LIBRARY_PATH = os.path.join(LIBRARY_DIRECTORY, 'default_curves_library.json')

JOINT_LIBRARY_PATH = os.path.join(LIBRARY_DIRECTORY, 'joints_library.json')
CURVE_LIBRARY_PATH = os.path.join(LIBRARY_DIRECTORY, 'curves_library.json')

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

class ColorSliderWidget(QtWidgets.QWidget):
	def __init__(self, parent=None):
		super().__init__(parent)
		self.color_layout = QtWidgets.QHBoxLayout(self)
		self.color_layout.setContentsMargins(0, 0, 0, 0)
		self.color_layout.setSpacing(8)

		self.base_color = QtGui.QColor(255, 255, 255) # สี default ขาว
		self.final_color = QtGui.QColor(255, 255, 255)

		self.color_show = QtWidgets.QPushButton()
		self.color_show.setFixedSize(50, 18)
		self.color_show.clicked.connect(self.pickColor)

		self.color_slider = QtWidgets.QSlider(QtCore.Qt.Horizontal)
		self.color_slider.setRange(0, 255) 
		self.color_slider.setValue(255) # เริ่มที่สว่างสุด
		self.color_slider.valueChanged.connect(self.updateColor)

		self.color_layout.addWidget(QtWidgets.QLabel("Color"))
		self.color_layout.addWidget(self.color_show)
		self.color_layout.addWidget(self.color_slider)

		#เรียกใช้ updateColor ให้สีแสดถูก
		self.updateColor(self.color_slider.value())

	def updateColor(self, value):
		h, s, _, a = self.base_color.getHsv()
		
		self.final_color = QtGui.QColor()
		self.final_color.setHsv(h, s, value, a)

		# อัปเดตสีที่ปุ่มแสดงผล
		r, g, b, _ = self.final_color.getRgb()
		self.color_show.setStyleSheet(f"	background-color: rgb({r},{g},{b}); border: 1px solid #555;")

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
		self.resize(315,600)
		
		self.library_data = {}
		self.curve_library_data = {}
		self.default_presetsJJ = ["hip", "L_clavicle", "root", "wrist"]
		self.default_presetsCC = ["circle", "cube", "star", "starburst"]
		
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
		self.JOINT_LIBRARY_PATH = JOINT_LIBRARY_PATH
		self.CURVE_LIBRARY_PATH = CURVE_LIBRARY_PATH
		self.JOINT_ICONS_DIRECTORY = JOINT_ICONS_DIRECTORY
		self.CURVE_ICONS_DIRECTORY = CURVE_ICONS_DIRECTORY

	#########################################################################     JIONT
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
		for w in [self.scale_LayoutJJX, self.scale_LayoutJJY, self.scale_LayoutJJZ]: 
			w.setValue(1.0)
			self.scale_LayoutJJ.addWidget(w)
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

	#########################################################################     CURVES
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
		for w in [self.scale_LayoutCCX, self.scale_LayoutCCY, self.scale_LayoutCCZ]: 
			w.setValue(1.0)
			self.scale_LayoutCC.addWidget(w)
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
#########################################################################
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
		sels = cmds.ls(sl=True, type='joint')
		if not sels:
			return cmds.warning("Select Root JOINT!!!!")

		joint_to_add = sels[0]

		short_name = joint_to_add.split('|')[-1]
		sanitized_name = sanitize_name(short_name)
		icon_path = os.path.join(JOINT_ICONS_DIRECTORY, f"{sanitized_name}.png")
		uai.playblast_icon(joint_to_add, icon_path)

		if not self.joint_listWidget.findItems(joint_to_add, QtCore.Qt.MatchExactly):
			item = utj.create_joint_item(joint_to_add)

			# 🟢ตั้งค่า icon จากไฟล์ที่ playblast มา
			if os.path.exists(icon_path):
				item.setIcon(QtGui.QIcon(icon_path))

			self.joint_listWidget.addItem(item)

		utj.save_Library(self, JOINT_LIBRARY_PATH)

	def del_joint_item(self):
	    selected_items = self.joint_listWidget.selectedItems()
	    if not selected_items:
	        return cmds.warning("Select JOINT to delete!!!!")

	    import util_addicon as uai
	    # โหลด JSON ปัจจุบัน
	    joint_json = {}
	    if os.path.exists(JOINT_LIBRARY_PATH):
	        try:
	            with open(JOINT_LIBRARY_PATH, 'r') as f:
	                joint_json = json.load(f)
	        except Exception as e:
	            cmds.warning(f"ERROR read joint.json: {e}")

	    removed_any = False

	    for item in selected_items:
	        name = item.text()

	        self.joint_listWidget.takeItem(self.joint_listWidget.row(item))

	        sanitized_short = name.split('|')[-1].replace(':', '_').replace('|', '_')
	        icon_path = os.path.join(JOINT_ICONS_DIRECTORY, f"{sanitized_short}.png")
	        uai.delete_icon_file(icon_path)

	        sanitized_full = name.replace(':', '_').replace('|', '_')
	        icon_path_full = os.path.join(JOINT_ICONS_DIRECTORY, f"{sanitized_full}.png")
	        uai.delete_icon_file(icon_path_full)

	        keys_to_remove = []
	        for key in list(joint_json.keys()):
	            key_short = key.split('|')[-1] if '|' in key else key
	            if key == name or key_short == name.split('|')[-1] or key_short == sanitized_short:
	                keys_to_remove.append(key)

	        if keys_to_remove:
	            removed_any = True
	            for k in keys_to_remove:
	                del joint_json[k]
	                print(f"[INFO] Removed '{k}' from joint.json")

	    if removed_any:
	        try:
	            with open(JOINT_LIBRARY_PATH, 'w') as f:
	                json.dump(joint_json, f, indent=4)
	            print(f"[INFO] Saved updated joint library : {JOINT_LIBRARY_PATH}")
	        except Exception as e:
	            cmds.warning(f"⚠️ Error updating joint.json: {e}")

	    #อัปเดต data
	    self.reload_all_libraries()

	def create_preset_item(self):
		utj.create_from_preset(self)

	def add_curve_item(self):
		selection = cmds.ls(sl=True)
		if not selection:
			return cmds.warning("Select CURVE to ADD!!!!")

		for sel in selection:
			shape = cmds.listRelatives(sel, s=True, type='nurbsCurve')
			if not shape: continue

			short_name = sel.split('|')[-1]
			sanitized_name = sanitize_name(short_name)
			icon_path = os.path.join(CURVE_ICONS_DIRECTORY, f"{sanitized_name}.png")

			playblast_icon(sel, icon_path)

			if not self.curves_listWidget.findItems(sel, QtCore.Qt.MatchExactly):
				item = utc.create_curve_item(sel)

				# 🟢ตั้งค่า icon จากไฟล์ที่ playblast มา
				if os.path.exists(icon_path):
					item.setIcon(QtGui.QIcon(icon_path))

				self.curves_listWidget.addItem(item)
		utc.save_curve_library(self, CURVE_LIBRARY_PATH)
		#self.reload_all_libraries()

	def del_curve_item(self):
		selected_items = self.curves_listWidget.selectedItems()
		if not selected_items: return

		for item in selected_items:
			curve_name = item.text()

			#สร้าง Path ไปไฟล์ Icon
			sanitized_name = sanitize_name(curve_name)
			icon_path = os.path.join(CURVE_ICONS_DIRECTORY, f"{sanitized_name}.png")

			#เช็คและลบไฟล์ภาพ
			try:
				if os.path.exists(icon_path):
					os.remove(icon_path)
					print(f"🗑️ Deleted icon : {icon_path}")
			except Exception as e:
				cmds.warning(f"ERROR delete icon {icon_path}: {e}")

			#ลบไอเท็มออกจาก UI
			self.curves_listWidget.takeItem(self.curves_listWidget.row(item))

		#save เปลี่ยนแปลงลงไฟล์ JSON
		utc.save_curve_library(self, CURVE_LIBRARY_PATH)

		#รีโหลด UI เพื่อให้แสดงผลถูก
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