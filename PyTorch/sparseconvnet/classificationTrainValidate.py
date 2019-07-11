# Copyright 2016-present, Facebook, Inc.
# All rights reserved.
#
# This source code is licensed under the license found in the
# LICENSE file in the root directory of this source tree.

import torch
import torch.nn as nn
import torch.optim as optim
import torch.nn.functional as F
from torch.autograd import Variable
import sparseconvnet as s
import time
import os
import math
import numpy as np
from PIL import Image
import pdb
def updateStats(stats, output, target, loss):
    batchSize = output.size(0)
    nClasses= output.size(1)
    if not stats:
        stats['top1'] = 0
        stats['top5'] = 0
        stats['n'] = 0
        stats['nll'] = 0
        stats['confusion matrix'] = output.new().resize_(nClasses,nClasses).zero_()
    stats['n'] = stats['n'] + batchSize
    stats['nll'] = stats['nll'] + loss * batchSize
    _, predictions = output.float().sort(1, True)
    correct = predictions.eq(
        target[:,None].expand_as(output))
    # Top-1 score
    stats['top1'] += correct.narrow(1, 0, 1).sum()
    # Top-5 score
    l = min(5, correct.size(1))
    stats['top5'] += correct.narrow(1, 0, l).sum()
    stats['confusion matrix'].index_add_(0,target,F.softmax(output).data)


def ClassificationTrainValidate(model, dataset, p):
    criterion = F.cross_entropy
    if 'n_epochs' not in p:
        p['n_epochs'] = 100
    if 'initial_lr' not in p:
        p['initial_lr'] = 1e-1
    if 'lr_decay' not in p:
        p['lr_decay'] = 4e-2
    if 'weight_decay' not in p:
        p['weight_decay'] = 1e-4
    if 'momentum' not in p:
        p['momentum'] = 0.9
    if 'check_point' not in p:
        p['check_point'] = False
    if 'use_gpu' not in p:
        p['use_gpu'] = torch.cuda.is_available()
    if p['use_gpu']:
        model.cuda()
    if 'test_reps' not in p:
        p['test_reps'] = 1
    optimizer = optim.SGD(model.parameters(),
        lr=p['initial_lr'],
        momentum = p['momentum'],
        weight_decay = p['weight_decay'],
        nesterov=True)
    if p['check_point'] and os.path.isfile('epoch.pth'):
        p['epoch'] = torch.load('epoch.pth') + 1
        print('Restarting at epoch ' +
              str(p['epoch']) +
              ' from model.pth ..')
        model.load_state_dict(torch.load('model.pth'))
    else:
        p['epoch']=1
    print(p)
    print('#parameters', sum([x.nelement() for x in model.parameters()]))
    for epoch in range(p['epoch'], p['n_epochs'] + 1):
        model.train()
        stats = {}
        for param_group in optimizer.param_groups:
            param_group['lr'] = p['initial_lr'] * \
            math.exp((1 - epoch) * p['lr_decay'])
        start = time.time()
        loss_print = 0
        for batch_idx, batch in enumerate(dataset['train']()):
            if p['use_gpu']:
                batch['input']=batch['input'].cuda()
                batch['target'] = batch['target'].cuda()
            batch['input'].to_variable(requires_grad=True)
            batch['target'] = Variable(batch['target'])
            optimizer.zero_grad()
            #model_start = time.time()
            output = model(batch['input'])
            #model_end = time.time()
            #print('model forward time:' + str(model_end - model_start))
            loss = criterion(output, batch['target'])
            loss_print += loss.data[0]

            if (batch_idx % 10) == 0:
                if (batch_idx == 0):
                    print('epoch:' + str(epoch) + ', batch:' + str(batch_idx) + ', loss:' + str(loss_print))  
                    loss_print = 0
                else:  
                    print('epoch:' + str(epoch) + ', batch:' + str(batch_idx) + ', loss:' + str(loss_print/10.0))
                    loss_print = 0
            updateStats(stats, output.data, batch['target'].data, loss.data[0])
            #back_start = time.time()
            loss.backward()
            #back_end = time.time()
            #print('backward time:'+str(back_end - back_start))
            optimizer.step()
        print(epoch, 'train: top1=%.2f%% top5=%.2f%% nll:%.2f time:%.1fs' %
              (100 *
               (1 -
                1.0 * stats['top1'] /
                   stats['n']), 100 *
                  (1 -
                   1.0 * stats['top5'] /
                   stats['n']), stats['nll'] /
                  stats['n'], time.time() -
                  start))
        cm=stats['confusion matrix'].cpu().numpy()
        np.savetxt('train confusion matrix.csv',cm,delimiter=',')
        cm*=255/(cm.sum(1,keepdims=True)+1e-9)
        Image.fromarray(cm.astype('uint8'),mode='L').save('train confusion matrix.png')
        if p['check_point']:
            torch.save(epoch, 'epoch.pth')
            torch.save(model.state_dict(),'model.pth')

        model.eval()
        s.forward_pass_multiplyAdd_count = 0
        s.forward_pass_hidden_states = 0
        start = time.time()
        if p['test_reps'] ==1:
            stats = {}
            for batch in dataset['val']():
                if p['use_gpu']:
                    batch['input']=batch['input'].cuda()
                    batch['target'] = batch['target'].cuda()
                batch['input'].to_variable()
                batch['target'] = Variable(batch['target'])
                output = model(batch['input'])
                loss = criterion(output, batch['target'])
                updateStats(stats, output.data, batch['target'].data, loss.data[0])
            print(epoch, 'test:  top1=%.2f%% top5=%.2f%% nll:%.2f time:%.1fs' %(
                100 * (1 - 1.0 * stats['top1'] / stats['n']),
                100 * (1 - 1.0 * stats['top5'] / stats['n']),
                stats['nll'] / stats['n'],
                time.time() - start),
                '%.3e MultiplyAdds/sample %.3e HiddenStates/sample' % (
                    s.forward_pass_multiplyAdd_count / stats['n'],
                    s.forward_pass_hidden_states / stats['n']))
        else:
            for rep in range(1,p['test_reps']+1):
                pr=[]
                ta=[]
                idxs=[]
                for batch in dataset['val']():
                    if p['use_gpu']:
                        batch['input']=batch['input'].cuda()
                        batch['target'] = batch['target'].cuda()
                        batch['idx'] = batch['idx'].cuda()
                    batch['input'].to_variable()
                    output = model(batch['input'])
                    pr.append( output.data )
                    ta.append( batch['target'] )
                    idxs.append( batch['idx'] )
                pr=torch.cat(pr,0)
                ta=torch.cat(ta,0)
                idxs=torch.cat(idxs,0)
                if rep==1:
                    predictions=pr.new().resize_as_(pr).zero_().index_add_(0,idxs,pr)
                    targets=ta.new().resize_as_(ta).zero_().index_add_(0,idxs,ta)
                else:
                    predictions.index_add_(0,idxs,pr)
                loss = criterion(predictions/rep, targets)
                stats = {}
                updateStats(stats, predictions, targets, loss.data[0])
                print(epoch, 'test rep ', rep,
                    ': top1=%.2f%% top5=%.2f%% nll:%.2f time:%.1fs' %(
                    100 * (1 - 1.0 * stats['top1'] / stats['n']),
                    100 * (1 - 1.0 * stats['top5'] / stats['n']),
                    stats['nll'] / stats['n'],
                    time.time() - start),
                    '%.3e MultiplyAdds/sample %.3e HiddenStates/sample' % (
                    s.forward_pass_multiplyAdd_count / stats['n'],
                    s.forward_pass_hidden_states / stats['n']))
        cm=stats['confusion matrix'].cpu().numpy()
        np.savetxt('test confusion matrix.csv',cm,delimiter=',')
        cm*=255/(cm.sum(1,keepdims=True)+1e-9)
        Image.fromarray(cm.astype('uint8'),mode='L').save('test confusion matrix.png')
