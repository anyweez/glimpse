import matplotlib.pyplot as plt
import enum, random

from scipy.spatial import voronoi_plot_2d

class Cell(object):
    Type = enum.Enum('CellType', 'NONE WATER LAND')

    def __init__(self, region_idx, location):
        self.region_idx = region_idx
        self.location = location
        self.neighbor_to = []

        # Does this cell exist on the border of the world?
        self.is_boundary = False

        self.type = Cell.Type.NONE

    def add_edge(self, cell):
        # Can't add existing neighbors, and can't add self
        if cell not in self.neighbor_to and cell.region_idx is not self.region_idx:
            self.neighbor_to.append(cell)

class World(object):
    def __init__(self, vor):
        self.cells = []
        self.vor = vor

        self._form_cells()
        self._label_boundary()
        self._add_water()
        self._terrainify()

    '''
    Generate a series of world cells based on the specified Voronoi diagram. A directed
    graph is also calculated based on which cells are touching each other.
    '''
    def _form_cells(self):
        # Create all cells
        for point_idx, region_idx in enumerate(self.vor.point_region):
            cell = Cell(region_idx, self.vor.points[point_idx])

            self.cells.append(cell)
        
        # Find neighbors; if cells share any vertices then they're neighbors
        for source in self.cells:
            for dest in self.cells:
                source_region = set( self.vor.regions[source.region_idx] )
                dest_region = set( self.vor.regions[dest.region_idx] )

                if -1 in source_region:
                    source_region.remove(-1)
                if -1 in dest_region:
                    dest_region.remove(-1)

                if not source_region.isdisjoint(dest_region):
                    source.add_edge(dest)
                    dest.add_edge(source)

    def _label_boundary(self):
        for cell in self.cells:
            region = self.vor.regions[cell.region_idx]

            if -1 in region:
                cell.is_boundary = True 
            else:
                coords = self.get_region_for_cell(cell.region_idx)

                for x, y in coords:
                    if x > 1.0 or x < 0.0:
                        cell.is_boundary = True
                    if y > 1.0 or y < 0.0:
                        cell.is_boundary = True

    def _add_water(self):
        for cell in self.cells:
            if cell.is_boundary:
                cell.type = Cell.Type.WATER

                # Traverse the cell graph twice randomly and turn each cell into
                # water. Two anecdotally gives decent results when PointCount = 250,
                # but the number should probably be a function of the number of cells.
                neighbor = cell
                for _ in range(2):
                    neighbor = random.choice(neighbor.neighbor_to)
                    neighbor.type = Cell.Type.WATER

                    neighbor = random.choice(neighbor.neighbor_to)

    def _terrainify(self):
        for cell in self.cells:
            if not cell.type == Cell.Type.WATER:
                cell.type = Cell.Type.LAND

    def get_cell_by_id(self, cell_id):
        for cell in self.cells:
            if cell.region_idx == cell_id:
                return cell
        
        return None
    
    def get_region_for_cell(self, cell_id):
        cell = self.get_cell_by_id(cell_id)

        if -1 in self.vor.regions[cell.region_idx]:
            return []

        return list( map(lambda r: self.vor.vertices[r], self.vor.regions[cell.region_idx]) )

    '''
    Fill the specified cell's region with the specified `color`. Supported colors are documented here:
        https://matplotlib.org/3.1.1/api/_as_gen/matplotlib.pyplot.fill.html
    '''
    def paint_cell(self, cell_id, color):
        region = self.get_region_for_cell(cell_id)

        x = list( map(lambda p: p[0], region) )
        y = list( map(lambda p: p[1], region) )
        plt.fill(x, y, color)

    def render(self, cell_labels=False, color_boundaries=False):
        voronoi_plot_2d(self.vor, show_vertices=False, show_points=False, line_width=0)
        axes = plt.gca()

        axes.set_xlim([0, 1])
        axes.set_ylim([0, 1])

        if cell_labels:
            for cell in self.cells:
                plt.text(cell.location[0], cell.location[1], cell.region_idx, fontsize=8)

        if color_boundaries:
            for cell in self.cells:
                if cell.type == Cell.Type.WATER:
                    self.paint_cell(cell.region_idx, '#0485d1')
                if cell.type == Cell.Type.LAND:
                    self.paint_cell(cell.region_idx, 'g')


        plt.title('Voronoi polygons')
        plt.show()