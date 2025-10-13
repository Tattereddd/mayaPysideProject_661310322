try:
    from PySide6 import QtGui
except:
    from PySide2 import QtGui

def get_maya_icon(name):
    icon = QtGui.QIcon(f":/{name}")
    if icon.isNull():
        script_dir = os.path.dirname(__file__)
        fallback = os.path.join(script_dir, "test", name)
        if os.path.exists(fallback):
            return QtGui.QIcon(fallback)
    return icon
