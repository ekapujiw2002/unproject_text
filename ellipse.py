#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''Functions for representing ellipses using various
parameterizations, and converting between them. There are three
parameterizations implemented by this module:

Geometric parameters:
---------------------

The geometric parameters are

  (x₀, y₀, a, b, θ)

The most simple parameterization of an ellipse is by its center point
(x0, y0), its semimajor and semiminor axes a and b, and its rotation
angle θ.

Conic:
------

This parameterization consists of six parameters A-F which establish
the implicit equation for a general conic:

  AX² + BXY + CY² + DX + EY + F = 0

Note that this equation may not represent only ellipses (it also
includes hyperbolas and parabolas).

Since multiplying the entire equation by any non-zero constant results
in the same ellipse, the six parameters are only described up to
scale, yielding five degrees of freedom. We can determine a canonical
scale factor k to scale this equation by such that

  A = a²(sin θ)² + b²(cos θ)²
  B = 2(b² - a²) sin θ cos θ
  C = a²(cos θ)² + b²(sin θ)²
  D = -2Ax₀ - By₀
  E = -Bx₀ - 2Cy₀
  F = Ax₀² + Bx₀y₀ + Cy₀² - a²b²

...in terms of the geometric parameters (x₀, y₀, a, b, θ).

Shape moments:
--------------

The shape moment parameters are

 (m₀₀, m₁₀, m₀₁, mu₂₀, mu₁₁, mu₀₂)

An ellipse may be completely specified by its shape moments up to
order 2. These include the area m₀₀, area-weighted center (m₁₀, m₀₁),
and the three second order central moments (mu₂₀, mu₁₁, mu₀₂).

'''

# pylint: disable=C0103
# pylint: disable=R0914
# pylint: disable=E1101

import numpy

def eigh_2x2(x, y, z):

    '''Computes the eigenvalues and eigenvectors of a 2x2 hermitian matrix
whose entries are [[x,y],[y,z]].'''

    q = numpy.sqrt(z**2 - 2*x*z + 4*y**2 + x**2)

    w = numpy.array([0.5 * (z + x - q),
                     0.5 * (z + x + q)])

    V = numpy.array([[2*y, 2*y],
                     [(z-x-q), (z-x+q)]])

    return w, V

def _params_str(names, params):

    '''Helper function for printing out the various parameters.'''

    return '({})'.format(', '.join('{}: {:g}'.format(n, p)
                                   for (n, p) in zip(names, params)))

######################################################################

GPARAMS_NAMES = ('x0', 'y0', 'a', 'b', 'theta')
GPARAMS_DISPLAY_NAMES = ('x₀', 'y₀', 'a', 'b', 'θ')

def gparams_str(gparams):
    '''Convert geometric parameters to nice printable string.'''
    return _params_str(GPARAMS_DISPLAY_NAMES, gparams)

def gparams_evaluate(gparams, phi):

    '''Evaluate the parametric formula for an ellipse at each angle
specified in the phi array. Returns two arrays x and y of the same
size as phi.

    '''

    x0, y0, a, b, theta = tuple(gparams)

    c = numpy.cos(theta)
    s = numpy.sin(theta)

    cp = numpy.cos(phi)
    sp = numpy.sin(phi)

    x = a*cp*c - b*sp*s + x0
    y = a*cp*s + b*sp*c + y0

    return x, y

def gparams_from_conic(conic):

    '''Convert the given conic parameters to geometric ellipse parameters.'''

    k, ab = conic_scale(conic)

    if numpy.isinf(ab):
        return None

    A, B, C, D, E, _ = tuple(conic)

    x0 = (B*E - 2*C*D)/(4*A*C - B**2)
    y0 = (-2*A*E + B*D)/(4*A*C - B**2)

    w, V = eigh_2x2(A, 0.5*B, C)

    b, a = tuple(numpy.sqrt(w/k))
    theta = numpy.arctan2(-V[0, 1], V[1, 1])

    return numpy.array((x0, y0, a, b, theta))

def gparams_from_moments(m):

    '''Convert the given moment parameters to geometric ellipse parameters.'''

    m00, m10, m01, mu20, mu11, mu02 = tuple(m)

    x0 = m10 / m00
    y0 = m01 / m00

    w, V = eigh_2x2(mu20/m00, mu11/m00, mu02/m00)

    b, a = tuple(2.0*numpy.sqrt(w))
    theta = numpy.arctan2(V[0, 0], -V[1, 0])

    return numpy.array((x0, y0, a, b, theta))

######################################################################

CONIC_NAMES = ('A', 'B', 'C', 'D', 'E', 'F')
CONIC_DISPLAY_NAMES = ('A', 'B', 'C', 'D', 'E', 'F')

def conic_str(conic):

    '''Convert conic parameters to nice printable string.'''
    return _params_str(CONIC_DISPLAY_NAMES, conic)

def conic_scale(conic):

    '''Returns a pair (k, ab) for the given conic parameters, where k is
the scale factor to divide all parameters by in order to normalize
them, and ab is the product of the semimajor and semiminor axis
(i.e. the ellipse's area, divided by pi). If the conic does not
describe an ellipse, then this returns infinity, infinity.

    '''

    A, B, C, D, E, F = tuple(conic)

    T = 4*A*C - B*B

    if T < 0.0:
        return numpy.inf, numpy.inf

    S = A*E**2 + B**2*F + C*D**2 - B*D*E - 4*A*C*F

    if not S:
        return numpy.inf, numpy.inf

    k = 0.25*T**2/S
    ab = 2.0*S/(T*numpy.sqrt(T))

    return k, ab

def conic_from_points(x, y):

    '''Fits conic pararameters using homogeneous least squares. The
resulting fit is unlikely to be numerically robust when the x/y
coordinates given are far from the [-1,1] interval.'''

    x = x.reshape((-1, 1))
    y = y.reshape((-1, 1))

    M = numpy.hstack((x**2, x*y, y**2, x, y, numpy.ones_like(x)))

    _, _, v = numpy.linalg.svd(M)

    return v[5, :].copy()

def conic_transform(conic, H):

    '''Returns the parameters of a conic after being transformed through a
3x3 homography H. This is straightforward since a conic can be
represented as a symmetric matrix (see
https://en.wikipedia.org/wiki/Matrix_representation_of_conic_sections).

    '''

    A, B, C, D, E, F = tuple(conic)

    M = numpy.array([[A, 0.5*B, 0.5*D],
                     [0.5*B, C, 0.5*E],
                     [0.5*D, 0.5*E, F]])

    Hinv = numpy.linalg.inv(H)

    M = numpy.dot(Hinv.T, numpy.dot(M, Hinv))

    A = M[0, 0]
    B = M[0, 1]*2
    C = M[1, 1]
    D = M[0, 2]*2
    E = M[1, 2]*2
    F = M[2, 2]

    return numpy.array((A, B, C, D, E, F))

def conic_from_gparams(gparams):

    '''Convert geometric parameters to conic parameters. Formulas from
https://en.wikipedia.org/wiki/Ellipse#General_ellipse.

    '''

    x0, y0, a, b, theta = tuple(gparams)
    c = numpy.cos(theta)
    s = numpy.sin(theta)

    A = a**2 * s**2 + b**2 * c**2
    B = 2*(b**2 - a**2) * s * c
    C = a**2 * c**2 + b**2 * s**2
    D = -2*A*x0 - B*y0
    E = -B*x0 - 2*C*y0
    F = A*x0**2 + B*x0*y0 + C*y0**2 - a**2*b**2

    return numpy.array((A, B, C, D, E, F))

def conic_from_moments(moments):

    '''Convert shape moments to conic parameters. Formulas derived through
trial and error.'''

    m00, m10, m01, mu20, mu11, mu02 = tuple(moments)

    x0 = m10/m00
    y0 = m01/m00

    A = 4*mu02/m00
    B = -8*mu11/m00
    C = 4*mu20/m00

    a2b2 = 0.25*(4*A*C - B*B)

    D = -2*A*x0 - B*y0
    E = -B*x0 - 2*C*y0
    F = A*x0**2 + B*x0*y0 + C*y0**2 - a2b2

    return numpy.array((A, B, C, D, E, F))

######################################################################

MOMENTS_NAMES = ('m00', 'm10', 'm01', 'mu20', 'mu11', 'mu02')
MOMENTS_DISPLAY_NAMES = ('m₀₀', 'm₁₀', 'm₀₁', 'mu₂₀', 'mu₁₁', 'mu₀₂')

def moments_from_dict(m):

    '''Create shape moments tuple from a dictionary (i.e. returned by cv2.moments).'''
    return numpy.array([m[n] for n in MOMENTS_NAMES])

def moments_str(m):
    '''Convert shape moments to nice printable string.'''
    return _params_str(MOMENTS_DISPLAY_NAMES, m)

def moments_from_gparams(gparams):

    '''Create shape moments from geometric parameters.'''
    x0, y0, a, b, theta = tuple(gparams)
    c = numpy.cos(theta)
    s = numpy.sin(theta)

    m00 = a*b*numpy.pi
    m10 = x0 * m00
    m01 = y0 * m00

    mu20 = (a**2 * c**2 + b**2 * s**2) * m00 * 0.25
    mu11 = -(b**2-a**2) * s * c * m00 * 0.25
    mu02 = (a**2 * s**2 + b**2 * c**2) * m00 * 0.25

    return numpy.array((m00, m10, m01, mu20, mu11, mu02))

def moments_from_conic(scaled_conic):

    '''Create shape moments from conic parameters.'''

    k, ab = conic_scale(scaled_conic)

    if numpy.isinf(ab):
        return None

    conic = numpy.array(scaled_conic)/k

    A, B, C, D, E, _ = tuple(conic)

    x0 = (B*E - 2*C*D)/(4*A*C - B**2)
    y0 = (-2*A*E + B*D)/(4*A*C - B**2)

    m00 = numpy.pi*ab
    m10 = x0*m00
    m01 = y0*m00

    mu20 = 0.25*C*m00
    mu11 = -0.125*B*m00
    mu02 = 0.25*A*m00

    return numpy.array((m00, m10, m01, mu20, mu11, mu02))

def moments_from_contour(xypoints):

    '''Create shape moments from points sampled from the outline of an
ellipse (note this is numerically inaccurate even for arrays of 1000s
of points. Included here mostly for testing.

This function is ported from OpenCV's contourMoments function in
opencv/modules/imgproc/src/moments.cpp, licensed as follows:

----------------------------------------------------------------------

By downloading, copying, installing or using the software you agree to
this license.  If you do not agree to this license, do not download,
install, copy or use the software.


                          License Agreement
               For Open Source Computer Vision Library
                       (3-clause BSD License)

Copyright (C) 2000-2016, Intel Corporation, all rights reserved.
Copyright (C) 2009-2011, Willow Garage Inc., all rights reserved.
Copyright (C) 2009-2016, NVIDIA Corporation, all rights reserved.
Copyright (C) 2010-2013, Advanced Micro Devices, Inc., all rights reserved.
Copyright (C) 2015-2016, OpenCV Foundation, all rights reserved.
Copyright (C) 2015-2016, Itseez Inc., all rights reserved.
Third party copyrights are property of their respective owners.

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are
met:

  * Redistributions of source code must retain the above copyright
    notice, this list of conditions and the following disclaimer.

  * Redistributions in binary form must reproduce the above copyright
    notice, this list of conditions and the following disclaimer in
    the documentation and/or other materials provided with the
    distribution.

  * Neither the names of the copyright holders nor the names of the
    contributors may be used to endorse or promote products derived
    from this software without specific prior written permission.

This software is provided by the copyright holders and contributors
"as is" and any express or implied warranties, including, but not
limited to, the implied warranties of merchantability and fitness for
a particular purpose are disclaimed.  In no event shall copyright
holders or contributors be liable for any direct, indirect,
incidental, special, exemplary, or consequential damages (including,
but not limited to, procurement of substitute goods or services; loss
of use, data, or profits; or business interruption) however caused and
on any theory of liability, whether in contract, strict liability, or
tort (including negligence or otherwise) arising in any way out of the
use of this software, even if advised of the possibility of such
damage.

    '''

    assert len(xypoints.shape) == 3
    assert xypoints.shape[1:] == (1, 2)

    xypoints = xypoints.reshape((-1, 2))

    a00 = 0
    a10 = 0
    a01 = 0
    a20 = 0
    a11 = 0
    a02 = 0

    xi_1, yi_1 = xypoints[-1]

    for xy in xypoints:

        xi, yi = xy
        xi2 = xi * xi
        yi2 = yi * yi
        dxy = xi_1 * yi - xi * yi_1
        xii_1 = xi_1 + xi
        yii_1 = yi_1 + yi

        a00 += dxy
        a10 += dxy * xii_1
        a01 += dxy * yii_1
        a20 += dxy * (xi_1 * xii_1 + xi2)
        a11 += dxy * (xi_1 * (yii_1 + yi_1) + xi * (yii_1 + yi))
        a02 += dxy * (yi_1 * yii_1 + yi2)

        xi_1 = xi
        yi_1 = yi

    if a00 > 0:
        db1_2 = 0.5
        db1_6 = 0.16666666666666666666666666666667
        db1_12 = 0.083333333333333333333333333333333
        db1_24 = 0.041666666666666666666666666666667
    else:
        db1_2 = -0.5
        db1_6 = -0.16666666666666666666666666666667
        db1_12 = -0.083333333333333333333333333333333
        db1_24 = -0.041666666666666666666666666666667

    m00 = a00 * db1_2
    m10 = a10 * db1_6
    m01 = a01 * db1_6
    m20 = a20 * db1_12
    m11 = a11 * db1_24
    m02 = a02 * db1_12

    inv_m00 = 1. / m00
    cx = m10 * inv_m00
    cy = m01 * inv_m00

    mu20 = m20 - m10 * cx
    mu11 = m11 - m10 * cy
    mu02 = m02 - m01 * cy

    return m00, m10, m01, mu20, mu11, mu02

######################################################################

def _perspective_transform(pts, H):

    '''Used for testing only.'''

    assert len(pts.shape) == 3
    assert pts.shape[1:] == (1, 2)

    pts = numpy.hstack((pts.reshape((-1, 2)),
                        numpy.ones((len(pts), 1), dtype=pts.dtype)))

    pts = numpy.dot(pts, H.T)

    pts = pts[:, :2] / pts[:, 2].reshape((-1, 1))

    return pts.reshape((-1, 1, 2))


def _test_ellipse():

    '''Run some basic unit tests for this module.'''

    ##################################################
    # test eigh_2x2

    print 'testing eigh_2x2 on a bunch of random 2x2 matrices...'

    for _ in range(100):
        theta = numpy.random.random()*2*numpy.pi
        a = numpy.random.random()*9 + 1
        b = numpy.random.random()*9 + 1
        a, b = max(a, b), min(a, b)
        c = numpy.cos(theta)
        s = numpy.sin(theta)
        R = numpy.array([[c, -s], [s, c]])
        A = numpy.dot(R, numpy.dot(numpy.diag([a, b]), R.T))
        assert numpy.allclose(A[1, 0], A[0, 1])
        w, V = eigh_2x2(A[0, 0], A[0, 1], A[1, 1])
        AA = numpy.dot(V, numpy.dot(numpy.diag(w), numpy.linalg.inv(V)))
        assert numpy.allclose(w, [b, a])
        assert numpy.allclose(A, AA)

    print '...it worked!'
    print


    # test that we can go from conic to geometric and back
    x0 = 450
    y0 = 320
    a = 300
    b = 200
    theta = -0.25

    gparams = numpy.array((x0, y0, a, b, theta))

    conic = conic_from_gparams(gparams)
    k, ab = conic_scale(conic)

    # ensure conic created from geometric params has trivial scale
    assert numpy.allclose((k, ab), (1.0, a*b))

    # evaluate parametric curve at different angles phi
    phi = numpy.linspace(0, 2*numpy.pi, 1001).reshape((-1, 1))
    x, y = gparams_evaluate(gparams, phi)

    # evaluate implicit conic formula at x,y pairs
    M = numpy.hstack((x**2, x*y, y**2, x, y, numpy.ones_like(x)))
    implicit_output = numpy.dot(M, conic)
    implicit_max = numpy.abs(implicit_output).max()

    # ensure implicit evaluates near 0 everywhere
    print 'max item from implicit: {} (should be close to 0)'.format(implicit_max)
    print
    assert implicit_max < 1e-5

    # ensure that scaled_conic has the scale we expect
    k = 1e-3
    scaled_conic = conic*k

    k2, ab2 = conic_scale(scaled_conic)

    print 'these should all be equal:'
    print
    print '  k  =', k
    print '  k2 =', k2
    assert numpy.allclose((k2, ab2), (k, a*b))
    print

    # convert the scaled conic back to geometric parameters
    gparams2 = gparams_from_conic(scaled_conic)

    print '  gparams  =', gparams_str(gparams)

    # ensure that converting back from scaled conic to geometric params is correct
    print '  gparams2 =', gparams_str(gparams2)
    assert numpy.allclose(gparams, gparams2)

    # convert original geometric parameters to moments
    m = moments_from_gparams(gparams)
    # ...and back
    gparams3 = gparams_from_moments(m)

    # ensure that converting back from moments to geometric params is correct
    print '  gparams3 =', gparams_str(gparams3)
    print
    assert numpy.allclose(gparams, gparams3)

    # convert moments parameterization to conic
    conic2 = conic_from_moments(m)

    # ensure that converting from moments to conics is correct
    print '  conic  =', conic_str(conic)
    print '  conic2 =', conic_str(conic2)
    assert numpy.allclose(conic, conic2)

    # create conic from homogeneous least squares fit of points
    skip = len(x) / 10
    conic3 = conic_from_points(x[::skip], y[::skip])

    # ensure that it has non-infinite area
    k3, ab3 = conic_scale(conic3)
    assert not numpy.isinf(ab3)

    # normalize
    conic3 /= k3

    # ensure that conic from HLS fit is same as other 2
    print '  conic3 =', conic_str(conic3)
    print
    assert numpy.allclose(conic, conic3)

    # convert from conic to moments
    m2 = moments_from_conic(scaled_conic)

    print '  m  =', moments_str(m)

    # ensure that conics->moments yields the same result as geometric
    # params -> moments.
    print '  m2 =', moments_str(m2)
    assert numpy.allclose(m, m2)

    # create moments from contour
    pts = numpy.hstack((x, y)).reshape((-1, 1, 2))
    m3 = moments_from_contour(pts)

    # ensure that moments from contour is reasonably close to moments
    # from geometric params.
    print '  m3 =', moments_str(m3)
    print
    assert numpy.allclose(m3, m, 1e-4, 1e-4)

    # create a homography H to map the ellipse through
    hx = 0.001
    hy = 0.0015

    H = numpy.array([
        [1, -0.2, 0],
        [0, 0.7, 0],
        [hx, hy, 1]])

    T = numpy.array([
        [1, 0, 400],
        [0, 1, 300],
        [0, 0, 1]])

    H = numpy.dot(T, numpy.dot(H, numpy.linalg.inv(T)))

    # transform the original points thru H
    Hpts = _perspective_transform(pts, H)

    # transform the conic parameters directly thru H
    Hconic = conic_transform(conic, H)

    # get the HLS fit of the conic corresponding to the transformed points
    Hconic2 = conic_from_points(Hpts[::skip, :, 0], Hpts[::skip, :, 1])

    # normalize the two conics
    Hk, Hab = conic_scale(Hconic)
    Hk2, Hab2 = conic_scale(Hconic2)
    assert not numpy.isinf(Hab) and not numpy.isinf(Hab2)

    Hconic /= Hk
    Hconic2 /= Hk2

    # ensure that the two conics are equal
    print '  Hconic  =', conic_str(Hconic)
    print '  Hconic2 =', conic_str(Hconic2)
    print
    assert numpy.allclose(Hconic, Hconic2)

    # get the moments from Hconic
    Hm = moments_from_conic(Hconic)

    # get the moments from the transformed points
    Hm2 = moments_from_contour(Hpts)

    # ensure that the two moments are close enough
    print '  Hm  =', moments_str(Hm)
    print '  Hm2 =', moments_str(Hm2)
    print
    assert numpy.allclose(Hm, Hm2, 1e-4, 1e-4)

    # tests complete, now visualize
    print 'all tests passed!'

    try:
        import cv2
        print 'visualizing results...'
    except ImportError:
        import sys
        print 'not visualizing results since module cv2 not found'
        sys.exit(0)
    
    shift = 3
    pow2 = 2**shift

    p0 = numpy.array([x0, y0], dtype=numpy.float32)
    p1 = _perspective_transform(p0.reshape((-1, 1, 2)), H).flatten()

    Hgparams = gparams_from_conic(Hconic)
    Hp0 = Hgparams[:2]

    skip = len(pts)/100

    display = numpy.zeros((600, 800, 3), numpy.uint8)

    def _asint(x, as_tuple=True):
        x = x*pow2 + 0.5
        x = x.astype(int)
        if as_tuple:
            return tuple(x)
        else:
            return x

    for (a, b) in zip(pts.reshape((-1, 2))[::skip],
                      Hpts.reshape((-1, 2))[::skip]):

        cv2.line(display, _asint(a), _asint(b),
                 (255, 0, 255), 1, cv2.LINE_AA, shift)

    cv2.polylines(display, [_asint(pts, False)], True,
                  (0, 255, 0), 1, cv2.LINE_AA, shift)

    cv2.polylines(display, [_asint(Hpts, False)], True,
                  (0, 0, 255), 1, cv2.LINE_AA, shift)

    r = 3.0

    cv2.circle(display, _asint(p0), int(r*pow2+0.5),
               (0, 255, 0), 1, cv2.LINE_AA, shift)

    cv2.circle(display, _asint(p1), int(r*pow2+0.5),
               (255, 0, 255), 1, cv2.LINE_AA, shift)

    cv2.circle(display, _asint(Hp0), int(r*pow2+0.5),
               (0, 0, 255), 1, cv2.LINE_AA, shift)

    cv2.imshow('win', display)

    print 'click in the display window & hit any key to quit.'

    while cv2.waitKey(5) < 0:
        pass

if __name__ == '__main__':

    _test_ellipse()
