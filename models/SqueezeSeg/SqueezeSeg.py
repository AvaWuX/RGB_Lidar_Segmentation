###############################################################
# 	 		Network definition for SqueezeSeg
#                       April 2020
#   	Neil Rodrigues | University of Pennsylvania
#               Adapted from Benjamin Young
###############################################################

import sys
import torch

import torchvision.models as models
sys.path.append('../../')
from config import *
import torch.nn as nn
import torch.nn.functional as F
import pdb

from models.SqueezeSeg.recurrent import Recurrent	
from models.SqueezeSeg.bilateral import BilateralFilter

class Conv(nn.Module):
	def __init__(self, in_channels, out_channels, kernel_size=3,stride=1, padding=1):
		super(Conv,self).__init__()
		self.conv = nn.Conv2d(in_channels, out_channels, kernel_size=kernel_size, stride=stride, padding=padding)
	
	def forward(self,x):
		return F.relu(self.conv(x))


class Deconv(nn.Module):
	def __init__(self, in_channels, out_channels, kernel_size, stride, padding):
		super(Deconv, self).__init__()
		self.deconv = nn.ConvTranspose2d(in_channels,out_channels,kernel_size=kernel_size, stride=stride,padding=padding)

	def forward(self, x):
		return F.relu(self.deconv(x))

def load_pretrained(model,squeezenet):
	name_squeezenet = [i for i,_ in squeezenet.state_dict().items()]
	param_squeezenet = [i for _,i in squeezenet.state_dict().items()]
	names_model = [i for i,_ in model.state_dict().items()]
	
	name_squeezenet.insert(2,0)
	name_squeezenet.insert(2,0)
	param_squeezenet.insert(2,0)
	param_squeezenet.insert(2,0)
	
	if len(names_model)>100:
		name_squeezenet = name_squeezenet[0:52]*2
		param_squeezenet = param_squeezenet[0:52]*2

	new_list = [0]*50
	name_squeezenet.extend(new_list)


	param_squeezenet.extend(new_list)
	i = 0
	
	new_dict = model.state_dict().copy()
	for name, param in model.state_dict().items():
		squeeze_name = name_squeezenet[i]
		squeeze_param = param_squeezenet[i]
		if squeeze_name == 0:
			pass
		elif name == 'fire10.layer_1.conv.weight':
			pass
		elif name == 'fire10.layer_1.conv.bias':
			pass
		else:
			new_dict[name] = squeeze_param
		i += 1
	
	model.load_state_dict(new_dict)


class Fire(nn.Module):
	def __init__( self, in_channels, c_1, c_2):
		"""	
		Args:
			in_channels : Input number of channels
			c_1 : input scaledown to c_1 channels using 1x1 kernel
			c_2 : parallel scaleup tp c_2 channels using 1x1 and 3x3 kernel
		"""
		super(Fire, self).__init__()
		self.layer_1 = Conv(in_channels, c_1, kernel_size=1, stride=1, padding=0)

		self.layer_2_a = Conv(c_1, c_2, kernel_size=1, stride=1, padding=0)
		self.layer_2_b = Conv(c_1, c_2, kernel_size=3, stride=1, padding=1)

	def forward(self,x):
		x = self.layer_1(x)
		x_1 = self.layer_2_a(x)
		x_2 = self.layer_2_b(x)

		return torch.cat([x_1,x_2],1)

class FireDeconv(nn.Module):
	def __init__(self, in_channels, c_1, c_2):
		"""	
		Args:
			in_channels : Input number of channels
			c_1 : input scaledown to c_1 channels using 1x1 kernel
			c_2 : parallel scaleup tp c_2 channels using 1x1 and 3x3 kernel
		"""
		super(FireDeconv, self).__init__()
		self.layer_1 = Conv(in_channels,c_1,kernel_size=1,stride=1,padding=0)
		self.deconv = Deconv(c_1,c_1, kernel_size=[1,4],stride=[1,2],padding=[0,1])

		self.layer_2_a = Conv(c_1, c_2, kernel_size=1, stride=1, padding=0)
		self.layer_2_b = Conv(c_1, c_2, kernel_size=3, stride=1, padding=1)

	def forward(self,x):
		x = self.layer_1(x)
		x = self.deconv(x)

		x_1 = self.layer_2_a(x)
		x_2 = self.layer_2_b(x)
		return torch.cat([x_1,x_2],1)


class SqueezeSeg(nn.Module):
	def __init__(self, data_value):
		super(SqueezeSeg, self).__init__()

		self.data_value = data_value
		self.conv1 = Conv(3, 64, 3, stride=(1,2), padding=1)
		self.conv1_skip = Conv(3, 64, 1, stride=1, padding=0)
		self.pool1 = nn.MaxPool2d(kernel_size=3, stride=(1,2), padding=(1,0),ceil_mode=True)

		self.fire2 = Fire(64, 16, 64)
		self.fire3 = Fire(128, 16, 64)
		self.pool3 = nn.MaxPool2d(kernel_size=3, stride=(1,2), padding=(1,0),ceil_mode=True)

		self.fire4 = Fire(128, 32, 128)
		self.fire5 = Fire(256, 32, 128)
		self.pool5 = nn.MaxPool2d(kernel_size=3, stride=(1,2), padding=(1,0),ceil_mode=True)

		self.fire6 = Fire(256, 48, 192)
		self.fire7 = Fire(384, 48, 192)
		self.fire8 = Fire(384, 64, 256)
		self.fire9 = Fire(512, 64, 256)


		self.fire10 = FireDeconv(512, 64, 128)
		self.fire11 = FireDeconv(256, 32, 64)
		self.fire12 = FireDeconv(128, 16, 32)
		self.fire13 = FireDeconv(64, 16, 32)

		self.drop = nn.Dropout2d()
		self.conv14 = nn.Conv2d(64,self.data_value.NUM_CLASSES,kernel_size=3,stride=1,padding=1)
		self.bf = BilateralFilter(self.data_value, stride=1, padding = (1,2))
		self.rc = Recurrent(self.data_value, stride=1, padding=(1,2))


	def forward(self, x,x2,lidar_mask):

		out_c1 = self.conv1(x)
		out = self.pool1(out_c1)

		out_f3  = self.fire3(self.fire2(out))
		out = self.pool3(out_f3)

		out_f5  = self.fire5(self.fire4(out))
		out = self.pool5(out_f5)		

		out = self.fire6(out)
		out = self.fire7(out)
		out = self.fire8(out)
		out = self.fire9(out)

		out = torch.add(self.fire10(out), out_f5)
		out = torch.add(self.fire11(out), out_f3)
		out = torch.add(self.fire12(out), out_c1)

		out_1 = self.fire13(out)
		out_2 = self.conv1_skip(x)
		
		out = self.drop(torch.add(out_1,out_2))

		out = self.conv14(out)
		if ARGS_BRC:
			bf_w = self.bf(x[:,:3,:,:])
			out = self.rc(out,lidar_mask,bf_w)
		return out

class Net(nn.Module):
	def __init__(self,init_dict):
		super(Net, self).__init__()
		self.model = SqueezeSeg(init_dict)
		squeezenet = models.squeezenet1_1(pretrained=True)
		load_pretrained(self.model,squeezenet)
		self.model.conv1.conv = nn.Conv2d(len(init_dict.CHANNELS), 64, 3, stride=(1,2), padding=1)
		self.model.conv1_skip.conv = nn.Conv2d(len(init_dict.CHANNELS),64, 1, stride=1, padding=0)

		
	def forward(self,x1,x2,mask):
		return self.model.forward(x1,x2,mask)

if __name__ == "__main__":
	import numpy as np
	import pdb
	x = torch.tensor(np.random.rand(2,8,64,512).astype(np.float32))
	
	model = Net(data_dict).cuda()
	mask = torch.tensor(np.random.rand(2,1,64,512).astype(np.float32))
	y = model(x.cuda(),x.cuda(),mask.cuda())
	print('output shape:', y.shape)
	assert y.shape == (2,4,64,512), 'output shape (2,4,64,512) is expected!'
	print('test ok!')
