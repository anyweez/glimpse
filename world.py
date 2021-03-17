import enum, random, string, numpy
import errors

from entity import Entity

class Cell(object):
    '''
    Cells represent sections of a World that have certain characteristics like terrain types
    and elevation. Cells are spatially defined by polygons, which are currently equivalent 
    to regions of a Voronoi diagram.
    '''
    Type = enum.Enum('CellType', 'NONE WATER LAND FIRE')

class AbstractCellGroup(object):
    def __init__(self, cell_idxs, vor, graph):
        self.__cell_idxs = cell_idxs
        self.graph = graph

        self.vertex_count = {}
        self.available_cells = set( cell_idxs )

    def cell_idxs(self):
        return self.__cell_idxs

    def contains(self, region_idx):
        return region_idx in self.available_cells

    def get_cellcount(self):
        return len( list(self.cell_idxs()) )

class World(AbstractCellGroup):
    '''
    A World is a container for most of the procedural state related to a generated world.
    Worlds are composed of three different types of state, all of which can be modified by plugins.

    1) Cell properties, i.e. elevation and cell type. A cell property is a single value per cell and is
    directly related to the cell.
    2) World params, i.e. water level. These are 'global' values generated over the course of the
    simulation.
    3) Entities, i.e. cities and rivers.

    Worlds do NOT represent the spatial characteristics of cells (VoronoiDiagrams do this) or the
    relationships between cells (Graphs do this).
    '''

    StandardDensityCellCount = 3500

    def __init__(self, cells, vor, graph):
        super().__init__(cells, vor, graph)

        self.continents = []
        self.id = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))

        self.__worldparams = {}
        self.__entities = []

    def add_cell_property(self, name, arr):
        setattr(self, 'cp_%s' % (name,), arr)

    def new_cp_array(self, dtype, default_value=None):
        if isinstance(default_value, list):
            return numpy.array(default_value, dtype=dtype)

        if default_value is not None:
            return numpy.full(self.get_cellcount(), default_value, dtype=dtype)

        return numpy.array(self.get_cellcount(), dtype=dtype)

    def set_param(self, name, value):
        self.__worldparams[name] = value
    
    def get_param(self, name):
        return self.__worldparams[name]
    
    def list_params(self):
        return list( self.__worldparams.keys() )

    def std_density(self, num):
        '''
        Returns a number that's adjusted for the number of cells in the world. The number
        is scaled up from 'standard density' (n=3500).
        '''
        ratio = len( self.cell_idxs() ) / World.StandardDensityCellCount

        return num * ratio

    def add_entity(self, entity):
        # if isinstance(entity, Entity):
        self.__entities.append(entity)
        # else:
        #     raise Exception( 'Trying to add non-Entity: %s' % (type(entity),) )

    def entities(self):
        return self.__entities

    def cell_pct(self, cell_count):
        '''
        Return the percentage of cells in the world that `cell_count` corresponds
        to. For example, if `cell_count` = 10 in a world containing 200 cells
        then a value of (10 / 200) = 0.05 will be returned.
        '''
        return cell_count / len( self.cell_idxs() )
    
    def cell_abs(self, cell_pct):
        return round( len(self.cell_idxs()) * cell_pct )