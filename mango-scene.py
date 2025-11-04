import c4d
import maxon
import json
import tempfile
import shutil
import os
import socket
import sys
import re
import uuid
import math
import stat
import ast
from pathlib import Path

# use c4d scene file tree structure for assignment setup
def rend(doc):
    sceneData = []
    return sceneData 

def context(i, len, steps):
    range = []
    if i > 0:
        min = math.floor(i * len/steps + 1)
    else: min = 0
    max = math.floor((i + 1) * len/steps)
    range.append(min)
    range.append(max)
    return range

def outputScene(doc, gui, mode, host, steps, passes, whereproject):
    binary = doc.GetDocumentName()    
    document = os.path.splitext(binary)[0]
    scene = [int(num) for num in re.findall(r'\d+', document)][0]
    file = str(f"animation/scene_{scene}/{binary}")
    dirty = False
    assignments = []
    assign = {
        "id": host,
        "job": "Name",
        "engine-passes": passes,
        "range-start": 0,
        "range-end": 0
    }
    scenejson = os.path.join(whereproject, "scene.json")
    if not os.path.exists(scenejson):
        data = {
        }
        with open(scenejson, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4)
    with open(scenejson, "r", encoding="utf-8") as f:
        data = json.load(f)
    if "sequences" not in data:
        data["sequences"] = []
    else:
        if mode == 0:
            steps = steps + len(data["sequences"])  
    print("File:",document)
    print(f"Scene:{scene}")
    length = doc.GetMaxTime().GetFrame(doc.GetFps())    
    for job in range(steps):
        session = str(uuid.uuid5(uuid.NAMESPACE_DNS, (str(job)+document)))
        assignment = assign.copy()
        if gui is False:
            range0 = context(job, length, steps)
        else: 
            collectiondata = rend()
            range0[0] = collectiondata[0]
            range0[1] = collectiondata[1]
        assignment["job"] = session
        assignment["engine-passes"] = passes[job]              
        assignment["range-start"] = range0[0]
        assignment["range-end"] = range0[1]
        for sequence in data["sequences"]:
            if sequence["scene"] == scene:
                dirty = True
                if "assigned" not in sequence or not isinstance(sequence["assigned"], list):
                    sequence["assigned"] = []
                queued = len(sequence["assigned"])
                print(f"Assigned Jobs:\n    ",queued)            
                if job >= queued or session not in sequence["assigned"][job]["job"]:
                    assignments.append(assignment)
                if steps > queued and job < queued:  
                    for i in range(queued):
                        sequence["assigned"][job]["range-start"] = range0[0]
                        sequence["assigned"][job]["range-end"] = range0[1]
                sequence["assigned"].extend(assignments)
        if not dirty:
            assignments.append(assignment)       
    if not dirty:
        data["sequences"].append({
            "scene": scene, 
            "file": file, 
            "length": length, 
            "assigned": assignments
            })
    # Save the updated JSON back to the file
    with open(scenejson, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)
        
def main():
    args = sys.argv[1:]
    if len(args) > 0:
        gui = False
        path = Path(args[1])
        parts = path.parts
        file = path.name
        scene = Path(*parts[2:-1])
        url = Path(args[6].replace("\\", "/")) if len(args) > 5 else ""
        print("URI:",url)
        mode = int(args[2]) if len(args) > 2 else 1
        host = args[3] if len(args) > 3 else socket.gethostname()
        steps = int(args[4]) if len(args) > 4 else 1
        passes = ast.literal_eval(args[5]) if len(args) > 5 else ["EMBREE", "SKETCH"]
        passes = [list(item.pop().split(',')) for item in passes]
    else:
        gui = True
    works = url.parent
    os.makedirs(works/"staging"/scene, exist_ok=True)
    shutil.copy(path, Path(works/"staging"/scene))
    document = Path(works/"staging"/scene/file)
    document = str(document)
    print("Loading: ",document)
    print("Found: ",len(passes),"Passes")
    doc = c4d.documents.LoadDocument(document, c4d.SCENEFILTER_IGNOREMISSINGPLUGINSINNONACTIVERENDERDATA)
    url = url if url else Path(doc.GetDocumentPath()).parents[1]
    print("BaseDocument:",doc)   
    outputScene(doc, gui, mode, host, steps, passes, url)
    c4d.EventAdd()
    c4d.documents.KillDocument(doc)
    if os.path.exists(works/"staging"):
        os.chmod(document, stat.S_IWRITE)
        os.remove(document)
        shutil.rmtree(works/"staging")
if __name__ == '__main__':
    main()        