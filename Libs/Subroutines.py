import pickle
import numpy
from fluidfoam import readmesh, readvector, readscalar
from scipy.interpolate import LinearNDInterpolator
from scipy.interpolate import RegularGridInterpolator
from scipy.interpolate import interpn
from scipy.interpolate import RBFInterpolator

class MESH:
      """
      Contains information of the mesh classes, which contains grid 3D points, velocity, U, and pressure, p, fields.
      """
      def __init__(self, Xg, Yg, Zg, xg, yg, zg, Pg, Ux, Uy, Uz):
           
           self.X = Xg
           self.Y = Yg
           self.Z = Zg
           self.x = xg
           self.y = yg
           self.z = zg
           self.Ux = Ux
           self.Uy = Uy
           self.Uz = Uz
           self.P = Pg



def loadMesh(filename):
    """ Read the mesh file that was previously stored as a binary file"""
    meshfile = open('./Data/'+filename, 'rb')   
    mesh = pickle.load(meshfile)
    meshfile.close()

    return mesh



def preProcess(timename, filename, **kwargs):
      """ Routine that reads OpenFOAM solution and creates a nice, structured, backup of numpy arrays """
      
      # folder = 'D:/OpenFOAM_Backups/Actuator_Surface_Project_2023/' + filename

      folder = './OFBackups/' + filename
      
      if kwargs['structured']:
            Xg, Yg, Zg = readmesh(folder, structured=True)
            velocity = readvector(folder, timename, 'U', structured=True)
            Pg = readscalar(folder, timename, 'p', structured=True)
            Ux, Uy, Uz = velocity[0,:,:,:], velocity[1,:,:,:], velocity[2,:,:,:]
      else :
            ## Access OpenFOAM data and obtain cell-centred data:
            x, y, z  = readmesh(folder, structured=False)
            velocity = readvector(folder, timename, 'U', structured=False)
            pressure =  readscalar(folder, timename, 'p', structured=False)

            ## Convert the (point) cell-centred data onto 3D-gridded data
            Xg, Yg, Zg, xg, yg, zg, Pg, Ux, Uy, Uz = interpolateToStructuredMesh(x, y, z, pressure, velocity, **kwargs)

      # database
      mesh = MESH(Xg, Yg, Zg, xg, yg, zg, Pg, Ux, Uy, Uz)
      
      # Its important to use binary mode
      meshfile = open('./Data/'+filename, 'ab')
      
      # source, destination
      pickle.dump(mesh, meshfile)                   
      meshfile.close()




def interpolateToStructuredMesh(x, y, z, pressure, velocity, **kwargs):
      """ Takes the bounds and sizes of the structured grid and returns structured data"""

      points = numpy.column_stack((x.flatten(), y.flatten(), z.flatten()))
      
      xmin, xmax, ymin, ymax, zmin, zmax = kwargs['domain_bounds']
      dx = kwargs['grid_spacing']

      print("Computing arrays")

      xg = numpy.arange(xmin, xmax, dx, dtype=float)
      yg = numpy.arange(ymin, ymax, dx, dtype=float)
      zg = numpy.arange(zmin, zmax, dx, dtype=float)
      Xg, Yg, Zg = numpy.meshgrid(xg, yg, zg, indexing='ij')

      ux_flat = velocity[0,:].flatten()
      uy_flat = velocity[1,:].flatten()
      uz_flat = velocity[2,:].flatten()
      XYZflat = numpy.column_stack((Xg.flatten(), Yg.flatten(), Zg.flatten()))

      print("Interpolating Ux")

      interfunc = RBFInterpolator(points, ux_flat, neighbors=5, kernel='linear', epsilon=20)
      Ux = interfunc(XYZflat)
      Ux = Ux.reshape(Xg.shape)

      print("Interpolating Uy")

      interfunc = RBFInterpolator(points, uy_flat, neighbors=5, kernel='linear', epsilon=20)
      Uy = interfunc(XYZflat)
      Uy = Uy.reshape(Xg.shape)

      print("Interpolating Uz")

      interfunc = RBFInterpolator(points, uz_flat, neighbors=5, kernel='linear', epsilon=20)
      Uz = interfunc(XYZflat)
      Uz = Uz.reshape(Xg.shape)

      print("Interpolating p")

      interfunc = RBFInterpolator(points, pressure, neighbors=5, kernel='linear', epsilon=20)
      Pg = interfunc(XYZflat)
      Pg = Pg.reshape(Xg.shape)

      return Xg, Yg, Zg, xg, yg, zg, Pg, Ux, Uy, Uz




# ===== Useful functions:




def findNearest(myarray, values):
    
      "Element in nd array `a` closest to the scalar value `a0`"
      values = numpy.array(values)
      myarray = numpy.array(myarray)

      idx = numpy.zeros(values.shape, dtype=int)

      for c, value in enumerate(values):
            idx[c] = int(numpy.abs(myarray - value).argmin())

      return idx


def findInterval(myarray, vmin, vmax):
    
      "Element in nd array `a` closest to the scalar value `a0`"

      indexes = numpy.where((myarray>=vmin) &  (myarray<=vmax))[0]

      return indexes[0], indexes[-1]