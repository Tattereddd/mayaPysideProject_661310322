#########################################   IMPORT   ###################################################

try:
	from PySide6 import QtGui, QtWidgets, QtCore
except:
	from PySide2 import QtGui, QtWidgets, QtCore

import maya.cmds as cmds
import json
import os
import importlib
import maya.api.OpenMaya as om
import glob


SCRIPT_DIRECTORY = os.path.dirname(__file__)
LIBRARY_DIRECTORY = os.path.join(SCRIPT_DIRECTORY, '..', 'LIBRARY')
ICONS_DIRECTORY = os.path.join(LIBRARY_DIRECTORY, 'ICONS')

CURVE_ICONS_DIRECTORY = os.path.join(os.path.dirname(__file__), '..', 'icons', 'icons_curves')

def create_curve_item(name):
	item = QtWidgets.QListWidgetItem(name)
	#แทนอักขระพิเศษด้วย _ 
	sanitized_name = name.replace(':', '_').replace('|', '_')
	custom_icon_path = os.path.join(CURVE_ICONS_DIRECTORY, f"{sanitized_name}.png")

	if os.path.exists(custom_icon_path):
		item.setIcon(QtGui.QIcon(custom_icon_path))

	return item

def save_curve_library(ui_instance, library_path):

	library_data = {}
	all_curve_names_in_ui = [ui_instance.curves_listWidget.item(i).text() for i in range(ui_instance.curves_listWidget.count())]

	for curve_name in all_curve_names_in_ui:
		if not cmds.objExists(curve_name):
			cmds.warning(f"'{curve_name}' not found")
			continue

		try:
			shapes = cmds.listRelatives(curve_name, s=True, ni=True, fullPath=True) or []
			curve_shapes = [s for s in shapes if cmds.nodeType(s) == 'nurbsCurve']
			if not curve_shapes: continue
			
			shape = curve_shapes[0]
			sel_list = om.MSelectionList()
			sel_list.add(shape)
			dag_path = sel_list.getDagPath(0)
			curve_fn = om.MFnNurbsCurve(dag_path)

			# ดึงข้อมูลทั้งหมด
			knots = list(curve_fn.knots())
			cvs = []
			for i in range(curve_fn.numCVs):
				pt = curve_fn.cvPosition(i, om.MSpace.kWorld)
				cvs.append([pt.x, pt.y, pt.z])
			
			curve_info = {
				"degree": curve_fn.degree,
				"spans": curve_fn.numSpans,
				"form": curve_fn.form,
				"cvs": cvs,
				"knots": knots
			}

			# ใช้ชื่อสั้นเป็น Key ใน .json
			short_name = curve_name.split('|')[-1]
			library_data[short_name] = curve_info

		except Exception as e:
			cmds.warning(f"ERROR not read data '{curve_name}': {e}")

	# บันทึกไฟล์ .json
	with open(library_path, 'w') as f:
		json.dump(library_data, f, indent=4)
	print(f"Curve library saved : {library_path}")

def load_default_curve_library(ui_instance, library_path):
	DEFAULT_ICONS_PATH = os.path.join(os.path.dirname(__file__), 'iconsdefault', 'curves')
	print(f"🔍 Checking default curve icons : {DEFAULT_ICONS_PATH}")

	library_data = {}
	#ถ้ามีไฟล์ .json ก็โหลดก่อน
	if os.path.exists(library_path):
		try:
			with open(library_path, 'r') as f:
				library_data = json.load(f)
		except Exception as e:
			cmds.warning(f"Error loading default curve library .json: {e}")

	#พิ่ม presets พร้อม icons
	for preset_name in ui_instance.default_presetsCC:
		if not ui_instance.curves_listWidget.findItems(preset_name, QtCore.Qt.MatchExactly):
			item = QtWidgets.QListWidgetItem(preset_name)

			preset_icon = os.path.join(DEFAULT_ICONS_PATH, f"{preset_name}.png")
			if os.path.exists(preset_icon):
				print(f"✅ Found curve icon '{preset_name}'")
				item.setIcon(QtGui.QIcon(preset_icon))
			else:
				print(f"⚠️Error not found '{preset_name}'")


			ui_instance.curves_listWidget.addItem(item)

	print(f"Loaded {len(library_data)} default curves.")
	return library_data


def load_curve_library(ui_instance, library_path):
    if not os.path.exists(library_path):
        return {}

    with open(library_path, 'r') as f:
        library_data = json.load(f)

    for curve_name, info in library_data.items():
        if not ui_instance.curves_listWidget.findItems(curve_name, QtCore.Qt.MatchExactly):
            icon_path = info.get("icon_path", "")
            item = create_curve_item(curve_name)

            # ใช้ icon_path จาก JSON ถ้ามี
            if icon_path and os.path.exists(icon_path):
                item.setIcon(QtGui.QIcon(icon_path))
            else:
                # fallback ใช้ไฟล์ในโฟลเดอร์ icons_curves ถ้ามี
                sanitized_name = curve_name.replace(':', '_').replace('|', '_')
                fallback_path = os.path.join(CURVE_ICONS_DIRECTORY, f"{sanitized_name}.png")
                if os.path.exists(fallback_path):
                    item.setIcon(QtGui.QIcon(fallback_path))

            ui_instance.curves_listWidget.addItem(item)

    print(f"✅ Loaded {len(library_data)} curves with icons")
    return library_data


def create_curve_from_preset(ui_instance):
	selected_items = ui_instance.curves_listWidget.selectedItems()
	if not selected_items:
		return cmds.warning("Select CURVE CREATE!!!!")

	preset_name = selected_items[0].text()

	if preset_name not in ui_instance.curve_library_data:
		return cmds.warning(f"Curve preset '{preset_name}' not found in .json")
	
	data = ui_instance.curve_library_data[preset_name]

	cvs = data.get("cvs", []) 
	degree = data.get("degree", 1)
	form = data.get("form", 0)
	knots = data.get("knots", None) 

	if not cvs:
		return cmds.warning(f"Curve preset '{preset_name}' no CV data.")

	user_prefix = ui_instance.name_lineEdit.text()
	user_suffix = ui_instance.suffix_lineEdit.text()
	rx = ui_instance.rotate_LayoutCCX.value()
	ry = ui_instance.rotate_LayoutCCY.value()
	rz = ui_instance.rotate_LayoutCCZ.value()
	sx = ui_instance.scale_LayoutCCX.value()
	sy = ui_instance.scale_LayoutCCY.value()
	sz = ui_instance.scale_LayoutCCZ.value()
	col = ui_instance.colorSliderCC.final_color
	should_group = ui_instance.Checkbox_CreateCurvesCC.isChecked()
	group_suffix = ui_instance.suffixNameGroup_layout_lineEdit.text() or "grp"

	selection = cmds.ls(sl=True)
	
	if selection:
		print(f"Found {len(selection)} selected objects")
		for target_object in selection:
			name_prefix = user_prefix or target_object
			final_name = f"{name_prefix}_{user_suffix}" if user_suffix else name_prefix
			
			if knots:
				curve = cmds.curve(p=cvs, d=degree, k=knots, name=final_name)
			else:
				curve = cmds.curve(p=cvs, d=degree, name=final_name)


			cmds.xform(curve, centerPivots=True)

			try:
				cmds.matchTransform(curve, target_object, pos=True, rot=True, scl=False)
			except Exception as e:
				cmds.warning(f"Not match transform {target_object}: {e}")

			cmds.rotate(rx, ry, rz, curve, relative=True, objectSpace=True)
			cmds.scale(sx, sy, sz, curve, relative=True)
			
			shapes = cmds.listRelatives(curve, shapes=True, type="nurbsCurve") or []
			if shapes:
				shape_node = shapes[0]
				cmds.setAttr(f"{shape_node}.overrideEnabled", 1)
				cmds.setAttr(f"{shape_node}.overrideRGBColors", 1)
				cmds.setAttr(f"{shape_node}.overrideColorRGB", col.redF(), col.greenF(), col.blueF())

			if should_group:
				grp = cmds.group(empty=True, name=f"{curve}_{group_suffix}")
				cmds.matchTransform(grp, curve)
				cmds.parent(curve, grp)
		print("--- All curves created successfully. ---")
	
	else: 
		print("Nothing selected!!!!")

def del_curve_item(ui_instance):
	selected_items = ui_instance.curves_listWidget.selectedItems()
	if not selected_items:
		return cmds.warning("Select to DELETE!!!!")

	curve_library_path = getattr(ui_instance, "CURVE_LIBRARY_PATH", None)
	curve_icons_dir = getattr(ui_instance, "CURVE_ICONS_DIRECTORY", None)

	for item in selected_items:
		curve_name = item.text()
		row = ui_instance.curves_listWidget.row(item)
		ui_instance.curves_listWidget.takeItem(row)

		#ลบไฟล์ icon
		if curve_icons_dir:
			sanitized_name = curve_name.replace(':', '_').replace('|', '_')
			icon_pattern = os.path.join(curve_icons_dir, f"{sanitized_name}_*.png")
			for f in glob.glob(icon_pattern):
				try:
					os.remove(f)
					print(f"[INFO] 🟢Deleted curve icon: {f}")
				except Exception as e:
					cmds.warning(f"⚠️Error delete curve icon: {e}")

		#ลบข้อมูลออกจาก .json
		if curve_library_path and os.path.exists(curve_library_path):
			try:
				with open(curve_library_path, 'r') as f:
					data = json.load(f)
				if curve_name in data:
					del data[curve_name]
					with open(curve_library_path, 'w') as f:
						json.dump(data, f, indent=4)
					print(f"[INFO] 🟢Removed '{curve_name}' from curve.json")
			except Exception as e:
				cmds.warning(f"⚠️Error updating curve.json: {e}")
#