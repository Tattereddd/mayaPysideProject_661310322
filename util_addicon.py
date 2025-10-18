try:
    from PySide6 import QtWidgets
except:
    from PySide2 import QtWidgets

import maya.cmds as cmds
import os

def playblast_icon(object_name, output_path, width=128, height=128):
    
    if not cmds.objExists(object_name):
        cmds.warning(f"'{object_name}' not found")
        return

    cmds.select(object_name, r=True)
    
    visible_panels = []
    for p in cmds.getPanel(type='modelPanel'):
        # <<< จุดแก้ไขสำคัญ: เปลี่ยนไปใช้ cmds.control เพื่อเช็คสถานะ visible >>>
        if cmds.control(p, query=True, visible=True):
            visible_panels.append(p)
    
    if not visible_panels:
        cmds.warning("Could not find any visible 3D viewport panels.")
        return
    panel = visible_panels[0]

    original_settings = {
        'grid': cmds.modelEditor(panel, query=True, grid=True),
        'manipulators': cmds.modelEditor(panel, query=True, manipulators=True)
    }

    try:
        cmds.isolateSelect(panel, state=True)
        cmds.viewFit(panel, animate=False)

        cmds.modelEditor(panel, edit=True, grid=False)
        cmds.modelEditor(panel, edit=True, manipulators=False)
        cmds.modelEditor(panel, edit=True, displayAppearance='smoothShaded')
        cmds.modelEditor(panel, edit=True, displayTextures=True)

        cmds.playblast(
            format="image",
            filename=output_path,
            sequenceTime=0,
            clearCache=1,
            viewer=False,
            showOrnaments=False, 
            frame=[cmds.currentTime(q=True)], 
            percent=100,
            compression="png",
            quality=100,
            widthHeight=[width, height]
        )
        print(f"Thumbnail captured: {output_path}")

    except Exception as e:
        cmds.warning(f"Failed to capture thumbnail: {e}")

    finally:
        try:
            if cmds.panel(panel, exists=True):
                cmds.isolateSelect(panel, state=False)
                cmds.modelEditor(panel, edit=True, grid=original_settings['grid'])
                cmds.modelEditor(panel, edit=True, manipulators=original_settings['manipulators'])
        except Exception as e:
            print(f"Could not restore panel settings: {e}")