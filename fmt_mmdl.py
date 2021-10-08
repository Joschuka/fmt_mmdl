from inc_noesis import *

#Version 0.1

# =================================================================
# Plugin options
# =================================================================


# =================================================================
# Misc
# =================================================================
def registerNoesisTypes():
    handle = noesis.register("Metroid dread",".mmdl")
    noesis.setHandlerTypeCheck(handle, CheckType)
    noesis.setHandlerLoadModel(handle, LoadModel)	
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

# =================================================================
# Load model
# =================================================================

def LoadModel(data, mdlList):
    
    ctx = rapi.rpgCreateContext()
    bs = NoeBitStream(data)
    bs.setEndian(NOE_LITTLEENDIAN)
    
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
                normalCoords = [[bs2.readFloat() for _ in range(3)] for __ in range(vCount)]
                
                
                mat = NoeMat43()
                mat[3] = transform
                positions = [mat.transformPoint(pos) for j,pos in enumerate(positions)]
                
                positions = [joints[jMap[jIdxValues[jIdxCount * j]]].getMatrix().transformPoint(pos) for j,pos in enumerate(positions)]
                normalCoords = [joints[jMap[jIdxValues[jIdxCount * j]]].getMatrix().transformNormal(norm) for j,norm in enumerate(normalCoords)]                    
                positions = [x for v in positions for x in v ]
                normalCoords = [x for v in normalCoords for x in v]
                
                posBuffer = struct.pack("<" + 'f'*len(positions), *positions)
                normBuffer = struct.pack("<" + 'f'*len(normalCoords), *normalCoords)
                rapi.rpgBindPositionBuffer(posBuffer, noesis.RPGEODATA_FLOAT, 12)
                rapi.rpgBindNormalBuffer(normBuffer, noesis.RPGEODATA_FLOAT, 12)
            #otherwise just bind directly
            else:
                rapi.rpgBindPositionBufferOfs(vBuffer, noesis.RPGEODATA_FLOAT, 12, posOffset)
                rapi.rpgBindNormalBufferOfs(vBuffer, noesis.RPGEODATA_FLOAT, 12, normalOffset)            
            
            #transform
            mat = NoeMat43()
            mat[3] = transform
            if not skinningType:
                mat *= joints[jMap[0]].getMatrix()
            if skinningType != 1:
                rapi.rpgSetTransform(mat)
            
            #mesh name
            rapi.rpgSetName(meshNames[meshIdx])
            
            #commit the tris
            rapi.rpgCommitTriangles(idxBuffer[idxOffset *2:],noesis.RPGEODATA_USHORT , idxCount,noesis.RPGEO_TRIANGLE, 1)
        
    try:
        mdl = rapi.rpgConstructModel()
    except:
        mdl = NoeModel()
    mdl.setBones(joints)
    mdlList.append(mdl)
    
    return 1
    
    