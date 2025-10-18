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


SCRIPT_DIRECTORY = os.path.dirname(__file__)
LIBRARY_DIRECTORY = os.path.join(SCRIPT_DIRECTORY, '..', 'LIBRARY')
ICONS_DIRECTORY = os.path.join(LIBRARY_DIRECTORY, 'ICONS')

JOINT_ICONS_DIRECTORY = os.path.join(os.path.dirname(__file__), '..', 'icons', 'icons_joint')

def create_joint_item(name):
	item = QtWidgets.QListWidgetItem(name)
	
	sanitized_name = name.replace(':', '_').replace('|', '_')
	custom_icon_path = os.path.join(JOINT_ICONS_DIRECTORY, f"{sanitized_name}.png")

	if os.path.exists(custom_icon_path):
		item.setIcon(QtGui.QIcon(custom_icon_path))
	else:
		item.setIcon(get_maya_icon("kinJoint.png"))

	return item

def add_Joint_WidgetsItem(ui_instance):
	sels = cmds.ls(sl=True, type='joint')
	if not sels:
		cmds.warning("Please select a root joint!")
		return
	if len(sels) > 1:
		cmds.warning("Please select only one root joint.")
		return

	joint_to_add = sels[0]
	existing_items = [ui_instance.joint_listWidget.item(i).text() for i in range(ui_instance.joint_listWidget.count())]

	if joint_to_add not in existing_items:
		item = create_joint_item(joint_to_add)
		ui_instance.joint_listWidget.addItem(item)
		print(f"Added '{joint_to_add}' to the library.")
	else:
		cmds.warning(f"'{joint_to_add}' is already in the library.")

def del_Joint_WidgetsItem(ui_instance):
	selected_items = ui_instance.joint_listWidget.selectedItems()
	if not selected_items:
		cmds.warning("Please select an item to delete.")
		return
	for item in selected_items:
		row = ui_instance.joint_listWidget.row(item)
		ui_instance.joint_listWidget.takeItem(row)

def save_Library(ui_instance, library_path):
	library_data = {}
	custom_joints = [
		ui_instance.joint_listWidget.item(i).text()
		for i in range(ui_instance.joint_listWidget.count())
		if ui_instance.joint_listWidget.item(i).text() not in ui_instance.default_presets
	]

	for root_name in custom_joints:
		if not cmds.objExists(root_name):
			continue
		
		full_root_name = cmds.ls(root_name, long=True)[0]
		hierarchy = cmds.listRelatives(full_root_name, ad=True, type='joint', f=True) or []
		hierarchy.append(full_root_name)
		hierarchy.sort(key=len)

		entry_data = {"joints": []}
		for joint_full_path in hierarchy:
			joint_short_name = joint_full_path.split('|')[-1]
			parent_list = cmds.listRelatives(joint_full_path, p=True, f=True)
			parent_short_name = parent_list[0].split('|')[-1] if parent_list else ""

			joint_info = {
				"name": joint_short_name, "parent": parent_short_name,
				"translation": cmds.xform(joint_full_path, q=True, ws=True, t=True),
				"orientation": cmds.getAttr(f"{joint_full_path}.jointOrient")[0]
			}
			entry_data["joints"].append(joint_info)
		
		library_data[root_name] = entry_data

	keys_to_delete = [key for key in ui_instance.library_data if key not in ui_instance.default_presets]
	for key in keys_to_delete:
		del ui_instance.library_data[key]
	ui_instance.library_data.update(library_data)

	try:
		with open(library_path, 'w') as f:
			json.dump(library_data, f, indent=4)
		print(f"saved to: {library_path}")
	except Exception as e:
		cmds.warning(f"not save: {e}")

def load_default_library(ui_instance, library_path):
	if not os.path.exists(library_path):
		for preset_name in ui_instance.default_presets:
			if not ui_instance.joint_listWidget.findItems(preset_name, QtCore.Qt.MatchExactly):
				item = create_joint_item(preset_name)
				ui_instance.joint_listWidget.addItem(item)
		return {}

	try:
		with open(library_path, 'r') as f:
			library_data = json.load(f)

		for root_name in library_data.keys():
			if not ui_instance.joint_listWidget.findItems(root_name, QtCore.Qt.MatchExactly):
				item = create_joint_item(root_name)
				ui_instance.joint_listWidget.addItem(item)

		print(f"Loaded {len(library_data)} default joint ")
		return library_data
	except Exception as e:
		cmds.warning(f"Error: {e}")
		return {}

def load_library(ui_instance, library_path):
	if not os.path.exists(library_path):
		return {}
	try:
		with open(library_path, 'r') as f:
			library_data = json.load(f)
		for root_name in library_data.keys():
			if not ui_instance.joint_listWidget.findItems(root_name, QtCore.Qt.MatchExactly):
				item = create_joint_item(root_name)
				ui_instance.joint_listWidget.addItem(item)
		print(f"Loaded {len(library_data)} joint")
		return library_data
	except Exception as e:
		cmds.warning(f"Error: {e}")
		return {}

def create_from_preset(ui_instance):
	selected_items = ui_instance.joint_listWidget.selectedItems()
	if not selected_items:
		return cmds.warning("select item to create.")
	preset_name = selected_items[0].text()

	if preset_name not in ui_instance.library_data:
		return cmds.warning(f"'{preset_name}' not found!")

	blueprint = ui_instance.library_data[preset_name]["joints"]
	name_map = {}
	cmds.select(cl=True)

	for joint_info in blueprint:
		blueprint_name = joint_info["name"]
		actual_name = cmds.joint(name=blueprint_name, p=joint_info["translation"])
		name_map[blueprint_name] = actual_name.split('|')[-1]
		cmds.select(cl=True)

	for joint_info in blueprint:
		blueprint_child_name = joint_info["name"]
		blueprint_parent_name = joint_info["parent"]
		if blueprint_parent_name:
			actual_child = name_map.get(blueprint_child_name)
			actual_parent = name_map.get(blueprint_parent_name)
			if actual_parent and actual_child and cmds.objExists(actual_child) and cmds.objExists(actual_parent):
				try:
					cmds.parent(actual_child, actual_parent)
				except Exception as e:
					print(f"  ERROR {e}")

	root_joint_actual_name = name_map[blueprint[0]["name"]]
	cmds.joint(root_joint_actual_name, edit=True, orientJoint='xyz', secondaryAxisOrient='yup', children=True, zeroScaleOrient=True)

	newly_created_joints = list(name_map.values())

	if ui_instance.Checkbox_CreateCurvesJJ.isChecked() and newly_created_joints:
		print("Creating curves...")
		for jnt in newly_created_joints:
			create_curve_on_joint(ui_instance, jnt)

	cmds.select(root_joint_actual_name)
	print(f"Successfully created '{preset_name}'.")


def create_curve_on_joint(ui_instance, joint_name):
	if not cmds.objExists(joint_name):
		cmds.warning(f"Joint '{joint_name}' not found!")
		return None

	curve = cmds.circle(n=f"{joint_name}_ctrl", nr=(1, 0, 0), ch=False)[0]
	cmds.matchTransform(curve, joint_name)

	#Rotation
	try:
		rx = ui_instance.rotate_LayoutJJX.value()
		ry = ui_instance.rotate_LayoutJJY.value()
		rz = ui_instance.rotate_LayoutJJZ.value()
		cmds.rotate(rx, ry, rz, curve, relative=True)
	except:
		pass

	#Scale
	try:
		sx = ui_instance.scale_LayoutJJX.value()
		sy = ui_instance.scale_LayoutJJY.value()
		sz = ui_instance.scale_LayoutJJZ.value()
		cmds.scale(sx, sy, sz, curve, relative=True)
	except:
		pass

	#Color
	try:
		color = ui_instance.colorSliderJJ.base_color
		shapes = cmds.listRelatives(curve, s=True, type="nurbsCurve")
		if shapes:
			shape = shapes[0]
			cmds.setAttr(f"{shape}.overrideEnabled", 1)
			cmds.setAttr(f"{shape}.overrideRGBColors", 1)
			cmds.setAttr(f"{shape}.overrideColorRGB", color.redF(), color.greenF(), color.blueF())
	except:
		pass

	# Group checked
	if ui_instance.Checkbox_CreateGroupJJ.isChecked():
		grp = cmds.group(empty=True, name=f"{curve}_grp")
		cmds.matchTransform(grp, curve)
		cmds.parent(curve, grp)
		return grp

	return curve