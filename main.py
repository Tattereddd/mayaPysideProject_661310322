try:
	from PySide6 import QtCore, QtGui, QtWidgets
	from shiboken6 import wrapInstance
except:
	from PySide2 import QtCore, QtGui, QtWidgets
	from shiboken2 import wrapInstance

import maya.OpenMayaUI as omui

class FramLayout(QtWidgets.QWidget):
	def __init__(self, title="", parent=None):
		super().__init__(parent)

		#สร้างตรงหัวชื่อกับลูกศรเปิดปิดแล้วเชื่อมกับdefเช็คtoggleเปิดปิด
		self.namehead = QtWidgets.QToolButton(text=title, checkable=True, checked=True)
		self.namehead.setToolButtonStyle(QtCore.Qt.ToolButtonTextBesideIcon)
		self.namehead.setArrowType(QtCore.Qt.DownArrow)
		self.namehead.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
		self.namehead.toggled.connect(self.checkedToggled)

		#frameใส่ของด้านใน
		self.frame = QtWidgets.QFrame()
		self.frame.setFrameShape(QtWidgets.QFrame.StyledPanel)
		self.frame.setFrameShadow(QtWidgets.QFrame.Raised)
		self.frameLayout = QtWidgets.QVBoxLayout(self.frame)

		#เอาเข้าmainlayout
		self.mainLayout = QtWidgets.QVBoxLayout(self)
		self.mainLayout.setSpacing(0)
		self.mainLayout.setContentsMargins(0,0,0,0) 
		self.mainLayout.addWidget(self.namehead)
		self.mainLayout.addWidget(self.frame)

	#เช็คtoggleเปิดปิด	
	def checkedToggled(self, checked):
		self.namehead.setArrowType(QtCore.Qt.DownArrow if checked else QtCore.Qt.RightArrow)
		self.frame.setVisible(checked)

	def addWidget(self, widget):
		self.frameLayout.addWidget(widget)


class JoinCurvesLibaryDialog(QtWidgets.QDialog):
	def __init__(self,parent=None):
		super().__init__(parent)

		self.setWindowTitle('Join&Curves Libary')
		self.resize(400,500)

		self.mainLayout = QtWidgets.QVBoxLayout()
		self.setLayout(self.mainLayout)

##############################   JOINT    #########################################
		self.joint_frameLayout = FramLayout("Joint Create")
		
		self.joint_listWidget = QtWidgets.QListWidget()
		self.joint_listWidget.setIconSize(QtCore.QSize(60,60))
		self.joint_listWidget.setSpacing(5)
		self.joint_listWidget.setViewMode(QtWidgets.QListView.IconMode)
		self.joint_listWidget.setMovement(QtWidgets.QListView.Static)
		self.joint_listWidget.setResizeMode(QtWidgets.QListView.Adjust)
		self.joint_frameLayout.addWidget(self.joint_listWidget)

		self.buttonJJAddDel_Layout=QtWidgets.QHBoxLayout()
		self.joint_frameLayout.frameLayout.addLayout(self.buttonJJAddDel_Layout)
		self.buttonJJAdd = QtWidgets.QPushButton('ADD')
		self.buttonJJDel = QtWidgets.QPushButton('DEL')
		self.buttonJJAddDel_Layout.addWidget(self.buttonJJAdd)
		self.buttonJJAddDel_Layout.addWidget(self.buttonJJDel)

		self.CheckboxGroup_Layout = QtWidgets.QHBoxLayout()
		self.Label_CreateCurves = QtWidgets.QLabel('Create Curves With Joint')
		self.Checkbox_CreateCurves = QtWidgets.QCheckBox()
		self.CheckboxGroup_Layout.addWidget(self.Label_CreateCurves)
		self.CheckboxGroup_Layout.addWidget(self.Checkbox_CreateCurves)
		self.CheckboxGroup_Layout.addStretch()



		
		self.joint_frameLayout.frameLayout.addLayout(self.CheckboxGroup_Layout)

##############################   CURVE    #########################################

		self.curves_frameLayout = FramLayout("Curves Create")

		self.curves_listWidget = QtWidgets.QListWidget()
		self.curves_listWidget.setIconSize(QtCore.QSize(60,60))
		self.curves_listWidget.setSpacing(5)
		self.curves_listWidget.setViewMode(QtWidgets.QListView.IconMode)
		self.curves_listWidget.setMovement(QtWidgets.QListView.Static)
		self.curves_listWidget.setResizeMode(QtWidgets.QListView.Adjust)
		self.curves_frameLayout.addWidget(self.curves_listWidget)

		self.buttonCCAddDel_Layout=QtWidgets.QHBoxLayout()
		self.curves_frameLayout.frameLayout.addLayout(self.buttonCCAddDel_Layout)
		self.buttonCCAdd = QtWidgets.QPushButton('ADD')
		self.buttonCCDel = QtWidgets.QPushButton('DEL')
		self.buttonCCAddDel_Layout.addWidget(self.buttonCCAdd)
		self.buttonCCAddDel_Layout.addWidget(self.buttonCCDel)

##############################   ADDALL    #########################################

		self.mainLayout.addWidget(self.joint_frameLayout)
		self.mainLayout.addWidget(self.curves_frameLayout)
		self.mainLayout.addStretch()


def run():
	global ui
	try:
		ui.close
	except:
		pass

	ptr = wrapInstance(int(omui.MQtUtil.mainWindow()),QtWidgets.QWidget)
	ui = JoinCurvesLibaryDialog(parent=ptr)
	ui.show()