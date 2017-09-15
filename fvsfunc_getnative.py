import vapoursynth as vs
import re
from functools import partial
import havsfunc as haf  # https://github.com/HomeOfVapourSynthEvolution/havsfunc
import mvsfunc as mvf  # https://github.com/HomeOfVapourSynthEvolution/mvsfunc
import muvsfunc as muf  # https://github.com/WolframRhodium/muvsfunc
import nnedi3_rpow2  # https://gist.github.com/4re/342624c9e1a144a696c6

# Small collection of VapourSynth functions I used at least once.
# Most are simple wrappers or ports of AviSynth functions.

# Included functions:
#
#       GradFun3mod
#       descale_getnativeM (DebilinearM, DebicubicM etc.)
#       Downscale444
#       JIVTC
#       OverlayInter
#       AutoDeblock
#       ReplaceFrames (ReplaceFramesSimple)
#       maa
#       TemporalDegrain
#       descale_getnativeAA
#       InsertSign


core = vs.core


"""
VapourSynth port of Gebbi's GradFun3mod

Based on Muonium's GradFun3 port:
https://github.com/WolframRhodium/muvsfunc

If you don't use any of the newly added arguments
it will behave just like unmodified GradFun3.

Differences:

 - added smode=5 that uses a bilateral filter on the GPU (CUDA)
   output should be very similar to smode=2
 - fixed the strength of the bilateral filter when using 
   smode=2 to match the AviSynth version
 - changed argument lsb to bits (default is input bitdepth)
 - case of the resizer doesn't matter anymore
 - every resizer supported by fmtconv.resample can be specified
 - yuv444 can now be used with any output resolution
 - removed fh and fv arguments for all resizers

Requirements:

 - muvsfunc  https://github.com/WolframRhodium/muvsfunc
 - havsfunc  https://github.com/HomeOfVapourSynthEvolution/havsfunc
 - mvsfunc  https://github.com/HomeOfVapourSynthEvolution/mvsfunc
 - Bilateral  https://github.com/HomeOfVapourSynthEvolution/VapourSynth-Bilateral
 - BilateralGPU (optional, needs OpenCV 3.2 with CUDA module)  https://github.com/WolframRhodium/VapourSynth-BilateralGPU
 - fmtconv  https://github.com/EleonoreMizo/fmtconv
 - descale_getnative (optional)  https://github.com/Frechdachs/vapoursynth-descale_getnative
 - dfttest  https://github.com/HomeOfVapourSynthEvolution/VapourSynth-DFTTest
 - nnedi3  https://github.com/dubhater/vapoursynth-nnedi3
 - nnedi3_rpow2  https://gist.github.com/4re/342624c9e1a144a696c6

Original header:

##################################################################################################################
#
#   High bitdepth tools for Avisynth - GradFun3mod r6
#       based on Dither v1.27.2
#   Author: Firesledge, slightly modified by Gebbi
#
#  What?
#       - This is a slightly modified version of the original GradFun3.
#       - It combines the usual color banding removal stuff with resizers during the process
#         for sexier results (less detail loss, especially for downscales of cartoons).
#       - This is a starter script, not everything is covered through parameters. Modify it to your needs.
#
#   Requirements (in addition to the Dither requirements):
#       - AviSynth 2.6.x
#       - Debilinear, Debicubic, DebilinearM
#       - NNEDI3 + nnedi3_resize16
#
#  Changes from the original GradFun3:
#       - yuv444 = true
#         (4:2:0 -> 4:4:4 colorspace conversion, needs 1920x1080 input)
#       - resizer = [ "none", "Debilinear", "DebilinearM", "Debicubic", "DebicubicM", "Spline16",
#         "Spline36", "Spline64", "lineart_rpow2", "lineart_rpow2_bicubic" ] 
#         (use it only for downscales)
#           NOTE: As of r2 Debicubic doesn't have 16-bit precision, so a Y (luma) plane fix by torch is used here,
#                 more info: https://mechaweaponsvidya.wordpress.com/2015/07/07/a-precise-debicubic/
#                 Without yuv444=true Dither_resize16 is used with an inverse bicubic kernel.
#       - w = 1280, h = 720
#         (output width & height for the resizers; or production resolution for resizer="lineart_rpow2")
#       - smode = 4
#         (the old GradFun3mod behaviour for legacy reasons; based on smode = 1 (dfttest);
#         not useful anymore in most cases, use smode = 2 instead (less detail loss))
#       - deb = true
#         (legacy parameter; same as resizer = "DebilinearM")
#
#  Usage examples:
#       - Source is bilinear 720p->1080p upscale (BD) with 1080p credits overlayed,
#         revert the upscale without fucking up the credits:
#               lwlibavvideosource("lol.m2ts")
#               GradFun3mod(smode=1, yuv444=true, resizer="DebilinearM")
#
#       - same as above, but bicubic Catmull-Rom upscale (outlines are kind of "blocky" and oversharped):
#               GradFun3mod(smode=1, yuv444=true, resizer="DebicubicM", b=0, c=1)
#               (you may try any value between 0 and 0.2 for b, and between 0.7 and 1 for c)
#
#       - You just want to get rid off the banding without changing the resolution:
#               GradFun3(smode=2)
#
#       - Source is 1080p production (BD), downscale to 720p:
#               GradFun3mod(smode=2, yuv444=true, resizer="Spline36")
#
#       - Source is a HDTV transportstream (or CR or whatever), downscale to 720p:
#               GradFun3mod(smode=2, resizer="Spline36")
#
#       - Source is anime, 720p->1080p upscale, keep the resolution
#         but with smoother lineart instead of bilinear upscaled shit:
#               GradFun3mod(smode=2, resizer="lineart_rpow2")
#         This won't actually resize the video but instead mask the lineart and re-upscale it using
#         nnedi3_rpow2 which often results in much better looking lineart (script mostly by Daiz).
#
#       Note: Those examples don't include parameters like thr, radius, elast, mode, ampo, ampn, staticnoise.
#             You probably don't want to use the default values.
#             For 16-bit output use:
#              GradFun3mod(lsb=true).Dither_out()
#
#  What's the production resolution of my korean cartoon?
#       - Use your eyes combined with Debilinear(1280,720) - if it looks like oversharped shit,
#         it was probably produced in a higher resolution.
#       - Use Debilinear(1280,720).BilinearResize(1920,1080) for detail loss search.
#       - Alternatively you can lookup the (estimated) production resolution at
#         http://anibin.blogspot.com  (but don't blindly trust those results)
#
#   This program is free software. It comes without any warranty, to
#   the extent permitted by applicable law. You can redistribute it
#   and/or modify it under the terms of the Do What The Fuck You Want
#   To Public License, Version 2, as published by Sam Hocevar. See
#   http://sam.zoy.org/wtfpl/COPYING for more details.
#
##################################################################################################################

"""
# Helpers

# Wrapper with fmtconv syntax that tries to use the internal resizers whenever it is possible
def Resize(src, w, h, sx=None, sy=None, sw=None, sh=None, kernel='spline36', taps=None, a1=None,
             a2=None, a3=None, invks=None, invkstaps=None, fulls=None, fulld=None):

    bits = src.format.bits_per_sample

    if (src.width, src.height, fulls) == (w, h, fulld):
        return src

    if kernel is None:
        kernel = 'spline36'
    kernel = kernel.lower()

    if invks and kernel == 'bilinear' and hasattr(core, 'unresize') and invkstaps is None:
        return core.unresize.Unresize(src, w, h, src_left=sx, src_top=sy)
    if invks and kernel in ['bilinear', 'bicubic', 'lanczos', 'spline16', 'spline36'] and hasattr(core, 'descale_getnative') and invkstaps is None:
        return descale_getnative(src, w, h, kernel=kernel, b=a1, c=a2, taps=taps)
    if not invks:
        if kernel == 'bilinear':
            return core.resize.Bilinear(src, w, h, range=fulld, range_in=fulls, src_left=sx, src_top=sy,
                                        src_width=sw, src_height=sh)
        if kernel == 'bicubic':
            return core.resize.Bicubic(src, w, h, range=fulld, range_in=fulls, filter_param_a=a1, filter_param_b=a2,
                                       src_left=sx, src_top=sy, src_width=sw, src_height=sh)
        if kernel == 'spline16':
            return core.resize.Spline16(src, w, h, range=fulld, range_in=fulls, src_left=sx, src_top=sy,
                                        src_width=sw, src_height=sh)
        if kernel == 'spline36':
            return core.resize.Spline36(src, w, h, range=fulld, range_in=fulls, src_left=sx, src_top=sy,
                                        src_width=sw, src_height=sh)
        if kernel == 'lanczos':
            return core.resize.Lanczos(src, w, h, range=fulld, range_in=fulls, filter_param_a=taps,
                                       src_left=sx, src_top=sy, src_width=sw, src_height=sh)
    return Depth(core.fmtc.resample(src, w, h, sx=sx, sy=sy, sw=sw, sh=sh, kernel=kernel, taps=taps,
                              a1=a1, a2=a2, a3=a3, invks=invks, invkstaps=invkstaps, fulls=fulls, fulld=fulld), bits)


def Debilinear(src, width, height, yuv444=False, gray=False, chromaloc=None):
    return descale_getnative(src, width, height, kernel='bilinear', b=None, c=None, taps=None, yuv444=yuv444, gray=gray, chromaloc=chromaloc)


def Debicubic(src, width, height, b=1/3, c=1/3, yuv444=False, gray=False, chromaloc=None):
    return descale_getnative(src, width, height, kernel='bicubic', b=b, c=c, taps=None, yuv444=yuv444, gray=gray, chromaloc=chromaloc)


def Delanczos(src, width, height, taps=3, yuv444=False, gray=False, chromaloc=None):
    return descale_getnative(src, width, height, kernel='lanczos', b=None, c=None, taps=taps, yuv444=yuv444, gray=gray, chromaloc=chromaloc)


def Despline16(src, width, height, yuv444=False, gray=False, chromaloc=None):
    return descale_getnative(src, width, height, kernel='spline16', b=None, c=None, taps=None, yuv444=yuv444, gray=gray, chromaloc=chromaloc)


def Despline36(src, width, height, yuv444=False, gray=False, chromaloc=None):
    return descale_getnative(src, width, height, kernel='spline36', b=None, c=None, taps=None, yuv444=yuv444, gray=gray, chromaloc=chromaloc)


def descale_getnative(src, width, height, kernel='bilinear', b=1/3, c=1/3, taps=3, yuv444=False, gray=False, chromaloc=None):
    src_f = src.format
    src_cf = src_f.color_family
    src_st = src_f.sample_type
    src_bits = src_f.bits_per_sample
    src_sw = src_f.subsampling_w
    src_sh = src_f.subsampling_h

    descale_getnative_filter = get_descale_getnative_filter(b, c, taps, kernel)

    if src_cf == vs.RGB and not gray:
        rgb = descale_getnative_filter(to_rgbs(src), width, height)
        return rgb.resize.Point(format=src_f.id)

    y = descale_getnative_filter(to_grays(src), width, height)
    y_f = core.register_format(vs.GRAY, src_st, src_bits, 0, 0)
    y = y.resize.Point(format=y_f.id)

    if src_cf == vs.GRAY or gray:
        return y

    if not yuv444 and ((width % 2 and src_sw) or (height % 2 and src_sh)):
        raise ValueError('descale_getnative: The output dimension and the subsampling are incompatible.')

    uv_f = core.register_format(src_cf, src_st, src_bits, 0 if yuv444 else src_sw, 0 if yuv444 else src_sh)
    uv = src.resize.Spline36(width, height, format=uv_f.id, chromaloc_s=chromaloc)

    return core.std.ShufflePlanes([y,uv], [0,1,2], vs.YUV)


def to_grays(src):
    return src.resize.Point(format=vs.GRAYS)


def to_rgbs(src):
    return src.resize.Point(format=vs.RGBS)


def get_plane(src, plane):
    return core.std.ShufflePlanes(src, plane, vs.GRAY)


def get_descale_getnative_filter(b, c, taps, kernel):
    kernel = kernel.lower()
    if kernel == 'bilinear':
        return core.descale_getnative.Debilinear
    elif kernel == 'bicubic':
        return partial(core.descale_getnative.Debicubic, b=b, c=c)
    elif kernel == 'lanczos':
        return partial(core.descale_getnative.Delanczos, taps=taps)
    elif kernel == 'spline16':
        return core.descale_getnative.Despline16
    elif kernel == 'spline36':
        return core.descale_getnative.Despline36
    else:
        raise ValueError('descale_getnative: Invalid kernel specified.')


def Depth(src, bits, dither_type='error_diffusion', range=None, range_in=None):
    src_f = src.format
    src_cf = src_f.color_family
    src_bits = src_f.bits_per_sample
    src_sw = src_f.subsampling_w
    src_sh = src_f.subsampling_h
    dst_st = vs.INTEGER if bits < 32 else vs.FLOAT

    if isinstance(range, str):
        range = RANGEDICT[range]

    if isinstance(range_in, str):
        range_in = RANGEDICT[range_in]

    if (src_bits, range_in) == (bits, range):
        return src
    out_f = core.register_format(src_cf, dst_st, bits, src_sw, src_sh)
    return core.resize.Point(src, format=out_f.id, dither_type=dither_type, range=range, range_in=range_in)


RANGEDICT = {'limited': 0, 'full': 1}
