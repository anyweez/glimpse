import matplotlib.pyplot as plt
import enum, random, math, colour, collections, pprint

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

        # What tectonic plate is this cell a part of?
        self.plate_id = None

class WorldRegion(object):
    def __init__(self, cells, vor):
        self.cellmap = {}
        for cell in cells:
            self.cellmap[cell.region_idx] = cell
        
        self.cells = cells
        self.vor = vor

        # 'Neighbor map': Map the idx of the cell in self.cells to the idx of all neighbors
        self.nmap = {}

        self._build_graph()

    def _add_edge(self, src_idx, dest_idx):
        if src_idx not in self.nmap:
            self.nmap[src_idx] = set()

        self.nmap[src_idx].add(dest_idx)

    def _build_graph(self):
        for source in self.cells:
            for dest in self.cells:
                if source.region_idx != dest.region_idx:
                    source_region = set( self.vor.regions[source.region_idx] )
                    dest_region = set( self.vor.regions[dest.region_idx] )

                    if -1 in source_region:
                        source_region.remove(-1)
                    if -1 in dest_region:
                        dest_region.remove(-1)

                    if not source_region.isdisjoint(dest_region):
                        self._add_edge(source.region_idx, dest.region_idx)
                        self._add_edge(dest.region_idx, source.region_idx)

    def neighbors(self, region_idx, dist=1):
        # If we're looking for immediate neighbors, jump straight to the nmap where this is explicitly
        # known. This also allows us to use neighbors(dist=1) for calculations when dist != 1
        if dist == 1:
            return list( map(lambda idx: self.cellmap[idx], self.nmap[region_idx]) )

        by_distance = []
        added = set([self.cellmap[region_idx],])

        for curr_dist in range(dist):
            if curr_dist == 0:
                by_distance.append( self.neighbors(region_idx, dist=1) )

                for c in by_distance[curr_dist]:
                    added.add(c)

            else:
                next_round = []
                for parent in by_distance[curr_dist - 1]:
                    for cell in self.neighbors(parent.region_idx, dist=1):
                        next_round.append(cell)

                next_round = list( set(next_round) )
                # De-duplicate and flatten a list of the neighbors of all cells
                by_distance.append( [c for c in next_round if c not in added] )

                for c in by_distance[curr_dist]:
                    added.add(c)

        return by_distance[dist - 1]

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

        # Establish tectonic plates. Once this is done we'll create a separate region for each.
        wr = WorldRegion(self.cells, self.vor)
        self._form_plates(wr)

        for plate_id in set([c.plate_id for c in self.cells]):
            cells = [c for c in self.cells if c.plate_id == plate_id]

            region = WorldRegion(cells, self.vor)

            self._add_ocean(region)
            self._terrainify(region)
        # Run world generation functions on each plate independently.

        # self._add_ocean()
        # self._terrainify()
        # self._add_elevation()


    def _form_plates(self, region):
        plate_centers = random.choices(region.cells, k=3)

        for idx, center in enumerate(plate_centers):
            center.plate_id = idx

        # Function to check whether a cell still needs to have a plate assigned. Boundary cells
        # are excluded.
        still_available = lambda cell: cell.plate_id is None

        remaining = sum( [1 for cell in region.cells if still_available(cell)] )

        # Add all cells to a plate
        while remaining > 0:
            # For each plate, expand out from the center
            for center in plate_centers:
                dist = 1
                avail = [c for c in region.neighbors(center.region_idx, dist) if still_available(c)]

                while len(avail) == 0:
                    dist += 1
                    avail = [c for c in region.neighbors(center.region_idx, dist) if still_available(c)]

                mark = random.choice(avail)
                mark.plate_id = center.plate_id

                # Count remaining cells to be marked; break the loop if we're done.
                remaining = sum( [1 for cell in region.cells if still_available(cell)] )

                if remaining == 0:
                    break

            print(remaining)
            # There's a chance to add a new plate each iteration. New plates
            # can only exist in unmarked cells.
            # if random.random() < 0.05:
            #     avail = [c for c in self.cells if c.plate_id is None]

            #     if len(avail) > 0:
            #         cell = random.choice(avail)
                    
            #         cell.plate_id = len(plate_centers)
            #         plate_centers.append(cell)

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
        # for source in self.cells:
        #     for dest in self.cells:
        #         if source.region_idx != dest.region_idx:
        #             source_region = set( self.vor.regions[source.region_idx] )
        #             dest_region = set( self.vor.regions[dest.region_idx] )

        #             if -1 in source_region:
        #                 source_region.remove(-1)
        #             if -1 in dest_region:
        #                 dest_region.remove(-1)

        #             if not source_region.isdisjoint(dest_region):
        #                 source.add_edge(dest)
        #                 dest.add_edge(source)

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
    def _add_ocean(self, region):
        for cell in region.cells:
            if cell.is_boundary:
                cell.type = Cell.Type.WATER

                # Traverse the cell graph twice randomly and turn each cell into
                # water. Two anecdotally gives decent results when PointCount = 250,
                # but the number should probably be a function of the number of cells.
                neighbor = cell

                iterations = round( math.sqrt(math.sqrt(len(region.cells))) )

                for _ in range(iterations):
                    neighbor = random.choice(region.neighbors(neighbor.region_idx))

                    if (random.random() < 0.8):
                        neighbor.type = Cell.Type.WATER

    def _terrainify(self, region):
        for cell in region.cells:
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

    def render(self, cell_labels=False, color_boundaries=False, cell_elevation=False, tectonics=False, show_graph=False):
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

        if tectonics:
            num_plates = len( set([c.plate_id for c in self.cells]) )

            print('num_plates=%d' % (num_plates))
            random_color = lambda: colour.rgb2hex( (random.random(), random.random(), random.random()) )
            colors = [ random_color() for plate in range(num_plates) ]
            
            for cell in self.cells:
                # self.paint_cell(cell.region_idx, colors[cell.plate_id])

                plt.text(cell.location[0], cell.location[1], cell.plate_id, fontsize=8)

        if show_graph:
            for node in self.cells[0:100]:
                for neighbor in node.neighbor_to:
                    x = (node.location[0], neighbor.location[0])
                    y = (node.location[1], neighbor.location[1])

                    plt.plot(x, y, linestyle='dashed', color='red', linewidth=1)

                plt.plot(node.location[0], node.location[1], 'bo')

        plt.title('Rendered world')
        plt.show()