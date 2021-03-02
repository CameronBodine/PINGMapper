


from common_funcs import *
from c_sonObj import sonObj
import time

#===========================================
def rectify_master_func(sonFiles, humFile, projDir):
    start_time = time.time()

    #############################
    # Create a smoothed trackline    # Create a sonObj instance to process trackline
    son = sonObj(sonFiles[2], humFile, projDir)

    # Load son metadata
    



    print(son)
