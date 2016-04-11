#!/usr/bin/python
"""
Training Two stacked layer of

Convolutional Autoencoder (CAE)

with ReLu Acticvation Function

"""

# system library modules

import os, sys, time 
import scipy.io as sio

# try:
#     import PIL.image as Image
# except ImportError:
#     import Image
from PIL import Image


# public library modules

import numpy as np 
import theano 
import theano.tensor as T 
from theano import sandbox
import ipdb
import cPickle
import pickle
import matplotlib.pyplot as plt
import matplotlib.cm as cm
# private library modules

from cae_tools import load_data 
from conv_aes.ConvAE import ConvAE 
from conv_aes.ConvAE import ConvRWAE 
from dlt_utils import tile_raster_images 
from conv_aes.ConvNet import ConvNetLayer 
import scipy.io as sio

### Global wise parameter

print '... Loading data and parameters'

batch_size = 2000                      # number of images in each batch
n_epochs = 100                        # number of experiment epochs
learning_rate = 0.1                   # learning rate of SGD
nkerns = 16                           # number of feature maps in ConvAE
dataset = 'data/mnist.pkl.gz'         # address of data
rng = np.random.RandomState(23455)  # random generator
filter_size = 5
n_images = 20
results_dir = 'results/'

# datasets=load_data(dataset)
#ipdb.set_trace()
### Loading and preparing dataset
# train_set_x, train_set_y = datasets[0]
# valid_set_x, valid_set_y = datasets[1]
# test_set_x, test_set_y = datasets[2]

data_x = pickle.load(open('cifar10_patches_8x8.pkl','r'))
n_samples, n_feat = data_x.shape
data_x = data_x.reshape((n_samples, 8, 8, 3))
data_x = np.transpose(data_x, axes=[0, 3, 1, 2])
train_set_x = theano.shared(np.asarray(data_x,
                                          dtype=theano.config.floatX),
                            borrow=True)
ipdb.set_trace()
n_train_batches=train_set_x.get_value(borrow=True).shape[0]
# n_valid_batches=valid_set_x.get_value(borrow=True).shape[0]
# n_test_batches=test_set_x.get_value(borrow=True).shape[0]

n_train_batches /= batch_size  # number of train data batches
# n_valid_batches /= batch_size  # number of valid data batches
# n_test_batches /= batch_size   # number of test data batches

def plot_recon():
    data = cPickle.load(open('cae_results.pkl', 'r'))
    train_data = train_set_x.get_value()
    orig = train_data.reshape(train_data.shape[0], 28, 28)
    recon = data[0].reshape(data[0].shape[0], 28, 28)
    fig = plt.figure()
    for i in range(1, 4):
        print i
        ax1 = fig.add_subplot(2, 3, i)
        ax1.imshow(orig[i, :], cmap=cm.Greys)
        ax2 = fig.add_subplot(2, 3, i+3)
        ax2.imshow(recon[i, :], cmap=cm.Greys)
    plt.show()

def plt_weights():
    data = cPickle.load(open('cae_results.pkl', 'r'))
    w1 = data[1]
    w1 = w1.reshape(w1.shape[0], 5, 5)
    w2 = data[2]
    w2 = w2.reshape(w1.shape[0], 5, 5)
    fig1 = plt.figure()
    fig2 = plt.figure()
    for i in range(1, 50):
        print i
        ax1 = fig1.add_subplot(5, 10, i)
        ax1.imshow(w1[i, :], cmap=cm.Greys)
        ax2 = fig2.add_subplot(5, 10, i)
        ax2.imshow(w2[i, :], cmap=cm.Greys)
    plt.show()


################
# Train 1st CAE
#################

index=T.lscalar()  # batch index

# x = T.matrix('x')   # input data source
x = T.ftensor4('x')   # input data source
y = T.ivector('y')  # input data label

# ishape = (28, 28)  # image shape
ishape = (3, 8, 8)  # image shape

print '... Input data and parameters are loaded'

### Building model

print '... Building CAE model'

# data_in = x.reshape((batch_size, 1, 28, 28))
data_in = x.reshape((batch_size, 3, 8, 8))

#CAE=ConvRWAE(rng,
#             data_in=data_in,
#             image_shape=(batch_size, 1, 28, 28),
#             filter_shape=(nkerns, 1, 14, 14))

CAE_1 = ConvAE(rng,
             data_in = data_in,
             image_shape = (batch_size, 3, 8, 8),
           filter_shape = (nkerns, 3, filter_size, filter_size),
           activation_function = 'sigmoid'
           )


cost, updates, grads, feature_map, feature_map1, feature_map2, feat_sparsity, examp_sparsity, sparsity, sparse_filter = CAE_1.get_cost_update(learning_rate=learning_rate)

## Test model

# test_model = theano.function(
#                            [index],
#                            cost,
#                            #sandbox.cuda.basic_ops.gpu_from_host(cost),
#                            #sandbox.gpuarray.basic_ops.gpu_from_host(cost),
#                            givens={
#                                    x: test_set_x[index*batch_size:(index+1)*batch_size]
#                                    }
#                            )

## Validate model

# validate_model=theano.function(
#                                [index],
#                                cost,
#                                #sandbox.cuda.basic_ops.gpu_from_host(cost),
#                                #sandbox.gpuarray.basic_ops.gpu_from_host(cost),
#                                givens={
#                                        x: valid_set_x[index*batch_size:(index+1)*batch_size]
#                                        }
#                                )
## Train model

train_model=theano.function(
                            inputs=[index],
                            #outputs=sandbox.cuda.basic_ops.gpu_from_host(cost),
                            #outputs=sandbox.gpuarray.basic_ops.gpu_from_host(cost),
                            outputs=(cost, updates[0][0], grads[0], feature_map, feature_map1, feature_map2, feat_sparsity, examp_sparsity, sparsity, sparse_filter),
                            updates=updates,
                            givens={x: train_set_x[index*batch_size:(index+1)*batch_size]}
                            )

## Get Feature Map

get_feature_map = theano.function(
                            inputs=[index],
                            #outputs=sandbox.cuda.basic_ops.gpu_from_host(CAE_1.get_hidden_values()),
                            #outputs=sandbox.gpuarray.basic_ops.gpu_from_host(cost),
                            outputs=CAE_1.get_hidden_values(),
                            givens={x: train_set_x[index*batch_size:(index+1)*batch_size]}
                            )

get_reconstruction = theano.function(
                            inputs=[index],
                            outputs=CAE_1.get_reconstruction(),
                            givens={x: train_set_x[index*batch_size:(index+1)*batch_size]}
                            )

print '... 1st CAE model is built'

print '... Training 1st CAE'

start_time = time.clock()
#ipdb.set_trace()

###### Train the model ########
for epoch in xrange(n_epochs):
    cost_hist = np.empty((n_train_batches,), dtype=theano.config.floatX)
    #print 'epoch %d'% epoch
    for batch_index in xrange(n_train_batches):
    #for batch_index in xrange(1):
        #print 'batch %d' % batch_index
        # cost.append(np.asarray(train_model(batch_index)))
        loss,  updates, grads, feature_map, feature_map1, feature_map2, \
        feat_sparsity, examp_sparsity, sparsity, sparse_filter = train_model(batch_index)
        #print loss
        cost_hist[batch_index] = loss
    print 'Training epoch %d, cost' % epoch, np.mean(cost_hist)
end_time = time.clock()

print 'Training is complete in %.2fm' % ((end_time-start_time)/60.)

#ipdb.set_trace()
###### Get Reconstruction ########

# n_batches = train_set_x.get_value(borrow=True).shape[0] / 1000
n_batches = 100
reconstructed = np.empty((n_batches*batch_size, 1, ishape[0], ishape[1]), dtype=theano.config.floatX)
feature_map = np.empty((n_batches*batch_size, nkerns, ishape[0]+filter_size-1, ishape[1]+filter_size-1),
                       dtype=theano.config.floatX)
# for batch_index in xrange(n_train_batches):
for batch_index in xrange(n_batches):
    #print batch_index
    recon = get_reconstruction(batch_index)
    # reconstructed[batch_index*batch_size:(batch_index+1)*batch_size, :] = recon.reshape((batch_size, np.prod(ishape)))
    reconstructed[batch_index*batch_size:(batch_index+1)*batch_size, :, :, :] = recon
    feat_map = get_feature_map(batch_index)
    feature_map[batch_index*batch_size:(batch_index+1)*batch_size, :, :, :] = feat_map


sio.savemat(results_dir+'reconstructed.mat', {'reconstructed':reconstructed})
sio.savemat(results_dir+'feature_map.mat', {'feature_map':feature_map})
sio.savemat(results_dir+'encode_w.mat', {'encode_w':CAE_1.hidden_layer.W.get_value()})
sio.savemat(results_dir+'decode_w.mat', {'decode_w':CAE_1.recon_layer.W.get_value()})

# ipdb.set_trace()
# save first image feature map
I = np.zeros((n_images*nkerns, feature_map.shape[2] ** 2))
for i in xrange(n_images):
    for j in xrange(nkerns):
        #print i*nkerns+j
        I[i*nkerns+j, :] = feature_map[i,j,:,:].flatten(1)
image = Image.fromarray(
                        tile_raster_images(X=I,
                                           img_shape=feature_map.shape[-2:],
                                           tile_shape=(n_images, nkerns),
                                           tile_spacing=(2, 2))
                        )
image.save('results/1st_CAE_featuremap.png')

ipdb.set_trace()
I = np.zeros((n_images, reconstructed.shape[2] ** 2))
for i in xrange(n_images):
    I[i, :] = reconstructed[i,:,:,:].flatten(1)
# ipdb.set_trace()
image = Image.fromarray(
                        tile_raster_images(X=I,
                                           img_shape=reconstructed.shape[-2:],
                                           tile_shape=(n_images,1),
                                           tile_spacing=(2, 2))
                        )
image.save('results/1st_CAE_reconstructed.png')

# ipdb.set_trace()
### save encoder weights as image ###
I = np.zeros((nkerns, filter_size ** 2))
A = CAE_1.hidden_layer.W.get_value(borrow=True)
for i in xrange(nkerns):
    I[i, :] = A[i, :, :].flatten()
image = Image.fromarray(
                        tile_raster_images(X=I,
                        img_shape=(filter_size, filter_size), tile_shape=(1, nkerns),
                        tile_spacing=(2, 2))
                        )
image.save('results/1st_CAE_filter_image.png')

# ipdb.set_trace()
# save decoder weights as image
I = np.zeros((nkerns, filter_size ** 2))
A = CAE_1.recon_layer.W.get_value(borrow=True)
for i in xrange(nkerns):
    I[i, :] = A[0, i, :, :].flatten(1)
image = Image.fromarray(
                        tile_raster_images(X=I,
                        img_shape=(filter_size, filter_size), tile_shape=(1, nkerns),
                        tile_spacing=(2, 2))
                        )
image.save('results/1st_CAE_decode_image.png')


ipdb.set_trace()


################
# Train 2nd CAE
#################

#batch_size=50

# get trainig data for 2nd CAE
first_hidden_layer = ConvNetLayer(rng,
                                  data_in=data_in,
                                  image_shape=(batch_size, 1, 28, 28),
                                  filter_shape=(nkerns, 1, filter_size, filter_size),
                                  if_pool=True,
                                  activate_mode='relu')
first_hidden_layer.W.set_value(CAE_1.hidden_layer.W.get_value(borrow=True),borrow=True)
first_hidden_layer.b.set_value(CAE_1.hidden_layer.b.get_value(borrow=True),borrow=True)

first_hidden_activation=theano.function(
                            inputs=[index],
                            outputs=sandbox.cuda.basic_ops.gpu_from_host(first_hidden_layer.output),
                            #outputs=sandbox.gpuarray.basic_ops.gpu_from_host(cost),
                            #outputs=first_hidden_layer.output,
                            #updates=updates,
                            givens={
                                    x:train_set_x[index*batch_size:(index+1)*batch_size]
                                    }
                            )

# get hidden actication as training data for 2nd CAE
hidden_set=np.zeros((50000*nkerns,11**2))
for j in xrange(n_train_batches):
    A=np.asarray(first_hidden_activation(j))
    for k in xrange(batch_size):
        for i in xrange(nkerns):
            hidden_set[j*k*nkerns+k*nkerns+i,:]=A[k,i,:,:].flatten(1)

hidden_set=np.asarray(hidden_set,dtype='float32')
shared_hidden_set=theano.shared(np.asarray(hidden_set, )
                         , borrow=True)


# define 2nd CAE
#batch_size=50
hidden_in=x.reshape((batch_size, nkerns, 11, 11))

CAE_2=ConvAE(rng,
             data_in=hidden_in,
             image_shape=(batch_size, nkerns, 11, 11),
             #filter_shape=(nkerns, 1, 14, 14)
           filter_shape=(nkerns, nkerns, filter_size, filter_size),
           activation_function="relu"
           )


cost, updates=CAE_2.get_cost_update(learning_rate=learning_rate)

train_model=theano.function(
                            inputs=[index],
                            outputs=sandbox.cuda.basic_ops.gpu_from_host(cost),
                            #outputs=sandbox.gpuarray.basic_ops.gpu_from_host(cost),
                            #outputs=cost,
                            updates=updates,
                            givens={
                                    x:shared_hidden_set[index*batch_size*nkerns:(index+1)*batch_size*nkerns]
                                    }
                            )

print '... 2nd CAE model is built'

print '... Train 2nd CAE'
for epoch in xrange(n_epochs):
    c=[]
    print 'epoch %d'% epoch

    for batch_index in xrange(n_train_batches):
        #print 'batch %d' % batch_index
        c.append(np.asarray(train_model(batch_index)))

    print 'Training epoch %d, cost' % epoch, np.mean(c)

end_time=time.clock()

print 'Training is complete in %.2fm' % ((end_time-start_time)/60.)

# save 2nd CAE encoder weights as image
I=np.zeros((nkerns ** 2, filter_size ** 2))
A=CAE_2.hidden_layer.W.get_value(borrow=True)
for i in xrange(nkerns):
    for j in xrange(nkerns):
        I[i*nkerns+j,:]=A[i,j,:,:].flatten(1)

image = Image.fromarray(
                        tile_raster_images(X=I,
                        img_shape=(filter_size, filter_size), tile_shape=(16, 16),
                        tile_spacing=(2, 2))
                        )
image.save('data/2nd_CAE_filter_image.png')

# save 2nd CAE decoder weights as image
I=np.zeros((nkerns ** 2, filter_size ** 2))
A=CAE_2.recon_layer.W.get_value(borrow=True)
for i in xrange(nkerns):
    for j in xrange(nkerns):
        I[i*nkerns+j,:]=A[j,i,:,:].flatten(1)

image = Image.fromarray(
                        tile_raster_images(X=I,
                        img_shape=(filter_size, filter_size), tile_shape=(16, 16),
                        tile_spacing=(2, 2))
                        )
image.save('data/2nd_CAE_decode_image.png')

# save {w,b} of the trained 2nd Autoencoder
sio.savemat('data/2nd_CAE_w_encoding',{'w_encoding': CAE_2.hidden_layer.W.get_value(borrow=True)})
sio.savemat('data/2nd_CAE_w_decoding',{'w_decoding': CAE_2.recon_layer.W.get_value(borrow=True)})
sio.savemat('data/2nd_CAE_b_encoding',{'b_encoding': CAE_2.hidden_layer.b.get_value(borrow=True)})
sio.savemat('data/2nd_CAE_b_decoding',{'b_decoding': CAE_2.recon_layer.b.get_value(borrow=True)})

# function for extracting featuremap in 2nd CAE
get_feature_map=theano.function(
                            inputs=[index],
                            outputs=sandbox.cuda.basic_ops.gpu_from_host(CAE_2.get_hidden_values()),
                            #outputs=sandbox.gpuarray.basic_ops.gpu_from_host(cost),
                            #outputs=CAE_2.get_hidden_values(),
                            #updates=updates,
                            givens={
                                    x:shared_hidden_set[index*batch_size*nkerns:(index+1)*batch_size*nkerns]
                                    }
                            )

# save first image feature map in 2nd CAE
I=np.zeros((nkerns ** 2, 17 ** 2))
im=np.asarray(get_feature_map(0))
for i in xrange(nkerns):
    for j in xrange(nkerns):
        I[i*nkerns+j,:]=im[j,i,:,:].flatten(1)

image = Image.fromarray(
                        tile_raster_images(X=I,
                        img_shape=(17, 17), tile_shape=(16, 16),
                        tile_spacing=(2, 2))
                        )
image.save('data/2nd_CAE_featuremap.png')