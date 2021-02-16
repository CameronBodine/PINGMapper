

from common_funcs import *

class sonObj:
    def __init__(self, sonFile, humFile, projDir, tempC, nchunk):
        # Create necessary attributes
        self.sonFile = sonFile
        self.humFile = humFile
        self.projDir = projDir
        self.tempC = tempC
        self.nchunk = nchunk

        return

    # =========================================================
    def _fread(self, infile, num, typ):
    #def _fread(self, object infile, int num, str typ):
       dat = arr(typ)
       dat.fromfile(infile, num)
       return(list(dat))
