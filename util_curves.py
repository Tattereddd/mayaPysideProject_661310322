import maya.cmds as cmds

def add_Curves_WidgetsItem(self)
	
	sels = cmds.ls(sl=True)
	if not sels:
		cmds.warning("Go to select!!!")
		return

	nodetype = cmds.nodeType(sels[0])
	shapes = cmds.listRelatives(sels[0], s=True)
	if shapes:
		result = cmds.nodeType(shapes[0])
		if result == 'nurbsCurve':
			existing = [list_widget.item(i).text() for i in range(list_widget.count())]
			print("OH")

		else :
	        cmds.warning("NOT CURVES!!!")


