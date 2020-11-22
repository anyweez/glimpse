import errors, collections

class Graph(object):
    def __init__(self, edges):
        self.directed_edgedict = {}

        for (src, dest) in edges:
            if src not in self.directed_edgedict:
                self.directed_edgedict[src] = []
            
            if dest not in self.directed_edgedict[src]:
                self.directed_edgedict[src].append(dest)

    def node_count(self):
        nodes = set()

        for k, v in self.directed_edgedict.items():
            nodes.add(k)
            nodes.update(v)
        
        return len(nodes)

    def edge_count(self):
        return sum([len(v) for v in self.directed_edgedict.values()])

    def edges(self):
        for src in self.directed_edgedict.keys():
            for dest in self.directed_edgedict[src]:
                yield (src, dest)

    def neighbors(self, region_idx, dist=1):
        '''
        Find all neighbors @ distance `dist` for the specified node.
        '''
        if region_idx not in self.directed_edgedict:
            return []

        # If we're looking for immediate neighbors, jump straight to the nmap where this is explicitly
        # known. This also allows us to use neighbors(dist=1) for calculations when dist != 1
        if dist == 1:
            return self.directed_edgedict[region_idx]

        by_distance = []
        added = set( [region_idx,] )

        for curr_dist in range(dist):
            if curr_dist == 0:
                by_distance.append( self.neighbors(region_idx) )

                added.update(by_distance[curr_dist])

            else:
                next_round = set()
                for parent_idx in by_distance[curr_dist - 1]:
                    next_round.update(self.neighbors(parent_idx))

                # De-duplicate and flatten a list of the neighbors of all cells
                by_distance.append( [c for c in next_round if c not in added] )

                added.update(by_distance[curr_dist])

        return by_distance[dist - 1]

    def distance(self, region_idx, traverse_func, dest_func, max_distance=None):
        '''
        Find path from region_idx to a node that satisfies `dest_func`, traveling
        only through nodes that satisfy `traverse_func`. Return the destination idx
        as well as the shortest distance from `region_idx` to the destination.

        The returned `dist` is guaranteed to be the shortest distance.
        '''
        queue = collections.deque()
        queue.append( (region_idx, 0) )

        added = set()
        added.add(region_idx)

        while len(queue) > 0:
            (idx, dist) = queue.popleft()

            # If no valid destination is discovered by taking `max_distance` steps
            # then stop looking.
            if max_distance and dist > max_distance:
                return (None, -1)

            if dest_func(idx):
                return (idx, dist)

            for next_idx in traverse_func(idx, self.neighbors(idx), {}):
                if next_idx not in added:
                    queue.append( (next_idx, dist + 1) )
                    added.add(next_idx)
        
        return (None, -1)

    def floodfill(self, region_idx, fill_func):
        '''
        Expand in all directions from `region_idx` as long as new cells satisfy
        the `fill_func`.
        '''
        cells = [region_idx, ]

        queue = collections.deque([region_idx,])
        added = set([region_idx,])

        while len(queue) > 0:
            next_idx = queue.popleft()

            for neighbor_idx in self.neighbors(next_idx):
                if neighbor_idx not in added and fill_func(neighbor_idx):
                    cells.append(neighbor_idx)  # Store this cell as part of the resulting set
                    queue.append(neighbor_idx)  # Continue flood to this cell's neighbors

                    added.add(neighbor_idx)     # Ensure we don't revisit this cell later

        return cells

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