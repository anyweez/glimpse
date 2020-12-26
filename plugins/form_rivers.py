import functools, numpy

from entity import Entity
from world import Cell
from graph import Graph

from decorators import genreq

class River(Entity):
    def __init__(self, graph):
        '''
        A river's Graph is an EDGE graph, not a cell graph -- each vertex of the vonoroi diagram is a node.
        '''
        super().__init__(graph)

    def render_stage1(self, ctx, world, vd, theme):
        ctx.push_group()

        for edge in self.graph.edges():
            (src, dest) = edge

            src_pt = Entity._transform_pt(vd.vertex_location(src))
            dest_pt = Entity._transform_pt(vd.vertex_location(dest))

            ctx.move_to(*src_pt)
            ctx.line_to(*dest_pt)

        ctx.set_source_rgba(*theme.WaterRiver)
        ctx.set_line_width(0.0012)
        ctx.stroke()

        ctx.pop_group_to_source()

        ctx.paint()

'''
1. build edge/vertex graph
2. calculate which cells are water  (if any neighbors are water, cell is water)
3. calculate elevation              (avg of cell elevations)
4. pathfind
'''
@genreq(cellprops=['celltype', 'elevation', 'latitude', 'longitude'])
def generate(world, vd):
    MinFlowThreshold = world.std_density(3)
    MinRiverLength = world.std_density(4)

    edgegraph = Graph(vd.edges())

    edge_celltype = [Cell.Type.LAND for _ in range(edgegraph.node_count())]
    edge_elevation = [0.0 for _ in range(edgegraph.node_count())]

    for vertex_id in edgegraph.nodes():
        included_cells = vd.included_cells(vertex_id)

        # Elevation is the average of all included cells
        edge_elevation[vertex_id] = sum( [world.cp_elevation[cell_idx] for cell_idx in included_cells] ) / len(included_cells)
        edge_celltype[vertex_id] = Cell.Type.WATER if Cell.Type.WATER in [world.cp_celltype[idx] for idx in included_cells] else Cell.Type.LAND

    def lower_cell(first, second):
        return first if edge_elevation[first] <= edge_elevation[second] else second

    edges = {}

    def flow(src_idx):
        '''
        Recursive function that calculates the flow rate through cells by
        calculating flow via the steepest downhills.
        '''

        if edge_celltype[src_idx] == Cell.Type.WATER:
            return

        lowest_idx = functools.reduce(
            lower_cell, 
            edgegraph.neighbors(src_idx),
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

        flow(lowest_idx)
    
    # Flow rainfall down all land cells
    for idx, celltype in enumerate(edge_celltype):
        if celltype == Cell.Type.LAND:
            flow(idx)
    
    rivergraph = Graph([pair for pair, flow_rate in edges.items() if flow_rate > MinFlowThreshold])
    all_rivers = set()

    for idx in rivergraph.nodes():
        if idx not in all_rivers:
            river_set = rivergraph.floodfill(idx)

            water_cells = [idx for idx in river_set if edge_celltype[idx] == Cell.Type.WATER]

            def single_river(edge):
                return edge[0] in river_set and edge[1] in river_set

            if len(river_set) >= MinRiverLength and len(water_cells) > 0:
                r = River( rivergraph.subgraph(single_river) )

                # Add the river to the world
                world.add_entity(r)
                # Remove these cells from consideration for future rivers
                all_rivers.update(river_set)