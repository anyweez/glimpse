import enum, cairo, colour, math

from structs import Cell

class RenderOptions(object):
    CellColorMode = enum.Enum('CellColorMode', 'ELEVATION')

    def __init__(self):
        self.CellColorMode = RenderOptions.CellColorMode.ELEVATION
        self.scale_x = 600
        self.scale_y = 400

def transform(point):
    return (point[0], 1.0 - point[1])

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

def render(world, cities, opts):
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
                color_idx = math.floor( cell.elevation / (1.0 / num_colors) )

                region = list( map(lambda pt: transform(pt), world.get_region(cell.region_idx)) )
                draw_region(ctx, region, gradient[color_idx].rgb)
            
            if cell.type == Cell.Type.WATER:
                # water color: https://www.color-hex.com/color/0485d1
                color = (0.0157, 0.5216, 0.820)

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

        surface.write_to_png('world-%s.png' % (world.id,))