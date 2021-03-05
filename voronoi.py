import numpy, math
import matplotlib.pyplot as plt

from scipy.spatial import Voronoi, KDTree, SphericalVoronoi
from ai import cs

from shapely.geometry import Polygon, MultiPolygon, multipolygon
from shapely.ops import unary_union

def to_latlong(cart3d):
    '''
    Convert from 3d Cartesian coordinates to lat/long
    '''
    _, theta, phi = cs.cart2sp(*cart3d)

    return (
        math.degrees(theta),
        math.degrees(phi),
    )

def to_cartesian(sphere3d):
    # If the value passed in only includes lat & long (no elevation),
    # add 1.0 as elevation
    if len(sphere3d) == 2:
        sphere3d = (1.0, sphere3d[0], sphere3d[1])

    x, y, z = cs.sp2cart(*sphere3d)

    return (
        math.radians(x),
        math.radians(y),
        math.radians(z),
    )

class VoronoiDiagram(object):
    def __init__(self, vor, mapping):
        self.vor = vor
        self.mapping = mapping # cell_idx => voronoi_idx

        self.center = {}

        # Calculate centroids of each cell
        for cell_idx in self.mapping.keys():
            region = self.get_region(cell_idx)

            if len(region) == 0:
                self.center[cell_idx] = None
            else:
                cell_x = list( map(lambda pt: pt[0], region) )
                cell_y = list( map(lambda pt: pt[1], region) )

                center_x = sum(cell_x) / len(cell_x)
                center_y = sum(cell_y) / len(cell_y)

                self.center[cell_idx] = (center_x, center_y)

        # Set up a data structure to quickly determine whether a particular
        # cell has a particular vertex.
        self.cells_with_vertex = {}

        for cell_idx in self.mapping.keys():
            region = self.get_region(cell_idx, locations=False)

            for vertex_id in [idx for idx in region if idx != -1]:
                if vertex_id not in self.cells_with_vertex:
                    self.cells_with_vertex[vertex_id] = set()

                self.cells_with_vertex[vertex_id].add(cell_idx)
        
        # Calculate edges between nodes based on shared vertices. Any node that
        # shares one or more vertex is considered to be a neighbor.
        self.cell_edges = set()
        self.vertices = {}
        for cell_idx in self.mapping.keys():
            region = self.get_region(cell_idx, locations=False)

            for vertex_id in [idx for idx in region if idx != -1]:
                if vertex_id not in self.vertices:
                    self.vertices[vertex_id] = [cell_idx,]
                else:
                    for other_cell_idx in self.vertices[vertex_id]:
                        self.cell_edges.add( (cell_idx, other_cell_idx) )
                        self.cell_edges.add( (other_cell_idx, cell_idx) )
                    
                    self.vertices[vertex_id].append(cell_idx)
        
        # Populate KD-Tree for fast find_cell() below -- use self.center points
        # for each cell. Index in list = cell_idx
        centers = [None] * len(self.center)
        for cell_idx, center_pt in self.center.items():
            centers[cell_idx] = center_pt

        self.kdtree = KDTree(centers)

    def get_region(self, cell_idx, locations=True):
        '''
        Get the polygon that defines the region for the specified cell_id/region_id.
        Returns a list of 2D points, or an empty list if the region isn't defined within
        the Voronoi diagram; see more about when this happens here:

        https://docs.scipy.org/doc/scipy/reference/generated/scipy.spatial.Voronoi.html
        '''
        v_idx = self.mapping[cell_idx]

        region = [region for region in self.vor.regions[v_idx] if region != -1]

        if locations:
            return list( map(lambda r: to_latlong(self.vor.vertices[r]), region) )
        else:
            return region

    def edges(self):
        '''
        Return a list of (src, dest) cell_idx pairs for each cell that shares a vertex.
        This function will return one item for each direction, i.e. (src, dest) and
        (dest, src) will both appear.
        '''
        return list(self.cell_edges)

    def included_cells(self, vertex_id):
        return list( self.cells_with_vertex[vertex_id] )

    def vertex_location(self, vertex_id):
        return to_latlong( self.vor.vertices[vertex_id] )

    def centroid(self, cell_idx):
        '''
        Return the center of the region as a lat/long.
        '''
        return self.center[cell_idx]

    def find_cell(self, x, y):
        '''
        Find the cell whose center is closest to the provided point.
        '''
        (_, idx) = self.kdtree.query((x, y), k=1)

        return idx

    def outline(self, cell_idxs):
        ridges = []

        '''
        get all allowed regions
        for all ridge vertices
            check if ridge is in exactly one region
        '''
        supported_regions = list( map(lambda idx: self.vor.regions[self.mapping[idx]], cell_idxs) )

        regions_with_ridge = lambda ridge: list( filter(lambda region: ridge[0] in region and ridge[1] in region, supported_regions) )

        for ridge in self.vor.ridge_vertices:
            if len(regions_with_ridge(ridge)) == 1 and -1 not in ridge:
                ridges.append(ridge)

        # if sort:
        #     ridges = self.sort_ridges(ridges)

        return list(map(lambda r: (self.vor.vertices[r[0]], self.vor.vertices[r[1]]), ridges))

    # def outline_polygon(self, cell_idxs):
    #     polygons = [ Polygon(self.get_region(cell_idx)) for cell_idx in cell_idxs ]

    #     print(MultiPolygon(polygons).wkt)

    #     return list( unary_union(polygons).exterior.coords )

    def outline_polygons(self, cell_idxs):
        '''
        Calculate the smallest number of polygons that contain the area of all of the cells
        defined by `cell_idxs`. This function yields one or more lists of coordinate pairs
        that represents the sorted order of the points in each polygon.
        '''
        self.vor.sort_vertices_of_regions()

        # Create all edges
        outer_edges = set()
        inner_edges = set()

        for cell_idx in cell_idxs:
            vertices = self.get_region(cell_idx, locations=False)

            for idx in range( -1, len(vertices) - 1 ):
                edge = ( 
                    min(vertices[idx], vertices[idx + 1]),
                    max(vertices[idx], vertices[idx + 1]),
                )

                # If this edge is already identified as an inner edge, nothing new to record.
                if edge in inner_edges:
                    pass
                # If not but if was previous considered an outer edge, its now an inner edge
                elif edge in outer_edges:
                    outer_edges.remove(edge)
                    inner_edges.add(edge)
                # If its neither of the above, we haven't seen it before. Its an outer edge 
                # until proven otherwise.
                else:
                    outer_edges.add(edge)

        outer_edges = list(outer_edges)

        # Iterate through all outer edges and trace the outer edge until a circuit is completed.
        # Once we've completed a circuit, yield the point list and search for another circuit. 
        # Terminate once all outside edges have been assigned to a polygon.
        while len(outer_edges) > 0:
            (start, next_vertex) = outer_edges.pop()
            ordered_vertices = [start, next_vertex]

            while start != next_vertex:
                (src, dest) = [edge for edge in outer_edges if edge[0] == next_vertex or edge[1] == next_vertex][0]

                outer_edges.remove( (src, dest) )

                # Add in the missing value as the next vertex (could be src or dest -- effectively random
                # so we need to check).
                if next_vertex == src:
                    ordered_vertices.append(dest)
                else:
                    ordered_vertices.append(src)

                next_vertex = ordered_vertices[-1]
            
            yield list( map(lambda v: self.vertex_location(v), ordered_vertices) )

    # def sort_ridges(self, ridges):
    #     polygons = []

    #     polygon = [ ridges[0], ]
    #     ridges.pop(0)

    #     next_id = polygon[0][1]

    #     # Store the starting vertex of the polygon. Once we get back, we need to pick a new
    #     # polygon_start_id from the remaining vertices. This will cover landforms with multiple
    #     # polygons, such as continents with both a coast and lakes.
    #     polygon_start_id = next_id

    #     remaining = len(ridges)
    #     while len(ridges) > 0:
    #         for idx, ridge in enumerate(ridges):
    #             if ridge[0] == next_id:
    #                 polygon.append(ridge)

    #                 ridges.pop(idx)
    #                 next_id = ridge[1]

    #                 break

    #             if ridge[1] == next_id:
    #                 polygon.append(ridge)

    #                 ridges.pop(idx)
    #                 next_id = ridge[0]

    #                 break

    #         # Didn't remove a ridge. Switch to new polygon.
    #         if len(ridges) == remaining:
    #             polygons.append(polygon)
    #             polygon = [ ridges[0], ]

    #             ridges.pop(0)
    #             next_id = polygon[-1][1]
            
    #         remaining = len(ridges)
        
    #     if len(polygon) > 0:
    #         polygons.append(polygon)

    #     return polygons

'''
TODO: the spherical projection causes points to be pulled away from the anti-meridian (180 long)
if too many smoothing operations are performed. This is because cells that cross the boundary
involve averaging very high & very low (-180, 180) values, which pulls those cells to the ~middle.

The more smoothing iterations we make, the more pronounced the problem is.
'''

def generate(points, n_smooth=2):
    vor = None

    spherical = numpy.array( [
        cs.sp2cart(r=1.0, theta=math.radians(lat), phi=math.radians(long)) 
        for (lat, long) in points
    ] )

    # Make several iterations, using the centroid of the polygons from the previous iteration
    # as the new point cloud.
    for _ in range(n_smooth):
        vor = SphericalVoronoi(spherical)

        # Find the centroid of each cell; this requires converting back to lat/long so we can find
        # centroids (can't avg radius w/ cartesian coords or you leave the spherical surface).
        for idx, region_idxs in enumerate(vor.regions):
            region_latlong = list(map(
                lambda pt: (math.degrees(pt[1]), math.degrees(pt[2])),      # ignore pt[0], which is r (elevation)
                [cs.cart2sp(*vor.vertices[idx]) for idx in region_idxs],
            ))

            # avg_w_singularity(region_latlong)

            centroid = numpy.mean(region_latlong, 0)
            centroid_spherical = cs.sp2cart(r=1.0, theta=math.radians(centroid[0]), phi=math.radians(centroid[1]))

            spherical[idx] = centroid_spherical

    # Sort the vertices to be in counter-clockwise order for polygon-drawing later.
    vor.sort_vertices_of_regions()

    ## Uncomment below to plot voronoi cell centroids
    # fig = plt.figure()
    # ax = fig.add_subplot(111, projection='3d')

    # ax.scatter(spherical[:, 0], spherical[:, 1], spherical[:, 2], c='b')
    # # ax.scatter(vor.vertices[:, 0], vor.vertices[:, 1], vor.vertices[:, 2], c='g')

    # ax.azim = 10
    # ax.elev = 40
    # _ = ax.set_xticks([])
    # _ = ax.set_yticks([])
    # _ = ax.set_zticks([])
    # fig.set_size_inches(4, 4)
    # plt.show()
    ## </uncomment>
    
    return vor

def prebuilt_vor1():
    points = numpy.array([
        [0.40262444, 0.89010797],
        [0.46321667, 0.38315214],
        [0.44349672, 0.18688911],
        [0.68745787, 0.69143624],
        [0.81944654, 0.15131946],
        [0.72458714, 0.22609854],
        [0.09813275, 0.10948937],
        [0.70126296, 0.75512688],
        [0.94840268, 0.1245352 ],
        [0.67502909, 0.67320131],
        [0.51403338, 0.19046477],
        [0.50371745, 0.11135518],
        [0.82637509, 0.8662734 ],
        [0.73357888, 0.17471943],
        [0.03979779, 0.03844015],
        [0.98681669, 0.93202815],
        [0.37459058, 0.38567779],
        [0.97938578, 0.79391543],
        [0.72289236, 0.1089072 ],
        [0.78337802, 0.73216984],
        [0.19575816, 0.81631711],
        [0.97356313, 0.82395971],
        [0.10195127, 0.01111625],
        [0.78762842, 0.95231354],
        [0.4559196 , 0.01983087],
        [0.94214394, 0.19983331],
        [0.80805499, 0.75741924],
        [0.01387654, 0.4010178 ],
        [0.29149957, 0.11556165],
        [0.66567361, 0.92751248],
        [0.59049409, 0.32640914],
        [0.38291789, 0.92962468],
        [0.10056959, 0.56028808],
        [0.78515087, 0.86267363],
        [0.71865541, 0.22180088],
        [0.05040245, 0.7702802 ],
        [0.37084486, 0.36057732],
        [0.64849443, 0.40721157],
        [0.15563548, 0.90238154],
        [0.58745176, 0.90352623],
        [0.12489829, 0.32289921],
        [0.34419703, 0.86792104],
        [0.50676785, 0.40017397],
        [0.50834899, 0.65523267],
        [0.36487756, 0.62471309],
        [0.39764789, 0.2181109 ],
        [0.3011823 , 0.0222423 ],
        [0.2143103 , 0.60207535],
        [0.13990504, 0.17716391],
        [0.90438299, 0.66031845],
        [0.40423086, 0.56533161],
        [0.79536783, 0.37672868],
        [0.43392892, 0.32567715],
        [0.17528278, 0.05660193],
        [0.21399672, 0.68699174],
        [0.47474729, 0.35745426],
        [0.29068082, 0.59539884],
        [0.36700722, 0.13542221],
        [0.79564283, 0.95248314],
        [0.68364939, 0.60702048],
        [0.57251765, 0.6317786 ],
        [0.21822423, 0.7171864 ],
        [0.6573202 , 0.65521942],
        [0.08380973, 0.23864449],
        [0.73907708, 0.78899286],
        [0.24951666, 0.50910092],
        [0.48166857, 0.93009483],
        [0.52880764, 0.76343148],
        [0.14900537, 0.81545771],
        [0.63578057, 0.69103053],
        [0.66096026, 0.51938303],
        [0.17768932, 0.78702168],
        [0.89266581, 0.2582247 ],
        [0.52915596, 0.67159946],
        [0.6047453 , 0.26361231],
        [0.76748022, 0.45862889],
        [0.86477637, 0.44603271],
        [0.82338454, 0.98428034],
        [0.20278993, 0.06884434],
        [0.15602841, 0.8087541 ],
        [0.99733613, 0.98585632],
        [0.23368683, 0.65465301],
        [0.24976235, 0.38553243],
        [0.76690454, 0.78862475],
        [0.15056952, 0.96460832],
        [0.23950245, 0.28971527],
        [0.74287355, 0.06861326],
        [0.63059252, 0.7292568 ],
        [0.28497952, 0.94096798],
        [0.29997593, 0.31476221],
        [0.34970587, 0.84843535],
        [0.09496377, 0.31222525],
        [0.82098736, 0.52918112],
        [0.92285489, 0.15623229],
        [0.19687324, 0.55516564],
        [0.45493029, 0.02460928],
        [0.55018825, 0.75980363],
        [0.33457664, 0.21343718],
        [0.20419116, 0.13904349],
        [0.27995101, 0.04775983],
    ])

    return generate(points)