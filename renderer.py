import enum, cairo, colour, math, random

from structs import Cell

class RenderOptions(object):
    CellColorMode = enum.Enum('CellColorMode', 'ELEVATION')

    def __init__(self):
        self.CellColorMode = RenderOptions.CellColorMode.ELEVATION
        self.scale_x = 1200
        self.scale_y = 800

        self.filename = 'world.png'

def transform(point):
    return (point[0], 1.0 - point[1])

def rgb(r, g, b):
    return (r / 255.0, g / 255.0, b / 255.0)

def draw_region(ctx, points, fill_color):
    if len(points) == 0:
        return

    ctx.move_to(points[0][0], points[0][1])

    for point in points[1:]:
        ctx.line_to(point[0], point[1])

    ctx.close_path()
    ctx.set_source_rgb(*fill_color)
    ctx.fill_preserve()

    ctx.set_source_rgb(*fill_color)
    ctx.set_line_width(0.003)
    ctx.stroke()

def draw_outline(ctx, start_pt, end_pt):
    ctx.move_to(*start_pt)

    ctx.line_to(*end_pt)

    ctx.set_source_rgb(0.0, 0.0, 0.0)
    ctx.set_line_width(0.004)
    ctx.stroke()

def draw_city(ctx, city):
    city_radius = 0.012
    city_loc = transform(city.location)

    ctx.set_source_rgb(1.0, 1.0, 1.0)
    ctx.arc(city_loc[0], city_loc[1], city_radius, 0, 2 * math.pi)
    ctx.fill_preserve()

    ctx.set_source_rgb(0.0, 0.0, 0.0)
    ctx.set_line_width(0.005)

    ctx.stroke()

def draw_tree(ctx, point):
    tree_height = 0.015
    top = transform(point)

    top = (top[0], top[1] - tree_height)

    # Build the triangle
    ctx.set_source_rgb(*rgb(46, 74, 19))
    
    bottom_left = (top[0] - (tree_height / 2.5), 1 - (top[1] + tree_height))
    bottom_right = (top[0] + (tree_height / 2.5), 1 - (top[1] + tree_height))

    ctx.move_to(*top)
    ctx.line_to(*transform(bottom_left))
    ctx.line_to(*transform(bottom_right))
    ctx.close_path()

    ctx.fill()


def render(world, cities=[], forests=[], poi_lib=None, opts=RenderOptions()):
    # with cairo.SVGSurface('world.svg', image_scale, image_scale) as surface:
    with cairo.ImageSurface(cairo.FORMAT_ARGB32, opts.scale_x, opts.scale_y) as surface:
        ctx = cairo.Context(surface)
        ctx.scale(opts.scale_x, opts.scale_y)

        ctx.rectangle(0, 0, 1, 1)
        ctx.set_source_rgb(1.0, 1.0, 1.0)
        ctx.fill()

        ## Draw all cells
        color_sealevel = colour.Color('green')
        color_peak = colour.Color('red')

        num_colors = 25
        gradient = list( color_sealevel.range_to(color_peak, num_colors) )

        for cell in world.cells:
            if cell.type == Cell.Type.LAND:
                color_idx = math.floor( cell.elevation * num_colors )

                region = list( map(lambda pt: transform(pt), world.get_region(cell.region_idx)) )
                draw_region(ctx, region, gradient[color_idx].rgb)
            
            if cell.type == Cell.Type.WATER:
                def land(idx):
                    return world.get_cell(idx).type == Cell.Type.LAND

                (_, dist) = world.graph.distance(cell.region_idx, lambda _, idxs, __: idxs, land, max_distance=10)

                region = list( map(lambda pt: transform(pt), world.get_region(cell.region_idx)) )

                if dist < 4:
                    draw_region(ctx, region, rgb(1, 133, 209))
                elif dist < 8 and random.random() < 0.5:
                    draw_region(ctx, region, rgb(1, 133, 209))
                else:
                    draw_region(ctx, region, rgb(3, 119, 188))
        
        ## Draw forests
        for f in forests:
            for cell in f.cells:
                region = list( map(lambda pt: transform(pt), world.get_region(cell.region_idx)) )

                # draw_region(ctx, region, rgb(255, 0, 0))

                if random.random() < 0.33:
                    draw_tree(ctx, cell.location)

        ## Highlight points of interest
        if poi_lib is not None:
            for poi_type in poi_lib.list_types():
                # For each point of interest....
                for poi in poi_lib.get_type(poi_type):
                    colors = [rgb(255, 255, 0), rgb(0, 255, 255), rgb(255, 0, 255), rgb(128, 0, 255)]
                    color = random.choice(colors)

                    for cell in poi.cells:
                        region = list( map(lambda pt: transform(pt), world.get_region(cell.region_idx)) )
                        draw_region(ctx, region, color)

        ## Draw landform outlines
        for continent in world.continents:
            outlines = continent.outline()

            for outline in outlines:
                start = transform(outline[0])
                end = transform(outline[1])

                draw_outline(ctx, start, end)

        ## Draw cities
        for city in cities:
            draw_city(ctx, city)

        surface.write_to_png(opts.filename)