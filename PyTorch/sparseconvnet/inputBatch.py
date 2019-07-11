# Copyright 2016-present, Facebook, Inc.
# All rights reserved.
#
# This source code is licensed under the license found in the
# LICENSE file in the root directory of this source tree.

import torch
from .metadata import Metadata
from .utils import toLongTensor, dim_fn
from .sparseConvNetTensor import SparseConvNetTensor

class InputBatch(SparseConvNetTensor):
    def __init__(self, dimension, spatial_size):
        self.dimension = dimension
        self.spatial_size = toLongTensor(dimension, spatial_size)
        SparseConvNetTensor.__init__(self, None, None, spatial_size)
        self.features = torch.FloatTensor()
        self.metadata = Metadata(dimension)
        dim_fn(dimension, 'setInputSpatialSize')(
            self.metadata.ffi, self.spatial_size)

    def addSample(self):
        dim_fn(self.dimension, 'batchAddSample')(
            self.metadata.ffi)

    def setLocation(self, location, vector, overwrite=False):
        assert location.min() >= 0 and (self.spatial_size - location).min() > 0
        dim_fn(self.dimension, 'setInputSpatialLocation')(
            self.metadata.ffi, self.features, location, vector, overwrite)

    def setLocation_(self, location, vector, overwrite=False):
        dim_fn(self.dimension, 'setInputSpatialLocation')(
            self.metadata.ffi, self.features, location, vector, overwrite)

    def setLocations(self, locations, vectors, overwrite=False):
        """
        To set n locations in d dimensions, locations can be
        - A size (n,d) LongTensor, giving d-dimensional coordinates -- points
          are added to the current sample, or
        - A size (n,d+1) LongTensor; the extra column specifies the sample
          number (within the minibatch of samples).

          Example with d=3 and n=2:
          Set
          locations = LongTensor([[1,2,3],
                                  [4,5,6]])
          to add points to the current sample at (1,2,3) and (4,5,6).
          Set
          locations = LongTensor([[1,2,3,7],
                                  [4,5,6,9]])
          to add point (1,2,3) to sample 7, and (4,5,6) to sample 9 (0-indexed).

        """
        l = locations.narrow(1,0,self.dimension)
        assert l.min() >= 0 and (self.spatial_size.expand_as(l) - l).min() > 0
        dim_fn(self.dimension, 'setInputSpatialLocations')(
            self.metadata.ffi, self.features, locations, vectors, overwrite)

    def setLocations_(self, locations, vector, overwrite=False):
        dim_fn(self.dimension, 'setInputSpatialLocations')(
            self.metadata.ffi, self.features, locations, vectors, overwrite)
    
    def setInputBatchLocations(self, locations, vectors, nz_nums):
        assert locations.size(0) == nz_nums.sum()
        dim_fn(self.dimension, 'setInputBatchSpatialLocations')(
            self.metadata.ffi, self.features, locations, vectors, nz_nums)

    def addSampleFromTensor(self, tensor, offset, threshold=0):
        self.nActive = dim_fn(
            self.dimension,
            'addSampleFromThresholdedTensor')(
            self.metadata.ffi,
            self.features,
            tensor,
            offset,
            self.spatial_size,
            threshold)

    def precomputeMetadata(self, stride):
        if stride == 2:
            dim_fn(self.dimension, 'generateRuleBooks2s2')(self.metadata.ffi)
        else:
            dim_fn(self.dimension, 'generateRuleBooks3s2')(self.metadata.ffi)
            
    # def getConvMask(self, filter_size):
    #    filter_size = toLongTensor(self.dimension, filter_size)
    #    mask = torch.FloatTensor(self.features.size(0)).fill_(0)
    #    dim_fn(self.dimension, 'getConvMask')(self.metadata.ffi, self.spatial_size, filter_size, mask)
    #    return mask

    def __repr__(self):
        return 'InputBatch<<' + repr(self.features) + repr(self.metadata) + \
            repr(self.spatial_size) + '>>'
