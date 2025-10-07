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
		
		#ที่เก็บของ
		self.joint_listWidget = QtWidgets.QListWidget()
		self.joint_listWidget.setIconSize(QtCore.QSize(60,60))
		self.joint_listWidget.setSpacing(5)
		self.joint_listWidget.setViewMode(QtWidgets.QListView.IconMode)
		self.joint_listWidget.setMovement(QtWidgets.QListView.Static)
		self.joint_listWidget.setResizeMode(QtWidgets.QListView.Adjust)
		self.joint_frameLayout.addWidget(self.joint_listWidget)

		#ปุ่มaddกับdel
		self.buttonAddDel_LayoutJJ=QtWidgets.QHBoxLayout()
		self.joint_frameLayout.frameLayout.addLayout(self.buttonAddDel_LayoutJJ)
		self.buttonAddJJ = QtWidgets.QPushButton('ADD')
		self.buttonDelJJ = QtWidgets.QPushButton('DEL')
		self.buttonAddDel_LayoutJJ.addWidget(self.buttonAddJJ)
		self.buttonAddDel_LayoutJJ.addWidget(self.buttonDelJJ)

		#checkbox Create Curves With Joint ใหญ่สุด
		self.CheckboxGroup_LayoutJJ = QtWidgets.QHBoxLayout()
		self.Label_CreateCurvesJJ = QtWidgets.QLabel('Create Curves With Joint') #แยกชื่อ
		self.Checkbox_CreateCurvesJJ = QtWidgets.QCheckBox() #แยกcheckbox
		self.CheckboxGroup_LayoutJJ.addWidget(self.Label_CreateCurvesJJ) #จับมารวมกันถ้าไม่แยกcheckboxมันจะไปอยู่หลังข้อความ
		self.CheckboxGroup_LayoutJJ.addWidget(self.Checkbox_CreateCurvesJJ)#จับมารวมกันถ้าไม่แยกcheckboxมันจะไปอยู่หลังข้อความ
		self.CheckboxGroup_LayoutJJ.addStretch()
		self.joint_frameLayout.frameLayout.addLayout(self.CheckboxGroup_LayoutJJ)

		self.childJJ = QtWidgets.QWidget()
		self.childJJ_frameLayout = QtWidgets.QVBoxLayout(self.childJJ)
		self.childJJ_frameLayout.setContentsMargins(25,0,0,0)
		self.childJJ_frameLayout.setSpacing(4)


		self.Checkbox_CreateGroupJJ = QtWidgets.QCheckBox('Group Curves')
		self.childJJ_frameLayout.addWidget(self.Checkbox_CreateGroupJJ)

		self.rotate_LayoutJJ = QtWidgets.QHBoxLayout()
		self.rotate_LayoutJJ.addWidget(QtWidgets.QLabel('Rotate'))
		self.rotate_LayoutJJX = QtWidgets.QDoubleSpinBox(); self.rotate_LayoutJJX.setRange(0,360)
		self.rotate_LayoutJJY = QtWidgets.QDoubleSpinBox(); self.rotate_LayoutJJY.setRange(0,360)
		self.rotate_LayoutJJZ = QtWidgets.QDoubleSpinBox(); self.rotate_LayoutJJZ.setRange(0,360)
		for i in [self.rotate_LayoutJJX, self.rotate_LayoutJJY, self.rotate_LayoutJJZ]: i.setEnabled(False)
		self.rotate_LayoutJJ.addWidget(self.rotate_LayoutJJX)
		self.rotate_LayoutJJ.addWidget(self.rotate_LayoutJJY)
		self.rotate_LayoutJJ.addWidget(self.rotate_LayoutJJZ)
		self.childJJ_frameLayout.addLayout(self.rotate_LayoutJJ)

		self.scale_LayoutJJ = QtWidgets.QHBoxLayout()
		self.scale_LayoutJJ.addWidget(QtWidgets.QLabel('Scale'))
		self.scale_LayoutJJX = QtWidgets.QDoubleSpinBox(); self.scale_LayoutJJX.setRange(0,999)
		self.scale_LayoutJJY = QtWidgets.QDoubleSpinBox(); self.scale_LayoutJJY.setRange(0,999)
		self.scale_LayoutJJZ = QtWidgets.QDoubleSpinBox(); self.scale_LayoutJJZ.setRange(0,999)
		for i in [self.scale_LayoutJJX, self.scale_LayoutJJY, self.scale_LayoutJJZ]: i.setEnabled(False)
		self.scale_LayoutJJ.addWidget(self.scale_LayoutJJX)
		self.scale_LayoutJJ.addWidget(self.scale_LayoutJJY)
		self.scale_LayoutJJ.addWidget(self.scale_LayoutJJZ)
		self.childJJ_frameLayout.addLayout(self.scale_LayoutJJ)

		
		self.joint_frameLayout.frameLayout.addWidget(self.childJJ)
		self.childJJ.setEnabled(False)
		self.Checkbox_CreateGroupJJ.toggled.connect(self.rotate_LayoutJJ.setEnabled)
		self.Checkbox_CreateGroupJJ.toggled.connect(self.scale_LayoutJJ.setEnabled)


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
def toggle_curve_controls(self, state):
		enabled = state == QtCore.Qt.Checked
		for w in [self.rotate_LayoutJJX, self.rotate_LayoutJJY, self.rotate_LayoutJJZ,]:
			w.setEnabled(enabled)
def run():
	global ui
	try:
		ui.close
	except:
		pass

	ptr = wrapInstance(int(omui.MQtUtil.mainWindow()),QtWidgets.QWidget)
	ui = JoinCurvesLibaryDialog(parent=ptr)
	ui.show()