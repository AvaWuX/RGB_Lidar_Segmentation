ROOT_DIR = '/home/neil/cis_522/squeezeSeg/data/CamVid/'
IMG_WIDTH = 512


#### DATALOADER ####
NUM_CLASSES=4
ARGS_NUM_WORKERS = 10
ARGS_TRAIN_BATCH_SIZE=7
ARGS_VAL_BATCH_SIZE=1
ARGS_INPUT_TYPE = 'XYZDIRGB'


ARGS_MODEL = 'SqueezeSeg_1/'
ARGS_SAVE_DIR = '/home/neil/cis_522/squeezeSeg/Saved_model/' 
ARGS_TRAIN_DIR = '/home/neil/cis_522/squeezeSeg/'
ARGS_CUDA = True
ARGS_PRETRAINED = True

OPT_LEARNING_RATE_INIT 	= 1e-4

OPT_BETAS 		= (0.9, 0.999)
OPT_EPS_LOW 		= 1e-08
OPT_WEIGHT_DECAY 	= 1e-4

ARGS_NUM_EPOCHS = 2000
