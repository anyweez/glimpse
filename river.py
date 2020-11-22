import functools
import structs

from structs import Cell
from graph import Graph

class River(structs.AbstractCellGroup):
    def __init__(self, cells, vor, graph):
        super().__init__(cells, vor, graph)

    def segments(self):
        # Return a series of (src_idx, dest_idx, flow_rate) tuples
        segment_list = []

        region_idx = self.cells[0].region_idx
        for idx in self.graph.floodfill(region_idx):
            for neighbor_idx in self.graph.neighbors(idx):
                segment_list.append( (idx, neighbor_idx, 1) )

        return segment_list

def FormRivers(world):
    # Threshold for flow rate required to be visible
    # Rainfall everywhere, flows to lowest neighbor
    # Add weight to graph edge, continue adding until we reach a water cell

    cells = world.cells
    graph = world.graph

    edges = {}

    def lower_cell(first_idx, second_idx):
        first = world.get_cell(first_idx)
        second = world.get_cell(second_idx)

        if first.elevation <= second.elevation:
            return first_idx
        else:
            return second_idx

    def flow(src_idx):
        '''
        Recursive function that calculates the flow rate through cells by
        calculating flow via the steepest downhills.
        '''
        lowest_idx = functools.reduce(
            lower_cell, 
            graph.neighbors(src_idx),
            src_idx,
        )

        # If we're at the lowest point already, return.
        if src_idx == lowest_idx:
            return

        # Add to the flow between src and lowest
        edge_idx = (src_idx, lowest_idx)
        if edge_idx not in edges:
            edges[edge_idx] = 0
        
        edges[edge_idx] += 1

        if world.get_cell(src_idx).type == Cell.Type.WATER:
            return

        flow(lowest_idx)

    ## Calculate how much water flows through every cell. Lots of water turns
    ## into rivers...see below.
    for cell in [c for c in cells if c.type == Cell.Type.LAND]:
        flow(cell.region_idx)

    ## TODO:
    ##   * edges.keys() is the list of edges for the graph; only include if flow rate > X
    ##   * use this graph ^^ for creating the river
    ##   * delete River.edges property, use the graph instead in segments()
    ##   * delete cell flow for now, always return 1

    rivergraph = Graph([pair for pair, flow_rate in edges.items() if flow_rate > 10])

    rivers = []
    all_rivers = set()

    for cell in [c for c in cells if c.type == Cell.Type.LAND]:
        if cell.region_idx not in all_rivers:
            river_set = rivergraph.floodfill(cell.region_idx, lambda idx: True)

            if len(river_set) > 6:
                r = River(world.get_cells(river_set), world.vor, rivergraph)
                rivers.append(r)

                all_rivers.update(river_set)

    return rivers