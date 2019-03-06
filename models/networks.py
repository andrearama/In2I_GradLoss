import torch
import torch.nn as nn
from torch.nn import init
import functools
from torch.autograd import Variable
from torch.optim import lr_scheduler
import numpy as np
from scipy.signal import gaussian

###############################################################################
# Functions
###############################################################################



def weights_init_normal(m):
    classname = m.__class__.__name__
    # print(classname)
    if classname.find('Conv') != -1:
        init.uniform(m.weight.data, 0.0, 0.02)
    elif classname.find('Linear') != -1:
        init.uniform(m.weight.data, 0.0, 0.02)
    elif classname.find('BatchNorm2d') != -1:
        init.uniform(m.weight.data, 1.0, 0.02)
        init.constant(m.bias.data, 0.0)


def weights_init_xavier(m):
    classname = m.__class__.__name__
    # print(classname)
    if classname.find('Conv') != -1:
        init.xavier_normal(m.weight.data, gain=1)
    elif classname.find('Linear') != -1:
        init.xavier_normal(m.weight.data, gain=1)
    elif classname.find('BatchNorm2d') != -1:
        init.uniform(m.weight.data, 1.0, 0.02)
        init.constant(m.bias.data, 0.0)


def weights_init_kaiming(m):
    classname = m.__class__.__name__
    # print(classname)
    if classname.find('Conv') != -1:
        init.kaiming_normal(m.weight.data, a=0, mode='fan_in')
    elif classname.find('Linear') != -1:
        init.kaiming_normal(m.weight.data, a=0, mode='fan_in')
    elif classname.find('BatchNorm2d') != -1:
        init.uniform(m.weight.data, 1.0, 0.02)
        init.constant(m.bias.data, 0.0)


def weights_init_orthogonal(m):
    classname = m.__class__.__name__
    print(classname)
    if classname.find('Conv') != -1:
        init.orthogonal(m.weight.data, gain=1)
    elif classname.find('Linear') != -1:
        init.orthogonal(m.weight.data, gain=1)
    elif classname.find('BatchNorm2d') != -1:
        init.uniform(m.weight.data, 1.0, 0.02)
        init.constant(m.bias.data, 0.0)


def init_weights(net, init_type='normal'):
    print('initialization method [%s]' % init_type)
    if init_type == 'normal':
        net.apply(weights_init_normal)
    elif init_type == 'xavier':
        net.apply(weights_init_xavier)
    elif init_type == 'kaiming':
        net.apply(weights_init_kaiming)
    elif init_type == 'orthogonal':
        net.apply(weights_init_orthogonal)
    else:
        raise NotImplementedError('initialization method [%s] is not implemented' % init_type)


def get_norm_layer(norm_type='instance'):
    if norm_type == 'batch':
        norm_layer = functools.partial(nn.BatchNorm2d, affine=True)
    elif norm_type == 'instance':
        norm_layer = functools.partial(nn.InstanceNorm2d, affine=False)
    elif layer_type == 'none':
        norm_layer = None
    else:
        raise NotImplementedError('normalization layer [%s] is not found' % norm_type)
    return norm_layer


def get_scheduler(optimizer, opt, lr=-1):
    if lr == -1:
        lr = opt.lr
    if opt.lr_policy == 'lambda':
        def lambda_rule(epoch):
            lr_l = (1.0 - max(0, epoch - opt.niter) / float(opt.niter_decay+1))
            return lr_l
        scheduler = lr_scheduler.LambdaLR(optimizer, lr_lambda=lambda_rule)
    elif opt.lr_policy == 'step':
        scheduler = lr_scheduler.StepLR(optimizer, step_size=opt.lr_decay_iters, gamma=0.1)
    elif opt.lr_policy == 'plateau':
        scheduler = lr_scheduler.ReduceLROnPlateau(optimizer, mode='min', factor=0.2, threshold=0.01, patience=5)
    else:
        return NotImplementedError('learning rate policy [%s] is not implemented', opt.lr_policy)
    return scheduler


def define_G(input_nc, output_nc, ngf, which_model_netG, norm='batch', use_dropout=False, init_type='normal', gpu_ids=[]):
    netG = None
    use_gpu = len(gpu_ids) > 0
    norm_layer = get_norm_layer(norm_type=norm)

    if use_gpu:
        assert(torch.cuda.is_available())


    if which_model_netG == 'unetMM':
        netG = UnetGeneratorMMU(input_nc, output_nc, 8, ngf, norm_layer=norm_layer, 
use_dropout=use_dropout,  gpu_ids=gpu_ids)
        
    elif which_model_netG == 'resnetMM':
        netG = ResnetGeneratorMM(input_nc, output_nc, ngf, norm_layer=norm_layer, use_dropout=use_dropout, n_blocks=9, gpu_ids=gpu_ids)
    elif which_model_netG == 'resnetMMReverse':
        netG = ResnetGeneratorMMReverse( output_nc, input_nc, ngf, norm_layer=norm_layer, use_dropout=use_dropout, n_blocks=9, gpu_ids=gpu_ids)
    elif which_model_netG == 'resnet_9blocks':
        netG = ResnetGenerator(input_nc, output_nc, ngf, norm_layer=norm_layer, use_dropout=use_dropout, n_blocks=9, gpu_ids=gpu_ids)
    elif which_model_netG == 'resnet_6blocks':
        netG = ResnetGenerator(input_nc, output_nc, ngf, norm_layer=norm_layer, use_dropout=use_dropout, n_blocks=6, gpu_ids=gpu_ids)
    elif which_model_netG == 'unet_128':
        netG = UnetGenerator(input_nc, output_nc, 7, ngf, norm_layer=norm_layer, use_dropout=use_dropout, gpu_ids=gpu_ids)
    elif which_model_netG == 'unet_256':
        netG = UnetGenerator(input_nc, output_nc, 8, ngf, norm_layer=norm_layer, use_dropout=use_dropout, gpu_ids=gpu_ids)
    else:
        raise NotImplementedError('Generator model name [%s] is not recognized' % which_model_netG)
    if len(gpu_ids) > 0:
        netG.cuda(device=gpu_ids[0])
    init_weights(netG, init_type=init_type)
    return netG


def define_D(input_nc, ndf, which_model_netD,
             n_layers_D=3, norm='batch', use_sigmoid=False, init_type='normal', gpu_ids=[]):
    netD = None
    use_gpu = len(gpu_ids) > 0
    norm_layer = get_norm_layer(norm_type=norm)

    if use_gpu:
        assert(torch.cuda.is_available())
    if which_model_netD == 'basic':
        netD = NLayerDiscriminator(input_nc, ndf, n_layers=3, norm_layer=norm_layer, use_sigmoid=use_sigmoid, gpu_ids=gpu_ids)
    elif which_model_netD == 'n_layers':
        netD = NLayerDiscriminator(input_nc, ndf, n_layers_D, norm_layer=norm_layer, use_sigmoid=use_sigmoid, gpu_ids=gpu_ids)
    else:
        raise NotImplementedError('Discriminator model name [%s] is not recognized' %
                                  which_model_netD)
    if use_gpu:
        netD.cuda(device=gpu_ids[0])
    init_weights(netD, init_type=init_type)
    return netD


def print_network(net):
    num_params = 0
    for param in net.parameters():
        num_params += param.numel()
    print(net)
    print('Total number of parameters: %d' % num_params)


##############################################################################
# Classes
##############################################################################


# Defines the GAN loss which uses either LSGAN or the regular GAN.
# When LSGAN is used, it is basically same as MSELoss,
# but it abstracts away the need to create the target label tensor
# that has the same size as the input
class GANLoss(nn.Module):
    def __init__(self, use_lsgan=True, target_real_label=1.0, target_fake_label=0.0,
                 tensor=torch.FloatTensor):
        super(GANLoss, self).__init__()
        self.real_label = target_real_label
        self.fake_label = target_fake_label
        self.real_label_var = None
        self.fake_label_var = None
        self.Tensor = tensor
        if use_lsgan:
            self.loss = nn.MSELoss()
        else:
            self.loss = nn.BCELoss()

    def get_target_tensor(self, input, target_is_real):
        target_tensor = None
        if target_is_real:
            create_label = ((self.real_label_var is None) or
                            (self.real_label_var.numel() != input.numel()))
            if create_label:
                real_tensor = self.Tensor(input.size()).fill_(self.real_label)
                self.real_label_var = Variable(real_tensor, requires_grad=False)
            target_tensor = self.real_label_var
        else:
            create_label = ((self.fake_label_var is None) or
                            (self.fake_label_var.numel() != input.numel()))
            if create_label:
                fake_tensor = self.Tensor(input.size()).fill_(self.fake_label)
                self.fake_label_var = Variable(fake_tensor, requires_grad=False)
            target_tensor = self.fake_label_var
        return target_tensor

    def __call__(self, input, target_is_real):
        target_tensor = self.get_target_tensor(input, target_is_real)
        return self.loss(input, target_tensor)


# Defines the generator that consists of Resnet blocks between a few
# downsampling/upsampling operations.
# Code and idea originally from Justin Johnson's architecture.
# https://github.com/jcjohnson/fast-neural-style/
class ResnetGenerator(nn.Module):
    def __init__(self, input_nc, output_nc, ngf=64, norm_layer=nn.BatchNorm2d, use_dropout=False, n_blocks=6, gpu_ids=[], padding_type='reflect'):
        assert(n_blocks >= 0)
        super(ResnetGenerator, self).__init__()
        self.input_nc = input_nc
        self.output_nc = output_nc
        self.ngf = ngf
        self.gpu_ids = gpu_ids
        if type(norm_layer) == functools.partial:
            use_bias = norm_layer.func == nn.InstanceNorm2d
        else:
            use_bias = norm_layer == nn.InstanceNorm2d

        model = [nn.ReflectionPad2d(3),
                 nn.Conv2d(input_nc, ngf, kernel_size=7, padding=0,
                           bias=use_bias),
                 norm_layer(ngf),
                 nn.ReLU(True)]

        n_downsampling = 2
        for i in range(n_downsampling):
            mult = 2**i
            model += [nn.Conv2d(ngf * mult, ngf * mult * 2, kernel_size=3,
                                stride=2, padding=1, bias=use_bias),
                      norm_layer(ngf * mult * 2),
                      nn.ReLU(True)]

        mult = 2**n_downsampling
        for i in range(n_blocks):
            model += [ResnetBlock(ngf * mult, padding_type=padding_type, norm_layer=norm_layer, use_dropout=use_dropout, use_bias=use_bias)]

        for i in range(n_downsampling):
            mult = 2**(n_downsampling - i)
            model += [nn.ConvTranspose2d(ngf * mult, int(ngf * mult / 2),
                                         kernel_size=3, stride=2,
                                         padding=1, output_padding=1,
                                         bias=use_bias),
                      norm_layer(int(ngf * mult / 2)),
                      nn.ReLU(True)]
        model += [nn.ReflectionPad2d(3)]
        model += [nn.Conv2d(ngf, output_nc, kernel_size=7, padding=0)]
        model += [nn.Tanh()]

        self.model = nn.Sequential(*model)

    def forward(self, input):
        if self.gpu_ids and isinstance(input.data, torch.cuda.FloatTensor):
            return nn.parallel.data_parallel(self.model, input, self.gpu_ids)
        else:
            return self.model(input)


class ResnetGeneratorMMReverse(nn.Module):
    def __init__(self, input_nc, output_nc, ngf=64, norm_layer=nn.BatchNorm2d, use_dropout=False, n_blocks=6, gpu_ids=[], padding_type='reflect'):
        assert(n_blocks >= 0)
        super(ResnetGeneratorMMReverse, self).__init__()
        self.input_nc = input_nc
        self.output_nc = output_nc
        self.ngf = ngf
        self.gpu_ids = gpu_ids
        if type(norm_layer) == functools.partial:
            use_bias = norm_layer.func == nn.InstanceNorm2d
        else:
            use_bias = norm_layer == nn.InstanceNorm2d

        model = [nn.ReflectionPad2d(3),

                 nn.Conv2d(input_nc, ngf, kernel_size=7, padding=0,
                           bias=use_bias),
                 norm_layer(ngf),
                 nn.ReLU(True)]


        n_downsampling = 2
        for i in range(n_downsampling):
            mult = 2**i
            model += [nn.Conv2d(ngf * mult, ngf * mult * 2, kernel_size=3,
                                stride=2, padding=1, bias=use_bias),
                      norm_layer(ngf * mult * 2),
                      nn.ReLU(True)]

        pre_f_blocks = 4
        pre_l_blocks = 7
        mult = 2**n_downsampling

        for i in range(pre_f_blocks):
            model += [ResnetBlock(ngf * mult, padding_type=padding_type, norm_layer=norm_layer, use_dropout=use_dropout, use_bias=use_bias)]
        model_pre = []
        for i in range(pre_f_blocks,pre_l_blocks):
            model_pre += [ResnetBlock(ngf * mult, padding_type=padding_type, norm_layer=norm_layer, use_dropout=use_dropout, use_bias=use_bias)]
        

        model_post1 = []
        model_post2 = []
        model_post3 = []
        for i in range(pre_l_blocks,n_blocks):
            model_post1 += [ResnetBlock(ngf * mult, padding_type=padding_type, norm_layer=norm_layer, use_dropout=use_dropout, use_bias=use_bias)]
            model_post2 += [ResnetBlock(ngf * mult, padding_type=padding_type, norm_layer=norm_layer, use_dropout=use_dropout, use_bias=use_bias)]
            model_post3 += [ResnetBlock(ngf * mult, padding_type=padding_type, norm_layer=norm_layer, use_dropout=use_dropout, use_bias=use_bias)]

        for i in range(n_downsampling):
            mult = 2**(n_downsampling - i)
            model_post1 += [nn.ConvTranspose2d(ngf * mult, int(ngf * mult / 2),
                                         kernel_size=3, stride=2,
                                         padding=1, output_padding=1,
                                         bias=use_bias),
                      norm_layer(int(ngf * mult / 2)),
                      nn.ReLU(True)]

            model_post2 += [nn.ConvTranspose2d(ngf * mult, int(ngf * mult / 2),
                                         kernel_size=3, stride=2,
                                         padding=1, output_padding=1,
                                         bias=use_bias),
                      norm_layer(int(ngf * mult / 2)),
                      nn.ReLU(True)]

            model_post3 += [nn.ConvTranspose2d(ngf * mult, int(ngf * mult / 2),
                                         kernel_size=3, stride=2,
                                         padding=1, output_padding=1,
                                         bias=use_bias),
                      norm_layer(int(ngf * mult / 2)),
                      nn.ReLU(True)]

        model_post1 += [nn.ReflectionPad2d(3)]
        model_post1 += [nn.Conv2d(ngf, output_nc, kernel_size=7, padding=0)]
        model_post1 += [nn.Tanh()]


        model_post2 += [nn.ReflectionPad2d(3)]
        model_post2 += [nn.Conv2d(ngf, 1, kernel_size=7, padding=0)]
        model_post2 += [nn.Tanh()]

        model_post3 += [nn.ReflectionPad2d(3)]
        model_post3 += [nn.Conv2d(ngf, 3, kernel_size=7, padding=0)]  #HC
        model_post3 += [nn.Tanh()]

        self.model_post1 = nn.Sequential(*model_post1)
        self.model_post2 = nn.Sequential(*model_post2)
        self.model_post3 = nn.Sequential(*model_post3)
        self.model_pre = nn.Sequential(*model_pre)
        self.model = nn.Sequential(*model)

    def forward(self, input):
         
            latent = self.model(input)
            fuse_ip = self.model_pre(latent)
            out1 = self.model_post1(fuse_ip) 
            out2 = self.model_post2(fuse_ip)
            out3 = self.model_post3(fuse_ip)
            return out1, out2, out3, latent



class ResnetGeneratorMM(nn.Module):
    def __init__(self, input_nc, output_nc, ngf=64, norm_layer=nn.BatchNorm2d, use_dropout=False, n_blocks=6, gpu_ids=[], padding_type='reflect'):
        assert(n_blocks >= 0)
        super(ResnetGeneratorMM, self).__init__()
        self.input_nc = input_nc
        self.output_nc = output_nc
        self.ngf = ngf
        self.gpu_ids = gpu_ids
        if type(norm_layer) == functools.partial:
            use_bias = norm_layer.func == nn.InstanceNorm2d
        else:
            use_bias = norm_layer == nn.InstanceNorm2d
        model1 = [nn.ReflectionPad2d(3),

                 nn.Conv2d(input_nc, ngf, kernel_size=7, padding=0,
                           bias=use_bias),
                 norm_layer(ngf),
                 nn.ReLU(True)]

        model2 = [nn.ReflectionPad2d(3),
                 nn.Conv2d(1, ngf, kernel_size=7, padding=0,
                           bias=use_bias),
                 norm_layer(ngf),
                 nn.ReLU(True)]

        model3 = [nn.ReflectionPad2d(3),
                 nn.Conv2d(3, ngf, kernel_size=7, padding=0, #HC
                           bias=use_bias),
                 norm_layer(ngf),
                 nn.ReLU(True)]
        

        n_downsampling = 2
        for i in range(n_downsampling):
            mult = 2**i
            model1 += [nn.Conv2d(ngf * mult, ngf * mult * 2, kernel_size=3,
                                stride=2, padding=1, bias=use_bias),
                      norm_layer(ngf * mult * 2),
                      nn.ReLU(True)]

            model2 += [nn.Conv2d(ngf * mult, ngf * mult * 2, kernel_size=3,
                                stride=2, padding=1, bias=use_bias),
                      norm_layer(ngf * mult * 2),
                      nn.ReLU(True)]
        
            model3 += [nn.Conv2d(ngf * mult, ngf * mult * 2, kernel_size=3,
                                stride=2, padding=1, bias=use_bias),
                      norm_layer(ngf * mult * 2),
                      nn.ReLU(True)]


        pre_f_blocks = 4
        pre_l_blocks = 7
        mult = 2**n_downsampling

        for i in range(pre_f_blocks):
            model1 += [ResnetBlock(ngf * mult, padding_type=padding_type, norm_layer=norm_layer, use_dropout=use_dropout, use_bias=use_bias)]
            model2 += [ResnetBlock(ngf * mult, padding_type=padding_type, norm_layer=norm_layer, use_dropout=use_dropout, use_bias=use_bias)]
            model3 += [ResnetBlock(ngf * mult, padding_type=padding_type, norm_layer=norm_layer, use_dropout=use_dropout, use_bias=use_bias)]
        model_pre = []
        model_post = []
        for i in range(pre_f_blocks,pre_l_blocks):
            model_pre += [ResnetBlock(ngf * mult, padding_type=padding_type, norm_layer=norm_layer, use_dropout=use_dropout, use_bias=use_bias)]
        
        for i in range(pre_l_blocks,n_blocks):
            model_post += [ResnetBlock(ngf * mult, padding_type=padding_type, norm_layer=norm_layer, use_dropout=use_dropout, use_bias=use_bias)]


        model_fusion = []
        #p = 0
        #if padding_type == 'reflect':
        #    model_fusion += [nn.ReflectionPad2d(1)]
        #elif padding_type == 'replicate':
        #    model_fusion += [nn.ReplicationPad2d(1)]
        #elif padding_type == 'zero':
        #    p = 1
        #else:
        #    raise NotImplementedError('padding [%s] is not implemented' % padding_type)

        model_fusion = [nn.Conv2d(ngf * mult*3, ngf * mult , kernel_size=3, padding=1, bias=use_bias),    #################### inestead of *2
                       norm_layer(ngf * mult),
                       nn.ReLU(True)]

        model = []
        for i in range(n_downsampling):
            mult = 2**(n_downsampling - i)
            model_post += [nn.ConvTranspose2d(ngf * mult, int(ngf * mult / 2),
                                         kernel_size=3, stride=2,
                                         padding=1, output_padding=1,
                                         bias=use_bias),
                      norm_layer(int(ngf * mult / 2)),
                      nn.ReLU(True)]
        model_post += [nn.ReflectionPad2d(3)]
        model_post += [nn.Conv2d(ngf, output_nc, kernel_size=7, padding=0)]
        model_post += [nn.Tanh()]
        self.model1 = nn.Sequential(*model1)
        self.model2 = nn.Sequential(*model2)
        self.model3 = nn.Sequential(*model3)
        self.model_pre = nn.Sequential(*model_pre)
        self.model_post = nn.Sequential(*model_post)
        self.model_fusion = nn.Sequential(*model_fusion)

    def forward(self, input, input2, input3):
            m1=self.model1(input)
            m2 = self.model2(input2)
            m3 = self.model3(input3)
            latent =    self.model_pre(self.model_fusion(torch.cat([m1, m2, m3], dim =1 )))
            out = self.model_post(latent)
            return out, latent





# Define a resnet block
class ResnetBlock(nn.Module):
    def __init__(self, dim, padding_type, norm_layer, use_dropout, use_bias):
        super(ResnetBlock, self).__init__()
        self.conv_block = self.build_conv_block(dim, padding_type, norm_layer, use_dropout, use_bias)

    def build_conv_block(self, dim, padding_type, norm_layer, use_dropout, use_bias):
        conv_block = []
        p = 0
        if padding_type == 'reflect':
            conv_block += [nn.ReflectionPad2d(1)]
        elif padding_type == 'replicate':
            conv_block += [nn.ReplicationPad2d(1)]
        elif padding_type == 'zero':
            p = 1
        else:
            raise NotImplementedError('padding [%s] is not implemented' % padding_type)

        conv_block += [nn.Conv2d(dim, dim, kernel_size=3, padding=p, bias=use_bias),
                       norm_layer(dim),
                       nn.ReLU(True)]
        if use_dropout:
            conv_block += [nn.Dropout(0.5)]

        p = 0
        if padding_type == 'reflect':
            conv_block += [nn.ReflectionPad2d(1)]
        elif padding_type == 'replicate':
            conv_block += [nn.ReplicationPad2d(1)]
        elif padding_type == 'zero':
            p = 1
        else:
            raise NotImplementedError('padding [%s] is not implemented' % padding_type)
        conv_block += [nn.Conv2d(dim, dim, kernel_size=3, padding=p, bias=use_bias),
                       norm_layer(dim)]

        return nn.Sequential(*conv_block)

    def forward(self, x):
        out = x + self.conv_block(x)
        return out


# Defines the Unet generator.
# |num_downs|: number of downsamplings in UNet. For example,
# if |num_downs| == 7, image of size 128x128 will become of size 1x1
# at the bottleneck
class UnetGenerator(nn.Module):
    def __init__(self, input_nc, output_nc, num_downs, ngf=64,
                 norm_layer=nn.BatchNorm2d, use_dropout=False, gpu_ids=[]):
        super(UnetGenerator, self).__init__()
        self.gpu_ids = gpu_ids

        # construct unet structure
        unet_block = UnetSkipConnectionBlock(ngf * 8, ngf * 8, input_nc=None, submodule=None, norm_layer=norm_layer, innermost=True)
        for i in range(num_downs - 5):
            unet_block = UnetSkipConnectionBlock(ngf * 8, ngf * 8, input_nc=None, submodule=unet_block, norm_layer=norm_layer, use_dropout=use_dropout)
        unet_block = UnetSkipConnectionBlock(ngf * 4, ngf * 8, input_nc=None, submodule=unet_block, norm_layer=norm_layer)
        unet_block = UnetSkipConnectionBlock(ngf * 2, ngf * 4, input_nc=None, submodule=unet_block, norm_layer=norm_layer)
        unet_block = UnetSkipConnectionBlock(ngf, ngf * 2, input_nc=None, submodule=unet_block, norm_layer=norm_layer)
        unet_block = UnetSkipConnectionBlock(output_nc, ngf, input_nc=input_nc, submodule=unet_block, outermost=True, norm_layer=norm_layer)

        self.model = unet_block

    def forward(self, input):
        if self.gpu_ids and isinstance(input.data, torch.cuda.FloatTensor):
            return nn.parallel.data_parallel(self.model, input, self.gpu_ids)
        else:
            return self.model(input)


class UnetGeneratorMM(nn.Module):
    def __init__(self, input_nc, output_nc, num_downs, ngf=64,
                 norm_layer=nn.BatchNorm2d, use_dropout=False, gpu_ids=[]):
        super(UnetGeneratorMM, self).__init__()
        self.gpu_ids = gpu_ids

        # construct unet structure
        unet_block = UnetSkipConnectionBlock(ngf * 8, ngf * 8, input_nc=None, submodule=None, norm_layer=norm_layer, innermost=True)
        for i in range(num_downs - 5):
            unet_block = UnetSkipConnectionBlock(ngf * 8, ngf * 8, input_nc=None, submodule=unet_block, norm_layer=norm_layer, use_dropout=use_dropout)
        unet_block = UnetSkipConnectionBlock(ngf * 4, ngf * 8, input_nc=None, submodule=unet_block, norm_layer=norm_layer)
        unet_block = UnetSkipConnectionBlock(ngf * 2, ngf * 4, input_nc=None, submodule=unet_block, norm_layer=norm_layer)
        unet_block = UnetSkipConnectionBlock(ngf, ngf * 2, input_nc=None, submodule=unet_block, norm_layer=norm_layer)
        unet_block = UnetSkipConnectionBlock(output_nc, ngf, input_nc=input_nc, submodule=unet_block, norm_layer=norm_layer, outermost=True)

        self.model = unet_block

    def forward(self, input, input2):
            return self.model(input)


class UnetGeneratorMMU(nn.Module):
    def __init__(self, input_nc, output_nc, num_downs, ngf=64,
                 norm_layer=nn.BatchNorm2d, use_dropout=False, gpu_ids=[]):
        super(UnetGeneratorMMU, self).__init__()
        self.gpu_ids = gpu_ids

        '''self.en1 = EnLayerBi(output_nc, ngf, input_nc=input_nc, norm_layer=norm_layer, outermost=True) #128
        self.t11 = TransLayer(output_nc, ngf, input_nc=input_nc, norm_layer=norm_layer, outermost=True, factor=2)
        self.t12 = TransLayer(output_nc, ngf, input_nc=input_nc, norm_layer=norm_layer, outermost=True, factor=2)
        self.en2 = EnLayerBi(ngf, ngf * 2, input_nc=None, norm_layer=norm_layer) #64
        self.t21 = TransLayer(ngf, ngf * 2, input_nc=None, norm_layer=norm_layer, factor=2)
        self.t22 = TransLayer(ngf, ngf * 2, input_nc=None, norm_layer=norm_layer, factor=2)             
        self.en3 = EnLayerBi(ngf * 2, ngf * 4, input_nc=None,norm_layer=norm_layer) #32
        self.t31 = TransLayer(ngf * 2, ngf * 4, input_nc=None,norm_layer=norm_layer, factor=2)
        self.t32 = TransLayer(ngf * 2, ngf * 4, input_nc=None,norm_layer=norm_layer, factor=2)
        self.en4 = EnLayerBi(ngf * 4, ngf * 8, input_nc=None, norm_layer=norm_layer,  factor=2)#16
        self.t41 = TransLayer(ngf * 4, ngf * 8, input_nc=None, norm_layer=norm_layer, factor=2)
        self.t42 = TransLayer(ngf * 4, ngf * 8, input_nc=None, norm_layer=norm_layer, factor=2)
        self.en5 = EnLayer(ngf * 8, ngf * 8, input_nc=None,  norm_layer=norm_layer, use_dropout=use_dropout) #8
        self.t5 = TransLayer(ngf * 8, ngf * 8, input_nc=None,  norm_layer=norm_layer, use_dropout=use_dropout)
        self.en6 = EnLayer(ngf * 8, ngf * 8, input_nc=None, norm_layer=norm_layer) #4
        self.t6 = TransLayer(ngf * 8, ngf * 8, input_nc=None, norm_layer=norm_layer) 
        self.en7 = EnLayer(ngf * 8, ngf * 8, input_nc=None,  norm_layer=norm_layer) #2
        self.t7 = TransLayer(ngf * 8, ngf * 8, input_nc=None,  norm_layer=norm_layer)
        self.en8 = EnLayer(ngf * 8, ngf * 8, input_nc=None, norm_layer=norm_layer, innermost=True) #1
        self.t8 = TransLayer(ngf * 8, ngf * 8, input_nc=None, norm_layer=norm_layer, innermost=True)
        self.de8 = DeLayer(ngf * 8, ngf * 8, input_nc=None, norm_layer=norm_layer, innermost=True) #2
        self.de7 = DeLayer(ngf * 8, ngf * 8, input_nc=None, norm_layer=norm_layer) #4
        self.de6 = DeLayer(ngf * 8, ngf * 8, input_nc=None,norm_layer=norm_layer) #8
        self.de5 = DeLayer(ngf * 8, ngf * 8, input_nc=None,  norm_layer=norm_layer, use_dropout=use_dropout) #16
        self.de4 = DeLayer(ngf * 4, ngf * 8, input_nc=None, norm_layer=norm_layer) #32
        self.de3 = DeLayer(ngf * 2, ngf * 4, input_nc=None,  norm_layer=norm_layer) #64
        self.de2 = DeLayer(ngf, ngf * 2, input_nc=None, norm_layer=norm_layer) #128
        self.de1 = DeLayer(output_nc, ngf, input_nc=input_nc,  norm_layer=norm_layer, outermost=True) # 256
        

    def forward(self, input, input2):
            oe11, oe12 = self.en1(input, input2)  #128 te2       
            te21, te22, oe21, oe22 = self.en2(oe11,oe12) 
            te31, te32, oe31, oe32 = self.en3(oe21, oe22) 
            te41, te42, oe41, oe42 = self.en4(oe31, oe32)  
            te5, oe5 = self.en5(torch.cat([oe41, oe42],1)) 
            te6, oe6 = self.en6(oe5) 
            te7, oe7 = self.en7(oe6)
            te8, oe8 = self.en8(oe7)
            te7 = self.t7(te7)
            te6 = self.t6(te6)
            te5 = self.t5(te5)
            te41 = self.t41(te41)
            te42 = self.t42(te42)
            te31 = self.t31(te31)
            te32 = self.t32(te32)
            te21 = self.t21(te21)
            te22 = self.t22(te22)
            te8 = self.t8(te8)
            od8 = torch.cat([self.de8(oe8), te8],1)       
            od7 = torch.cat([self.de7(od8), te7],1)     
            od6 = torch.cat([self.de6(od7), te6],1)
            od5 = torch.cat([self.de5(od6), te5],1)     
            od4 = torch.cat([self.de4(od5), torch.cat([te41,te42],1)],1)          
            od3 = torch.cat([self.de3(od4), torch.cat([te31,te32],1)],1)          
            od2 = torch.cat([self.de2(od3), torch.cat([te21,te22],1)],1)          
            od1 = self.de1(od2)
            return(od1)'''


        '''self.en1 = EnLayerBi(output_nc, ngf, input_nc=input_nc, norm_layer=norm_layer, outermost=True) #128
        self.t11 = TransLayer(output_nc, ngf, input_nc=input_nc, norm_layer=norm_layer, outermost=True, factor=2)
        self.t12 = TransLayer(output_nc, ngf, input_nc=input_nc, norm_layer=norm_layer, outermost=True, factor=2)
        self.en2 = EnLayerBi(ngf, ngf * 2, input_nc=None, norm_layer=norm_layer) #64
        self.t21 = TransLayer(ngf, ngf * 2, input_nc=None, norm_layer=norm_layer, factor=2)
        self.t22 = TransLayer(ngf, ngf * 2, input_nc=None, norm_layer=norm_layer, factor=2)             
        self.en3 = EnLayerBi(ngf * 2, ngf * 4, input_nc=None,norm_layer=norm_layer, factor = 2) #32
        self.t31 = TransLayer(ngf * 2, ngf * 4, input_nc=None,norm_layer=norm_layer, factor=2)
        self.t32 = TransLayer(ngf * 2, ngf * 4, input_nc=None,norm_layer=norm_layer, factor=2)
        self.en4 = EnLayer(ngf * 4, ngf * 8, input_nc=None, norm_layer=norm_layer)#16
        #self.t41 = TransLayer(ngf * 4, ngf * 8, input_nc=None, norm_layer=norm_layer, factor=2)
        self.t4 = TransLayer(ngf * 4, ngf * 8, input_nc=None, norm_layer=norm_layer, factor=1)
        self.en5 = EnLayer(ngf * 8, ngf * 8, input_nc=None,  norm_layer=norm_layer, use_dropout=use_dropout) #8
        self.t5 = TransLayer(ngf * 8, ngf * 8, input_nc=None,  norm_layer=norm_layer, use_dropout=use_dropout)
        self.en6 = EnLayer(ngf * 8, ngf * 8, input_nc=None, norm_layer=norm_layer) #4
        self.t6 = TransLayer(ngf * 8, ngf * 8, input_nc=None, norm_layer=norm_layer) 
        self.en7 = EnLayer(ngf * 8, ngf * 8, input_nc=None,  norm_layer=norm_layer) #2
        self.t7 = TransLayer(ngf * 8, ngf * 8, input_nc=None,  norm_layer=norm_layer)
        self.en8 = EnLayer(ngf * 8, ngf * 8, input_nc=None, norm_layer=norm_layer, innermost=True) #1
        self.t8 = TransLayer(ngf * 8, ngf * 8, input_nc=None, norm_layer=norm_layer, innermost=True)
        self.de8 = DeLayer(ngf * 8, ngf * 8, input_nc=None, norm_layer=norm_layer, innermost=True) #2
        self.de7 = DeLayer(ngf * 8, ngf * 8, input_nc=None, norm_layer=norm_layer) #4
        self.de6 = DeLayer(ngf * 8, ngf * 8, input_nc=None,norm_layer=norm_layer) #8
        self.de5 = DeLayer(ngf * 8, ngf * 8, input_nc=None,  norm_layer=norm_layer, use_dropout=use_dropout) #16
        self.de4 = DeLayer(ngf * 4, ngf * 8, input_nc=None, norm_layer=norm_layer) #32
        self.de3 = DeLayer(ngf * 2, ngf * 4, input_nc=None,  norm_layer=norm_layer) #64
        self.de2 = DeLayer(ngf, ngf * 2, input_nc=None, norm_layer=norm_layer) #128
        self.de1 = DeLayer(output_nc, ngf, input_nc=input_nc,  norm_layer=norm_layer, outermost=True) # 256'''

        self.en1 = EnLayerBi(output_nc, ngf, input_nc=input_nc, norm_layer=norm_layer, outermost=True) #128
        self.t11 = TransLayer(output_nc, ngf, input_nc=input_nc, norm_layer=norm_layer, outermost=True, factor=2)
        self.t12 = TransLayer(output_nc, ngf, input_nc=input_nc, norm_layer=norm_layer, outermost=True, factor=2)
        self.en2 = EnLayerBi(ngf, ngf * 2, input_nc=None, norm_layer=norm_layer) #64
        self.t21 = TransLayer(ngf, ngf * 2, input_nc=None, norm_layer=norm_layer, factor=2)
        self.t22 = TransLayer(ngf, ngf * 2, input_nc=None, norm_layer=norm_layer, factor=2)             
        self.en3 = EnLayerBi(ngf * 2, ngf * 4, input_nc=None,norm_layer=norm_layer, factor = 1) #32
        self.t31 = TransLayer(ngf * 2, ngf * 4, input_nc=None,norm_layer=norm_layer, factor=2)
        self.t32 = TransLayer(ngf * 2, ngf * 4, input_nc=None,norm_layer=norm_layer, factor=2)
        self.en4 = EnLayer(ngf * 8, ngf * 8, input_nc=None, norm_layer=norm_layer)#16
        #self.t41 = TransLayer(ngf * 4, ngf * 8, input_nc=None, norm_layer=norm_layer, factor=2)
        self.t4 = TransLayer(ngf * 8, ngf * 8, input_nc=None, norm_layer=norm_layer, factor=2)
        self.en5 = EnLayer(ngf * 8, ngf * 8, input_nc=None,  norm_layer=norm_layer, use_dropout=use_dropout) #8
        self.t5 = TransLayer(ngf * 8, ngf * 8, input_nc=None,  norm_layer=norm_layer, use_dropout=use_dropout)
        self.en6 = EnLayer(ngf * 8, ngf * 8, input_nc=None, norm_layer=norm_layer) #4
        self.t6 = TransLayer(ngf * 8, ngf * 8, input_nc=None, norm_layer=norm_layer) 
        self.en7 = EnLayer(ngf * 8, ngf * 8, input_nc=None,  norm_layer=norm_layer) #2
        self.t7 = TransLayer(ngf * 8, ngf * 8, input_nc=None,  norm_layer=norm_layer)
        self.en8 = EnLayer(ngf * 8, ngf * 8, input_nc=None, norm_layer=norm_layer, innermost=True) #1
        self.t8 = TransLayer(ngf * 8, ngf * 8, input_nc=None, norm_layer=norm_layer, innermost=True)
        self.de8 = DeLayer(ngf * 8, ngf * 8, input_nc=None, norm_layer=norm_layer, innermost=True) #2
        self.de7 = DeLayer(ngf * 8, ngf * 8, input_nc=None, norm_layer=norm_layer) #4
        self.de6 = DeLayer(ngf * 8, ngf * 8, input_nc=None,norm_layer=norm_layer) #8
        self.de5 = DeLayer(ngf * 8, ngf * 8, input_nc=None,  norm_layer=norm_layer, use_dropout=use_dropout) #16
        self.de4 = DeLayer(ngf * 4, ngf * 8, input_nc=None, norm_layer=norm_layer) #32
        self.de3 = DeLayer(ngf * 2, ngf * 4, input_nc=None,  norm_layer=norm_layer) #64
        self.de2 = DeLayer(ngf, ngf * 2, input_nc=None, norm_layer=norm_layer) #128
        self.de1 = DeLayer(output_nc, ngf, input_nc=input_nc,  norm_layer=norm_layer, outermost=True)

        

    def forward(self, input, input2):
            oe11, oe12 = self.en1(input, input2)  #128 te2 
            #print([oe11.size(), oe12.size()])           
            te21, te22, oe21, oe22 = self.en2(oe11,oe12) 
            #print([oe21.size(), oe22.size()])           
            te31, te32, oe31, oe32 = self.en3(oe21, oe22) 
            #print([oe31.size(), oe32.size()])           
            te4, oe4 = self.en4(torch.cat([oe31, oe32],1))  
            #print(oe4.size())  
            #te5, oe5 = self.en5(torch.cat([oe41, oe42],1)) 
            te5, oe5 = self.en5(oe4)
            #print(oe5.size())  
            te6, oe6 = self.en6(oe5) 
            #print(oe6.size())  
            te7, oe7 = self.en7(oe6)
            #print(oe7.size())  
            te8, oe8 = self.en8(oe7)
            #print(oe8.size())  
            te8 = self.t8(te8)
            te7 = self.t7(te7)
            te6 = self.t6(te6)
            te5 = self.t5(te5)
            #te41 = self.t41(te41)
            te4 = self.t4(te4)
            te31 = self.t31(te31)
            te32 = self.t32(te32)
            te21 = self.t21(te21)
            te22 = self.t22(te22)
            #print('-----en--de-----')
             
            od8 = torch.cat([self.de8(oe8), te8],1)
            #print(od8.size())           
            od7 = torch.cat([self.de7(od8), te7],1)
            #print(od7.size())  
            od6 = torch.cat([self.de6(od7), te6],1)
            #print(od6.size())  
            od5 = torch.cat([self.de5(od6), te5],1)     
            #print(od5.size())  
            #print('start of d4')
            #print(te4.size())
            od4 = torch.cat([self.de4(od5),te4],1)       
            #od4 = torch.cat([self.de4(od5), torch.cat([te41,te42],1)],1)
            #print(od4.size())   
            #print('---') 
            od3 = torch.cat([self.de3(od4), torch.cat([te31,te32],1)],1)
            #print(od3.size())            
            od2 = torch.cat([self.de2(od3), torch.cat([te21,te22],1)],1)
            #print(od2.size())            
            od1 = self.de1(od2)
            #print(od1.size())  
            return(od1)


class TransLayer(nn.Module):
    def __init__(self, outer_nc, inner_nc, input_nc=None,
                 submodule=None, outermost=False, innermost=False, norm_layer=nn.BatchNorm2d, use_dropout=False, factor = 1):
        super(TransLayer, self).__init__()
        self.outermost = outermost
        if type(norm_layer) == functools.partial:
            use_bias = norm_layer.func == nn.InstanceNorm2d
        else:
            use_bias = norm_layer == nn.InstanceNorm2d
        if input_nc is None:
            input_nc = outer_nc
        transconv = nn.Conv2d(input_nc, outer_nc/factor, kernel_size=3,
                stride=1, padding=1)
        transnorm = norm_layer(input_nc/factor)
        transrelu = nn.LeakyReLU(0.2, True)
        trans = [transconv, transnorm, transrelu]
        self.trans = nn.Sequential(*trans)

    def forward(self, x):
           return self.trans(x)
           
        



class EnLayer(nn.Module):
    def __init__(self, outer_nc, inner_nc, input_nc=None,
                 submodule=None, outermost=False, innermost=False, norm_layer=nn.BatchNorm2d, use_dropout=False):
        super(EnLayer, self).__init__()
        self.outermost = outermost
        if type(norm_layer) == functools.partial:
            use_bias = norm_layer.func == nn.InstanceNorm2d
        else:
            use_bias = norm_layer == nn.InstanceNorm2d
        if input_nc is None:
            input_nc = outer_nc
        downconv = nn.Conv2d(input_nc, inner_nc, kernel_size=4,
                             stride=2, padding=1, bias=use_bias)
        downrelu = nn.LeakyReLU(0.2, True)
        downnorm = norm_layer(inner_nc)
        
        transconv = nn.Conv2d(input_nc, outer_nc, kernel_size=3,
                stride=1, padding=1)
        transnorm = norm_layer(input_nc)
        transrelu = nn.LeakyReLU(0.2, True)
        trans = [transconv, transnorm, transrelu]
        
        if outermost:
           
            down = [downconv]
            model = down 
        
        elif innermost:
         
            down = [downrelu, downconv]
            model = down 
                
        else:
            down = [downrelu, downconv, downnorm]
            model = down              
        self.model = nn.Sequential(*model)
        self.trans = nn.Sequential(*trans)

    def forward(self, x):
        if self.outermost:
            return self.model(x)
        else:
            return [x, self.model(x)]




class EnLayerBi(nn.Module):
    def __init__(self, outer_nc, inner_nc, input_nc=None,
                 submodule=None, outermost=False, innermost=False, norm_layer=nn.BatchNorm2d, use_dropout=False, factor = 1):
        super(EnLayerBi, self).__init__()
        self.outermost = outermost
        if type(norm_layer) == functools.partial:
            use_bias = norm_layer.func == nn.InstanceNorm2d
        else:
            use_bias = norm_layer == nn.InstanceNorm2d
        if input_nc is None:
            input_nc = outer_nc
        downconv = nn.Conv2d(input_nc, inner_nc/ factor, kernel_size=4,
                             stride=2, padding=1, bias=use_bias)
        downrelu = nn.LeakyReLU(0.2, True)
        downnorm = norm_layer(inner_nc/ factor)
        downconv2 = nn.Conv2d(input_nc, inner_nc/ factor, kernel_size=4,
                             stride=2, padding=1, bias=use_bias)
        downrelu2 = nn.LeakyReLU(0.2, True)
        downnorm2 = norm_layer(inner_nc/ factor)

        if outermost:
           
            down = [downconv]
            model = down 
            down2 = [downconv2]
            model2 = down2 
        
        elif innermost:
         
            down = [downrelu, downconv]
            model = down 
            down2 = [downrelu2, downconv2]
            model2 = down2 
                
        else:
            down = [downrelu, downconv, downnorm]
            model = down 
            down2 = [downrelu2, downconv2, downnorm2]
            model2 = down2                    
        self.model2 = nn.Sequential(*model2)
        self.model = nn.Sequential(*model)
        

    def forward(self, x,y):
        if self.outermost:
            return [ self.model(x), self.model2(y)]
        else:
            return [x, y, self.model(x), self.model2(y)]



class DeLayer(nn.Module):
    def __init__(self, outer_nc, inner_nc, input_nc=None,
                 submodule=None, outermost=False, innermost=False, norm_layer=nn.BatchNorm2d, use_dropout=False):
        super(DeLayer, self).__init__()
        self.outermost = outermost
        if type(norm_layer) == functools.partial:
            use_bias = norm_layer.func == nn.InstanceNorm2d
        else:
            use_bias = norm_layer == nn.InstanceNorm2d
        if input_nc is None:
            input_nc = outer_nc
        
        uprelu = nn.ReLU(True)
        upnorm = norm_layer(outer_nc)
        
        if outermost:
            upconv = nn.ConvTranspose2d(inner_nc * 2, outer_nc,
                                        kernel_size=4, stride=2,
                                        padding=1)
            up = [uprelu, upconv, nn.Tanh()]
            model = up
        
        elif innermost:
            upconv = nn.ConvTranspose2d(inner_nc, outer_nc,
                                        kernel_size=4, stride=2,
                                        padding=1, bias=use_bias)
          
            up = [uprelu, upconv, upnorm]
            model = up
                
        else:
            upconv = nn.ConvTranspose2d(inner_nc * 2, outer_nc,
                                        kernel_size=4, stride=2,
                                        padding=1, bias=use_bias)
            up = [uprelu, upconv, upnorm]

            if use_dropout:
                model =  up + [nn.Dropout(0.5)]
            else:
                model = up                    
        self.model = nn.Sequential(*model)
    def forward(self, x):
            return self.model(x)
 







class UnetGeneratorMM(nn.Module):
    def __init__(self, input_nc, output_nc, num_downs, ngf=64,
                 norm_layer=nn.BatchNorm2d, use_dropout=False, gpu_ids=[]):
        super(UnetGeneratorMM, self).__init__()
        self.gpu_ids = gpu_ids

        # construct unet structure
        unet_block = UnetSkipConnectionBlock(ngf * 8, ngf * 8, input_nc=None, submodule=None, norm_layer=norm_layer, innermost=True)
        for i in range(num_downs - 5):
            unet_block = UnetSkipConnectionBlock(ngf * 8, ngf * 8, input_nc=None, submodule=unet_block, norm_layer=norm_layer, use_dropout=use_dropout)
        unet_block = UnetSkipConnectionBlock(ngf * 4, ngf * 8, input_nc=None, submodule=unet_block, norm_layer=norm_layer)

        unet_block = UnetSkipConnectionBlock(ngf * 2, ngf * 4, input_nc=None, submodule=unet_block, norm_layer=norm_layer)
        unet_block = UnetSkipConnectionBlock(ngf, ngf * 2, input_nc=None, submodule=unet_block, norm_layer=norm_layer)
        unet_block = UnetSkipConnectionBlock(output_nc, ngf, input_nc=input_nc, submodule=unet_block, norm_layer=norm_layer, outermost=True)

        self.model = unet_block

    def forward(self, input, input2):
            return self.model(input)

# Defines the submodule with skip connection.
# X -------------------identity---------------------- X
#   |-- downsampling -- |submodule| -- upsampling --|
class UnetSkipConnectionBlock(nn.Module):
    def __init__(self, outer_nc, inner_nc, input_nc=None,
                 submodule=None, outermost=False, innermost=False, norm_layer=nn.BatchNorm2d, use_dropout=False):
        super(UnetSkipConnectionBlock, self).__init__()
        self.outermost = outermost
        if type(norm_layer) == functools.partial:
            use_bias = norm_layer.func == nn.InstanceNorm2d
        else:
            use_bias = norm_layer == nn.InstanceNorm2d
        if input_nc is None:
            input_nc = outer_nc
        downconv = nn.Conv2d(input_nc, inner_nc, kernel_size=4,
                             stride=2, padding=1, bias=use_bias)
        downrelu = nn.LeakyReLU(0.2, True)
        downnorm = norm_layer(inner_nc)
        uprelu = nn.ReLU(True)
        upnorm = norm_layer(outer_nc)
        transconv = nn.Conv2d(input_nc, outer_nc, kernel_size=3,
                stride=1, padding=1)
        transnorm = norm_layer(input_nc)
        trans = [transconv, transnorm]
        
        #self.trans =nn.Sequential(nn.Conv2d(input_nc, outer_nc, kernel_size=3,
        #       stride=1, padding=1))
        #self.trans = nn.Sequential(nn.UpsamplingNearest2d(scale_factor=2), nn.MaxPool2d(2))
        if outermost:
            upconv = nn.ConvTranspose2d(inner_nc * 2, outer_nc,
                                        kernel_size=4, stride=2,
                                        padding=1)
            down = [downconv]
            up = [uprelu, upconv, nn.Tanh()]
            model = down + [submodule] + up
        
        elif innermost:
            upconv = nn.ConvTranspose2d(inner_nc, outer_nc,
                                        kernel_size=4, stride=2,
                                        padding=1, bias=use_bias)
            down = [downrelu, downconv]
            up = [uprelu, upconv, upnorm]
            model = down + up
                
        else:
            upconv = nn.ConvTranspose2d(inner_nc * 2, outer_nc,
                                        kernel_size=4, stride=2,
                                        padding=1, bias=use_bias)
            down = [downrelu, downconv, downnorm]
            up = [uprelu, upconv, upnorm]

            if use_dropout:
                model = down + [submodule] + up + [nn.Dropout(0.5)]
            else:
                model = down + [submodule] + up               
        self.model = nn.Sequential(*model)
    def forward(self, x):
        if self.outermost:
            return self.model(x)
        else:
            #out1 = self.trans(x)
            #out1 = 
            out2 = self.model(x)
            return torch.cat((x, out2), 1)

class UnetSkipConnectionBlockMM(nn.Module):
    def __init__(self, outer_nc, inner_nc, input_nc=None,
                 submodule=None, outermost=False, innermost=False, norm_layer=nn.BatchNorm2d, use_dropout=False):
        super(UnetSkipConnectionBlockMM, self).__init__()
        self.outermost = outermost
        self.innermost = innermost
        if type(norm_layer) == functools.partial:
            use_bias = norm_layer.func == nn.InstanceNorm2d
        else:
            use_bias = norm_layer == nn.InstanceNorm2d
        if input_nc is None:
            input_nc = outer_nc

        if innermost:            

                downconv1 = nn.Conv2d(input_nc, inner_nc/2, kernel_size=4,
                             stride=2, padding=1, bias=use_bias)
                downconv2 = nn.Conv2d(input_nc, inner_nc/2, kernel_size=4,
                             stride=2, padding=1, bias=use_bias)
                uprelu = nn.ReLU(True)
                upnorm = norm_layer(outer_nc)
                upconv = nn.ConvTranspose2d(inner_nc * 2, outer_nc,
                                        kernel_size=4, stride=2,
                                        padding=1)
        
                down1 =[downconv1]
                self.down1 = nn.Sequential(*down1)
                down2 = [downconv2]     
                self.down2 = nn.Sequential(*down2)
                up = [uprelu, upconv, nn.Tanh()]
                model =  [submodule] + up
                self.model = nn.Sequential(*model)
                

        elif outermost:
                downconv1 = nn.Conv2d(input_nc, inner_nc, kernel_size=4,
                             stride=2, padding=1, bias=use_bias)
                downconv2 = nn.Conv2d(input_nc, inner_nc, kernel_size=4,
                             stride=2, padding=1, bias=use_bias)
                uprelu = nn.ReLU(True)
                upnorm = norm_layer(outer_nc)
                upconv = nn.ConvTranspose2d(inner_nc * 2, outer_nc,
                                        kernel_size=4, stride=2,
                                        padding=1)


                transconv1 = nn.Conv2d(input_nc, outer_nc/2, kernel_size=3,
                                stride=0, padding=1, bias=use_bias)
                transnorm1 = norm_layer(outer_nc)

                transconv2 = nn.Conv2d(input_nc, outer_nc/2, kernel_size=3,
                                stride=0, padding=1, bias=use_bias)
                transnorm2 = norm_layer(outer_nc)
                #self.trans1 =nn.Sequential(trans1)
                #self.trans2 =nn.Sequential(*trans2) 


                down1 =[downconv1]
                self.down1 = nn.Sequential(*down1)
                down2 = [downconv2]     
                self.down2 = nn.Sequential(*down2)
                up = [uprelu, upconv, nn.Tanh()]
                model =  [submodule] + up
                self.submodule = submodule
                self.up = nn.Sequential(*up) ####
                
        
    def forward(self, x, y):
        print("MM")
        print(self.innermost)
        print(x.size())
        if self.innermost:      
            return torch.cat([x,self.model(torch.cat((self.down1(x),self.down2(y)),dim=1))],1)
            #return torch.cat((x,self.model(self.down1(x))), dim = 1)
            #return self.model(self.down1(x))
        if self.outermost:      
            return self.up(self.submodule(self.down1(x),self.down2(y))) 


# Defines the PatchGAN discriminator with the specified arguments.
class NLayerDiscriminator(nn.Module):
    def __init__(self, input_nc, ndf=64, n_layers=3, norm_layer=nn.BatchNorm2d, use_sigmoid=False, gpu_ids=[]):
        super(NLayerDiscriminator, self).__init__()
        self.gpu_ids = gpu_ids
        if type(norm_layer) == functools.partial:
            use_bias = norm_layer.func == nn.InstanceNorm2d
        else:
            use_bias = norm_layer == nn.InstanceNorm2d

        kw = 4
        padw = 1
        sequence = [
            nn.Conv2d(input_nc, ndf, kernel_size=kw, stride=2, padding=padw),
            nn.LeakyReLU(0.2, True)
        ]

        nf_mult = 1
        nf_mult_prev = 1
        for n in range(1, n_layers):
            nf_mult_prev = nf_mult
            nf_mult = min(2**n, 8)
            sequence += [
                nn.Conv2d(ndf * nf_mult_prev, ndf * nf_mult,
                          kernel_size=kw, stride=2, padding=padw, bias=use_bias),
                norm_layer(ndf * nf_mult),
                nn.LeakyReLU(0.2, True)
            ]

        nf_mult_prev = nf_mult
        nf_mult = min(2**n_layers, 8)
        sequence += [
            nn.Conv2d(ndf * nf_mult_prev, ndf * nf_mult,
                      kernel_size=kw, stride=1, padding=padw, bias=use_bias),
            norm_layer(ndf * nf_mult),
            nn.LeakyReLU(0.2, True)
        ]

        sequence += [nn.Conv2d(ndf * nf_mult, 1, kernel_size=kw, stride=1, padding=padw)]

        if use_sigmoid:
            sequence += [nn.Sigmoid()]

        self.model = nn.Sequential(*sequence)

    def forward(self, input):
        if len(self.gpu_ids) and isinstance(input.data, torch.cuda.FloatTensor):
            return nn.parallel.data_parallel(self.model, input, self.gpu_ids)
        else:
            return self.model(input)

        
        
###############################################################################

class Net(nn.Module):
    def __init__(self, threshold=10.0, use_cuda=False):
        super(Net, self).__init__()

        self.threshold = threshold
        self.use_cuda = use_cuda

        filter_size = 5
        generated_filters = gaussian(filter_size,std=1.0).reshape([1,filter_size])

        self.gaussian_filter_horizontal = nn.Conv2d(in_channels=1, out_channels=1, kernel_size=(1,filter_size), padding=(0,filter_size//2))
        self.gaussian_filter_horizontal.weight.data.copy_(torch.from_numpy(generated_filters))
        self.gaussian_filter_horizontal.bias.data.copy_(torch.from_numpy(np.array([0.0])))
        self.gaussian_filter_vertical = nn.Conv2d(in_channels=1, out_channels=1, kernel_size=(filter_size,1), padding=(filter_size//2,0))
        self.gaussian_filter_vertical.weight.data.copy_(torch.from_numpy(generated_filters.T))
        self.gaussian_filter_vertical.bias.data.copy_(torch.from_numpy(np.array([0.0])))

        sobel_filter = np.array([[1, 0, -1],
                                 [2, 0, -2],
                                 [1, 0, -1]])

        self.sobel_filter_horizontal = nn.Conv2d(in_channels=1, out_channels=1, kernel_size=sobel_filter.shape, padding=sobel_filter.shape[0]//2)
        self.sobel_filter_horizontal.weight.data.copy_(torch.from_numpy(sobel_filter))
        self.sobel_filter_horizontal.bias.data.copy_(torch.from_numpy(np.array([0.0])))
        self.sobel_filter_vertical = nn.Conv2d(in_channels=1, out_channels=1, kernel_size=sobel_filter.shape, padding=sobel_filter.shape[0]//2)
        self.sobel_filter_vertical.weight.data.copy_(torch.from_numpy(sobel_filter.T))
        self.sobel_filter_vertical.bias.data.copy_(torch.from_numpy(np.array([0.0])))

        # filters were flipped manually
        filter_0 = np.array([   [ 0, 0, 0],
                                [ 0, 1, -1],
                                [ 0, 0, 0]])

        filter_45 = np.array([  [0, 0, 0],
                                [ 0, 1, 0],
                                [ 0, 0, -1]])

        filter_90 = np.array([  [ 0, 0, 0],
                                [ 0, 1, 0],
                                [ 0,-1, 0]])

        filter_135 = np.array([ [ 0, 0, 0],
                                [ 0, 1, 0],
                                [-1, 0, 0]])

        filter_180 = np.array([ [ 0, 0, 0],
                                [-1, 1, 0],
                                [ 0, 0, 0]])

        filter_225 = np.array([ [-1, 0, 0],
                                [ 0, 1, 0],
                                [ 0, 0, 0]])

        filter_270 = np.array([ [ 0,-1, 0],
                                [ 0, 1, 0],
                                [ 0, 0, 0]])

        filter_315 = np.array([ [ 0, 0, -1],
                                [ 0, 1, 0],
                                [ 0, 0, 0]])

        all_filters = np.stack([filter_0, filter_45, filter_90, filter_135, filter_180, filter_225, filter_270, filter_315])

        self.directional_filter = nn.Conv2d(in_channels=1, out_channels=8, kernel_size=filter_0.shape, padding=filter_0.shape[-1] // 2)
        self.directional_filter.weight.data.copy_(torch.from_numpy(all_filters[:, None, ...]))
        self.directional_filter.bias.data.copy_(torch.from_numpy(np.zeros(shape=(all_filters.shape[0],))))

    def forward(self, img):
        img_r = img[:,0:1]
        img_g = img[:,1:2]
        img_b = img[:,2:3]

        blur_horizontal = self.gaussian_filter_horizontal(img_r)
        blurred_img_r = self.gaussian_filter_vertical(blur_horizontal)
        blur_horizontal = self.gaussian_filter_horizontal(img_g)
        blurred_img_g = self.gaussian_filter_vertical(blur_horizontal)
        blur_horizontal = self.gaussian_filter_horizontal(img_b)
        blurred_img_b = self.gaussian_filter_vertical(blur_horizontal)

        blurred_img = torch.stack([blurred_img_r,blurred_img_g,blurred_img_b],dim=1)
        blurred_img = torch.stack([torch.squeeze(blurred_img)])

        grad_x_r = self.sobel_filter_horizontal(blurred_img_r)
        grad_y_r = self.sobel_filter_vertical(blurred_img_r)
        grad_x_g = self.sobel_filter_horizontal(blurred_img_g)
        grad_y_g = self.sobel_filter_vertical(blurred_img_g)
        grad_x_b = self.sobel_filter_horizontal(blurred_img_b)
        grad_y_b = self.sobel_filter_vertical(blurred_img_b)

        # COMPUTE THICK EDGES

        grad_mag = torch.sqrt(grad_x_r**2 + grad_y_r**2)
        grad_mag += torch.sqrt(grad_x_g**2 + grad_y_g**2)
        grad_mag += torch.sqrt(grad_x_b**2 + grad_y_b**2)
        grad_orientation = (torch.atan2(grad_y_r+grad_y_g+grad_y_b, grad_x_r+grad_x_g+grad_x_b) * (180.0/3.14159))
        grad_orientation += 180.0
        grad_orientation =  torch.round( grad_orientation / 45.0 ) * 45.0

        # THIN EDGES (NON-MAX SUPPRESSION)

        all_filtered = self.directional_filter(grad_mag)

        inidices_positive = (grad_orientation / 45) % 8
        inidices_negative = ((grad_orientation / 45) + 4) % 8

        height = inidices_positive.size()[2]
        width = inidices_positive.size()[3]
        pixel_count = height * width
        pixel_range = torch.FloatTensor([range(pixel_count)])
        if self.use_cuda:
            pixel_range = torch.cuda.FloatTensor([range(pixel_count)])

        indices = (inidices_positive.view(-1).data * pixel_count + pixel_range).squeeze()
        channel_select_filtered_positive = all_filtered.view(-1)[indices.long()].view(1,height,width)

        indices = (inidices_negative.view(-1).data * pixel_count + pixel_range).squeeze()
        channel_select_filtered_negative = all_filtered.view(-1)[indices.long()].view(1,height,width)

        channel_select_filtered = torch.stack([channel_select_filtered_positive,channel_select_filtered_negative])

        is_max = channel_select_filtered.min(dim=0)[0] > 0.0
        is_max = torch.unsqueeze(is_max, dim=0)

        thin_edges = grad_mag.clone()
        thin_edges[is_max==0] = 0.0

        # THRESHOLD

        thresholded = thin_edges.clone()
        thresholded[thin_edges<self.threshold] = 0.0

        early_threshold = grad_mag.clone()
        early_threshold[grad_mag<self.threshold] = 0.0

        assert grad_mag.size() == grad_orientation.size() == thin_edges.size() == thresholded.size() == early_threshold.size()

        return blurred_img, grad_mag, grad_orientation, thin_edges, thresholded, early_threshold
        
        
        
        
        
