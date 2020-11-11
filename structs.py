import matplotlib.pyplot as plt
import enum, random, math, colour, collections, numpy, functools, string

from scipy.spatial import voronoi_plot_2d
from PIL import Image
from noise import snoise2

class InvalidCellError(Exception):
    pass

class Cell(object):
    '''
    Cells represent sections of a World that have certain characteristics like terrain types
    and elevation. Cells are spatially defined by polygons, which are currently equivalent 
    to regions of a Voronoi diagram.
    '''
    Type = enum.Enum('CellType', 'NONE WATER LAND FIRE')

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
        self.cells = cells
        self.vor = vor

        # 'Neighbor map': Map the idx of the cell in self.cells to the idx of all neighbors
        self.nmap = {}

        self.cellmap = {}

        for cell in cells:
            self.cellmap[cell.region_idx] = cell
            self.nmap[cell.region_idx] = set()

        # Count the number of appearances of each vertex. Regions that contain the sole reference to
        # a vertex are on the 'border' of the graph.
        self.vertex_count = {}

        self._build_graph()
        self._count_vertices()

    def _add_edge(self, src_idx, dest_idx):
        self.nmap[src_idx].add(dest_idx)

    '''
    Build a graph connecting notes that share vertices. This graph is built when the WorldRegion
    is initialized and only contains edges between cells included in the region.
    '''
    def _build_graph(self):
        # map vertex_id => region_idx that touch vertex
        regions_by_vertex = {}

        # List all regions that share each vertex
        for cell in self.cells:
            for vertex in self.vor.regions[cell.region_idx]:
                if vertex not in regions_by_vertex:
                    regions_by_vertex[vertex] = []

                regions_by_vertex[vertex].append(cell.region_idx)

        # Run through list of vertices and build edges between all connected regions
        for (vertex, region_idxs) in regions_by_vertex.items():
            for source in region_idxs:
                for dest in region_idxs:
                    if source != dest:
                        self._add_edge(source, dest)
                        self._add_edge(dest, source)

    '''
    Counts and caches the number of times each vertex is associated with a cell in the region.
    If a vertex only appears once, then the cell the vertex is associated with is considered a 
    'border' cell -- see WorldRegion.is_border() for more.
    '''
    def _count_vertices(self):
        for cell in self.cells:
            indeces = set( self.vor.regions[cell.region_idx] )

            for idx in indeces:
                if idx not in self.vertex_count:
                    self.vertex_count[idx] = 0
                
                self.vertex_count[idx] += 1

    def neighbors(self, region_idx, dist=1):
        if region_idx not in self.cellmap:
            raise InvalidCellError('Cell does not exist in region')

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
                next_round = set()
                for parent in by_distance[curr_dist - 1]:
                    for cell in self.neighbors(parent.region_idx, dist=1):
                        next_round.add(cell)

                next_round = list( next_round )
                # De-duplicate and flatten a list of the neighbors of all cells
                by_distance.append( [c for c in next_round if c not in added] )

                for c in by_distance[curr_dist]:
                    added.add(c)

        return by_distance[dist - 1]

    def watershed(self):
        '''
        Create lakes in low 'bowls' where water runs downhill and doesn't have a way to get out to an
        ocean. Simulate rainfall and fill areas at the bottom of the hill.
        '''

        water_depth = {}

        for cell in self.cells:
            water_depth[cell.region_idx] = 0

        # Find the cell with the lowest elevation out of a list of cells
        lowest_cell = lambda all_cells: functools.reduce(lambda a, b: a if a.elevation < b.elevation else b, all_cells, all_cells[0])

        # For each land cell, visit neighbors @ lower elevations until you reach water or don't have
        # neighbors @ lower elevation. If you reach water, end with no side-effects. If you reach a
        # bowl, increase water depth by one.
        for current_cell in [c for c in self.cells if c.type == Cell.Type.LAND]:
            neighbors = self.neighbors(current_cell.region_idx)
            next_cell = lowest_cell(neighbors)

            # Keep flowing while 
            while next_cell.elevation < current_cell.elevation:
                current_cell = next_cell

                neighbors = self.neighbors(current_cell.region_idx)
                next_cell = lowest_cell(neighbors)

                # If we've hit a cell that's already water, finish.
                if next_cell.type == Cell.Type.WATER:
                    break
            
            # If we ended on land, increase water depth.
            if next_cell.type == Cell.Type.LAND:
                water_depth[next_cell.region_idx] += 1

        # Convert cells to water if enough water has pooled up. If the pool is big enough, start
        # filling up surrounding cells as well.
        for (region_idx, depth) in water_depth.items():
            if depth > 5:
                cell = self.cell_by_region_idx(region_idx)
                cell.type = Cell.Type.WATER

                pool = [cell,]

                # If we've over-filled a cell, flow into the next lowest cell connected to the pool.
                # Each time the pool expands, future expansions can go into the neighboring LAND cells
                # connected to any part of the pool. The lowest elevation cell will always be selected.
                for _ in range( math.floor(depth / 10) ):
                    neighbors = []
                    for c in pool:
                        for neighbor in [n for n in self.neighbors(c.region_idx) if n.type == Cell.Type.LAND]:
                            neighbors.append(neighbor)
    
                    lowest = lowest_cell(neighbors)

                    lowest.type = Cell.Type.WATER
                    pool.append(lowest)


    def cell_by_region_idx(self, region_idx):
        for cell in self.cells:
            if cell.region_idx == region_idx:
                return cell

        return None

    '''
    Check whether the specified region is on the 'border' of the region. A cell is on the border if
    it contains a vertex that isn't shared by any other cell in the region.
    '''
    def is_border(self, region_idx):
        if region_idx not in self.cellmap:
            raise InvalidCellError('Cell does not exist in region')

        region = self.vor.regions[region_idx]

        for r in region:
            if self.vertex_count[r] == 1:
                return True
        
        return False

    def floodfill(self, region_idx, predicate):
        if region_idx not in self.cellmap:
            raise InvalidCellError('Cell does not exist in region')

        cells = [self.cellmap[region_idx], ]

        queue = collections.deque([self.cellmap[region_idx], ])
        added = set([region_idx,])

        while len(queue) > 0:
            next_cell = queue.popleft()

            for cell in self.neighbors(next_cell.region_idx):
                if predicate(cell) and cell.region_idx not in added:
                    cells.append(cell)
                    queue.append(cell)
                    added.add(cell.region_idx)

        return cells


class Landform(object):
    def __init__(self, cells, vor):
        self.cells = cells
        self.vor = vor

        self.included_cells = set()
        for cell in self.cells:
            self.included_cells.add(cell.region_idx)
    
    def contains(self, region_idx):
        return region_idx in self.included_cells

    def outline(self):
        ridges = []

        '''
        get all allowed regions
        for all ridge vertices
            check if ridge is in exactly one region
        '''
        supported_regions = list( map(lambda cell: self.vor.regions[cell.region_idx], self.cells) )

        regions_with_ridge = lambda ridge: list( filter(lambda region: ridge[0] in region and ridge[1] in region, supported_regions) )

        for ridge in self.vor.ridge_vertices:
            if len(regions_with_ridge(ridge)) == 1 and -1 not in ridge:
                ridges.append(ridge)

        return list(map(lambda r: (self.vor.vertices[r[0]], self.vor.vertices[r[1]]), ridges))


class World(object):
    '''
    Worlds contain a series of Cells, and store the Voronoi diagram used to define the region
    and position of each. Worlds also include much of the logic for world generation and any 
    configuration variables needed to do so.
    '''

    # Currently worldwide configuration so elevation looks smooth across nearby landforms and (eventually)
    # underwater surfaces.

    # Definition of what these are here:
    # http://libnoise.sourceforge.net/glossary/
    NoiseConfig = {
        'scale': 2.5,           # top tweak
        'octaves': 5,
        'persistence': 4.5,
        'lacunarity': 2.0,
        'base': random.randint(0, 1000)
    }

    LandformConfig = {
        'InitialPlateSplitProb': 0.01,
    }

    def __init__(self, vor):
        self.vor = vor
        self.cells = []

        self.continents = []
        self.id = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))

    def _gen_noise(self, x, y):
        scaled_x = x / World.NoiseConfig['scale']
        scaled_y = y / World.NoiseConfig['scale']

        octaves = World.NoiseConfig['octaves']
        persistence = World.NoiseConfig['persistence']
        lacunarity = World.NoiseConfig['lacunarity']

        base = World.NoiseConfig['base']

        return ( snoise2(scaled_x, scaled_y, octaves=octaves, persistence=persistence, lacunarity=lacunarity, base=base) + 1.0) / 2.0

    def build(self):
        self.cells = self._form_cells()
        self._label_boundary(self.cells)

        # Establish tectonic plates. Once this is done we'll create a separate region for each.
        wr = WorldRegion(self.cells, self.vor)
        self._form_plates(wr)

        gen_noise = lambda x, y: self._gen_noise(x, y)

        # Run world generation functions on each plate independently.
        for plate_id in set([c.plate_id for c in self.cells]):
            cells = [c for c in self.cells if c.plate_id == plate_id]

            region = WorldRegion(cells, self.vor)

            self._add_ocean(region)
            self._terrainify(region)
            self._add_elevation(region, gen_noise)
            
            region.watershed()
        
    def label(self):
        wr = WorldRegion(self.cells, self.vor)

        # Start a continuent at a random land cell
        land_cells = list( filter(lambda c: c.type == Cell.Type.LAND, self.cells) )
        for cell in land_cells:
            # if the cell is not yet part of a continent
            if sum( map(lambda con: con.contains(cell.region_idx), self.continents) ) == 0:
                # Flood fill across Land cells to generate the full continent
                continent_cells = wr.floodfill(cell.region_idx, lambda c: c.type == Cell.Type.LAND)

                # Create a Landform and add it to the continent list
                self.continents.append( Landform(continent_cells, self.vor) )

    def _form_plates(self, region):
        plate_centers = random.choices(region.cells, k=3)
        plate_dist = [1, 1, 1]  # distance to go out from the center to find available cells

        for idx, center in enumerate(plate_centers):
            center.plate_id = idx

        # Function to check whether a cell still needs to have a plate assigned. Boundary cells
        # are excluded.
        still_available = lambda cell: cell.plate_id is None

        remaining = sum( [1 for cell in region.cells if still_available(cell)] )


        # Add all cells to a plate
        while remaining > 0:
            # For each plate, expand out from the center
            for plate_id, center in enumerate(plate_centers):
                avail = [c for c in region.neighbors(center.region_idx, plate_dist[plate_id]) if still_available(c)]

                while len(avail) == 0:
                    plate_dist[plate_id] += 1
                    avail = [c for c in region.neighbors(center.region_idx, plate_dist[plate_id]) if still_available(c)]

                mark = random.choice(avail)
                mark.plate_id = center.plate_id

                # Count remaining cells to be marked; break the loop if we're done.
                remaining = sum( [1 for cell in region.cells if still_available(cell)] )

                if remaining == 0:
                    break

            # There's a chance to add a new plate each iteration. New plates
            # can only exist in unmarked cells.
            if random.random() < (World.LandformConfig['InitialPlateSplitProb'] / len(plate_centers)):
                avail = [c for c in self.cells if c.plate_id is None]

                if len(avail) > 0:
                    cell = random.choice(avail)
                    
                    cell.plate_id = len(plate_centers)
                    plate_centers.append(cell)
                    plate_dist.append(1) # all plates start at dist=1

    '''
    Generate a series of world cells based on the specified Voronoi diagram. A directed
    graph is also calculated based on which cells are touching each other.
    '''
    def _form_cells(self):
        cells = []

        for point_idx, region_idx in enumerate(self.vor.point_region):
            cell = Cell(region_idx, self.vor.points[point_idx])

            cells.append(cell)

        return cells

    '''
    A boundary cell is a cell that extends beyond the edge of the world.
    '''
    def _label_boundary(self, cells):
        for cell in cells:
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
            if region.is_border(cell.region_idx):
                cell.type = Cell.Type.WATER

                # Traverse the cell graph twice randomly and turn each cell into
                # water. Two anecdotally gives decent results when PointCount = 250,
                # but the number should probably be a function of the number of cells.
                neighbor = cell

                iterations = round( math.sqrt(math.sqrt(len(region.cells))) )

                for _ in range(iterations):
                    if (random.random() < 0.8):
                        avail = region.neighbors(neighbor.region_idx)

                        if len(avail) > 0:
                            neighbor = random.choice(avail)
                            neighbor.type = Cell.Type.WATER

    def _terrainify(self, region):
        for cell in region.cells:
            if not cell.type == Cell.Type.WATER:
                cell.type = Cell.Type.LAND

    def _add_elevation(self, region, gen_noise):
        # Different regions may have different elevation profiles - some will be more
        # mountainous and others may be flatter. The 'dampener' approximates this profile
        # and is assigned randomly. Regions with smaller dampener values will tend to be
        # flatter.
        #
        # TODO: improve this -- really cool effect but did this in 30 seconds
        dampener = random.choice([0.4, 0.4, 0.6, 1.0])

        for cell in region.cells:
            if cell.type == Cell.Type.LAND:
                cell.elevation = gen_noise(cell.location[0], cell.location[1]) * dampener

                dist_from_water = self.__distance_from_water(cell, region)

                if dist_from_water < 5:
                    fade_pct = [.3, .5, .8, .9]
                    cell.elevation = cell.elevation * fade_pct[dist_from_water - 1]

    '''
    Find the shortest distance from the specified cell to water. Distance is defined
    as the lowest number of edges in the world graph that need to be traversed to 
    reach a water cell.
    '''
    def __distance_from_water(self, cell, region):
        queue = collections.deque()
        queue.append( (cell, 0) )

        # Keep track of which cells have already been searched.
        added = set()
        added.add(cell.region_idx)

        while len(queue) > 0:
            (cell, dist) = queue.popleft()

            if cell.type == Cell.Type.WATER:
                return dist

            for next_cell in region.neighbors(cell.region_idx):
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

    def render(self, cell_labels=False, color_boundaries=False, cell_elevation=False, tectonics=False, show_graph=False, outline_landforms=False, heightmap=False):
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
                if cell.type == Cell.Type.FIRE:
                    self.paint_cell(cell.region_idx, 'red')

        if cell_elevation:
            color_sealevel = colour.Color('green')
            color_peak = colour.Color('red')

            num_colors = 25
            gradient = list( color_sealevel.range_to(color_peak, num_colors) )

            for cell in self.cells:
                # if cell.type == Cell.Type.WATER:
                #     self.paint_cell(cell.region_idx, '#0485d1')
                if cell.type == Cell.Type.LAND:
                    color_idx = math.floor( cell.elevation / (1.0 / num_colors) )
                    self.paint_cell(cell.region_idx, gradient[color_idx].hex)

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

        if outline_landforms:
            for continent in self.continents:
                outlines = continent.outline()

                for outline in outlines:
                    x = (outline[0][0], outline[1][0])
                    y = (outline[0][1], outline[1][1])

                    plt.plot(x, y, '#222222', linewidth=1)

        if heightmap:
            grid = numpy.zeros((1000, 1000),)

            for y in range(1000):
                for x in range(1000):
                    grid[x][y] = self._gen_noise(x / 1000.0, y / 1000.0)

            grid = (255 * grid).astype('uint8')
            img = Image.fromarray(grid, mode='L')
            img.save('heightmap.png')

        plt.title('Rendered world')

        plt.savefig('world-%s.png' % (self.id,))
        # plt.show()
