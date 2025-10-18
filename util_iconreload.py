try:
	from PySide6 import QtCore, QtGui, QtWidgets
	from shiboken6 import wrapInstance
except:
	from PySide2 import QtCore, QtGui, QtWidgets
	from shiboken2 import wrapInstance
import os

def get_maya_icon(name):
	script_dir = os.path.dirname(__file__)
	icon_path = os.path.join(script_dir, "test", name)
	
	if os.path.exists(icon_path):
		return QtGui.QIcon(icon_path)
	else:
		print(f"[Warning] Icon not found: {icon_path}")
		return QtGui.QIcon()