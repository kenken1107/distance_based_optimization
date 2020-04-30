import os
import warnings
import sys
from time import time
import search_optimization_execution as opt_exe

time_start = time()
warnings.filterwarnings("ignore")
##############################################################################################

#######################- YOU NEED TO DEFINE THE PATH of your location -#######################
# Please set your folder path for NN-based optimization folder
PC_folder    = '..\\nearest-neighbor-based-optimization-framework\\' # 1*This needs to be changed

# Please set your folder path for code_program
sys.path.insert(0, '..\\nearest-neighbor-based-optimization-framework\\code_program')# 2*This needs to be changed

# Please put your dataset name that is supposed to be inside "basedata_setting" folder
dataset_name = 'sample.csv' # 3*This needs to be changed as per required

# Please put the folder name for storing the optimization result
folder_name  = "test"    # 4*This needs to be changed

##############################################################################################
##############################################################################################

# Set the folder that stores optimization result
if not os.path.isdir(PC_folder + "\\optimization_results\\"):
    os.mkdir(PC_folder + "\\optimization_results\\")

###-Basic information setting for the optimization-###
opt_info_dict = {
    # the dataset file must be inside of the folder 'basedata_setting'
    "basedata_file":dataset_name,
    # the optimization parameters(DVs) setting file must be inside of the folder 'basedata_setting'
    "optimization_setting_file":"optimization_setting.xlsx",
}

###-search optimization execution-###
opt_exe.search_optimization_execution(PC_folder, opt_info_dict, folder_name)

time_stop = time()
print('Computational effort: {0:.2f} [s]'.format(time_stop - time_start))
