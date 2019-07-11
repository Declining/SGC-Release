# Copyright 2016-present, Facebook, Inc.
# All rights reserved.
#
# This source code is licensed under the license found in the
# LICENSE file in the root directory of this source tree.

# 'SubmanifoldConvolution == ValidConvolution'

import sparseconvnet
from torch.autograd import Function, Variable
from torch.nn import Module, Parameter
from .utils import *
from .sparseConvNetTensor import SparseConvNetTensor


class ValidConvolutionFunction(Function):
    @staticmethod
    def forward(
        ctx,
        input_features,
        weight,
        bias,
        input_metadata,
        spatial_size,
        dimension,
        filter_size):
        ctx.input_features=input_features
        ctx.input_metadata=input_metadata
        ctx.spatial_size=spatial_size
        ctx.weight=weight
        ctx.bias=bias
        ctx.output_features=input_features.new()
        ctx.dimension=dimension
        ctx.filter_size=filter_size
        sparseconvnet.forward_pass_multiplyAdd_count +=\
            dim_typed_fn(
                dimension, input_features, 'ValidConvolution_updateOutput')(
                spatial_size,
                filter_size,
                input_metadata.ffi,
                input_features,
                ctx.output_features,
                weight,
                bias if bias is not None else nullptr,
                0, #remove this parameter!!
                torch.cuda.IntTensor() if input_features.is_cuda else nullptr)
        sparseconvnet.forward_pass_hidden_states += ctx.output_features.nelement()
        return ctx.output_features
    @staticmethod
    def backward(ctx, grad_output):
        grad_input=Variable(grad_output.data.new())
        grad_weight=Variable(grad_output.data.new().resize_as_(ctx.weight).zero_())
        if ctx.bias is None:
            grad_bias=None
        else:
            grad_bias = Variable(grad_output.data.new().resize_as_(ctx.bias).zero_())
        dim_typed_fn(
            ctx.dimension, ctx.input_features, 'ValidConvolution_backward')(
            ctx.spatial_size,
            ctx.filter_size,
            ctx.input_metadata.ffi,
            ctx.input_features,
            grad_input.data,
            grad_output.data.contiguous(),
            ctx.weight,
            grad_weight.data,
            grad_bias.data if grad_bias is not None else nullptr,
            0, #remove this parameter
            torch.cuda.IntTensor() if ctx.input_features.is_cuda else nullptr)
        return grad_input, grad_weight, grad_bias, None, None, None, None

class ValidConvolution(Module):
    def __init__(self, dimension, nIn, nOut, filter_size, bias):
        Module.__init__(self)
        self.dimension = dimension
        self.nIn = nIn
        self.nOut = nOut
        self.filter_size = toLongTensor(dimension, filter_size)
        self.filter_volume = self.filter_size.prod()
        std = (2.0 / nIn / self.filter_volume)**0.5
        self.weight = Parameter(torch.Tensor(
            nIn * self.filter_volume, nOut
        ).normal_(0, std))
        if bias:
            self.bias = Parameter(torch.Tensor(nOut).zero_())
        else:
            self.bias = None

    def forward(self, input):
        assert input.features.ndimension()==0 or input.features.size(1) == self.nIn
        output = SparseConvNetTensor()
        output.metadata = input.metadata
        output.spatial_size = input.spatial_size
        output.features=ValidConvolutionFunction.apply(
            input.features,
            self.weight,
            self.bias,
            input.metadata,
            input.spatial_size,
            self.dimension,
            self.filter_size)
        return output

    def __repr__(self):
        s = 'ValidConvolution ' + str(self.nIn) + '->' + str(self.nOut) + ' C'
        if self.filter_size.max() == self.filter_size.min():
            s = s + str(self.filter_size[0])
        else:
            s = s + '(' + str(self.filter_size[0])
            for i in self.filter_size[1:]:
                s = s + ',' + str(i)
            s = s + ')'
        return s

    def input_spatial_size(self, out_size):
        return out_size

class SubmanifoldConvolution(ValidConvolution):
    pass
