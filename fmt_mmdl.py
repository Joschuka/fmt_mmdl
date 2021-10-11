from inc_noesis import *

#Version 0.6

# =================================================================
# Plugin options
# =================================================================

dumpPath = r"" # set the path dump, only necessary if you're using the texture scanning. For ex : r"D:\\Metroid dread\\010093801237C000\\romfs"
bTextureScanning = False #If set to True, try to guess which file is associated to the model using the helper file.
bLoadVertexColors = False #if set to True, load the vertex colors for the mesh

# =================================================================
# Misc
# =================================================================
def registerNoesisTypes():
    handle = noesis.register("Metroid dread",".mmdl")
    noesis.setHandlerTypeCheck(handle, CheckType)
    noesis.setHandlerLoadModel(handle, LoadModel)
    handle = noesis.register("Metroid dread",".bctex")
    noesis.setHandlerTypeCheck(handle, CheckTextureType)
    noesis.setHandlerLoadRGBA(handle, LoadRGBA)
    return 1

def CheckTextureType(data):
    bs = NoeBitStream(data)
    bs.setEndian(NOE_LITTLEENDIAN)
    if bs.readUInt() != 1415074893:
        return 0
    return 1
    
def CheckType(data):
    bs = NoeBitStream(data)
    bs.setEndian(NOE_LITTLEENDIAN)
    if bs.readUInt() != 1279544653:
        return 0
    return 1

# =================================================================
# Helper classes
# =================================================================

class VertexInfo:
    def __init__(self):
        self.semantic = None
        self.offset = None
        self.dataType = None
        self.count = None
        
    def parse(self,bs):
        self.semantic = bs.readUInt()
        self.offset = bs.readUInt()
        self.dataType = bs.readUShort() # guess
        self.count = bs.readUShort()
        bs.readUInt() #unk
        
class TexNamePathInfo:
    def __init__(self):
        self.diffuseName = None
        self.diffusePath = None
        self.normalName = None
        self.normalPath = None

class NvBlockHeader():
    def __init__(self):
        self.magic = None
        self.size_ = None
        self.dataSize = None
        self.dataOffset = None
        self.type_ = None
        self.id = None
        self.typeIdx = None

    def parse(self, bs):
        self.magic = bs.readUInt()
        self.size_ = bs.readUInt()
        self.dataSize = bs.readUInt64()
        self.dataOffset = bs.readUInt64()
        self.type_ = bs.readUInt()
        self.id = bs.readUInt()
        self.typeIdx = bs.readUInt()

class NvTextureHeader():
    def __init__(self):
        self.imageSize = None
        self.alignment = None
        self.width = None
        self.height = None
        self.depth = None
        self.target = None
        self.format_ = None
        self.numMips = None
        self.sliceSize = None
        self.textureLayout1 = None
        self.textureLayout2 = None

    def parse(self, bs):
        self.imageSize = bs.readUInt64()
        self.alignment = bs.readUInt()
        self.width = bs.readUInt()
        self.height = bs.readUInt()
        self.depth = bs.readUInt()
        self.target = bs.readUInt()
        self.format_ = bs.readUInt()
        self.numMips = bs.readUInt()
        self.sliceSize = bs.readUInt()
        bs.read('17i') #mip offsets, we only care about the first here
        self.textureLayout1 = bs.readUInt()
        self.textureLayout2 = bs.readUInt()
        bs.readUInt()

# =================================================================
# Load texture
# =================================================================

def LoadRGBA(data, texList):
    global textureList
    textureList = []
    processRGBA(data)
    for tex in textureList:
        texList.append(tex)
    return 1

def processRGBA(data, texName = None, bIsDiffuse = False):
    # Decompress
    tempBs = NoeBitStream(data)    
    tempBs.seek(tempBs.getSize() - 4)
    decompSize = tempBs.readUInt()
    tempBs.seek(8)    
    bs = NoeBitStream(rapi.decompInflate(tempBs.readBytes(tempBs.getSize() - 8),decompSize, 15+32))    
    bs.seek(0x20)
    bs.seek(bs.readUInt() - 8)
    
    # Process the actual xtx file, thanks for the tip KillZ. Credits to : https://github.com/aboood40091/XTX-Extractor/blob/master/xtx_extract.py for the specs
    
    #header
    assert bs.readUInt() == 1316374084, "Wrong texture header"
    headerSize, majorVersion, minorVersion = bs.readUInt(), bs.readUInt(), bs.readUInt()
    assert(majorVersion == 1)
    
    texHeadBlkType = 2
    dataBlkType = 3
    
    texInfo = []
    texData = []
    while(bs.tell() < bs.getSize()):
        checkpoint = bs.tell()
        block = NvBlockHeader()
        block.parse(bs)
        
        if block.magic != 1316373064:
            break
        bs.seek(checkpoint + block.dataOffset)
        if block.type_ == texHeadBlkType:
           texHead = NvTextureHeader()
           texHead.parse(bs)
           texInfo.append(texHead)
        elif block.type_ == dataBlkType:
           texData.append([bs.tell(), block.dataSize])
        bs.seek(checkpoint + block.dataOffset + block.dataSize)    
    
    for info, data in zip(texInfo, texData):
        bs.seek(data[0])
        textureData = bs.readBytes(data[1])
        
        width = info.width
        height = info.height
        format = info.format_       
        blockSize = 1 << (info.textureLayout1 & 7);

        if format == 0x44:
            format = noesis.NOESISTEX_DXT5
        elif format == 0x4b:
            format = noesis.FOURCC_BC5
        
        else:
            print("UNKNOWN TEXTURE FORMAT !" + str(hex(format)))
            format = noesis.NOESISTEX_UNKNOWN

        bRaw = type(format) == str
        if not bRaw:
            blockWidth = blockHeight = 4
            maxBlockHeight = rapi.callExtensionMethod("untile_blocklineargob_blockheight", height, 4)
            widthInBlocks = (width + (blockWidth - 1)) // blockWidth
            heightInBlocks = (height + (blockHeight - 1)) // blockHeight
            textureData = rapi.callExtensionMethod("untile_blocklineargob", textureData, widthInBlocks, heightInBlocks, blockSize, maxBlockHeight)
            textureData = rapi.imageDecodeDXT(textureData, width, height, format)
            format = noesis.NOESISTEX_RGBA32
        if bIsDiffuse:
            textureDataDiffuse = noesis.deinterleaveBytes(textureData, 0, 3, 4)
            textureDataDiffuse = rapi.imageDecodeRaw(textureDataDiffuse, width, height, "r8g8b8")
            textureDataOther = noesis.deinterleaveBytes(textureData, 3, 1, 4)
            #Convert to rgb texture
            convertedData = bytearray(3*len(textureDataOther))
            for i in range(3): convertedData[i::3] = textureDataOther[0::1]
            textureDataOther = rapi.imageDecodeRaw(convertedData, width, height, "r8g8b8")
            if texName is None: #this should never be hit in theory
                tex = NoeTexture("temp.dds", width, height, textureDataDiffuse, format)
                textureList.append(tex)
                tex = NoeTexture("temp_other.dds", width, height, textureDataOther, format)
                textureList.append(tex)
            else:
                tex = NoeTexture(texName + ".dds", width, height, textureDataDiffuse, format)
                textureList.append(tex)
                tex = NoeTexture(texName[:-3] + "_emi.dds", width, height, textureDataOther, format)
                textureList.append(tex)
        else:
            if texName is None:
                tex = NoeTexture("temp.dds", width, height, textureData, format)
            else:
                tex = NoeTexture(texName + ".dds", width, height, textureData, format)
            textureList.append(tex)    
    
    return 1

# =================================================================
# Load model
# =================================================================

def LoadModel(data, mdlList):
    
    ctx = rapi.rpgCreateContext()
    bs = NoeBitStream(data)
    bs.setEndian(NOE_LITTLEENDIAN)
    rapi.processCommands('-texnorepfn')    
    
    bs.readUInt() #fourcc
    bs.readUInt() #version info ?    
    offsets = bs.read('8Q') 
    vBuffOffsToTransform = {}
    
    # =================================================================
    # Joints
    # =================================================================
    
    bs.seek(offsets[7])
    jointCount = bs.readUInt()
    bs.readInt() #always -1 ?
    bs.seek(bs.readUInt64())
    jOffsets = []
    for _ in range(jointCount):
        jOffsets.append(bs.readUInt64())
        bs.readUInt64() #next offset, could be used as a stop when 0 but we already have the jCount
    
    joints = []
    for i,jOffset in enumerate(jOffsets):
        bs.seek(jOffset)
        jointTransOffs, jointNameOffs, jointParentNameOffs = bs.read('3Q')
        bs.seek(jointTransOffs)
        position = NoeVec3(bs.read('3f'))
        rotation = NoeAngles(bs.read('3f')).toDegrees()
        scale = NoeVec3(bs.read('3f')) #always (1,1,1), ignoring
        jointMat = rotation.toMat43_XYZ()
        jointMat[3] = position
        bs.seek(jointNameOffs)
        jointName = bs.readString()
        if jointParentNameOffs:
            bs.seek(jointParentNameOffs)
            jointParentName = bs.readString()
            joints.append(NoeBone(i, jointName, jointMat, jointParentName, -1))
        else:
            joints.append(NoeBone(i, jointName, jointMat, None, -1))
    
    joints = rapi.multiplyBones(joints)
    
    # =================================================================
    # Mesh info
    # =================================================================

    bs.seek(offsets[4])
    meshInfoOffsets = []    
    while(True):#read until the next offset is equal to zero,
        meshInfoOffs = bs.readUInt64()
        nextOffs = bs.readUInt64()
        meshInfoOffsets.append(meshInfoOffs)
        if not nextOffs:
            break
    
    #Get the offsets to the relevant info
    meshesHidden = []
    meshesInfo = []
    for meshInfoOffs in meshInfoOffsets:
        bs.seek(meshInfoOffs)
        meshesInfo.append(bs.read('3Q')) # specs, material info?, name
        meshesHidden.append(False if bs.readUByte() else True)
    
    #Grab the names
    meshNames = []
    for info in meshesInfo:
        bs.seek(info[2])
        bs.seek(bs.readUInt64())
        meshNames.append(bs.readString())
        
    #Grab the texture names if relevant
    textureNamePathInfo = []
    if bTextureScanning:
        textureNamesList = []
        for info in meshesInfo:
            bs.seek(info[1] + 304)
            diffuseNameOffs, _, normalNameOffs = bs.readUInt64(), bs.readUInt64(), bs.readUInt64()
            bs.seek(diffuseNameOffs)
            diffuseName = bs.readString()
            bs.seek(normalNameOffs)
            normalName = bs.readString()
            textureNamesList.append([diffuseName, normalName])
        
        #check if we have at list a valid name, if so load the map from the file
        bHasValidName = False
        for textureNames in textureNamesList:
            diffName, normName = textureNames[0], textureNames[1]
            if diffName or normName:
                bHasValidName = True
                break
                
        texNameMapPath = noesis.getPluginsPath() + os.sep + "python" + os.sep + "dreadMap.txt"
        if bHasValidName and rapi.checkFileExists(texNameMapPath):
            #load the map from the file
            texNameMap = {}
            with open(texNameMapPath) as f:                
                lines = f.readlines()
            for line in lines:
                texNameMap[line.split()[0]] = line.split()[1]
            
            for textureNames in textureNamesList:
                diffName, normName = textureNames[0], textureNames[1]
                info = TexNamePathInfo()
                if diffName and diffName in texNameMap:
                    info.diffuseName = diffName
                    info.diffusePath = dumpPath + os.sep + "textures" + os.sep + texNameMap[diffName]
                if normName and normName in texNameMap:
                    info.normalName = normName
                    info.normalPath =  dumpPath + os.sep + "textures" + os.sep + texNameMap[normName]
                textureNamePathInfo .append(info)
        
    global textureList
    textureList = []
    materialList = []
    textureAdded = {}
    for i, info in enumerate(textureNamePathInfo):
        material = NoeMaterial('mesh_' + str(i) +"_material", "")
        if info.diffusePath is not None:
            if info.diffuseName not in textureAdded:
                processRGBA(rapi.loadIntoByteArray(info.diffusePath),info.diffuseName, True)
                textureAdded[info.diffuseName] = True
            material.setTexture(info.diffuseName + ".dds")
        if info.normalPath is not None:
            if info.normalName not in textureAdded:
                processRGBA(rapi.loadIntoByteArray(info.normalPath),info.normalName)
                textureAdded[info.normalName] = True
            material.setNormalTexture(info.normalName + ".dds")
        materialList.append(material)
    
    
        
    #Grab the mesh specs and commit
    for meshIdx, info in enumerate(meshesInfo):
        if meshesHidden[meshIdx]:
            continue
    
        bs.seek(info[0] + 0x50)
        idxBufferInfoOffset, vBufferInfoOffset, submeshCount = bs.readUInt64(), bs.readUInt64(), bs.readUInt()
        bs.readInt() #always -1 it seems
        submeshInfoOffsetPtr = bs.readUInt64()
        transform = NoeVec3.fromBytes(bs.readBytes(12))
        
        bs.seek(submeshInfoOffsetPtr)
        submeshInfoOffsets = []
        for _ in range(submeshCount):
            submeshInfoOffsets.append(bs.readUInt64())
            bs.readUInt64()
        
        #vertex buffer. Due to some transform we can't commit some semantics directly
        bs.seek(vBufferInfoOffset + 12)
        vBufferSize = bs.readUInt()
        vCount = bs.readUInt()
        compSize = bs.readUInt()
        vBufferOffset = bs.readUInt64()        
        vInfoCount = bs.readUInt()
        vInfos = []
        bs.readInt() #always -1 ?
        
        for _ in range(vInfoCount):
            vInfo = VertexInfo()
            vInfo.parse(bs)
            vInfos.append(vInfo)
        
        bs.seek(vBufferOffset)
        vBuffer = None
        if bs.readUInt() != 559903: #check if buffer is gzip compressed
            bs.seek(-4,1)
            vBuffer = bs.readBytes(vBufferSize)
        else: #compressed
            bs.seek(-4,1)
            vBuffer = rapi.decompInflate(bs.readBytes(compSize),vBufferSize, 15+32) #gzip decomp, for 15 + 32 see : https://stackoverflow.com/questions/1838699/how-can-i-decompress-a-gzip-stream-with-zlib  
        
        #save position, normal and joint indices info because of eventual transforms
        posOffset, normalOffset, jIdxValues, jIdxCount = None, None, None, None
        hasNormals = False
        rapi.rpgClearBufferBinds()        
        for vInfo in vInfos:            
            #Position
            if vInfo.semantic == 0:
                if vInfo.dataType == 3:
                    # rapi.rpgBindPositionBufferOfs(vBuffer, noesis.RPGEODATA_FLOAT, vInfo.count * 4, vInfo.offset)
                    posOffset = vInfo.offset
                else:
                    print("unknown position data type")
                    return 0            
            #Normal
            elif vInfo.semantic == 1:
                if vInfo.dataType == 3:
                    # rapi.rpgBindNormalBufferOfs(vBuffer, noesis.RPGEODATA_FLOAT, vInfo.count * 4, vInfo.offset)
                    normalOffset = vInfo.offset
                    hasNormals = True
                else:
                    print("unknown normal data type")
                    return 0
            #UVs
            elif vInfo.semantic == 2:
                if vInfo.dataType == 3:
                    rapi.rpgBindUV1BufferOfs(vBuffer, noesis.RPGEODATA_FLOAT, vInfo.count * 4, vInfo.offset)
                else:
                    print("unknown uv data type")
                    return 0
            #2nd UV Layer
            elif vInfo.semantic == 3:
                if vInfo.dataType == 3:
                    rapi.rpgBindUV2BufferOfs(vBuffer, noesis.RPGEODATA_FLOAT, vInfo.count * 4, vInfo.offset)
                else:
                    print("unknown uv data type")
                    return 0
            #3rd UV Layer
            elif vInfo.semantic == 4:
                if vInfo.dataType == 3:
                    rapi.rpgBindUVXBufferOfs(vBuffer, noesis.RPGEODATA_FLOAT, vInfo.count * 4, 2, 2, vInfo.offset)
                else:
                    print("unknown uv data type")
                    return 0
            #Colors
            elif vInfo.semantic == 5 and bLoadVertexColors:
                if vInfo.dataType == 3:
                    rapi.rpgBindColorBufferOfs(vBuffer, noesis.RPGEODATA_FLOAT, vInfo.count * 4, vInfo.offset, 4)
                else:
                    print("unknown color data type")
                    return 0

            #Joint indices
            elif vInfo.semantic == 6:
                assert(vInfo.count == 4)
                if vInfo.dataType == 3: # why would you do that...
                    bs2 = NoeBitStream(vBuffer)
                    bs2.seek(vInfo.offset)
                    jIdxCount = vInfo.count
                    jIdxValues = bs2.read(str(vCount * vInfo.count) +'f')
                    jIdxValues = [int(value) for value in jIdxValues]
                    jointIndexBuffer = struct.pack("<" + 'H'*len(jIdxValues), *jIdxValues)
                    rapi.rpgBindBoneIndexBuffer(jointIndexBuffer, noesis.RPGEODATA_USHORT, vInfo.count * 2, vInfo.count)
                else:
                    print("unknown JI data type")
                    return 0
            #Joint weights
            elif vInfo.semantic == 7:
                if vInfo.dataType == 3:
                    rapi.rpgBindBoneWeightBufferOfs(vBuffer, noesis.RPGEODATA_FLOAT, vInfo.count * 4, vInfo.offset, vInfo.count)
                else:
                    print("unknown JW data type")
                    return 0

            #Tangents
            elif vInfo.semantic == 8:
                if vInfo.dataType == 3:
                    rapi.rpgBindTangentBufferOfs(vBuffer, noesis.RPGEODATA_FLOAT, vInfo.count * 4, vInfo.offset)
                else:
                    print("unknown tangent data type")
                    return 0
                    
        #index buffer
        bs.seek(idxBufferInfoOffset + 8)
        assert(bs.readUShort() == 2) # dataType (guess)
        assert(bs.readUShort() == 1) # "count", similar to vBuffer semantics
        idxCount = bs.readUInt()
        compSize = bs.readUInt()
        bs.readInt() #always -1 ?
        idxBufferOffset = bs.readUInt64()
        
        bs.seek(idxBufferOffset)
        idxBuffer = None
        if bs.readUInt() != 559903: #too lazy to find the actual compression flag, just check if the gzip header is there
            bs.seek(-4,1)
            idxBuffer = bs.readBytes(idxCount*2)
        else: #compressed
            bs.seek(-4,1)
            idxBuffer = rapi.decompInflate(bs.readBytes(compSize),idxCount*2, 15+32)        
        
        #Grab the joint map and index information, commit the tris
        skinType = None #a variable to make sure no different skinning types could happen in the same mesh
        for submeshInfoOffs in submeshInfoOffsets:
            bs.seek(submeshInfoOffs)
            skinningType = bs.readUInt()
            if skinType is None:
                skinType = skinningType
            elif skinningType != skinType:
                assert(0, "different skinning types in same mesh")
            idxOffset = bs.readUInt()
            idxCount = bs.readUInt()
            jMapEntryCount = bs.readUInt()
            jMapOffset = bs.readUInt64()
            
            #joint map
            bs.seek(jMapOffset)
            jMap = bs.read(str(jMapEntryCount) + "i")
            rapi.rpgSetBoneMap(jMap)
            
            #if the skinning type is 1, it's necessary to transform the vertices by the single joint they're deformed by
            if skinningType == 1:
                bs2 = NoeBitStream(vBuffer)
                bs2.seek(posOffset)
                positions = [[bs2.readFloat() for _ in range(3)] for __ in range(vCount)]
                bs2.seek(normalOffset)
                if hasNormals:
                    normalCoords = [[bs2.readFloat() for _ in range(3)] for __ in range(vCount)]
                
                
                mat = NoeMat43()
                mat[3] = transform
                positions = [mat.transformPoint(pos) for j,pos in enumerate(positions)]
                # positions = [joints[jMap[jIdxValues[jIdxCount * j]]].getMatrix().transformPoint(pos) for j,pos in enumerate(positions)]
                for j,pos in enumerate(positions):                    
                    if jIdxValues[jIdxCount * j] < len(jMap): #unfortunately hacky, some models (very few, 40/8000 roughly) seem to have indices exceeding the actual jMap length, not sure where this comes from. See Metroid Dread\maps\s010_cave\s010_cave\00000006.MMDL for example or Metroid Dread\maps\s010_cave\subareas\subareapack_chozowarriorx\00000001.MMDL
                        positions[j] = joints[jMap[jIdxValues[jIdxCount * j]]].getMatrix().transformPoint(pos)
                    else:
                        print(meshIdx)
                positions = [x for v in positions for x in v ]

                if hasNormals:
                    # normalCoords = [joints[jMap[jIdxValues[jIdxCount * j]]].getMatrix().transformNormal(norm) for j,norm in enumerate(normalCoords)]  
                    for j,norm in enumerate(normalCoords):                    
                        if jIdxValues[jIdxCount * j] < len(jMap):
                            normalCoords[j] = joints[jMap[jIdxValues[jIdxCount * j]]].getMatrix().transformNormal(norm)
                    normalCoords = [x for v in normalCoords for x in v]                  
                
                posBuffer = struct.pack("<" + 'f'*len(positions), *positions)
                rapi.rpgBindPositionBuffer(posBuffer, noesis.RPGEODATA_FLOAT, 12)
                if hasNormals:
                    normBuffer = struct.pack("<" + 'f'*len(normalCoords), *normalCoords)
                    rapi.rpgBindNormalBuffer(normBuffer, noesis.RPGEODATA_FLOAT, 12)
            #otherwise just bind directly
            else:
                rapi.rpgBindPositionBufferOfs(vBuffer, noesis.RPGEODATA_FLOAT, 12, posOffset)
                if hasNormals: rapi.rpgBindNormalBufferOfs(vBuffer, noesis.RPGEODATA_FLOAT, 12, normalOffset)            
            
            #transform
            mat = NoeMat43()
            mat[3] = transform
            if not skinningType:
                mat *= joints[jMap[0]].getMatrix()
            if skinningType != 1:
                rapi.rpgSetTransform(mat)
            
            #mesh name
            rapi.rpgSetName(meshNames[meshIdx])
            
            #material
            rapi.rpgSetMaterial('mesh_' + str(meshIdx) +"_material")
            
            #commit the tris
            rapi.rpgCommitTriangles(idxBuffer[idxOffset *2:],noesis.RPGEODATA_USHORT , idxCount,noesis.RPGEO_TRIANGLE, 1)
            
    try:
        mdl = rapi.rpgConstructModel()
    except:
        mdl = NoeModel()
    mdl.setModelMaterials(NoeModelMaterials(textureList, materialList))
    mdl.setBones(joints)
    mdlList.append(mdl)
    
    return 1
    
    
