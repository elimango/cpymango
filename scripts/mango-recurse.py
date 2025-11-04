import c4d

doc = c4d.documents.GetActiveDocument()

def recurse(doc, data):
    if not data:
        data = []
    while doc:
        data.append(doc.GetName())
        data += recurse(doc.GetDown())  # Recurse into children
        doc = doc.GetNext()
    return data

def main(): 
    if doc is None:
        print("No active document.")

    print("\nMaterials:")
    collectmats = recurse(doc.GetFirstMaterial())    
    for mat in collectmats:
        print(f"  {mat.GetName()}")
    print(f"Found {len(collectmats)}")           

    print("\nObjects:")   
    collectobj = recurse(doc.GetFirstObject())
    for obj in collectobj:
        print(f"  {obj.GetName()}")    
    print(f"Found {len(collectobj)}")   

    print("\nRender Settings:")   
    collectrd = recurse(doc.GetFirstRenderData())
    for rd in collectrd:
        print(f"  {rd.GetName()}")    
    print(f"Found {len(collectrd)}")      
    c4d.EventAdd()

if __name__ == '__main__':
    main()