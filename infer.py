###############################################################
# 	 Inference Code for Semantic Segmentation Networks
#                       April 2020
#   	Neil Rodrigues | University of Pennsylvania
###############################################################

# TODO: loop through images and save into a new folder

import os
import time
import numpy
import torch
import math
import pdb

import sys
import numpy as np
import torch.nn as nn
from PIL import Image, ImageOps
import torchvision.models as models

from torch.optim import SGD, Adam
from torch.autograd import Variable

from utils.dataloader import Squeeze_Seg
from torch.utils.data import DataLoader
from torchvision.transforms import ToTensor, ToPILImage, Resize

from utils.util_iou_eval import iouEval


#from dataloader import Squeeze_Seg
#from infer_config import *

#sys.path.append(os.path.join(ARGS_ROOT,'models',ARGS_MODEL_NAME+'/'))

#module = __import__(ARGS_MODEL_NAME)
#Network = getattr(module,"Net")

from utils.util_iou_eval import iouEval, getColorEntry
from utils.calculate_weights import load_class_weights
import pdb

def load_my_state_dict(model, state_dict):
    
    own_state = model.state_dict()
    
    for name, param in state_dict.items():
        if name not in own_state:
            print("[weight not copied for %s]"%(name)) 
            continue
        own_state[name].copy_(param)
    return model

def load_weights_serially(model, state_dict):
    
    own_state = model.state_dict()
    params = [param for _,param in state_dict.items()]
    names = [name for name in own_state]
    #pdb.set_trace()
    for i in range(len(names)):
        own_state[names[i]].copy_(params[i])
    
    return model




def test(model,loader_val,ARGS_CUDA):
	#print('Total Number of classes is {}'.format(NUM_CLASSES))
	'''
	dataset_val = Squeeze_Seg(ROOT_DIR,'val',ARGS_INPUT_TYPE_1,ARGS_INPUT_TYPE_2)

	loader_val = DataLoader(
		dataset_val,
		num_workers = ARGS_NUM_WORKERS,
		batch_size = ARGS_VAL_BATCH_SIZE,
		shuffle = False)
	'''
	weight = load_class_weights().cuda()

	iouEvalVal = iouEval(4)
	labels = np.array([(0,0,0),(255,0,0),(0,255,0),(0,0,255)] )
	model.eval()
	total_time=0
	for step, (image,image_2,mask,label) in enumerate(loader_val):
			
		#start_time = time.time()

		if ARGS_CUDA:
			image = image.cuda()
			image_2 = image_2.cuda()
			label = label.cuda()
			mask = mask.cuda()

		image = Variable(image)
		label = Variable(label)
		mask = Variable(mask)
		image_2 = Variable(image_2)
		start_time = time.time()
		output = model(image,image_2,mask)
		cycle_time = time.time()-start_time
		total_time += cycle_time

		#pdb.set_trace()
		iouEvalVal.addBatch(output.max(1)[1].unsqueeze(1).data, label.data)
		
		
		#label_out = output[0].max(0)[1].byte().cpu().data
		#label_out = torch.Tensor(labels[label_out])
		#label_out = ToPILImage()(label_out)
	    
		#label_in = label.squeeze().cpu()
		#depth = torch.cat([image[0,3:4,:,:].cpu()]*3).permute(1,2,0)

		#depth = (depth-depth.min())/(depth.max()-depth.min())

		#pdb.set_trace()
		#label_in = torch.Tensor(labels[label_in])
		#im = image_2.cpu().squeeze()[2:].permute(1,2,0)	
		#infer_label = np.vstack((label_in,label_out))
		#infer_label = torch.cat((im,depth,label_in/255,label_out/255),0)
		#infer_label = ToPILImage()(infer_label.permute(2,0,1))#.convert('RGB')
		#filename = ARGS_SAVE_DIR + 'infer_' + str(step).zfill(6)+'.png'
		#os.makedirs(os.path.dirname(filename),exist_ok=True)
		
		#infer_label.save(filename)
		#print('Saved file to ',filename)

		#pdb.set_trace()
	iouVal, iou_val_classes = iouEvalVal.getIoU()
	print('[IOU] Average | Background | Car | Pedestrian | Bicycle |  FPS')
	#pdb.set_trace()
	print("      {:.2f}   |    {:.2f}   |{:.2f}|    {:.2f}   |   {:.2f}  | {:.2f}"\
		.format(iouVal.item()*100,iou_val_classes[0].item()*100,iou_val_classes[1].item()*100,iou_val_classes[2].item()*100,\
		iou_val_classes[3].item()*100, step/total_time))

	
		



if __name__ == "__main__":
	model = Network(data_dict).cuda()
	torch.set_num_threads(ARGS_NUM_WORKERS)
	
	model = load_my_state_dict(model, torch.load(ARGS_INFERENCE_MODEL))
	test(model)
