import c4d
import maxon
import json
import os
import socket
import re
import uuid
from pathlib import Path

overrideName = "lightbox"

takeEmbree = "EMBREE"
takeSketch = "SKETCH"
takeEmbreeRay = "SMEAR"
takeRedshift = "REDSHIFT"
enumlist = [takeEmbree, takeSketch, takeEmbreeRay, takeRedshift]

doc = c4d.documents.GetActiveDocument()

def createOverrideMaterial(doc):
    idColorNode: maxon.Id = maxon.Id("net.maxon.asset.utility.color")

    # Instantiate a material, get its node material and the graph for the standard material space.
    material: c4d.BaseMaterial = c4d.BaseMaterial(c4d.Mmaterial)
    if not material:
        raise MemoryError(f"{material = }")

    nodeMaterial: c4d.NodeMaterial = material.GetNodeMaterialReference()
    graph: maxon.GraphModelRef = nodeMaterial.CreateDefaultGraph(maxon.Id("net.maxon.nodespace.standard"))
    if graph.IsNullValue():
        raise RuntimeError("Could not add standard graph to material.")

    # Attempt to find the BSDF node contained in the default graph setup.
    result: list[maxon.GraphNode] = []
    maxon.GraphModelHelper.FindNodesByAssetId(
        graph, maxon.Id("net.maxon.render.node.bsdf"), True, result)
    if len(result) < 1:
        raise RuntimeError("Could not find BSDF node in material.")
    findBsdf: maxon.GraphNode = result[0]

    # Attempt to find the BSDF node contained in the default graph setup.
    result: list[maxon.GraphNode] = []
    maxon.GraphModelHelper.FindNodesByAssetId(
        graph, maxon.Id("net.maxon.render.node.material"), True, result)
    if len(result) < 1:
        raise RuntimeError("Could not find Material node in material.")
    findMaterial: maxon.GraphNode = result[0]

    # Start modifying the graph by opening a transaction. Node graphs follow a database like 
    # transaction model where all changes are only finally applied once a transaction is committed.
    with graph.BeginTransaction() as transaction:
        maxon.GraphModelHelper.SelectNode(findBsdf)
        findBsdf.Remove()

        colorNode: maxon.GraphNode = graph.AddChild(maxon.Id(), idColorNode)

        # Set the default value of the 'Blend Mode' port, i.e., the value the port has when no 
        # wire is connected to it. This is equivalent to the user setting the value to "Darken" in 
        # the Attribute Manager.
        colorInPort: maxon.GraphNode = colorNode.GetInputs().FindChild("inport@Or_C4V8SClHr4QmvxqLgph")
        currentColor = colorInPort.GetPortValue()
        print(f"Current Color: {currentColor}")
        colorInPort.SetPortValue(maxon.Color64(1.0, 1.0, 1.0))
        colorOutPort: maxon.GraphNode = colorNode.GetOutputs().FindChild("out@BtsN1JSIPNxtPaPD6c_4sl")

        # Get the fore- and background port of the blend node and the color port of the BSDF node.
        materialEmissionInPort: maxon.GraphNode = findMaterial.GetInputs().FindChild("emission")

        # Wire up the two texture nodes to the blend node and the blend node to the BSDF node.
        colorOutPort.Connect(materialEmissionInPort, modes=maxon.WIRE_MODE.NORMAL, reverse=False)

        # Finish the transaction to apply the changes to the graph.
        transaction.Commit()

    # Insert the material into the document and push an update event.
    material.SetName(overrideName)
    doc.InsertMaterial(material)
    return material
def generateRenders(renderData, name, material):
    renderData.SetName(str("elimango/"+name))
    #Change main render settings
    if name == takeSketch:
        renderData[c4d.RDATA_RENDERENGINE] = c4d.RDATA_RENDERENGINE_STANDARD
        renderData[c4d.RDATA_MATERIAL_OVERRIDE] = True
        renderData[c4d.RDATA_MATERIAL_OVERRIDE_LINK] = material
    if name == takeEmbree or name == takeEmbreeRay:
        renderData[c4d.RDATA_RENDERENGINE] = c4d.RDATA_RENDERENGINE_PHYSICAL
        renderData[c4d.RDATA_MATERIAL_OVERRIDE] = False
    if name == takeRedshift:
        renderData[c4d.RDATA_RENDERENGINE] = c4d.RDATA_RENDERENGINE_REDSHIFT
    return renderData

def generatePasses(takeData, enum, objects, material):  
    new = takeData.AddTake(enum, None, None)            
    if new is None:  
        raise RuntimeError("Failed to create the take.")
    group = new.AddOverrideGroup()
    for obj in objects:
        print(f"  {obj.GetName()}")
        # texture_tag = c4d.BaseTag(c4d.Ttexture)
        # texture_tag[c4d.TEXTURETAG_MATERIAL] = material
        if group is None:
            return        
        group.AddToGroup(takeData, obj)
        tag = group.AddTag(takeData, c4d.Ttexture, material)        
        tag[c4d.TEXTURETAG_PROJECTION] = c4d.TEXTURETAG_PROJECTION_UVW           

def getAllObjects(doc):
    """Recursively collects all objects in the hierarchy starting from op."""
    objects = []
    while doc:
        objects.append(doc)
        objects += getAllObjects(doc.GetDown())  # Recurse into children
        doc = doc.GetNext()  # Move to next sibling
    return objects

def getAllRenderData(op):
    settings = []
    while op:
        settings.append(op.GetName())
        settings += getAllRenderData(op.GetDown())  # Recurse into children
        op = op.GetNext()
    return settings

def checkMaterial(doc, name):
    mat = doc.GetFirstMaterial()
    while mat:
        if mat.GetName() == name:
            return mat
        mat = mat.GetDown()
    return

def main():
    if doc is None:
        print("Not in active document.")
        return
    active = doc.GetActiveRenderData()
    takeData = doc.GetTakeData()
    if takeData is None:
        raise RuntimeError("Failed to retrieve the take data.")    
    main = takeData.GetMainTake()
    take = main.GetDown()

    materiallib = checkMaterial(doc, overrideName)
    if materiallib is None:
        material = createOverrideMaterial(doc)
        print(f"Creating Override Material: {overrideName}")
    else:
        material = materiallib
        print(f"Override Material: {materiallib.GetName()}")

    collectobj = getAllObjects(doc.GetFirstObject())
    
    renderers = []
    collectrd = getAllRenderData(doc.GetFirstRenderData())
    for name in enumlist:
        child = active.GetClone()
        child = generateRenders(child, name, material)
        renderers.append(child)
    renderers = list(reversed(renderers))
    for index, i in enumerate(renderers): 
        if i is None or i.GetName() in collectrd:
            print("No render settings found")
            continue
        else:
            doc.InsertRenderData(i, active)
    for name in enumlist:        
        if take is None:
            take = takeData.GetMainTake()
            generatePasses(takeData, name, collectobj, material)
        if name != take.GetName():
            take = take.GetNext()
    # Pushes an update event to Cinema 4D
    c4d.EventAdd()

if __name__ == '__main__':
    main()