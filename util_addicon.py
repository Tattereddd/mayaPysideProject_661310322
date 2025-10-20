#########################################   IMPORT   ###################################################

try:
	from PySide6 import QtWidgets
except:
	from PySide2 import QtWidgets

import maya.cmds as cmds
import os
import time
import glob


def sanitize_name(name):
	#แทนอักขระพิเศษด้วย _ 
	return name.replace(':', '_').replace('|', '_')


def playblast_icon(object_name, output_path, width=128, height=128):

	if not cmds.objExists(object_name):
		cmds.warning(f"'{object_name}' not found")
		return

	print(f"\n🟡 Starting ICON capture : {object_name}")

	# F โฟกัสวัตถุในมุมมอง
	cmds.select(object_name, r=True)
	try:
		cmds.viewFit(animate=False)
	except Exception as e:
		print(f"[!] ERROR not F view: {e}")

	# ตั้งชื่อไฟล์ชั่วคราว
	base_path_without_ext = os.path.splitext(output_path)[0]
	temp_filename = f"{base_path_without_ext}_{int(time.time())}"
	temp_png_file = f"{temp_filename}.png"

	print(f"  📸 Playblast temporary file: {temp_png_file}")

	try:
		cmds.playblast(
			filename=temp_filename,
			format="image",
			compression="png",
			forceOverwrite=True,
			sequenceTime=0,
			clearCache=1,
			viewer=False,
			showOrnaments=False,
			frame=[cmds.currentTime(q=True)],
			percent=100,
			quality=100,
			widthHeight=[width, height]
		)

		# 🔍 ตรวจสอบว่ามีไฟล์ชื่อ .0000.png ไหม
		if not os.path.exists(temp_png_file):
			possible_files = glob.glob(f"{temp_filename}*.png")
			if possible_files:
				temp_png_file = possible_files[0]

		# ✅ ย้ายไฟล์ไปตำแหน่ง output
		if os.path.exists(temp_png_file):
			# ลบไฟล์เก่าก่อน ถ้ามี
			if os.path.exists(output_path):
				os.remove(output_path)

			os.makedirs(os.path.dirname(output_path), exist_ok=True)
			os.rename(temp_png_file, output_path)
			print(f"  ✅ ICONS saved to: {output_path}")
		else:
			print(f"  ❌ ERROR Playblast. No image file found.")

	except Exception as e:
		cmds.warning(f"⚠️ Playblast ERROR: {e}")

def delete_icon_file(icon_path):
    import glob
    base_no_ext = os.path.splitext(icon_path)[0]
    pattern = f"{base_no_ext}*.png"
    found = glob.glob(pattern)
    deleted_any = False
    for p in found:
        try:
            os.remove(p)
            deleted_any = True
            print(f"[INFO] Deleted icon: {p}")
        except Exception as e:
            print(f"[Warning] ERROR not delete {p}: {e}")
    if not deleted_any:
        print(f"[Info] ERROR No icons found : {pattern}")