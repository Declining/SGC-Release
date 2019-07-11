# Copyright 2016-present, Facebook, Inc.
# All rights reserved.
#
# This source code is licensed under the license found in the
# LICENSE file in the root directory of this source tree.

import sparseconvnet
import torch.nn.functional as F
from torch.autograd import Function, Variable
from torch.nn import Module, Parameter
from .utils import *
from .sparseConvNetTensor import SparseConvNetTensor
from .batchNormalization import BatchNormalization

class Sigmoid(Module):
    def forward(self, input):
        output = SparseConvNetTensor()
        output.features = F.sigmoid(input.features)
        output.metadata = input.metadata
        output.spatial_size = input.spatial_size
        return output

class Tanh(Module):
    def forward(self, input):
        output = SparseConvNetTensor()
        output.features = F.tanh(input.features)
        output.metadata = input.metadata
        output.spatial_size = input.spatial_size
        return output

class ReLU(Module):
    def forward(self, input):
        output = SparseConvNetTensor()
        output.features = F.relu(input.features)
        output.metadata = input.metadata
        output.spatial_size = input.spatial_size
        return output

class ELU(Module):
    def forward(self, input):
        output = SparseConvNetTensor()
        output.features = F.elu(input.features)
        output.metadata = input.metadata
        output.spatial_size = input.spatial_size
        return output