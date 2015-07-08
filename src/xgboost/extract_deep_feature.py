#!/usr/bin/env python

import os, sys
import time
import argparse
import cPickle
import numpy as np

CAFFE_ROOT = 'third-parties/caffe'
sys.path.insert(0, os.path.join(CAFFE_ROOT, 'python'))
import caffe

parser = argparse.ArgumentParser(description='Train a caffe model')
parser.add_argument('--gpu_id', dest='gpu_id',
                    help='GPU device to use [0]',
                    default=0, type=int)
parser.add_argument('--rank_num)', dest='rank_num',
                    help='rank num',
                    default=1, type=int)
parser.add_argument('--phase', dest='phase',
                    help='train test',
                    default='train', type=str)
parser.add_argument('--task', dest='task',
                    help='all front rear side front_side rear_side',
                    default='all', type=str)
parser.add_argument('--level', dest='level',
                    help='make model',
                    default='make', type=str)
args = parser.parse_args()

if args.task == 'all':
    task_str = ''
else:
    task_str = '_'+args.task
level_str = '_'+args.level
solver_prototxt = 'models/compcar'+task_str+level_str+'/solver.prototxt'
pretrained_model = 'models/bvlc_googlenet.caffemodel'


DATA_ROOT = 'data'
im_list_file = 'data/train_test_split/classification/'+args.phase+task_str+'.txt'
with open(im_list_file) as fd:
    gt = map(lambda s: s.strip(), fd.readlines())

FEAT_FILE = './cache/%s_deep_feat.pkl' % args.phase


if os.path.exists(FEAT_FILE):
    with open(FEAT_FILE, 'r') as fd:
        feat = cPickle.load(fd)
        print "feature file loaded from " + FEAT_FILE
else:
    caffe.set_device(args.gpu_id)
    net = caffe.Net(solver_prototxt, pretrained_model, caffe.TEST)
    caffe.set_mode_gpu()
    transformer = caffe.io.Transformer({'data': net.blobs['data'].data.shape})
    transformer.set_transpose('data', (2, 0, 1))
    transformer.set_raw_scale('data', 255)
    transformer.set_channel_swap('data', (2, 1, 0))

    net.blobs['data'].reshape(1, 3, 224, 224)

    feats = np.zeros([len(gt), net.blobs['pool5/7x7_s1'].data.shape[1]])
    print 'feature extraction begins ... ...'
    for i, img_path in enumerate(gt):
        t1 = time.time()
        net.blobs['data'].data[...] = transformer.preprocess('data', caffe.io.load_image(os.path.join(DATA_ROOT, 'cropped_image', img_path)))
        out = net.forward()
        feats[i, :] = net.blobs['pool5/7x7_s1'].data.flatten()
        t2 = time.time()
        print img_path+' finished in %f seconds' % (t2-t1)
    print 'feature extraction finished ... ...'
    feats = ([x[0] for x in gt], feats)
    with open(FEAT_FILE, 'wb') as fd:
        cPickle.dump(feats, fd, cPickle.HIGHEST_PROTOCOL)