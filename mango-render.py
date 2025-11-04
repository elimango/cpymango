import re
import socket
import os
import time
import pip
import json 
import math
import shlex
import random
import subprocess
import tkinter as tk
from tkinter import filedialog
from pathlib import Path

##===========================================================================================##
##-----------------------------MANGOFARM RENDER SEQUENCE MANAGER-----------------------------##
##==========================================================================================-##
## This script is designed to run on systems with Cinema 4D installed (needs c4d module).    ##
## As a proof of concept, it is in *heavy* prototyping stage and is not consumer-ready OOTB. ##
## It was created specifically for elimango/studio and may not work on other systems without ##
## modifications, requiring a project structure where it lives at the root of the project,   ##
## demands './composite/', './animation/', and scene files are conventionally                ##
## declared as './animation/scene_#/scene_#.c4d'                                             ##
##===========================================================================================##

root = tk.Tk()
root.withdraw()

## print codes, used for terminal output
GOLD = '\033[33m'
LIGHT_BLUE = '\033[94m'
LIGHT_YELLOW = '\033[93m'
BAD = '\033[31m'
GREEN = '\033[32m'
UNDERLINE = '\033[4m'
RESET = '\033[0m'

# grab the hostname of the machine
duration = 0.13
host = socket.gethostname()

whereproject = Path(__file__).parent.resolve()
wherecomp = whereproject / 'composite'
whereanimation = whereproject / 'animation'

def confirm(prompt, dialogue):
    while True:
        answer = input(f"{"--"*50}\n{prompt}\n{"--"*50}\n{dialogue}\nSelect : ").lower()
        if answer in ["2","1","0","yes","no"]:
            return answer
        else:
            print("Invalid input. Please enter '0' or '1'.")

def prompt(prompt, dialogue):
    print(f"{"--"*50}\n{prompt}\n{"--"*50}\n{dialogue}\nSelect : ")

def scenes(where):
    paths = []
    for root, _, files in os.walk(where):
        for file in files:
            if file.endswith(".c4d"):
                path = os.path.join(root, file)
                paths.append(path)
                print(f"    {path}")
    return paths
def query(path, start, end):
    aovs = os.listdir(path)
    print('\t'f"﹂AOVS: {aovs}")
    if not aovs:
        print('\t'f"﹂EXRs: {files}")        
        return files
    for aov in aovs:
        currentAov = str(Path((path) / aov))
        if not os.path.exists(currentAov):
            continue
        for exr in os.listdir(currentAov):
            match = re.findall(r'\d+', exr)
            # If numbers are found, check whether they are within range
            if match:
                number = int(match[0])
                if number >= start and number <= end and exr not in files:
                    files.append(exr)
    print('\t'*2,f"﹂EXRs: {files[start:(start+5)]}{RESET}...")
    return files

def queue(sequence):
    stage.clear()
    file = str(Path(whereproject) / sequence["file"])
    print(f"Scene: {GREEN}{sequence['scene']}{RESET}")
    print(f"  ﹂C4D: {file}"
          '\n',
          '\n',
          " |"
          '\n',
          " v"), 
    for index, systems in enumerate(sequence["assigned"]):
        time.sleep(duration)         
        stage.append({
            "output": Path(wherecomp) / f"Scene_{sequence['scene']}",
            "length": (sequence["length"] + 1),
            "assigned": index,
            "id": systems["id"],
            "engine": systems["engine-passes"],
            "start": systems["range-start"],
            "end": systems["range-end"]
        })
        inrange = (stage[index]["end"] - stage[index]["start"]) + 1
        print(f"\nAssigned: {UNDERLINE}{GOLD}{systems['id']}{RESET} For {stage[index]["start"]} - {stage[index]["end"]} (Counted {GREEN}{inrange}{RESET} total.){RESET}")
        if not os.path.exists(file):
            return
        if host == stage[index]["id"]:
            print(f"Hostname matches ID, render queue {GREEN}OK{RESET}!")
            for current in stage[index]["engine"]:
                time.sleep(duration) 
                print('\t'f"Pass: {LIGHT_BLUE}{current}{RESET}")
                output = Path(stage[index]["output"]) / current
                frames = 0
                renderValid = False
                if os.path.exists(output):
                    renderValid = True
                    renders = query(output, (stage[index]["start"]), (stage[index]["end"]))
                    if renders:
                        frames = len(renders)
                weightcount = frames - stage[index]["start"]                                
                weightmin = stage[index]["start"]
                if frames < stage[index]["end"]:
                    if renderValid:
                        for i, frame in enumerate(renders):
                            if i < stage[index]["end"] and frames> stage[index]["start"]:
                                weightmin = weightmin + 1
                    dispatch = str(f"{commandline} -render {'"{}"'.format(file)} -take {current} -frame {weightmin} {stage[index]["end"]}")                    
                    jobs.append(dispatch)
                    print('\t'*2,"﹂Pass needs to be rendered.")
                    if renderValid:
                        print('\t'*2,f"  Render directory: {output}")
                    else:
                        print('\t'*2,f"  {BAD}Renderless directory{RESET}: {output}")
                else:
                    if weightcount == inrange:
                        STATUS = GREEN
                    else:
                        STATUS = GOLD
                    print('\t'*3,"Frames Rendered:",STATUS,weightcount,RESET,"of",GREEN,inrange,RESET,"[",frames,"in sequence of",stage[index]["length"],"]") 
                    if frames < stage[index]["end"]:
                        print('\t'*3,"Pass is missing frames.")
                    else:
                        print('\t'*3,f"Render of pass is complete! ✔️")
        else:
            print("Hostname does not match ID, skipping render")

# parse our scene manager file and return objects as a dictionary
client = {
}
dirty = False
found = False
clientjson = f"{whereproject}/client.json"
client["users"] = []
users = []
files = []
jobs  = []
stage = []

if os.path.exists(clientjson):
    with open(clientjson, "r", encoding="utf-8") as f:
        client = json.load(f)
if len(client["users"]) > 0:
    for user in client["users"]:
        if user.get("id") == host:
            found = True
            users.append(user["id"])   
            home = user["install"]
            assetsdb = user["database"]
    dirty = True
if len(client["users"]) < 1 or found is False:
    home = filedialog.askdirectory(initialdir="/",title="Select Cinema 4D home directory: (../Maxon/Cinema 4D 2025/)")
    if home:
        print(f"Selected directory for C4D home: {home}")
    assetsdb = filedialog.askdirectory(initialdir="/",title="Select assetsdb directory: (../assetsdb/)")
    if assetsdb:
        print(f"Selected directory for connected assetsdb: {assetsdb}")
    client["users"].append({
            "id": host, 
            "install": home,
            "database": assetsdb
            })
with open(clientjson, "w", encoding="utf-8") as f:
    json.dump(client, f, indent=4)
    
install = '"{}"'.format(home)
commandline = str('"{}"'.format(f"{home}/Commandline.exe") + "g_connectdatabase=" + '"{}"'.format(assetsdb))
c4dpy = '"{}"'.format(f"{home}/c4dpy.exe")

# get scenes
print(f"Animation Scene Files:")
animation = scenes(whereanimation)
print(c4dpy)
print(commandline)

# localization
in0 = f"[0] : {LIGHT_YELLOW}MANGOFARM RENDER CLIENT{RESET} \n  ﹂If this is a render machine, select this to enter 'RENDER' state. Unless instructed otherwise, proceed here.\n[1] : {LIGHT_YELLOW}MANGOFARM CONFIG CLIENT{RESET}\n  ﹂If you are an administrator, select this to enter 'CONFIGURATION' state.\n  ﹂If you were instructed to make changes, you will be asked to:\n\t -> {UNDERLINE}Assign number of render jobs.{RESET}\n\t -> {UNDERLINE}Assign engine passes per job.{RESET}"
in1 = f"[0] : {LIGHT_YELLOW}APPEND BOOT MODE{RESET} \n  ﹂Appends each new job in range to the currently present job queue in your scene dispatch file (scene.json)\n[1] : {LIGHT_YELLOW}CLEAN BOOT MODE{RESET}\n  ﹂Treats queue assignment as a fresh instance, if jobs are present, re-assigns them."
in2 = f"[0] : {LIGHT_YELLOW}RENDER QUEUE AMOUNT{RESET}\n  ﹂Amount of different node-locked render jobs to assign."
in3 = f"[0] : {LIGHT_YELLOW}LOCAL USER{RESET}\n  ﹂Assigns hostname of the current local user to render job.\n[1] : {LIGHT_YELLOW}RANDOM USER{RESET}\n  ﹂Assigns random client id (client.json) to render job.\n[2] : {LIGHT_YELLOW}CUSTOM USER{RESET}\n  ﹂Manually assign a user to render job (string)."
in4 = f"[0] : {LIGHT_YELLOW}UNASSIGNED{RESET}\n  ﹂If you want to skip the current indexed pass slot, proceed here.\n{'--'*50}\n[1] : {LIGHT_YELLOW}EMBREE{RESET}\n[2] : {LIGHT_YELLOW}SKETCH{RESET}\n[3] : {LIGHT_YELLOW}SMEAR{RESET}\n[4] : {LIGHT_YELLOW}REDSHIFT{RESET}"

out1 = confirm(f"⚙️ 0/4 {UNDERLINE}CONFIGURATION MODE{RESET}: Enter '0' or '1' to proceed.", in0)
if out1 == "2":
    print("Configuring render jobs...\n")
    for doc in animation:
        out2 = 4
        passes = [
        ]
        for job in range(out2):
            if dirty == True:
                host = random.choice(users)
            takes = []
            takes.append('"{}"'.format("EMBREE"))
            takes.append('"{}"'.format("SKETCH"))
            takes = ",".join(takes)
            passes.append([takes])
            print(passes[job],"In Job:",job)
        print(f"Queued Passes:",passes)
        command = str(f'{c4dpy} "{whereproject}/mango-scene.py/" False "{doc}" {1} "{host}" {str(out2)} "{passes}" "{whereproject}"')
        print(command)        
        subprocess.run(command)
if out1 == "1":
    print("Configuring render jobs...\n")
    mode = confirm(f"⚙️ 1/4 {UNDERLINE}MANGOSCENE BOOT MODE{RESET}: Enter '0' or '1' to proceed.", in1)
    for doc in animation:
        prompt(f"⚙️ 2/4 {UNDERLINE}QUEUE {RESET}: Enter a value (Int)", in2)
        out2 = int(input("Rendering __ amount of jobs:"))
        for job in range(out2):
            prompt(f"⚙️ 3/4 {UNDERLINE}ASSIGNING SYSTEM HOSTNAME TO{RESET}: Job {job+1}. Enter '0' or '1' to proceed.", in3)
            j = int(input(f"Enter :"))
            if j == 1:
                if dirty == True:
                    host = random.choice(users)
            if j == 2:
                host = str(input(f"Enter :"))
            prompt(f"⚙️ 4/4 {UNDERLINE}ASSIGNING ENGINE PASSES FOR{RESET}: Job {job+1}. Enter '0' or '1' to proceed.", in4)
            passes = []
            for i in range(4):
                takes = []
                j = int(input(f"[{i}/4] Assign pass in list:"))
                if not j:
                    j = 0
                if j > 0:
                    if j == 1:
                        takes.append("{}".format("EMBREE"))
                    if j == 2:
                        takes.append("{}".format("SKETCH"))
                    if j == 3:
                        takes.append("{}".format("SMEAR"))
                    if j == 4:
                        takes.append("{}".format("REDSHIFT"))
                takes = ",".join(takes)
                passes.append([takes])
            print(passes)
            command = str(f'{c4dpy} "{whereproject}/mango-scene.py/" False "{doc}" {mode} "{host}" {str(out2)} "{passes}" "{whereproject}"')
            print(command)        
            subprocess.run(command)
if out1 == "0":
    print("Querying render jobs...\n")

scenejson = open(f"{whereproject}/scene.json")
data = json.load(scenejson)
for sequence in data["sequences"]:
    time.sleep(1)
    queue(sequence)
    print('\n',"--"*50)
print(*jobs, sep='\n')
input("Press 'Enter' to start queue...")
for job in jobs:
    result = subprocess.run(job)    
scenejson.close()
time.sleep(3000000)



