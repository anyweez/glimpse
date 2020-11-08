import matplotlib.pyplot as plt
import enum, random, math, colour, collections

from scipy.spatial import voronoi_plot_2d

'''
Cells represent sections of a World that have certain characteristics like terrain types
and elevation. Cells are spatially defined by polygons, which are currently equivalent 
to regions of a Voronoi diagram.
'''
class Cell(object):
    Type = enum.Enum('CellType', 'NONE WATER LAND')

    def __init__(self, region_idx, location):
        self.region_idx = region_idx
        self.location = location
        self.neighbor_to = []

        # Does this cell exist on the border of the world?
        self.is_boundary = False

        self.type = Cell.Type.NONE
        self.elevation = 0

    def add_edge(self, cell):
        # Can't add existing neighbors, and can't add self
        if cell not in self.neighbor_to and cell.region_idx is not self.region_idx:
            self.neighbor_to.append(cell)

'''
Worlds contain a series of Cells, and store the Voronoi diagram used to define the region
and position of each. Worlds also include much of the logic for world generation and any 
configuration variables needed to do so.
'''
class World(object):
    def __init__(self, vor):
        self.cells = []
        self.vor = vor

        self._form_cells()
        self._label_boundary()
        self._add_ocean()
        self._terrainify()
        self._add_elevation()

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

    '''
    A boundary cell is a cell that extends beyond the edge of the world.
    '''
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

    '''
    All cells at the edge of the map are water. We then traverse the graph from each of the boundary cells
    and mark cells along the path as water (% chance).
    '''
    def _add_ocean(self):
        for cell in self.cells:
            if cell.is_boundary:
                cell.type = Cell.Type.WATER

                # Traverse the cell graph twice randomly and turn each cell into
                # water. Two anecdotally gives decent results when PointCount = 250,
                # but the number should probably be a function of the number of cells.
                neighbor = cell

                iterations = round( math.sqrt(math.sqrt(len(self.cells))) )

                for _ in range(iterations):
                    neighbor = random.choice(neighbor.neighbor_to)

                    if (random.random() < 0.8):
                        neighbor.type = Cell.Type.WATER

    def _terrainify(self):
        for cell in self.cells:
            if not cell.type == Cell.Type.WATER:
                cell.type = Cell.Type.LAND

    def _add_elevation(self):
        max_elevation = 0

        for cell in self.cells:
            cell.elevation = self.__distance_from_water(cell)

            if cell.elevation > max_elevation:
                max_elevation = cell.elevation

        # A percentage of land cells should take on the height of a random
        # neighbor cell.
        for cell in self.cells:
            if cell.type != Cell.Type.WATER and random.random() < 0.1:
                # Get all land cells
                eligible_neighbors = list( filter(lambda c: c.type != Cell.Type.WATER, cell.neighbor_to) )

                if len(eligible_neighbors) > 0:
                    neighbor = random.choice(eligible_neighbors)
                    cell.elevation = neighbor.elevation

    '''
    Find the shortest distance from the specified cell to water. Distance is defined
    as the lowest number of edges in the world graph that need to be traversed to 
    reach a water cell.
    '''
    def __distance_from_water(self, cell):
        queue = collections.deque()
        queue.append( (cell, 0) )

        # Keep track of which cells have already been searched.
        added = set()
        added.add(cell.region_idx)

        while len(queue) > 0:
            (cell, dist) = queue.popleft()

            if cell.type == Cell.Type.WATER:
                return dist

            for next_cell in cell.neighbor_to:
                if next_cell.region_idx not in added:
                    queue.append( (next_cell, dist + 1) ) 
                    added.add( next_cell.region_idx )

    '''
    Get Cell by cell_id/region_id.
    '''
    def get_cell_by_id(self, cell_id):
        for cell in self.cells:
            if cell.region_idx == cell_id:
                return cell
        
        return None
    
    '''
    Get the polygon that defines the region for the specified cell_id/region_id.
    Returns a list of 2D points, or an empty list if the region isn't defined within
    the Voronoi diagram; see more about when this happens here:

    https://docs.scipy.org/doc/scipy/reference/generated/scipy.spatial.Voronoi.html
    '''
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

    def render(self, cell_labels=False, color_boundaries=False, cell_elevation=False):
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

        if cell_elevation:
            color_sealevel = colour.Color('green')
            color_peak = colour.Color('white')

            num_colors = max(map(lambda c: c.elevation, self.cells))
            gradient = list( color_sealevel.range_to(color_peak, num_colors) )

            for cell in self.cells:
                # if cell.type == Cell.Type.WATER:
                #     self.paint_cell(cell.region_idx, '#0485d1')
                if cell.type == Cell.Type.LAND:
                    self.paint_cell(cell.region_idx, gradient[cell.elevation - 1].hex)

        plt.title('Voronoi polygons')
        plt.show()