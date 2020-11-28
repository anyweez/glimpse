import functools, numpy

from entity import Entity
from world import Cell
from graph import Graph

from decorators import genreq

class River(Entity):
    def __init__(self, graph):
        super().__init__(graph)

    def render_stage1(self, ctx, world, vd, theme):
        def draw_line_between(ctx, src, dest, color, linewidth=0.003):
            ctx.set_source_rgba(*color)

            ctx.move_to(*src)
            ctx.line_to(*dest)
            ctx.set_line_width(linewidth)
            ctx.stroke()

        for edge in self.graph.edges():
            (src, dest) = edge

            src_pt = Entity._transform_pt((
                world.cp_latitude[src],
                world.cp_longitude[src],
            ))
            
            dest_pt = Entity._transform_pt((
                world.cp_latitude[dest],
                world.cp_longitude[dest],
            ))

            draw_line_between(ctx, src_pt, dest_pt, theme.WaterRiver, 0.002)

@genreq(cellprops=['celltype', 'elevation', 'latitude', 'longitude'])
def generate(world, vd):
    MinFlowThreshold = world.std_density(10)
    MinRiverLength = world.std_density(5)

    def lower_cell(first, second):
        return first if world.cp_elevation[first] <= world.cp_elevation[second] else second
    
    graph = world.graph

    edges = {}

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

        if world.cp_celltype[src_idx] == Cell.Type.WATER:
            return

        flow(lowest_idx)
    
    # Flow rainfall down all land cells
    for idx in numpy.argwhere(world.cp_celltype == Cell.Type.LAND)[:, 0]:
        flow(idx)
    
    rivergraph = Graph([pair for pair, flow_rate in edges.items() if flow_rate > MinFlowThreshold])

    all_rivers = set()

    for idx in rivergraph.nodes():
        if idx not in all_rivers:
            river_set = rivergraph.floodfill(idx)

            def single_river(edge):
                return edge[0] in river_set and edge[1] in river_set

            if len(river_set) >= MinRiverLength:
                r = River(rivergraph.subgraph(single_river))

                # Add the river to the world
                world.add_entity(r)
                # Remove these cells from consideration for future rivers
                all_rivers.update(river_set)