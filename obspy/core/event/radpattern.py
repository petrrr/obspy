# -*- coding: utf-8 -*-
# -------------------------------------------------------------------
# Filename: radpattern.py
#  Purpose: Computes and plots radiation patterns
# ---------------------------------------------------------------------

"""
This script contains the following functions to compute and plot radiation
patterns:
    farfield_p
    farfield_s
    plot_3drpattern

:copyright:
    The ObsPy Development Team (devs@obspy.org)
:license:
    GNU Lesser General Public License, Version 3
    (http://www.gnu.org/copyleft/lesser.html)
"""
from __future__ import (absolute_import, division, print_function,
                        unicode_literals)
from future.builtins import *  # NOQA @UnusedWildImport

import numpy as np
import matplotlib.pyplot as plt
from obspy.imaging.scripts.mopad import MomentTensor, BeachBall
from obspy.imaging.mopad_wrapper import Beach
from mpl_toolkits.mplot3d import Axes3D  # NOQA


def plot_3drpattern(mt, kind='both_sphere', coordinate_system='RTP',
                    p_sphere_direction='inwards'):
    """
    Plots the P farfield radiation pattern on a unit sphere grid
    calculations are based on Aki & Richards Eq 4.29


    :param mt: Focal mechanism NM x 6 (M11, M22, M33, M12, M13, M23 - the
        six independent components of the moment tensor, where the coordinate
        system is 1,2,3 = Up,South,East which equals r,theta,phi -
        Harvard/Global CMT convention). The relation to Aki and Richards
        x,y,z equals North,East,Down convention is as follows: Mrr=Mzz,
        Mtt=Mxx, Mpp=Myy, Mrt=Mxz, Mrp=-Myz, Mtp=-Mxy.

    :param kind: can be one of the following options:
                 'p_quiver': matplotlib quiver plot of p wave farfield
                 's_quiver': matplotlib quiver plot of s wave farfield
                 'both_quiver': matplotlib quiver plot of s and p wave farfield
                 'p_sphere': matplotlib surface plot of p wave farfield
                 's_sphere': matplotlib surface plot of s wave farfield
                 'mayavi': uses the mayavi library (not yet available under
                           python 3 and problematic with anaconda)
                 'vtk': This vtk option writes three vtk files to the current
                        working directory. rpattern.vtk contains the p and s
                        wave farfield vector field beachlines.vtk contains the
                        nodal lines of the radiation pattern rpattern.pvsm
                        is a state file that sets paraview parameters to plot
                        rpattern.vtk and beachlines.vtk

    :return: 3D grid point array with shape [3,npts] that contains
             the sperical grid points

             3D vector array with shape [3,npts] that contains the
             displacement vector for each grid point
    """

    # reoorder all moment tensors to NED convention
    # name : COMPONENT              : NED sign and index
    # NED  : NN, EE, DD, NE, ND, ED : [0, 1, 2, 3, 4, 5]
    # USE  : UU, SS, EE, US, UE, SE : [1, 2, 0, -5, 3, -4]
    # RTP  : RR, TT, PP, RT, RP, TP : [1, 2, 0, -5, 3, -4]
    # DSE  : DD, SS, EE, DS, DE, SE : [1, 2, 0, -5, -3, 4]
    if coordinate_system == 'RTP' or coordinate_system == 'USE':
        signs = [1, 1, 1, -1, 1, -1]
        indices = [1, 2, 0, 5, 3, 4]
        ned_mt = [sign * mt[ind] for sign, ind in zip(signs, indices)]
    elif coordinate_system == 'DSE':
        signs = [1, 1, 1, -1, -1, 1]
        indices = [1, 2, 0, 5, 3, 4]
        ned_mt = [sign * mt[ind] for sign, ind in zip(signs, indices)]
    elif coordinate_system == 'NED':
        ned_mt = mt
    else:
        msg = 'coordinate system {:s} not known'.format(coordinate_system)
        raise NotImplementedError(msg)

    # adjusted beachball plot:
    #ax3d = fig.add_axes((0.01, 0.01, 0.48, 0.98), projection='3d')
    #size = 0.8  # shrink ax to make it more similar to the 3d plot
    #width, height = size * 0.5, size * 1.
    #left = 0.5 + (0.5-width)/2.
    #bottom = (1.-height)/2.
    #axbball = fig.add_axes((left, bottom, width, height))

    #ax2d.spines['left'].set_position('center')
    #ax2d.spines['right'].set_color('none')
    #ax2d.spines['bottom'].set_position('center')
    #ax2d.spines['top'].set_color('none')
    if isinstance(kind, list):
        nplots = len(kind)
        maxcolumns = 3  # the maximum number of plots in one row
        ncols = min(nplots, maxcolumns)
        nrows = int(np.ceil(nplots / ncols))
        figsize = ncols * 5., nrows * 5.
        fig = plt.figure(figsize=figsize, facecolor='white')

        for iplot in range(nplots):
            iax = iplot + 1
            if kind[iplot] == 'p_quiver':
                ax3d = fig.add_subplot(nrows, ncols, iax, projection='3d')
                _plot_p_quiver(ax3d, ned_mt)

            elif kind[iplot] == 'p_sphere':
                ax3d = fig.add_subplot(nrows, ncols, iax, projection='3d')
                _plot_p_sphere(ax3d, ned_mt, p_sphere_direction)

            elif kind[iplot] == 's_quiver':
                ax3d = fig.add_subplot(nrows, ncols, iax, projection='3d')
                _plot_s_quiver(ax3d, ned_mt)

            elif kind[iplot] == 's_sphere':
                ax3d = fig.add_subplot(nrows, ncols, iax, projection='3d')
                _plot_s_sphere(ax3d, ned_mt)

            elif kind[iplot] == 'beachball':
                ax2d = fig.add_subplot(nrows, ncols, iax)
                ax2d.spines['left'].set_position('center')
                ax2d.spines['right'].set_color('none')
                ax2d.spines['bottom'].set_position('center')
                ax2d.spines['top'].set_color('none')
                _plot_beachball(ax2d, mt)

        fig.tight_layout(pad=0.1)
        plt.show()

    elif kind == 'mayavi':
        _plot_mayavi(ned_mt)

    elif kind == 'vtk':
        # this saves two files, one with the vector field and one
        # with the nodal lines of the beachball
        fname_rpattern = 'rpattern.vtk'
        fname_beachlines = 'beachlines.vtk'
        _write_vtk_files(ned_mt,
                         fname_rpattern=fname_rpattern,
                         fname_beachlines=fname_beachlines)

    else:
        raise NotImplementedError('{:s} not implemented yet'.format(kind))


def _plot_p_quiver(ax3d, ned_mt):
    """
    private routine that plots the p_wave farfield into the
    input ax object

    :param ax3d: a matplotlib ax with 3d projection activated
    :param ned_mt: the 6 comp moment tensor in NED orientation
    """
    # precompute even spherical grid and directional cosine array
    points = equalarea_spherical_grid(nlat=14)

    # get radiation pattern
    disp = farfield_p(ned_mt, points)

    # normalized magnitude:
    magn = np.sum(disp * points, axis=0)
    magn /= np.max(np.abs(magn))

    # there is a mlab3d bug that quiver vector colors and lengths
    # can only be changed if we plot each arrow independently
    for loc, vec, mag in zip(points.T, disp.T, magn.T):
        # compute colours and displace points along normal
        norm = plt.Normalize(-1., 1.)
        cmap = plt.get_cmap('bwr')
        loc *= (1. + mag/2.)
        color = cmap(norm(mag))
        ax3d.quiver(loc[0], loc[1], loc[2], vec[0], vec[1], vec[2],
                    length=abs(mag)/2., color=color)
    ax3d.set(xlim=(-1.5, 1.5), ylim=(-1.5, 1.5), zlim=(-1.5, 1.5),
             xticks=[-1, 1], yticks=[-1, 1], zticks=[-1, 1],
             xticklabels=['South', 'North'],
             yticklabels=['West', 'East'],
             zticklabels=['Up', 'Down'],
             title='p-wave farfield')
    ax3d.view_init(elev=-110., azim=0.)


def _plot_p_sphere(ax3d, ned_mt, p_sphere_direction):
    """
    private function that plots a p radiation pattern sphere into
    ax3d
    :param ax3d: matplotlib 3d ax object
    :param ned_mt: moment tensor in NED convention
    :param p_sphere_direction: if this is 'inwards', the tension regions
                               of the beachball deform the radiation sphere
                               inwards. If 'outwards' it deforms outwards.
    """
    # generate spherical mesh that is aligned with the moment tensor null
    # axis. MOPAD should use NED coordinate system to avoid internal
    # coordinate transformations
    mtensor = MomentTensor(ned_mt, system='NED')

    # use the most isolated eigenvector as axis of symmetry
    evecs = mtensor.get_eigvecs()
    evals = np.abs(mtensor.get_eigvals())**2
    evals_dev = np.abs(evals-np.mean(evals))
    if p_sphere_direction == 'outwards':
        evec_max = evecs[np.argmax(evals_dev)]
    elif p_sphere_direction == 'inwards':
        evec_max = evecs[np.argmax(evals)]
    orientation = np.ravel(evec_max)

    # get a uv sphere that is oriented along the moment tensor axes
    ntheta, nphi = 100, 100
    points = oriented_uv_sphere(ntheta=ntheta, nphi=nphi,
                                orientation=orientation)
    sshape = (ntheta, nphi)

    # get radiation pattern
    disp = farfield_p(ned_mt, points)
    magn = np.sum(disp * points, axis=0)
    magn /= np.max(np.abs(magn))

    # compute colours and displace points along normal
    norm = plt.Normalize(-1., 1.)
    cmap = plt.get_cmap('bwr')
    if p_sphere_direction == 'outwards':
        points *= (1. + np.abs(magn) / 2.)
    elif p_sphere_direction == 'inwards':
        points *= (1. + magn/2.)
    colors = np.array([cmap(norm(val)) for val in magn])
    colors = colors.reshape(ntheta, nphi, 4)

    x = points[0].reshape(sshape)
    y = points[1].reshape(sshape)
    z = points[2].reshape(sshape)

    # plot 3d radiation pattern and beachball
    ax3d.plot_surface(x, y, z, rstride=4, cstride=4, facecolors=colors)
    ax3d.set(xlim=(-1.5, 1.5), ylim=(-1.5, 1.5), zlim=(-1.5, 1.5),
             xticks=[-1, 1], yticks=[-1, 1], zticks=[-1, 1],
             xticklabels=['South', 'North'],
             yticklabels=['West', 'East'],
             zticklabels=['Up', 'Down'],
             title='p-wave farfield')
    ax3d.view_init(elev=-110., azim=0.)


def _plot_s_quiver(ax3d, ned_mt):
    """
    private routine that plots the s_wave farfield into the
    input ax object

    :param ax3d: a matplotlib ax with 3d projection activated
    :param ned_mt: the 6 comp moment tensor in NED orientation
    """
    # precompute even spherical grid and directional cosine array
    points = equalarea_spherical_grid(nlat=14)

    # get radiation pattern
    disp = farfield_s(ned_mt, points)

    # normalized magnitude (positive only):
    magn = np.sqrt(np.sum(disp * disp, axis=0))
    magn /= np.max(np.abs(magn))

    # plot
    # there is a mlab3d bug that quiver vector colors and lengths
    # can only be changed if we plot each arrow independently
    for loc, vec, mag in zip(points.T, disp.T, magn.T):
        norm = plt.Normalize(-1., 1.)
        cmap = plt.get_cmap('Greens')
        color = cmap(norm(mag))
        ax3d.quiver(loc[0], loc[1], loc[2], vec[0], vec[1], vec[2],
                    length=abs(mag)/5., color=color)
    ax3d.set(xlim=(-1.5, 1.5), ylim=(-1.5, 1.5), zlim=(-1.5, 1.5),
             xticks=[-1, 1], yticks=[-1, 1], zticks=[-1, 1],
             xticklabels=['South', 'North'],
             yticklabels=['West', 'East'],
             zticklabels=['Up', 'Down'],
             title='s-wave farfield')
    ax3d.view_init(elev=-110., azim=0.)


def _plot_s_sphere(ax3d, ned_mt):
    """
    private function that plots a s radiation pattern sphere into
    ax3d
    :param ax3d: matplotlib 3d ax object
    :param ned_mt: moment tensor in NED convention
    :param p_sphere_direction: if this is 'inwards', the tension regions
                               of the beachball deform the radiation sphere
                               inwards. If 'outwards' it deforms outwards.
    """
    # generate spherical mesh that is aligned with the moment tensor null
    # axis. MOPAD should use NED coordinate system to avoid internal
    # coordinate transformations
    mtensor = MomentTensor(ned_mt, system='NED')

    # use the most isolated eigenvector as axis of symmetry
    evecs = mtensor.get_eigvecs()
    evals = np.abs(mtensor.get_eigvals())**2
    evals_dev = np.abs(evals-np.mean(evals))
    evec_max = evecs[np.argmax(evals_dev)]
    orientation = np.ravel(evec_max)

    # get a uv sphere that is oriented along the moment tensor axes
    ntheta, nphi = 100, 100
    points = oriented_uv_sphere(ntheta=ntheta, nphi=nphi,
                                orientation=orientation)
    sshape = (ntheta, nphi)

    # get radiation pattern
    disp = farfield_s(ned_mt, points)
    magn = np.sqrt(np.sum(disp * disp, axis=0))
    magn /= np.max(np.abs(magn))

    # compute colours and displace points along normal
    norm = plt.Normalize(0., 1.)
    cmap = plt.get_cmap('Greens')
    points *= (1. + magn/2.)
    colors = np.array([cmap(norm(val)) for val in magn])
    colors = colors.reshape(ntheta, nphi, 4)

    x = points[0].reshape(sshape)
    y = points[1].reshape(sshape)
    z = points[2].reshape(sshape)

    # plot
    ax3d.plot_surface(x, y, z, rstride=4, cstride=4, facecolors=colors)
    ax3d.set(xlim=(-1.5, 1.5), ylim=(-1.5, 1.5), zlim=(-1.5, 1.5),
             xticks=[-1, 1], yticks=[-1, 1], zticks=[-1, 1],
             xticklabels=['South', 'North'],
             yticklabels=['West', 'East'],
             zticklabels=['Up', 'Down'],
             title='p-wave farfield')
    ax3d.view_init(elev=-110., azim=0.)


def _plot_beachball(ax2d, rtp_mt):
    """
    private function that plots a beachball into a 2d matplotlib ax

    :param ax2d: 2d matplotlib ax
    :param rtp_mt: moment tensor in RTP convention
    """
    norm = plt.Normalize(-1., 1.)
    cmap = plt.get_cmap('bwr')
    bball = Beach(rtp_mt, xy=(0, 0), width=50, facecolor=cmap(norm(0.7)),
                  bgcolor=cmap(norm(-0.7)))

    ax2d.add_collection(bball)
    ax2d.set(xlim=(-50, 50), ylim=(-50, 50),
             xticks=(-40, 40), yticks=(-40, 40),
             xticklabels=('West', 'East'),
             yticklabels=('South', 'North'),
             title='lower hemisphere stereographical projection')


def _plot_mayavi(ned_mt):
    # use mayavi if possible.
    try:
        from mayavi import mlab
    except ImportError as err:
        print(err)
        print("mayavi import error. Use kind='vtk' for vtk file "
              "output of the radiation pattern that can be used "
              "by external software like paraview")

    # get mopad moment tensor
    mopad_mt = MomentTensor(ned_mt, system='NED')
    bb = BeachBall(mopad_mt, npoints=200)
    bb._setup_BB(unit_circle=False)

    # extract the coordinates of the nodal lines
    neg_nodalline = bb._nodalline_negative
    pos_nodalline = bb._nodalline_positive

    # plot radiation pattern and nodal lines
    points = spherical_grid(nlat=nlat)
    dispp = farfield_p(ned_mt, points)
    disps = farfield_s(ned_mt, points)

    # get vector lengths
    normp = np.sum(dispp * points, axis=0)
    normp /= np.max(np.abs(magn))

    norms = np.sqrt(np.sum(disps * disps, axis=0))
    norms /= np.max(np.abs(magn))

    # p wave radiation pattern
    mlab.figure(size=(800, 800), bgcolor=(0, 0, 0))
    pts1 = mlab.quiver3d(points[0], points[1], points[2],
                         dispp[0], dispp[1], dispp[2],
                         scalars=normp, vmin=-rangep, vmax=rangep)
    pts1.glyph.color_mode = 'color_by_scalar'
    mlab.plot3d(*neg_nodalline, color=(0, 0.5, 0), tube_radius=0.01)
    mlab.plot3d(*pos_nodalline, color=(0, 0.5, 0), tube_radius=0.01)
    plot_sphere(0.7)

    # s wave radiation pattern
    mlab.figure(size=(800, 800), bgcolor=(0, 0, 0))
    pts2 = mlab.quiver3d(points[0], points[1], points[2],
                         disps[0], disps[1], disps[2], scalars=norms,
                         vmin=-ranges, vmax=ranges)
    pts2.glyph.color_mode = 'color_by_scalar'
    mlab.plot3d(*neg_nodalline, color=(0, 0.5, 0), tube_radius=0.01)
    mlab.plot3d(*pos_nodalline, color=(0, 0.5, 0), tube_radius=0.01)
    plot_sphere(0.7)

    mlab.show()


def _write_vtk_files(ned_mt, fname_rpattern='rpattern.vtk',
                     fname_beachlines='beachlines.vtk'):
    # output a vtkfile that can for exampled be displayed by paraview
    mtensor = MomentTensor(ned_mt, system='NED')
    bb = BeachBall(mtensor, npoints=200)
    bb._setup_BB(unit_circle=False)

    # extract the coordinates of the nodal lines
    neg_nodalline = bb._nodalline_negative
    pos_nodalline = bb._nodalline_positive

    # plot radiation pattern and nodal lines
    points = spherical_grid()
    ndim, npoints = points.shape
    dispp = farfield_p(ned_mt, points)
    disps = farfield_s(ned_mt, points)

    # write vector field
    with open(fname_rpattern, 'w') as vtk_file:
        vtk_header = '# vtk DataFile Version 2.0\n' + \
                     'radiation pattern vector field\n' + \
                     'ASCII\n' + \
                     'DATASET UNSTRUCTURED_GRID\n' + \
                     'POINTS {:d} float\n'.format(npoints)

        vtk_file.write(vtk_header)
        # write point locations
        for x, y, z in np.transpose(points):
            vtk_file.write('{:.3e} {:.3e} {:.3e}\n'.format(x, y, z))
        # write vector field
        vtk_file.write('POINT_DATA {:d}\n'.format(npoints))
        vtk_file.write('VECTORS s_radiation float\n')
        for x, y, z in np.transpose(disps):
            vtk_file.write('{:.3e} {:.3e} {:.3e}\n'.format(x, y, z))
        vtk_file.write('VECTORS p_radiation float\n'.format(npoints))
        for x, y, z in np.transpose(dispp):
            vtk_file.write('{:.3e} {:.3e} {:.3e}\n'.format(x, y, z))

    # write nodal lines
    with open(fname_beachlines, 'w') as vtk_file:
        npts_neg = neg_nodalline.shape[1]
        npts_pos = pos_nodalline.shape[1]
        npts_tot = npts_neg+npts_pos
        vtk_header = '# vtk DataFile Version 2.0\n' + \
                     'beachball nodal lines\n' + \
                     'ASCII\n' + \
                     'DATASET UNSTRUCTURED_GRID\n' + \
                     'POINTS {:d} float\n'.format(npts_tot)

        vtk_file.write(vtk_header)
        # write point locations
        for x, y, z in np.transpose(neg_nodalline):
            vtk_file.write('{:.3e} {:.3e} {:.3e}\n'.format(x, y, z))
        for x, y, z in np.transpose(pos_nodalline):
            vtk_file.write('{:.3e} {:.3e} {:.3e}\n'.format(x, y, z))

        # write line segments
        vtk_file.write('\nCELLS 2 {:d}\n'.format(npts_tot + 4))

        ipoints = list(range(0, npts_neg)) + [0]
        vtk_file.write('{:d} '.format(npts_neg+1))
        for ipoint in ipoints:
            if ipoint % 30 == 29:
                vtk_file.write('\n')
            vtk_file.write('{:d} '.format(ipoint))
        vtk_file.write('\n')

        ipoints = list(range(0, npts_pos)) + [0]
        vtk_file.write('{:d} '.format(npts_pos + 1))
        for ipoint in ipoints:
            if ipoint % 30 == 29:
                vtk_file.write('\n')
            vtk_file.write('{:d} '.format(ipoint + npts_neg))
        vtk_file.write('\n')

        # cell types. 4 means cell type is a poly_line
        vtk_file.write('\nCELL_TYPES 2\n')
        vtk_file.write('4\n4')


# ===== SUPPORT FUNCTIONS FOR SPHERICAL MESHES ETC STARTING HERE:
def oriented_uv_sphere(ntheta=100, nphi=100, orientation=[0., 0., 1.]):
    """
    returns a uv sphere (equidistant lat/lon grid) with its north-pole
    rotated to the input axis. It returns the spherical grid points
    that can be used to generate a QuadMesh on the sphere for surface
    plotting.

    :param nlat: number of latitudinal grid points (default = 100)
    :param nphi: number of longitudinal grid points (default = 100)
    :param orientation: axis of the north-pole of the sphere
                        (default = [0, 0, 1])
    """
    # make rotation matrix (after numpy mailing list)
    zaxis = np.array([0., 0., 1.])
    raxis = np.cross(orientation, zaxis)  # rotate z axis to null
    raxis_norm = np.linalg.norm(raxis)
    if raxis_norm < 1e-10:  # check for zero or 180 degree rotation
        rotmtx = np.eye(3, dtype=np.float64)
    else:
        raxis /= raxis_norm

        # angle between z and null
        angle = np.arccos(np.dot(zaxis, orientation))

        eye = np.eye(3, dtype=np.float64)
        raxis2 = np.outer(raxis, raxis)
        skew = np.array([[0, raxis[2], -raxis[1]],
                         [-raxis[2], 0, raxis[0]],
                         [raxis[1], -raxis[0], 0]])

        rotmtx = (raxis2 + np.cos(angle) * (eye - raxis2) +
                  np.sin(angle) * skew)

    # make uv sphere that is aligned with z-axis
    ntheta, nphi = 100, 100
    u = np.linspace(0, 2 * np.pi, nphi)
    v = np.linspace(0, np.pi, ntheta)

    x = np.outer(np.cos(u), np.sin(v))
    y = np.outer(np.sin(u), np.sin(v))
    z = np.outer(np.ones(np.size(u)), np.cos(v))

    # ravel point array and rotate them to the null axis
    points = np.vstack((x.flatten(), y.flatten(), z.flatten()))
    points = np.dot(rotmtx, points)
    return points


def equalarea_spherical_grid(nlat=30):
    """
    generates a simple spherical equalarea grid that adjust the
    number of longitude samples to the longitude. This grid is useful
    to plot vectors on the sphere but not surfaces.

    :param nlat: number of nodes in lat direction. The number of
                 nodes in lon direction is 2*nlat+1 at the equator
    """

    ndim = 3
    colats = np.linspace(0., np.pi, nlat)
    norms = np.sin(colats)
    nlons = (2*nlat * norms + 1).astype(int)  # scale number of point with lat

    # make colat/lon grid
    colatgrid, longrid = [], []
    for ilat in range(nlat):
        nlon = nlons[ilat]
        dlon = 2.*np.pi / nlon
        lons = np.linspace(0.+dlon/2., 2.*np.pi-dlon/2., nlon)
        for ilon in range(nlon):
            colatgrid.append(colats[ilat])
            longrid.append(lons[ilon])
    npoints = len(longrid)

    # get cartesian coordinates of spherical grid
    points = np.empty((ndim, npoints))
    points[0] = np.sin(colatgrid) * np.cos(longrid)
    points[1] = np.sin(colatgrid) * np.sin(longrid)
    points[2] = np.cos(colatgrid)

    return points


def farfield_p(mt, points):
    """
    Returns the P farfield radiation pattern
    based on Aki & Richards Eq 4.29

    :param mt: Focal mechanism NM x 6 (Mxx, Myy, Mzz, Mxy, Mxz, Myz - the
               six independent components of the moment tensor)

    :param points: 3D vector array with shape [3,npts] (x,y,z) or [2,npts]
                   (theta,phi) The normalized displacement of the moment
                   tensor source is computed at these points.

    :return: 3D vector array with shape [3,npts] that contains the
             displacement vector for each grid point
    """
    ndim, npoints = points.shape
    if ndim == 2:
        # points are given as theta,phi
        points = np.empty((3, npoints))
        points[0] = np.sin(points[0]) * np.cos(points[1])
        points[1] = np.sin(points[0]) * np.sin(points[1])
        points[2] = np.cos(points[0])
    elif ndim == 3:
        # points are given as x,y,z, (same system as the moment tensor)
        pass
    else:
        raise ValueError('points should have shape 2 x npoints or 3 x npoints')
    Mpq = fullmt(mt)

    # precompute directional cosine array
    dists = np.sqrt(points[0] * points[0] + points[1] * points[1] +
                    points[2] * points[2])
    gammas = points / dists

    # initialize displacement array
    disp = np.empty((ndim, npoints))

    # loop through points
    for ipoint in range(npoints):
        # loop through displacement component [n index]
        gamma = gammas[:, ipoint]
        gammapq = np.outer(gamma, gamma)
        gammatimesmt = gammapq * Mpq
        for n in range(ndim):
            disp[n, ipoint] = gamma[n] * np.sum(gammatimesmt.flatten())

    return disp


def farfield_s(mt, points):
    """
    Returns the S farfield radiation pattern
    based on Aki & Richards Eq 4.29

    :param mt: Focal mechanism NM x 6 (Mxx, Myy, Mzz, Mxy, Mxz, Myz - the
               six independent components of the moment tensor)

    :param points: 3D vector array with shape [3,npts] (x,y,z) or [2,npts]
                   (theta,phi) The normalized displacement of the moment
                   tensor source is computed at these points.

    :return: 3D vector array with shape [3,npts] that contains the
             displacement vector for each grid point
    """
    ndim, npoints = points.shape
    if ndim == 2:
        # points are given as theta,phi
        points = np.empty((3, npoints))
        points[0] = np.sin(points[0]) * np.cos(points[1])
        points[1] = np.sin(points[0]) * np.sin(points[1])
        points[2] = np.cos(points[0])
    elif ndim == 3:
        # points are given as x,y,z, (same system as the moment tensor)
        pass
    else:
        raise ValueError('points should have shape 2 x npoints or 3 x npoints')
    Mpq = fullmt(mt)

    # precompute directional cosine array
    dists = np.sqrt(points[0] * points[0] + points[1] * points[1] +
                    points[2] * points[2])
    gammas = points / dists

    # initialize displacement array
    disp = np.empty((ndim, npoints))

    # loop through points
    for ipoint in range(npoints):
        # loop through displacement component [n index]
        gamma = gammas[:, ipoint]
        Mp = np.dot(Mpq, gamma)
        for n in range(ndim):
            psum = 0.0
            for p in range(ndim):
                deltanp = int(n == p)
                psum += (gamma[n] * gamma[p] - deltanp) * Mp[p]
            disp[n, ipoint] = psum

    return disp


def fullmt(mt):
    """takes 6 comp moment tensor and returns full 3x3 moment tensor"""
    mt_full = np.array(([[mt[0], mt[3], mt[4]],
                         [mt[3], mt[1], mt[5]],
                         [mt[4], mt[5], mt[2]]]))
    return mt_full


if __name__ == '__main__':
    import doctest
    doctest.testmod(exclude_empty=True)
