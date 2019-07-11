# Copyright 2016-present, Facebook, Inc.
# All rights reserved.
#
# This source code is licensed under the license found in the
# LICENSE file in the root directory of this source tree.

from torch.autograd import Function, Variable
from torch.nn import Module
from .utils import *
from .sparseConvNetTensor import SparseConvNetTensor
#from .concat import Concat
#from .structure import Structure

class JoinTable(Module):
    def forward(self, input):
        output = SparseConvNetTensor()
        output.metadata = input[0].metadata
        output.spatial_size = input[0].spatial_size
        output.features=torch.cat([i.features for i in input],1)
        return output
    def input_spatial_size(self,out_size):
        return out_size

class JoinTable2(Module):
    def __init__(self):
        super(JoinTable2, self).__init__()
        self.concat = Concat()
    def forward(self, input):
        return self.concat(input[0], input[1])
    def input_spatial_size(self,out_size):
        return out_size


class AddTable(Module):
    def forward(self, input):
        output = SparseConvNetTensor()
        output.metadata = input[0].metadata
        output.spatial_size = input[0].spatial_size
        output.features=sum([i.features for i in input])
        return output
    def input_spatial_size(self,out_size):
        return out_size

class ConcatTable(Module):
    def forward(self, input):
        return [module(input) for module in self._modules.values()]
    def add(self, module):
        self._modules[str(len(self._modules))]=module
        return self
    def input_spatial_size(self,out_size):
        return self._modules['0'].input_spatial_size(out_size)
