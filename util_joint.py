import maya.cmds as cmds

try:
	from PySide6 import QtCore, QtGui, QtWidgets
	from shiboken6 import wrapInstance
except:
	from PySide2 import QtCore, QtGui, QtWidgets
	from shiboken2 import wrapInstance


def add_Joint_WidgetsItem(list_widget):
	
	sels = cmds.ls(sl=True, type='joint')
	if not sels:
		cmds.warning("Select  joint!!!")
		return

	existing_items = [list_widget.item(i).text() for i in range(list_widget.count())]

	for sel_joint in sels:
		if sel_joint not in existing_items:
			item = QtWidgets.QListWidgetItem(sel_joint)
			icon = QtGui.QIcon(":/kinJoint.png") 
			item.setIcon(icon)
			list_widget.addItem(item)
			print(f"Added '{sel_joint}' to the list.")
		else:
			cmds.warning(f"'{sel_joint}' is already in the list.")


def del_Joint_WidgetsItem(list_widget):
	"""
	ฟังก์ชันสำหรับลบ item ที่เลือกใน QListWidget
	"""
	# 1. ดึง item ที่ถูกเลือกใน ListWidget
	selected_items = list_widget.selectedItems()
	if not selected_items:
		cmds.warning("Please select an item from the list to delete.")
		return

	# 2. วนลูปเพื่อลบ item ที่เลือกทั้งหมดออก
	for item in selected_items:
		# ดึง "แถว" ของ item ที่เลือก แล้วสั่งลบ
		row = list_widget.row(item)
		list_widget.takeItem(row)
		print(f"Removed '{item.text()}' from the list.")
