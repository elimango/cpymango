import c4d
from c4d import gui
import time

## ANOTHER PROTOTYPING SCRIPT !! IT WILL AND DOES CURRENTLY LOOK LIKE A MESS !! ##
keybrake = None
dispatch = False
doc = c4d.documents.GetActiveDocument()

ID_OBJECT_LINK = 1000
ID_STATIC_TEXT = 1001
ID_PRINT_BUTTON = 1002
ID_CHECK_VIEW = 1003
ID_CHECK_RANGE = 1004
ID_EDIT_MIN = 1005
ID_EDIT_MAX = 1006
ID_TARGET_LINK = 1007
ID_SOURCE_GROUP = 1008
ID_TOGGLE_GROUP = 1009
ID_RANGE_GROUP = 1010
ID_OPERATION_GROUP = 1011

def ParentObjectToCamera(obj, target):
    tag = obj.GetTag(c4d.Tcaconstraint)
    if not tag:
        tag = c4d.BaseTag(c4d.Tcaconstraint)
        obj.InsertTag(tag)    
    doc.AddUndo(c4d.UNDOTYPE_CHANGE, tag)   
    doc.AddUndo(c4d.UNDOTYPE_CHANGE, obj)
    tag[c4d.ID_CA_CONSTRAINT_TAG_PARENT] = True
    tag[c4d.ID_CA_CONSTRAINT_TAG_PARENT_RESET] = True
    tag[c4d.ID_CA_CONSTRAINT_TAG_PARENT_FROZEN] = True
    tag[c4d.ID_CA_CONSTRAINT_TAG_PSR_MAINTAIN] = True
    tag[30001] = target  # Target  
    obj.Message(c4d.MSG_UPDATE)
    obj.SetDirty(c4d.DIRTY_DATA)
    # Force a manual scene evaluation step
    doc.ExecutePasses(None, True, True, False, c4d.BUILDFLAGS_NONE)
    c4d.EventAdd()

def SetCurrentTime(currentTime, doc):
    doc.SetTime(currentTime)
    doc.ExecutePasses(None, True, True, False, 0)
    c4d.DrawViews(c4d.DA_ONLY_ACTIVE_VIEW | c4d.DA_NO_THREAD)        

def BakeFrames(obj, target, min, max):
    fps = doc.GetFps()     
    minTime = doc[c4d.DOCUMENT_MINTIME] if min is None else c4d.BaseTime(min, fps)
    maxTime = doc[c4d.DOCUMENT_MAXTIME] if max is None else c4d.BaseTime(max, fps)
    if minTime != maxTime:
        currentTime = minTime
        viewCamera = False
        source = False
        pos = c4d.ID_BASEOBJECT_ABS_POSITION
        rot = c4d.ID_BASEOBJECT_ABS_ROTATION
        ParentObjectToCamera(obj, target)          
        while (currentTime <= maxTime):
            SetCurrentTime(currentTime, doc)
            viewport = doc.GetRenderBaseDraw()
            currentCamera = viewport.GetSceneCamera(doc)
            if target == currentCamera:
                viewCamera = True
            elif target is None:
                source = True
            if viewCamera:
                print("Camera out of sync, updating on",currentTime.GetFrame(fps),"F...")
                target = currentCamera
            if not source:
                pos = c4d.ID_BASEOBJECT_FROZEN_POSITION
                rot = c4d.ID_BASEOBJECT_FROZEN_ROTATION              
                ParentObjectToCamera(obj, target)
            doc.AddUndo(c4d.UNDOTYPE_CHANGE, obj)   
            doc.RecordKey(obj, pos, 
                          c4d.BaseTime(currentTime.GetFrame(fps), fps))
            doc.RecordKey(obj, rot, 
                          c4d.BaseTime(currentTime.GetFrame(fps), fps))
            doc.EndUndo() 
            currentTime += c4d.BaseTime(1, fps)
    global dispatch
    dispatch = True            
    tag = obj.GetTag(c4d.Tcaconstraint)
    if tag:
        tag.Remove()
            
class KeyBrakeWrapper(gui.GeDialog): 

    def CreateLayout(self):
        self.SetTitle("Key Brake Manager")
        self.AddStaticText(ID_STATIC_TEXT, c4d.BFH_SCALEFIT, name="Operations")

        self.GroupBegin(ID_SOURCE_GROUP, c4d.BFH_SCALEFIT | c4d.BFV_SCALEFIT, cols=1, rows=1)
        self.GroupBorderSpace(5, 1, 1, 1)  # left, top, right, bottom
        self.GroupBorder(c4d.BORDER_GROUP_IN)
        self.GroupBegin(ID_SOURCE_GROUP, c4d.BFH_SCALEFIT, cols=1, rows=1)
        bc = c4d.BaseContainer()                
        self.AddStaticText(ID_STATIC_TEXT, c4d.BFH_LEFT, name="Source")
        self.source = self.AddCustomGui(ID_OBJECT_LINK, c4d.CUSTOMGUI_LINKBOX, "", c4d.BFH_SCALEFIT, 0, 0, bc)
        self.GroupEnd()  # End row group

        self.GroupBegin(ID_OPERATION_GROUP, c4d.BFH_SCALEFIT, cols=2, rows=1)
        self.GroupBorder(c4d.BORDER_GROUP_IN)
        self.GroupBorderSpace(0, 0, 0, 6)  # left, top, right, bottom        
        self.AddStaticText(ID_STATIC_TEXT, c4d.BFH_LEFT, name="Use Viewcam For Target")
        self.AddCheckbox(ID_CHECK_VIEW, c4d.BFH_RIGHT, initw=25, inith=12, name="")
        self.GroupEnd()        

        self.GroupBegin(ID_TOGGLE_GROUP, c4d.BFH_SCALEFIT, cols=1, rows=1)
        self.GroupBorderSpace(0, 1, 1, 1)  # left, top, right, bottom                
        self.AddStaticText(ID_STATIC_TEXT, c4d.BFH_LEFT, name="Target")    
        self.input = self.AddCustomGui(ID_TARGET_LINK, c4d.CUSTOMGUI_LINKBOX, "", c4d.BFH_SCALEFIT, 0, 0, bc)
        self.GroupEnd()
              
        self.GroupBegin(ID_OPERATION_GROUP, c4d.BFH_SCALEFIT, cols=2, rows=1)
        self.GroupBorder(c4d.BORDER_GROUP_IN)
        self.GroupBorderSpace(0, 0, 0, 6)  # left, top, right, bottom        
        self.AddStaticText(ID_STATIC_TEXT, c4d.BFH_LEFT, name="Use Range For Target")            
        self.AddCheckbox(ID_CHECK_RANGE, c4d.BFH_RIGHT, initw=25, inith=12, name="")
        self.GroupEnd()        

        self.GroupBegin(ID_RANGE_GROUP, c4d.BFH_SCALEFIT, cols=4, rows=14)
        self.AddStaticText(ID_STATIC_TEXT, c4d.BFH_LEFT, name="Start")
        self.AddEditNumberArrows(ID_EDIT_MIN, 30, 146, 0)
        self.AddStaticText(ID_STATIC_TEXT, c4d.BFH_LEFT, name="End")
        self.AddEditNumberArrows(ID_EDIT_MAX, 30, 146, 0)
        self.GroupEnd()

        self.AddButton(ID_PRINT_BUTTON, c4d.BFH_SCALEFIT, name="Bake Tracks")
        return True
    
    def InitValues(self):
        self.SetFloat(ID_EDIT_MIN, 0, 0, 999999, 1, c4d.FORMAT_FRAMES)
        self.SetFloat(ID_EDIT_MAX, 0, 0, 999999, 1, c4d.FORMAT_FRAMES)
        self.SetBool(ID_CHECK_RANGE, True)
        self.Enable(ID_RANGE_GROUP, True)
        self.Enable(ID_TOGGLE_GROUP, True)
        self.Enable(ID_RANGE_GROUP, True)        
        self.LayoutChanged(0)
        return True
        
    def Command(self, id, msg):  
        min = self.GetFloat(ID_EDIT_MIN) if self.GetBool(ID_CHECK_RANGE) else None
        max = self.GetFloat(ID_EDIT_MAX) if self.GetBool(ID_CHECK_RANGE) else None    
        viewport: c4d.BaseDraw = doc.GetRenderBaseDraw()
        camera: c4d.BaseObject = viewport.GetSceneCamera(doc)
        invalid = False
        target = None
        if id == ID_CHECK_VIEW:
            state = self.GetBool(ID_CHECK_VIEW)
            self.Enable(ID_TOGGLE_GROUP, not state)
            self.LayoutChanged(ID_TARGET_LINK)
        if id == ID_CHECK_RANGE:
            state = self.GetBool(ID_CHECK_RANGE)
            self.Enable(ID_RANGE_GROUP, state)
            self.LayoutChanged(ID_RANGE_GROUP)                   
        if id == ID_PRINT_BUTTON:        
            if not self.GetBool(ID_CHECK_VIEW):
                if self.input:
                    target = self.input.GetLink()         
            else:
                target = camera
            if self.source:
                source = self.source.GetLink()
                if source:
                    print("Source linked to:", source.GetName())
                else:
                    print("No object linked.")
                    invalid = True
            if not invalid:
                BakeFrames(source, target, min, max)
            self.SetTimer(255)
            return True
        return True
    def Timer(self, msg):
        self.SetTimer(0)
        if dispatch == True:
            self.Close()        
def main():
    global keybrake
    if keybrake is None:
        keybrake = KeyBrakeWrapper()
    keybrake.Open(c4d.DLG_TYPE_ASYNC, defaultw=350, defaulth=120)

main()