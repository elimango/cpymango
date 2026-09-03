import c4d
import heapq
from c4d import gui

## ANOTHER PROTOTYPING SCRIPT !! IT WILL AND DOES CURRENTLY LOOK LIKE A MESS !! ##

doc = c4d.documents.GetActiveDocument()

ID_SYNC_OPERATION_GROUP = 5000
ID_SYNC_CONFIGURE_GROUP = 5001
ID_BAKE_CONFIGURE_GROUP = 5002

ID_SYNC_TOGGLE_GROUP = 5003

ID_SOURCE_OBJECT_LINK = 5004
ID_TARGET_OBJECT_LINK = 5005
ID_SYNC_STATIC_TEXT = 5006
ID_SYNC_BUTTON = 5007
ID_INEXCLUDE = 5008

ID_SEPARATOR = 5009
ID_CHECK_VIEW = 5010
ID_CHECK_BAKE = 5011
ID_CHECK_ABS = 5012
ID_CHECK_GLOBAL = 5013
ID_CHECK_FROZEN = 5014

FIELDS = 2
mangoTrack = None 
sourceList = [] 
squash, isSquashed  = set(), False
depth = 0

def SetCurrentTime(currentTime, doc):
    doc.SetTime(currentTime)
    doc.ExecutePasses(None, True, True, False, 0)
    c4d.DrawViews(c4d.DA_ONLY_ACTIVE_VIEW | c4d.DA_NO_THREAD)        

def BakeKeys(obj, prvKeys=None):
    fps = doc.GetFps()     
    minTime = doc[c4d.DOCUMENT_MINTIME]
    maxTime = doc[c4d.DOCUMENT_MAXTIME]
    if minTime == maxTime:
        return
    currentTime = minTime
    params = [
        c4d.ID_BASEOBJECT_ABS_POSITION,
        c4d.ID_BASEOBJECT_ABS_SCALE,
        c4d.ID_BASEOBJECT_ABS_ROTATION
    ]
    params2 = [
        c4d.ID_BASEOBJECT_GLOBAL_POSITION,
        c4d.ID_BASEOBJECT_GLOBAL_ROTATION
    ]
    params3 = [
        c4d.ID_BASEOBJECT_FROZEN_POSITION,
        c4d.ID_BASEOBJECT_FROZEN_ROTATION,
        c4d.ID_BASEOBJECT_FROZEN_SCALE
    ]
    staging = []
    if mangoTrack.GetFloat(ID_CHECK_ABS) > 0:
        staging = staging.append(params)
    if mangoTrack.GetFloat(ID_CHECK_GLOBAL) > 0:
        staging = staging.append(params2)
    if mangoTrack.GetFloat(ID_CHECK_FROZEN) > 0:
        staging = staging.append(params3)
    while (currentTime <= maxTime):
        SetCurrentTime(currentTime, doc)
        for frame in prvKeys if prvKeys else []:
            if currentTime.GetFrame(fps) != frame:
                continue
            doc.AddUndo(c4d.UNDOTYPE_CHANGE, obj)
            for i in staging:
                doc.RecordKey(obj, i, c4d.BaseTime(currentTime.GetFrame(fps), fps))
            doc.EndUndo()
        currentTime += c4d.BaseTime(1, fps)

def Tree(level):
    indent = "\t" * level
    return str(indent)

def ObjectSelection(doc):
    selection = doc.GetActiveObjects(c4d.GETACTIVEOBJECTFLAGS_CHILDREN)
    return selection if len(selection) > 1 else None
selection = ObjectSelection(doc)
field = 1 if selection else 0

def IterateCurves(nxt, sourceTrack):
    prvCurve = sourceTrack.GetCurve() if sourceTrack else None
    for i, targetTrack in enumerate(nxt):        
        nxtCurve = targetTrack.GetCurve()
        yield i, targetTrack, nxtCurve, prvCurve

def SyncTracks(source, target):
    prv = source.GetCTracks()
    for obj in target:
        nxt = obj.GetCTracks()
        #print("Tracks on Target: \n", nxtNames, "\n" "\n" "Tracks on Source: \n", prvNames, "\n")
        global depth, squash
        for sourceTrack in prv:
            ListTracks(nxt, prv, sourceTrack)
            squash = sorted(squash) if depth == 0 else set()

def ListTracks(nxt, prv, sourceTrack):
    isMatching, isIdentical, isUnique = False
    prvNames, nxtNames = []
    global squash, isSquashed, depth
    if len(squash) > 0:
        isSquashed = True
    for name in prv:
        prvNames.append(str(name.GetName()))
    for name in nxt:
        nxtNames.append(str(name.GetName()))    
    for i, targetTrack, nxtCurve, prvCurve in IterateCurves(nxt, sourceTrack): 
        #print(" -> Target Track: {}".format(targetTrack.GetName()))
        if targetTrack.GetName() == sourceTrack.GetName():
            isMatching = True
        if nxtNames[i] not in prvNames:
            isUnique = True            
            #print("Tracks match in both objects!")
        if str(sourceTrack.GetName()) in nxtNames[i] and isUnique:
            #print(f"{Tree(2)}- Found identical track in source tracks\n",f"{Tree(4)}- Similar in Target: ", nxtNames[i], f"\n{Tree(4)}- Similar in Source: ", sourceTrack.GetName())
            isIdentical = True
        if not (isMatching or isIdentical):
            return
        #print(f"\nDiffing Source: \n{Tree(2)}",sourceTrack.GetName(),f"\nDiffing Target: \n{Tree(2)}",targetTrack.GetName())
        if depth == 0:
            squash |= set(StageKeys(prvCurve)) if not isSquashed else set()
            DiffTracks(nxtCurve, prvCurve, prvKeys=squash)
        else:
            DiffTracks(nxtCurve, prvCurve)
            
def DiffTracks(nxtCurve, prvCurve, nxtkeys=None, prvkeys=None):
    if not prvkeys:
        prvkeys = StageKeys(prvCurve)
    if not nxtkeys:
        nxtkeys = StageKeys(nxtCurve)
    print("Source Track Keys: \n",nxtkeys,"\n" "Target Track Keys: \n",prvkeys,"\n")
    for old in nxtkeys:
        for new in prvkeys:
            nxtkeys.remove(new) if old == new else []
    IsolateKeys(nxtkeys, nxtCurve)
    StepKeys(nxtCurve)

def StageKeys(nxtCurve):
    nxtkeys, nxtkey = [], 0
    while nxtkey < nxtCurve.GetKeyCount():
        index = nxtkeys[nxtkey] if len(nxtkeys) > 0 and nxtkey < len(nxtkeys) else nxtkey
        frame = nxtCurve.FindNextUnmuted(index)[0].GetTime().GetFrame(doc.GetFps())
        nxtkeys.append(frame)
        nxtkey += 1
    return nxtkeys

def StepKeys(nxtCurve):
    keyCount = nxtCurve.GetKeyCount()
    for i in range(keyCount):
        key = nxtCurve.GetKey(i)
        key.SetInterpolation(nxtCurve, c4d.CINTERPOLATION_STEP)
        
def IsolateKeys(nxtkeys, nxtCurve):
    print("Diffed Keys: \n", nxtkeys,"\n")
    for stashed in sorted(nxtkeys, reverse=True):
        nxtCurve.DelKey(stashed, bUndo=True, SynchronizeKeys=False)
    print("Stashed Keys: \n", nxtkeys,"\n")    

class MangoTrackWrapper(gui.GeDialog):
    def CreateLayout(self):
        global field
        self.SetTitle("Key Sync Manager")

        # Begin vertical group with border padding
        self.AddStaticText(ID_SYNC_STATIC_TEXT, c4d.BFH_LEFT, name="Operations")
    
        self.GroupBegin(ID_SYNC_OPERATION_GROUP, c4d.BFH_SCALEFIT | c4d.BFV_SCALEFIT, cols=1, rows=0)
        self.GroupBorderSpace(5, 1, 1, 1)  # left, top, right, bottom
        self.GroupBorder(c4d.BORDER_GROUP_IN)
        # Row group: label + link field
        if self.GroupBegin(ID_SYNC_TOGGLE_GROUP, c4d.BFH_SCALEFIT, cols=2, rows=1):
            bc = c4d.BaseContainer()
            for i in range(FIELDS):
                if i == 0:
                    self.AddStaticText(ID_SYNC_STATIC_TEXT+10, c4d.BFH_LEFT, name="Source")
                    if field == 1:
                        self.source = self.AddCustomGui(ID_INEXCLUDE, c4d.CUSTOMGUI_INEXCLUDE_LIST, "", c4d.IN_EXCLUDE_DATA_ROWFLAGS | c4d.IN_EXCLUDE_FLAG_SEND_SELCHANGE_MSG | c4d.IN_EXCLUDE_DATA_BACKGROUND | c4d.BFH_SCALEFIT, 0, 0, bc)
                    if field == 0:
                        self.source = self.AddCustomGui(ID_SOURCE_OBJECT_LINK, c4d.CUSTOMGUI_LINKBOX, "", c4d.BFH_SCALEFIT, 0, 0, bc)    
                if i == 1:
                    self.AddStaticText(ID_SYNC_STATIC_TEXT+20, c4d.BFH_LEFT, name="Target")
                    self.target = self.AddCustomGui(ID_TARGET_OBJECT_LINK, c4d.CUSTOMGUI_LINKBOX, "", c4d.BFH_SCALEFIT, 0, 0, bc)
        self.GroupEnd()  # End row group

        self.GroupBegin(ID_SYNC_CONFIGURE_GROUP, c4d.BFH_SCALEFIT, cols=2, rows=1)
        self.AddStaticText(ID_SYNC_STATIC_TEXT, c4d.BFH_LEFT, name="Track Depth ->")
        self.GroupBorder(c4d.BORDER_GROUP_IN)

        self.GroupBorderSpace(6, 1, 0, 6)  # left, top, right, bottom        
        self.AddEditSlider(ID_CHECK_VIEW, c4d.BFH_SCALEFIT, initw=50, inith=12)  
        self.AddStaticText(ID_SYNC_STATIC_TEXT, c4d.BFH_LEFT, name="Bake Keys    ->")
        self.AddEditSlider(ID_CHECK_BAKE, c4d.BFH_SCALEFIT, initw=50, inith=12)
        self.GroupEnd() 

        self.GroupBegin(ID_BAKE_CONFIGURE_GROUP, c4d.BFH_SCALEFIT, cols=2, rows=1)
        self.GroupBorder(c4d.BORDER_GROUP_IN)
        self.GroupBorderSpace(6, 1, 0, 6)  # left, top, right, bottom        
        self.AddStaticText(ID_SYNC_STATIC_TEXT, c4d.BFH_LEFT, name="(Abs.) Pos. / Rot. / Scale ")
        self.GroupBorderSpace(6, 1, 0, 6)  # left, top, right, bottom                
        self.AddEditSlider(ID_CHECK_ABS, c4d.BFH_SCALEFIT, initw=50, inith=12)  

        self.AddStaticText(ID_SYNC_STATIC_TEXT, c4d.BFH_LEFT, name="(Global.) Pos. / Rot. / Scale ")
        self.GroupBorderSpace(6, 1, 0, 6)  # left, top, right, bottom                        
        self.AddEditSlider(ID_CHECK_GLOBAL, c4d.BFH_SCALEFIT, initw=50, inith=12)

        self.AddStaticText(ID_SYNC_STATIC_TEXT, c4d.BFH_LEFT, name="(Frozen) Pos. / Rot. / Scale ")
        self.GroupBorderSpace(6, 1, 0, 6)  #  
        self.AddEditSlider(ID_CHECK_FROZEN, c4d.BFH_SCALEFIT, initw=50, inith=12)  

        self.GroupEnd() 
        self.AddButton(ID_SYNC_BUTTON, c4d.BFH_SCALEFIT, name="Sync Tracks")
        return True

    def InitValues(self):
        self.SetFloat(ID_CHECK_VIEW, 0, 0, 1, 1, c4d.FORMAT_FLOAT)
        self.SetFloat(ID_CHECK_BAKE, 0, 0, 1, 1, c4d.FORMAT_FLOAT)
        self.SetFloat(ID_CHECK_ABS, 0, 0, 1, 1, c4d.FORMAT_FLOAT)
        self.SetFloat(ID_CHECK_GLOBAL, 0, 0, 1, 1, c4d.FORMAT_FLOAT)
        self.SetFloat(ID_CHECK_FROZEN, 0, 0, 1, 1, c4d.FORMAT_FLOAT)
        ie = c4d.InExcludeData()
        global selection
        if selection:   
            for d in ObjectSelection(doc):
                ie.InsertObject(d, 0)      
            self.source.SetData(ie)
        self.LayoutChanged(0)
        return True
    
    def Command(self, id, msg):
        global depth
        hide, source, target = False, None, None
        depth = self.GetFloat(ID_CHECK_VIEW)
        if id == ID_CHECK_BAKE:
            state = self.GetFloat(ID_CHECK_BAKE)
            hide = True if state > 0 else False
            self.HideElement(ID_BAKE_CONFIGURE_GROUP, hide)
            self.LayoutChanged(ID_BAKE_CONFIGURE_GROUP)              
        if id == ID_SYNC_BUTTON:
            invalid = False
            if self.target:
                target = self.target.GetLink()
                if not target:
                    invalid = True            
            if self.source:
                global sourceList
                try:
                    ie = self.source.GetData()
                    count = ie.GetObjectCount()
                    for i in range(count):
                        source = ie.ObjectFromIndex(doc, i)
                        sourceList.append(source)
                except Exception:
                    source = self.source.GetLink()
                    sourceList.append(source)
                if not source and len(sourceList) == 0:
                    invalid = True
            if invalid:
                return True
            print("Sources:",sourceList)
            SyncTracks(target, sourceList)
            self.Close()
            return True
        return True

def main():
    global mangoTrack
    if mangoTrack is None:
        mangoTrack = MangoTrackWrapper()
    mangoTrack.Open(c4d.DLG_TYPE_ASYNC, defaultw=350, defaulth=120)

if __name__ == '__main__':
    main()        