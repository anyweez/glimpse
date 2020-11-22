import collections, igraph
import errors

class Graph(object):
    def __init__(self, edges):
        self.ig = igraph.Graph()

        # Count number of vertices
        region_idxs = set()
        for (src, dest) in edges:
            region_idxs.add(src)
            region_idxs.add(dest)

        if len(region_idxs) == 0:
            return

        self.ig.add_vertices(max(region_idxs) + 1)
        self.ig.add_edges(edges)

    def subgraph(self, edge_filter):
        edges = filter(edge_filter, self.edges())

        return Graph( list(edges) )

    def node_count(self):
        '''
        Return the number of nodes in the graph. This may be one (1) higher than expected
        because of how we build the graph.
        '''
        return self.ig.vcount()

    def edge_count(self):
        '''
        Return the number of edges in the graph.
        '''
        return self.ig.ecount()

    def nodes(self):
        '''
        Return a list containing all region_idxs represented in the graph. A node will only
        exist in the graph if there's at least one inbound or outbound edge.
        '''
        return self.ig.vs.indices

    def edges(self):
        '''
        Generator that iterates over all edges in the graph.
        '''
        for edge in self.ig.get_edgelist():
            yield edge

    def neighbors(self, region_idx, dist=1):
        '''
        Find all neighbors @ distance `dist` for the specified node.
        '''
        if region_idx >= self.node_count():
            return []

        neighbors = []

        for (vertex, vert_dist, _) in self.ig.bfsiter(int(region_idx), advanced=True):
            if vert_dist == dist:
                neighbors.append(vertex.index)
            
            if vert_dist > dist:
                return neighbors
        
        return neighbors

    def distance(self, region_idx, dest_func, max_distance=None):
        '''
        Find path from region_idx to a node that satisfies `dest_func`, traveling
        only through nodes that satisfy `traverse_func`. Return the destination idx
        as well as the shortest distance from `region_idx` to the destination.

        The returned `dist` is guaranteed to be the shortest distance.
        '''

        # region_idx doesn't exist in the graph
        if region_idx >= self.node_count():
            return (None, 0)

        for (vertex, vert_dist, _) in self.ig.bfsiter(int(region_idx), advanced=True):
            if dest_func(vertex.index):
                return (vertex.index, vert_dist)
            
            if max_distance and vert_dist > max_distance:
                return (None, max_distance)
        
        return (None, max_distance)


    def floodfill(self, region_idx):
        '''
        Expand in all directions from `region_idx` as long as new cells satisfy
        the `fill_func`.
        '''

        if region_idx >= self.node_count():
            return []

        return [ v.index for v in self.ig.bfsiter(int(region_idx)) ]

def BuildGraph(cells, vor):
    '''
    Build a graph connecting cells that share vertices.
    '''
    edges = []

    # map vertex_id => region_idx that touch vertex
    regions_by_vertex = {}

    # List all regions that share each vertex
    for cell in cells:
        for vertex in vor.regions[cell.region_idx]:
            if vertex not in regions_by_vertex:
                regions_by_vertex[vertex] = []

            regions_by_vertex[vertex].append(cell.region_idx)

    # Run through list of vertices and build edges between all connected regions
    for (_, region_idxs) in regions_by_vertex.items():
        for source in region_idxs:
            for dest in region_idxs:
                if source != dest:
                    edges.append( (source, dest) )
                    edges.append( (dest, source) )

    return Graph(edges)