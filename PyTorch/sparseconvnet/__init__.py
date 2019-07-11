# Copyright 2016-present, Facebook, Inc.
# All rights reserved.
#
# This source code is licensed under the license found in the
# LICENSE file in the root directory of this source tree.

forward_pass_multiplyAdd_count = 0
forward_pass_hidden_states = 0
from .abstract import abstract
from .activations import Tanh, Sigmoid, ReLU, ELU
from .add import Add_fun, Add2_fun
from .averagePooling import AveragePooling
from .batchNormalization import BatchNormalization, BatchNormReLU, BatchNormLeakyReLU
from .classificationTrainValidate import ClassificationTrainValidate
from .convolution import Convolution
from .deconvolution import Deconvolution
from .denseDeconvolution import DenseDeconvolution
from .denseToSparse import DenseToSparse
from .fusion import Fusion
from .getConvMask import GetConvMask
from .identity import Identity
from .inputBatch import InputBatch
from .linear import Linear
from .maxPooling import MaxPooling
from .metadata import Metadata
from .merge import Merge
from .networkArchitectures import *
from .networkInNetwork import NetworkInNetwork
from .sample import Sample, SampleLocation, SampleFeature
from .sequential import Sequential
from .sparseConvNetTensor import SparseConvNetTensor
from .sparseToDense import SparseToDense, SparseToDenseFunction
from .submanifoldConvolution import SubmanifoldConvolution, ValidConvolution
from .upSampleLocations import upSampleLocations
from .tables import *

def concatenate_feature_planes(input):
    output = SparseConvNetTensor()
    output.metadata = input[0].metadata
    output.spatial_size = input[0].metadata
    output.features=torch.cat([i.features for i in input],1)
    return output

def add_feature_planes(input):
    output = SparseConvNetTensor()
    output.metadata = input[0].metadata
    output.spatial_size = input[0].metadata
    output.features=sum([i.features for i in input])
    return output
