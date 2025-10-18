try:
	from PySide6 import QtGui, QtWidgets, QtCore
except:
	from PySide2 import QtGui, QtWidgets, QtCore

import maya.cmds as cmds
import json
import os
import importlib

import util_iconreload as uir
importlib.reload(uir)
from util_iconreload import get_maya_icon


def create_joint_item(name):
	item = QtWidgets.QListWidgetItem(name)
	item.setIcon(get_maya_icon("out_curve.png"))
	return item

def save_curve_library(ui_instance, library_path):
	library_data = {}
	all_curve_names_in_ui = [ui_instance.curves_listWidget.item(i).text() for i in range(ui_instance.curves_listWidget.count())]

	for curve_name in all_curve_names_in_ui:
		if not cmds.objExists(curve_name):
			continue

		shape_nodes = cmds.listRelatives(curve_name, shapes=True, type='nurbsCurve')
		if not shape_nodes:
			continue
		shape_node = shape_nodes[0]

		curve_info = {
			"points": cmds.getAttr(f"{shape_node}.cv[*]"),
			"degree": cmds.getAttr(f"{shape_node}.degree"),
			"form": cmds.getAttr(f"{shape_node}.form")
		}
		library_data[curve_name] = curve_info

	with open(library_path, 'w') as f:
		json.dump(library_data, f, indent=4)
	print(f"Curve library saved to: {library_path}")

def load_default_curve_library(ui_instance, library_path):
	if not os.path.exists(library_path):
		return {}
	with open(library_path, 'r') as f:
		library_data = json.load(f)

	for curve_name in library_data.keys():
		if not ui_instance.curves_listWidget.findItems(curve_name, QtCore.Qt.MatchExactly):
			item = create_joint_item(curve_name)
			ui_instance.curves_listWidget.addItem(item)
	return library_data

def load_curve_library(ui_instance, library_path):
	if not os.path.exists(library_path):
		return {}
	with open(library_path, 'r') as f:
		library_data = json.load(f)

	for curve_name in library_data.keys():
		if not ui_instance.curves_listWidget.findItems(curve_name, QtCore.Qt.MatchExactly):
			item = create_joint_item(curve_name)
			ui_instance.curves_listWidget.addItem(item)
	return library_data


def create_curve_from_preset(ui_instance):
	selected_items = ui_instance.curves_listWidget.selectedItems()
	if not selected_items:
		return cmds.warning("Please select a curve preset to create.")

	preset_name = selected_items[0].text()
	if preset_name not in ui_instance.curve_library_data:
		return cmds.warning(f"Curve preset '{preset_name}' not found in library.")

	data = ui_instance.curve_library_data[preset_name]
	points = data.get("points", [])
	degree = data.get("degree", 1)
	form = data.get("form", 0)

	if not points:
		return cmds.warning(f"Curve preset '{preset_name}' has no CV data.")

	# <<< แก้ไขส่วนที่ 1: การตั้งชื่อ >>>
	name_prefix = ui_instance.name_lineEdit.text() or preset_name
	name_suffix = ui_instance.suffix_lineEdit.text()
	final_name = f"{name_prefix}_{name_suffix}" if name_suffix else name_prefix
	
	# <<< เราจะใส่ 'name=final_name' เข้าไปในคำสั่งสร้างเลย >>>
	# และลบ cmds.rename ทิ้ง
	curve = cmds.curve(p=points, d=degree, name=final_name)
	if form == 2:
		cmds.closeCurve(curve, ch=False, ps=True, rpo=True)

	# Apply transforms
	try:
		rx = ui_instance.rotate_LayoutCCX.value()
		ry = ui_instance.rotate_LayoutCCY.value()
		rz = ui_instance.rotate_LayoutCCZ.value()
		cmds.rotate(rx, ry, rz, curve, relative=True)

		sx = ui_instance.scale_LayoutCCX.value()
		sy = ui_instance.scale_LayoutCCY.value()
		sz = ui_instance.scale_LayoutCCZ.value()
		cmds.scale(sx, sy, sz, curve, relative=True)
	except Exception as e:
		print(f"Could not apply transforms: {e}")

	# Color
	try:
		# <<< แก้ไขส่วนที่ 2: เปลี่ยนไปใช้ .final_color >>>
		col = ui_instance.colorSliderCC.final_color
		shapes = cmds.listRelatives(curve, shapes=True, type="nurbsCurve") or []
		if shapes:
			shape_node = shapes[0]
			cmds.setAttr(f"{shape_node}.overrideEnabled", 1)
			cmds.setAttr(f"{shape_node}.overrideRGBColors", 1)
			cmds.setAttr(f"{shape_node}.overrideColorRGB", col.redF(), col.greenF(), col.blueF())
	except:
		pass

	# Group
	if ui_instance.Checkbox_CreateCurvesCC.isChecked():
		group_suffix = ui_instance.suffixNameGroup_layout_lineEdit.text() or "grp"
		grp = cmds.group(empty=True, name=f"{curve}_{group_suffix}")
		cmds.matchTransform(grp, curve)
		cmds.parent(curve, grp)
		print(f"Created curve preset '{preset_name}' and grouped successfully.")
		return grp

	print(f"Created curve preset '{preset_name}' successfully.")
	return curve