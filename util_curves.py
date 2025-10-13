import maya.cmds as cmds
import json
import os
try:
	from PySide6 import QtGui, QtWidgets, QtCore
except:
	from PySide2 import QtGui, QtWidgets, QtCore

from mayaPysideProject_661310322.main import get_maya_icon

def save_curve_library(ui_instance, library_path):
	library_data = {}

	# อ่านชื่อทั้งหมดจาก UI List Widget ของ Curve
	all_curve_names_in_ui = []
	for i in range(ui_instance.curves_listWidget.count()):
		all_curve_names_in_ui.append(ui_instance.curves_listWidget.item(i).text())

	# สร้างพิมพ์เขียวเฉพาะจากชื่อที่อ่านได้
	for curve_name in all_curve_names_in_ui:
		if not cmds.objExists(curve_name):
			print(f"Warning: Curve '{curve_name}' not found in scene, skipping save.")
			continue

		shape_nodes = cmds.listRelatives(curve_name, shapes=True, type='nurbsCurve')
		if not shape_nodes:
			print(f"Warning: '{curve_name}' has no nurbsCurve shape, skipping.")
			continue
		shape_node = shape_nodes[0]

	# --- (แก้ไข) เพิ่ม try...except เพื่อรองรับ Procedural Curve ---
		knots_data = []
		try:
			knots_data = cmds.getAttr(f"{shape_node}.knots[*]")
		except ValueError:
			print(f"Warning: Could not get knots for '{shape_node}'. Consider deleting history.")


		curve_info = {
			"points": cmds.getAttr(f"{shape_node}.cv[*]"),
			"degree": cmds.getAttr(f"{shape_node}.degree"),
			"knots": knots_data,
			"form": cmds.getAttr(f"{shape_node}.form")
		}
		library_data[curve_name] = curve_info

	try:
		with open(library_path, 'w') as f:
			json.dump(library_data, f, indent=4)
		print(f"Curve library saved to: {library_path}")
	except Exception as e:
		cmds.warning(f"Could not save curve library: {e}")

def load_default_curve_library(ui_instance, library_path):
	if not os.path.exists(library_path):
		cmds.warning(f"Default curve library not found: {library_path}")
		return {}
	try:
		with open(library_path, 'r') as f:
			library_data = json.load(f)

		for curve_name in library_data.keys():
			if not ui_instance.curves_listWidget.findItems(curve_name, QtCore.Qt.MatchExactly):
				item = QtWidgets.QListWidgetItem(curve_name)
				item.setIcon(get_maya_icon("out_curve.png")) # เพิ่มไอคอน
				ui_instance.curves_listWidget.addItem(item)

		print(f"Loaded {len(library_data)} default curve blueprints.")
		return library_data
	except Exception as e:
		cmds.warning(f"Could not load default curve library. Error: {e}")
		return {}

def load_curve_library(ui_instance, library_path):
	#"""โหลด 'พิมพ์เขียว' ของ Curve จากไฟล์ JSON และเพิ่มชื่อเข้าไปใน UI"""
	if not os.path.exists(library_path):
		return {}
	try:
		with open(library_path, 'r') as f:
			library_data = json.load(f)

		for curve_name in library_data.keys():
			if not ui_instance.curves_listWidget.findItems(curve_name, QtCore.Qt.MatchExactly):
				item = QtWidgets.QListWidgetItem(curve_name)
				item.setIcon(get_maya_icon("out_curve.png"))
				ui_instance.curves_listWidget.addItem(item)

		print(f"Loaded {len(library_data)} user curve blueprints.")
		return library_data
	except Exception as e:
		cmds.warning(f"Could not load curve library. Error: {e}")
		return {}


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

    # สร้างเส้นโค้ง
    curve = cmds.curve(p=points, d=degree)
    if form == 2:  # closed
        cmds.closeCurve(curve, ch=False, ps=True, rpo=True)

    # ปรับแต่งการแสดงผล
    shapes = cmds.listRelatives(curve, shapes=True, type="nurbsCurve") or []
    if shapes:
        shape_node = shapes[0]
        try:
            cmds.setAttr(f"{shape_node}.overrideEnabled", 1)
            cmds.setAttr(f"{shape_node}.overrideRGBColors", 1)
            col = ui_instance.colorSliderCC.base_color
            cmds.setAttr(f"{shape_node}.overrideColorRGB", col.redF(), col.greenF(), col.blueF())
        except Exception as e:
            cmds.warning(f"Could not set color: {e}")
    else:
        cmds.warning(f"No shape node found for {curve}")

    cmds.select(curve)
    print(f"Created curve preset '{preset_name}' successfully.")
    return curve


