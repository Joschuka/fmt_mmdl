from inc_noesis import *
import os

#Version 0.8.1

# =================================================================
# Plugin options
# =================================================================

dumpPath = r"" # set the path dump, only necessary if you're using the texture scanning. For ex : r"D:\\Metroid dread\\010093801237C000\\romfs"
bLoadVertexColors = False #if set to True, load the vertex colors for the mesh
bShowAllMeshes = False #if set to True will display all meshes in the file, including vfx meshes and others
bLoadAnims = True #if set to True, will ask for an animation folder and load every file there

# =================================================================
# Misc
# =================================================================

def registerNoesisTypes():
    handle = noesis.register("Metroid dread",".mmdl;.bcmdl")
    noesis.setHandlerTypeCheck(handle, CheckType)
    noesis.setHandlerLoadModel(handle, LoadModel)
    handle = noesis.register("Metroid dread",".bctex")
    noesis.setHandlerTypeCheck(handle, CheckTextureType)
    noesis.setHandlerLoadRGBA(handle, LoadRGBA)
    return 1
    
def Align(bs, n):
    value = bs.tell() % n
    if (value):
        bs.seek(n - value, 1) 

#Thanks to @MrCheeze_ for the hash function info   
crcTable = [0x0000000000000000, 0xB32E4CBE03A75F6F, 0xF4843657A840A05B, 0x47AA7AE9ABE7FF34, 0x7BD0C384FF8F5E33, 0xC8FE8F3AFC28015C, 0x8F54F5D357CFFE68, 0x3C7AB96D5468A107,
0xF7A18709FF1EBC66, 0x448FCBB7FCB9E309, 0x0325B15E575E1C3D, 0xB00BFDE054F94352, 0x8C71448D0091E255, 0x3F5F08330336BD3A, 0x78F572DAA8D1420E, 0xCBDB3E64AB761D61,
0x7D9BA13851336649, 0xCEB5ED8652943926, 0x891F976FF973C612, 0x3A31DBD1FAD4997D, 0x064B62BCAEBC387A, 0xB5652E02AD1B6715, 0xF2CF54EB06FC9821, 0x41E11855055BC74E,
0x8A3A2631AE2DDA2F, 0x39146A8FAD8A8540, 0x7EBE1066066D7A74, 0xCD905CD805CA251B, 0xF1EAE5B551A2841C, 0x42C4A90B5205DB73, 0x056ED3E2F9E22447, 0xB6409F5CFA457B28,
0xFB374270A266CC92, 0x48190ECEA1C193FD, 0x0FB374270A266CC9, 0xBC9D3899098133A6, 0x80E781F45DE992A1, 0x33C9CD4A5E4ECDCE, 0x7463B7A3F5A932FA, 0xC74DFB1DF60E6D95,
0x0C96C5795D7870F4, 0xBFB889C75EDF2F9B, 0xF812F32EF538D0AF, 0x4B3CBF90F69F8FC0, 0x774606FDA2F72EC7, 0xC4684A43A15071A8, 0x83C230AA0AB78E9C, 0x30EC7C140910D1F3,
0x86ACE348F355AADB, 0x3582AFF6F0F2F5B4, 0x7228D51F5B150A80, 0xC10699A158B255EF, 0xFD7C20CC0CDAF4E8, 0x4E526C720F7DAB87, 0x09F8169BA49A54B3, 0xBAD65A25A73D0BDC,
0x710D64410C4B16BD, 0xC22328FF0FEC49D2, 0x85895216A40BB6E6, 0x36A71EA8A7ACE989, 0x0ADDA7C5F3C4488E, 0xB9F3EB7BF06317E1, 0xFE5991925B84E8D5, 0x4D77DD2C5823B7BA,
0x64B62BCAEBC387A1, 0xD7986774E864D8CE, 0x90321D9D438327FA, 0x231C512340247895, 0x1F66E84E144CD992, 0xAC48A4F017EB86FD, 0xEBE2DE19BC0C79C9, 0x58CC92A7BFAB26A6,
0x9317ACC314DD3BC7, 0x2039E07D177A64A8, 0x67939A94BC9D9B9C, 0xD4BDD62ABF3AC4F3, 0xE8C76F47EB5265F4, 0x5BE923F9E8F53A9B, 0x1C4359104312C5AF, 0xAF6D15AE40B59AC0,
0x192D8AF2BAF0E1E8, 0xAA03C64CB957BE87, 0xEDA9BCA512B041B3, 0x5E87F01B11171EDC, 0x62FD4976457FBFDB, 0xD1D305C846D8E0B4, 0x96797F21ED3F1F80, 0x2557339FEE9840EF,
0xEE8C0DFB45EE5D8E, 0x5DA24145464902E1, 0x1A083BACEDAEFDD5, 0xA9267712EE09A2BA, 0x955CCE7FBA6103BD, 0x267282C1B9C65CD2, 0x61D8F8281221A3E6, 0xD2F6B4961186FC89,
0x9F8169BA49A54B33, 0x2CAF25044A02145C, 0x6B055FEDE1E5EB68, 0xD82B1353E242B407, 0xE451AA3EB62A1500, 0x577FE680B58D4A6F, 0x10D59C691E6AB55B, 0xA3FBD0D71DCDEA34,
0x6820EEB3B6BBF755, 0xDB0EA20DB51CA83A, 0x9CA4D8E41EFB570E, 0x2F8A945A1D5C0861, 0x13F02D374934A966, 0xA0DE61894A93F609, 0xE7741B60E174093D, 0x545A57DEE2D35652,
0xE21AC88218962D7A, 0x5134843C1B317215, 0x169EFED5B0D68D21, 0xA5B0B26BB371D24E, 0x99CA0B06E7197349, 0x2AE447B8E4BE2C26, 0x6D4E3D514F59D312, 0xDE6071EF4CFE8C7D,
0x15BB4F8BE788911C, 0xA6950335E42FCE73, 0xE13F79DC4FC83147, 0x521135624C6F6E28, 0x6E6B8C0F1807CF2F, 0xDD45C0B11BA09040, 0x9AEFBA58B0476F74, 0x29C1F6E6B3E0301B,
0xC96C5795D7870F42, 0x7A421B2BD420502D, 0x3DE861C27FC7AF19, 0x8EC62D7C7C60F076, 0xB2BC941128085171, 0x0192D8AF2BAF0E1E, 0x4638A2468048F12A, 0xF516EEF883EFAE45,
0x3ECDD09C2899B324, 0x8DE39C222B3EEC4B, 0xCA49E6CB80D9137F, 0x7967AA75837E4C10, 0x451D1318D716ED17, 0xF6335FA6D4B1B278, 0xB199254F7F564D4C, 0x02B769F17CF11223,
0xB4F7F6AD86B4690B, 0x07D9BA1385133664, 0x4073C0FA2EF4C950, 0xF35D8C442D53963F, 0xCF273529793B3738, 0x7C0979977A9C6857, 0x3BA3037ED17B9763, 0x888D4FC0D2DCC80C,
0x435671A479AAD56D, 0xF0783D1A7A0D8A02, 0xB7D247F3D1EA7536, 0x04FC0B4DD24D2A59, 0x3886B22086258B5E, 0x8BA8FE9E8582D431, 0xCC0284772E652B05, 0x7F2CC8C92DC2746A,
0x325B15E575E1C3D0, 0x8175595B76469CBF, 0xC6DF23B2DDA1638B, 0x75F16F0CDE063CE4, 0x498BD6618A6E9DE3, 0xFAA59ADF89C9C28C, 0xBD0FE036222E3DB8, 0x0E21AC88218962D7,
0xC5FA92EC8AFF7FB6, 0x76D4DE52895820D9, 0x317EA4BB22BFDFED, 0x8250E80521188082, 0xBE2A516875702185, 0x0D041DD676D77EEA, 0x4AAE673FDD3081DE, 0xF9802B81DE97DEB1,
0x4FC0B4DD24D2A599, 0xFCEEF8632775FAF6, 0xBB44828A8C9205C2, 0x086ACE348F355AAD, 0x34107759DB5DFBAA, 0x873E3BE7D8FAA4C5, 0xC094410E731D5BF1, 0x73BA0DB070BA049E,
0xB86133D4DBCC19FF, 0x0B4F7F6AD86B4690, 0x4CE50583738CB9A4, 0xFFCB493D702BE6CB, 0xC3B1F050244347CC, 0x709FBCEE27E418A3, 0x3735C6078C03E797, 0x841B8AB98FA4B8F8,
0xADDA7C5F3C4488E3, 0x1EF430E13FE3D78C, 0x595E4A08940428B8, 0xEA7006B697A377D7, 0xD60ABFDBC3CBD6D0, 0x6524F365C06C89BF, 0x228E898C6B8B768B, 0x91A0C532682C29E4,
0x5A7BFB56C35A3485, 0xE955B7E8C0FD6BEA, 0xAEFFCD016B1A94DE, 0x1DD181BF68BDCBB1, 0x21AB38D23CD56AB6, 0x9285746C3F7235D9, 0xD52F0E859495CAED, 0x6601423B97329582,
0xD041DD676D77EEAA, 0x636F91D96ED0B1C5, 0x24C5EB30C5374EF1, 0x97EBA78EC690119E, 0xAB911EE392F8B099, 0x18BF525D915FEFF6, 0x5F1528B43AB810C2, 0xEC3B640A391F4FAD,
0x27E05A6E926952CC, 0x94CE16D091CE0DA3, 0xD3646C393A29F297, 0x604A2087398EADF8, 0x5C3099EA6DE60CFF, 0xEF1ED5546E415390, 0xA8B4AFBDC5A6ACA4, 0x1B9AE303C601F3CB,
0x56ED3E2F9E224471, 0xE5C372919D851B1E, 0xA26908783662E42A, 0x114744C635C5BB45, 0x2D3DFDAB61AD1A42, 0x9E13B115620A452D, 0xD9B9CBFCC9EDBA19, 0x6A978742CA4AE576,
0xA14CB926613CF817, 0x1262F598629BA778, 0x55C88F71C97C584C, 0xE6E6C3CFCADB0723, 0xDA9C7AA29EB3A624, 0x69B2361C9D14F94B, 0x2E184CF536F3067F, 0x9D36004B35545910,
0x2B769F17CF112238, 0x9858D3A9CCB67D57, 0xDFF2A94067518263, 0x6CDCE5FE64F6DD0C, 0x50A65C93309E7C0B, 0xE388102D33392364, 0xA4226AC498DEDC50, 0x170C267A9B79833F,
0xDCD7181E300F9E5E, 0x6FF954A033A8C131, 0x28532E49984F3E05, 0x9B7D62F79BE8616A, 0xA707DB9ACF80C06D, 0x14299724CC279F02, 0x5383EDCD67C06036, 0xE0ADA17364673F59]

def hashFunction(str):
    checksum = 0xffffffffffffffff
    for c in str:
        checksum = crcTable[(checksum & 0xff) ^ ord(c)] ^ (checksum >> 8)
    return checksum

def ValidateInputDirectory(inVal):
	if os.path.isdir(inVal) is not True:
		return "'" + inVal + "' is not a valid directory."
	return None

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
        # blockSize = 1 << (info.textureLayout1 & 7); breaks on characters\morphball\models\textures\samusvariamorph_d
        if format == 0x1:
            format = "r8"
        elif format == 0xd:
            format = "r8g8"
        elif format == 0x25:
            format = "r8g8b8a8"
        elif format == 0x42:
            format = noesis.NOESISTEX_DXT1
        elif format == 0x44:
            format = noesis.NOESISTEX_DXT5
        elif format == 0x4b:
            format = noesis.FOURCC_BC5 
        elif format == 0x6d:
            format = noesis.FOURCC_BC5 
        else:
            print("UNKNOWN TEXTURE FORMAT !" + str(hex(format)))
            format = noesis.NOESISTEX_UNKNOWN
        
        bRaw = type(format) == str
        if not bRaw:
            blockWidth = blockHeight = 4
            blockSize = 8 if format == noesis.NOESISTEX_DXT1 else 16
            mbH = 4 
            if width < 512:
                mbH = 3
            if width < 256:
                mbH = 2
            maxBlockHeight = rapi.callExtensionMethod("untile_blocklineargob_blockheight", height, mbH)
            widthInBlocks = (width + (blockWidth - 1)) // blockWidth
            heightInBlocks = (height + (blockHeight - 1)) // blockHeight
            textureData = rapi.callExtensionMethod("untile_blocklineargob", textureData, widthInBlocks, heightInBlocks, blockSize, maxBlockHeight)
            textureData = rapi.imageDecodeDXT(textureData, width, height, format)
            format = noesis.NOESISTEX_RGBA32
        else:
            blockWidth = blockHeight = 1
            blockSize = 2**(len(format)//2-1) #no clue if this is true or not but seems to work...
            widthInBlocks = (width + (blockWidth - 1)) // blockWidth
            heightInBlocks = (height + (blockHeight - 1)) // blockHeight
            maxBlockHeight = rapi.callExtensionMethod("untile_blocklineargob_blockheight", height, 4)
            textureData = rapi.callExtensionMethod("untile_blocklineargob", textureData, widthInBlocks, heightInBlocks, blockSize, maxBlockHeight)
            textureData = rapi.imageDecodeRaw(textureData, width, height, format)
            if format == "r8":
                textureData = noesis.deinterleaveBytes(textureData, 0, 1, 4)
                convertedData = bytearray(3*len(textureData))
                for i in range(3): convertedData[i::3] = textureData[0::1]
                textureData = rapi.imageDecodeRaw(convertedData, width, height, "r8g8b8")            
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
# Load animation
# =================================================================
def LoadKFValues(bs, offset, animName, frameCount):
    bs.seek(offset)
    
    seenTypes = [
    0x0,
    0x8 
    ]
    timingType = bs.readUShort() #leaving this name here but not sure if it's for this at all. Maybe some continuity specs 
    if timingType not in seenTypes:
        print("unknown timing type in anim", animName,"at offset", bs.tell()) 
        assert 0
    
    kfCount = bs.readUShort()
    timings = []
    values = []
    kfValues = []
    
    for _ in range(kfCount):
        if timingType: #8
            timings.append(bs.readUByte())
        else: #0
            timings.append(bs.readUShort())
    Align(bs,4)
    
    for _ in range(kfCount):
        values.append([bs.readFloat(), bs.readFloat()]) # first is value, second is derivative ?
        
    allValues = []    
    #linear interpolate for now to test
    # for i in range(len(timings)-1):
        # t0 = timings[i]
        # t1 = timings[i+1]
        # v0 = values[i][0]
        # v1 = values[i+1][0]
        # for t in range(t1-t0):
            # alpha = t/(t1-t0)
            # allValues.append(v0 * (1 - alpha) + v1 * alpha)
            
    #hermite interpolate (educated guess based on data)
    for i in range(len(timings)-1):
        t0 = timings[i]
        t1 = timings[i+1]
        v0 = values[i][0]
        v1 = values[i+1][0]
        s0 = values[i][1] # out slope for point 0
        s1 = values[i+1][1] # in slope for point 1
        # since it seems that this game has C1 continuity no need to bother with slopes, since with this condition in slope = out slope for every point
        for t in range(t1-t0):
            alpha = t/(t1-t0)
            cubicCoeffs = NoeVec4([v0,v1, s0, s1]) * NoeMat44([[2, -3, 0, 1], [-2, 3, 0, 0], [1, -2, 1, 0], [1, -1, 0, 0]])            
            allValues.append(NoeVec4([alpha**3, alpha**2, alpha,1]).dot(cubicCoeffs))
    
    return allValues

def LoadTracks(bs, frameCount, framerate, animName):

    flags = bs.readUInt()    
    semanticValues = []    
    checkpoint = bs.tell()
    
    for i in range(9):
        bs.seek(checkpoint + 4 * i)
        if flags & (2 ** i):
            semanticValues.append(LoadKFValues(bs, bs.readUInt() + checkpoint, animName, frameCount))
        else:
            value = bs.readFloat()
            semanticValues.append([value for _ in range(int(frameCount))])
    
    rotNoeKeyFramedValues = []
    posNoeKeyFramedValues = []
    scaleNoeKeyFramedValues = []
    
    #position
    for t,(x,y,z) in enumerate(zip(semanticValues[0],semanticValues[1],semanticValues[2])):
        posNoeKeyFramedValues.append(NoeKeyFramedValue(t / 30, NoeVec3([x,y,z])))
    #rotation
    for t,(x,y,z) in enumerate(zip(semanticValues[3],semanticValues[4],semanticValues[5])):
        rotNoeKeyFramedValues.append(NoeKeyFramedValue(t / 30, NoeAngles([x,y,z]).toDegrees().toMat43_XYZ().toQuat()))
    #scale
    for t,(x,y,z) in enumerate(zip(semanticValues[6],semanticValues[7],semanticValues[8])):
        scaleNoeKeyFramedValues.append(NoeKeyFramedValue(t / 30, NoeVec3([x,y,z])))    
    
    return [posNoeKeyFramedValues, rotNoeKeyFramedValues, scaleNoeKeyFramedValues]

def LoadAnim(data, joints, jointHashToIDMap, animName):
    bs = NoeBitStream(data)
    
    framerate = 30
    bs.readUInt() #fourCC
    bs.readUInt() #version stuff
    bs.readUInt() #reserved
    frameCount = bs.readFloat()
    entryCount = bs.readUInt()
    bs.readInt() #unk, always -1 ?
    keyframedJointList = []
    
    checkpoint = bs.tell()
    for i in range(entryCount):
        bs.seek(checkpoint + 0x30 * i)
        hash = bs.readUInt64()
        if hash not in jointHashToIDMap:
            continue
        jointID = jointHashToIDMap[hash]
        posNoeKeyFramedValues, rotNoeKeyFramedValues, scaleNoeKeyFramedValues = LoadTracks(bs, frameCount, framerate, animName)
        
        animatedJoint = NoeKeyFramedBone(jointID)
        animatedJoint.setRotation(rotNoeKeyFramedValues, noesis.NOEKF_ROTATION_QUATERNION_4,noesis.NOEKF_INTERPOLATE_NEAREST)
        animatedJoint.setTranslation(posNoeKeyFramedValues, noesis.NOEKF_TRANSLATION_VECTOR_3,noesis.NOEKF_INTERPOLATE_NEAREST)
        animatedJoint.setScale(scaleNoeKeyFramedValues, noesis.NOEKF_SCALE_VECTOR_3,noesis.NOEKF_INTERPOLATE_NEAREST)
        keyframedJointList.append(animatedJoint)
    
    anim = None
    if keyframedJointList:
        anim = NoeKeyFramedAnim(animName, joints, keyframedJointList, framerate)
    return anim

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
    bTextureScanning = False
    if dumpPath:
        bTextureScanning = True
    
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
    jointHashToIDMap = {}
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
    
    
        jointHashToIDMap[hashFunction(jointName)] = i
    joints = rapi.multiplyBones(joints)
    
    # =================================================================
    # Animations
    # =================================================================
    animList = []
    animPaths = []
    if bLoadAnims:
        animDir = noesis.userPrompt(noesis.NOEUSERVAL_FOLDERPATH, "Open Folder", "Select the folder to get the animations from", noesis.getSelectedDirectory(), ValidateInputDirectory)
        if animDir is not None:
            for root, dirs, files in os.walk(animDir):
                for fileName in files:
                    lowerName = fileName.lower()
                    if lowerName.endswith(".bcskla") or lowerName.endswith(".manm"):
                        fullPath = os.path.join(root, fileName)
                        animPaths.append(fullPath)
            for animPath in animPaths:
                with open(animPath, "rb") as animStream:
                    animName = "".join(os.path.basename(animPath).split(".")[:-1]) # Filename without extension
                    anim = LoadAnim(animStream.read(), joints, jointHashToIDMap, animName)
                    if anim is not None:
                        animList.append(anim)
                    
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
    
    #Grab the names
    meshNames = []
    for info in meshesInfo:
        bs.seek(info[2])
        nameOffset = bs.readUInt64()
        meshesHidden.append(True if bs.readUByte() else False)
        bs.seek(nameOffset)
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
    nonRigidMeshesInfo = []
    bAtLeastOneRigid = False
    for meshIdx, info in enumerate(meshesInfo):
        if not meshesHidden[meshIdx] and not bShowAllMeshes:
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
    if animList:
        mdl.setAnims(animList)
    mdlList.append(mdl)
    
    return 1
    
    
