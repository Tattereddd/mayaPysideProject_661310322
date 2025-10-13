import maya.cmds as cmds
import json
import os
try:
	from PySide6 import QtGui, QtWidgets, QtCore
except:
	from PySide2 import QtGui, QtWidgets, QtCore


from mayaPysideProject_661310322.main import get_maya_icon
# ===================================================================
# ฟังก์ชันจัดการรายการ (Add/Delete)
# ===================================================================

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
		item = QtWidgets.QListWidgetItem(joint_to_add)
		item.setIcon(get_maya_icon("kinJoint.png"))
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

# ===================================================================
# ฟังก์ชันบันทึกและโหลด Library (Save/Load)
# ===================================================================

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
#"""(เวอร์ชันแก้ไข) โหลด Default Joint Blueprint และเพิ่มชื่อเข้าไปใน UI"""
	if not os.path.exists(library_path):
		# ถ้าไม่มีไฟล์ default, ให้เพิ่มชื่อจาก list เข้าไปแทน
		for preset_name in ui_instance.default_presets:
			if not ui_instance.joint_listWidget.findItems(preset_name, QtCore.Qt.MatchExactly):
				item = QtWidgets.QListWidgetItem(preset_name)
				item.setIcon(get_maya_icon("kinJoint.png"))
				ui_instance.joint_listWidget.addItem(item)
		return {}
	# ถ้ามีไฟล์ default.json ให้โหลดข้อมูลจากไฟล์
	try:
		with open(library_path, 'r') as f:
			library_data = json.load(f)

		for root_name in library_data.keys():
			if not ui_instance.joint_listWidget.findItems(root_name, QtCore.Qt.MatchExactly):
				item = QtWidgets.QListWidgetItem(root_name)
				item.setIcon(get_maya_icon("kinJoint.png"))
				ui_instance.joint_listWidget.addItem(item)

		print(f"Loaded {len(library_data)} default joint blueprints.")
		return library_data
	except Exception as e:
		cmds.warning(f"Could not load default joint library file. Error: {e}")
		return {}

def load_library(ui_instance, library_path):
#"""โหลด User Joint Blueprint และเพิ่มชื่อเข้าไปใน UI"""
	if not os.path.exists(library_path):
		return {}
	try:
		with open(library_path, 'r') as f:
			library_data = json.load(f)
		for root_name in library_data.keys():
			if not ui_instance.joint_listWidget.findItems(root_name, QtCore.Qt.MatchExactly):
				item = QtWidgets.QListWidgetItem(root_name)
				item.setIcon(get_maya_icon("kinJoint.png"))
				ui_instance.joint_listWidget.addItem(item)

		print(f"Loaded {len(library_data)} user joint blueprints.")
		return library_data
	except Exception as e:
		cmds.warning(f"Could not load library file. Error: {e}")
		return {}



def create_from_preset(ui_instance):
	selected_items = ui_instance.joint_listWidget.selectedItems()
	if not selected_items:
		return cmds.warning("Please select an item to create.")
	preset_name = selected_items[0].text()

	if preset_name not in ui_instance.library_data:
		return cmds.warning(f"Blueprint for '{preset_name}' not found!")

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
					print(f"  ERROR parenting: {e}")

	root_joint_actual_name = name_map[blueprint[0]["name"]]
	cmds.joint(root_joint_actual_name, edit=True, orientJoint='xyz', secondaryAxisOrient='yup', children=True, zeroScaleOrient=True)

	newly_created_joints = list(name_map.values())
	if ui_instance.Checkbox_CreateCurvesJJ.isChecked() and newly_created_joints:
		print("Creating curves...")
		curves_and_offsets = []

		for jnt in newly_created_joints:
			created_curve = create_curve_on_joint(ui_instance, jnt)

			if ui_instance.Checkbox_CreateGroupJJ.isChecked():
				offset_grp = cmds.group(empty=True, name=f"{created_curve}_offset")
				cmds.matchTransform(offset_grp, jnt)
				cmds.parent(created_curve, offset_grp)
				curves_and_offsets.append(offset_grp)
			else:
				curves_and_offsets.append(created_curve)

	cmds.select(root_joint_actual_name)
	print(f"Successfully created '{preset_name}'.")

