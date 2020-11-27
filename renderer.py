import enum, cairo, colour, math, random, json, functools, numpy

import xml.etree.ElementTree as ET
from structs import Cell

class RenderOptions(object):
    CellColorMode = enum.Enum('CellColorMode', 'ELEVATION')

    def __init__(self):
        self.CellColorMode = RenderOptions.CellColorMode.ELEVATION
        self.scale_x = 2070
        self.scale_y = 1600

        self.filename = 'world.png'
        self.highlight_poi = False
        self.theme = 'fullcolor'

def transform(point):
    return (point[0], 1.0 - point[1])

def rgba(r, g, b, a=1.0):
    return (r / 255.0, g / 255.0, b / 255.0, a)

def draw_region(ctx, points, fill_color):
    if len(points) == 0:
        return

    ctx.move_to(points[0][0], points[0][1])

    for point in points[1:]:
        ctx.line_to(point[0], point[1])

    ctx.close_path()
    ctx.set_source_rgba(*fill_color)
    ctx.fill_preserve()

    ctx.set_source_rgba(*fill_color)
    ctx.set_line_width(0.003)
    ctx.stroke()

def draw_outline(ctx, start_pt, end_pt):
    ctx.move_to(*start_pt)

    ctx.line_to(*end_pt)

    # ctx.set_source_rgb(0.0, 0.0, 0.0)
    ctx.set_source_rgba(*FullColorTheme.WaterShore)
    ctx.set_line_width(0.0015)
    ctx.set_line_join(cairo.LINE_JOIN_BEVEL)
    ctx.set_line_cap(cairo.LINE_CAP_ROUND)

    ctx.stroke()

def draw_city(ctx, city):
    city_radius = 0.01
    city_loc = transform(city.location)

    ctx.set_source_rgba(1.0, 1.0, 1.0, 1.0)
    ctx.arc(city_loc[0], city_loc[1], city_radius, 0, 2 * math.pi)
    ctx.fill_preserve()

    ctx.set_source_rgba(0.0, 0.0, 0.0, 1.0)
    ctx.set_line_width(0.004)

    ctx.stroke()

def draw_tree(ctx, point):
    tree_height = 0.015
    top = transform(point)

    top = (top[0], top[1] - tree_height)

    # Build the triangle
    ctx.set_source_rgba(*rgba(46, 74, 19))
    
    bottom_left = (top[0] - (tree_height / 2.5), 1 - (top[1] + tree_height))
    bottom_right = (top[0] + (tree_height / 2.5), 1 - (top[1] + tree_height))

    ctx.move_to(*top)
    ctx.line_to(*transform(bottom_left))
    ctx.line_to(*transform(bottom_right))
    ctx.close_path()

    ctx.fill()

def draw_line_between(ctx, src, dest, color, linewidth=0.003):
    ctx.set_source_rgba(*color)

    ctx.move_to(*src)
    ctx.line_to(*dest)
    ctx.set_line_width(linewidth)
    ctx.stroke()


# class RenderColor(object):
#     '''
#     Color definitions
#     '''
#     WaterShallow =  rgb(1, 133, 209)
#     WaterDeep =     rgb(3, 119, 188)
#     WaterRiver =    rgb(0, 96, 152)


class Theme(object):
    def __init__(self):
        pass

class FullColorTheme(Theme):
    WaterShallow    = rgba(1, 133, 209)
    WaterDeep       = rgba(3, 119, 188)
    WaterRiver      = rgba(0, 96, 152)
    WaterShore      = rgba(0, 7, 12)
    
    @staticmethod
    def add_alpha(colors):
        return list( map(lambda c: (*c, 1.0), colors) )

    # def __init__(self, ctx):
    #     super().__init__()

    #     color_sealevel = colour.Color('green')
    #     color_peak = colour.Color('red')

    #     num_colors = 25

    #     self.gradient = list( color_sealevel.range_to(color_peak, num_colors) )
    #     self.ctx = ctx


class PrintTheme(Theme):
    WaterShallow    = rgba(1, 133, 209, 0.4)
    WaterDeep       = rgba(3, 119, 188, 0.4)
    WaterRiver      = rgba(0, 96, 152, 0.4)

    @staticmethod
    def add_alpha(colors):
        return list( map(lambda c: (*c, 0.4), colors) )

def render(world, cities=[], forests=[], poi_lib=None, rivers={}, names={}, opts=RenderOptions()):
    '''
    Renders world and all related entities to an image.
    '''
    def create_surface(fmt):
        if fmt == 'png':
            return cairo.ImageSurface(cairo.FORMAT_ARGB32, opts.scale_x, opts.scale_y)
        
        if fmt == 'svg':
            return cairo.SVGSurface(opts.filename, opts.scale_x, opts.scale_y)

        return Exception('Unknown image type requested: %s' % (fmt,))

    def close_surface(format, cairo_surface):
        if format == 'png':
            surface.write_to_png(opts.filename)
    
    themes = {
        'fullcolor': FullColorTheme,
        'print': PrintTheme,
    }

    theme = themes[opts.theme]
    output_fmt = opts.filename[-3:]

    with create_surface(output_fmt) as surface:
        ctx = cairo.Context(surface)
        ctx.scale(opts.scale_x, opts.scale_y)

        ctx.rectangle(0, 0, 1, 1)
        ctx.set_source_rgb(1.0, 1.0, 1.0)
        ctx.fill()

        if opts.theme == 'print':
            # world, cities=[], forests=[], poi_lib=None, rivers={}, names={}, opts=RenderOptions())
            render_print(ctx, world, cities, forests, poi_lib, rivers, names, opts)

            close_surface(output_fmt, surface)
            return

        ## Draw all land cells
        color_sealevel = colour.Color('green')
        color_peak = colour.Color('red')

        num_colors = 25

        gradient = theme.add_alpha( list( map(lambda c: c.rgb, color_sealevel.range_to(color_peak, num_colors)) ) )

        for cell in [c for c in world.cells if c.type == Cell.Type.LAND]:
            color_idx = math.floor( cell.elevation * len(gradient) )

            region = list( map(lambda pt: transform(pt), world.get_region(cell.region_idx)) )
            draw_region(ctx, region, gradient[color_idx])

        ## Draw rivers
        for r in rivers:
            for edge in r.graph.edges():
                src_pt = transform(world.get_cell(edge[0]).location)
                dest_pt = transform(world.get_cell(edge[1]).location)

                # 0,107,169
                draw_line_between(ctx, src_pt, dest_pt, theme.WaterRiver, 0.002)

        ## Draw forests
        for f in forests:
            for cell in f.cells:
                region = list( map(lambda pt: transform(pt), world.get_region(cell.region_idx)) )

                if random.random() < 0.33:
                    draw_tree(ctx, cell.location)

        ## Draw water
        def land(idx):
            return world.get_cell(idx).type == Cell.Type.LAND

        for cell in [c for c in world.cells if c.type == Cell.Type.WATER]:
            (_, dist) = world.graph.distance(cell.region_idx, land, max_distance=10)

            region = list( map(lambda pt: transform(pt), world.get_region(cell.region_idx)) )

            if dist < 4:
                draw_region(ctx, region, theme.WaterShallow)
            elif dist < 8 and random.random() < 0.5:
                draw_region(ctx, region, theme.WaterShallow)
            else:
                draw_region(ctx, region, theme.WaterDeep)

        ## Highlight points of interest
        if poi_lib is not None and opts.highlight_poi:
            colors = theme.add_alpha( [rgba(255, 255, 0), rgba(0, 255, 255), rgba(255, 0, 255), rgba(128, 0, 255)] )

            for poi_type in poi_lib.list_types():
                # For each point of interest....
                for poi in poi_lib.get_type(poi_type):
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

        close_surface(output_fmt, surface)

    ## Make some manual modifications to the svg file (if svg). Importantly this code is running
    ## outside of the `with` statement above to ensure the file's already been written to disk.
    if output_fmt == 'svg':
        ET.register_namespace('', 'http://www.w3.org/2000/svg')

        doc = ET.parse(opts.filename)

        # Remove width and height attributes that mess with web rendering
        doc.getroot().attrib.pop('width')
        doc.getroot().attrib.pop('height')

        # Add city hover regions
        for city in cities:
            city_el = ET.Element('circle')
            
            city_el.set('r', '20')
            city_el.set('cx', str(city.location[0] * opts.scale_x))
            city_el.set('cy', str(opts.scale_y - (city.location[1] * opts.scale_y)))

            city_el.set('class', 'city')
            city_el.set('details', '{ "name": "%s" }' % (names[city],))

            doc.getroot().append(city_el)

        if poi_lib:
            def map_region_pt(pt):
                x = str(transform(pt)[0] * opts.scale_x)
                y = str(transform(pt)[1] * opts.scale_y)

                return ','.join((x, y))

            for poi_type in poi_lib.list_types():
                # Create a SVG group for each POI.
                for poi in poi_lib.get_type(poi_type):
                    poi_group_el = ET.Element('g')
                    poi_group_el.set('class', str(poi_type).split('.')[1].lower())
                    poi_group_el.set('details',  '{ "name": "%s" }' % (names[poi],))
                    
                    # Add all cells to this <g>
                    for cell in poi.cells:
                        poi_el = ET.Element('polygon')

                        region = list( map(map_region_pt, world.get_region(cell.region_idx)) )
                        poi_el.set('points', ' '.join(region))

                        poi_group_el.append(poi_el)
                    
                    doc.getroot().append(poi_group_el)

        doc.write(opts.filename)


# world, cities=[], forests=[], poi_lib=None, rivers={}, names={}, opts=RenderOptions())
# def render_print(ctx, world, cities, forests, poi_lib, rivers, names, opts):
#     ## Draw landform outlines
#     ctx.set_line_cap(cairo.LINE_CAP_ROUND)
#     ctx.set_line_join(cairo.LINE_JOIN_ROUND)

#     for continent in world.continents:
#         outlines = continent.outline()

#         for outline in outlines:
#             start = transform(outline[0])
#             end = transform(outline[1])

#             draw_outline(ctx, start, end)


def simple_render(world, vd, opts):
    def create_surface(fmt):
        if fmt == 'png':
            return cairo.ImageSurface(cairo.FORMAT_ARGB32, opts.scale_x, opts.scale_y)
        
        if fmt == 'svg':
            return cairo.SVGSurface(opts.filename, opts.scale_x, opts.scale_y)

        return Exception('Unknown image type requested: %s' % (fmt,))

    def close_surface(format, cairo_surface):
        if format == 'png':
            surface.write_to_png(opts.filename)

    output_fmt = opts.filename[-3:]

    with create_surface(output_fmt) as surface:
        ctx = cairo.Context(surface)
        ctx.scale(opts.scale_x, opts.scale_y)

        ctx.rectangle(0, 0, 1, 1)
        ctx.set_source_rgb(1.0, 1.0, 1.0)
        ctx.fill()


        theme = FullColorTheme()

        color_sealevel = colour.Color('green')
        color_peak = colour.Color('brown')

        num_colors = 10

        gradient = theme.add_alpha( list( map(lambda c: c.rgb, color_sealevel.range_to(color_peak, num_colors)) ) )

        land_elevation_range = 1.0 - world.get_param('WaterlineHeight')

        # Draw land and water
        for idx in world.cell_idxs():
            region = list( map(lambda pt: transform(pt), vd.get_region(idx)) )

            if world.cp_celltype[idx] == Cell.Type.WATER:
                if world.cp_elevation[idx] < world.get_param('WaterlineHeight') / 2.0:
                    draw_region(ctx, region, FullColorTheme.WaterDeep)
                else:
                    draw_region(ctx, region, FullColorTheme.WaterShallow)

            else:
                # How far is this cell above sea level?
                distance_above_water = world.cp_elevation[idx] - world.get_param('WaterlineHeight')

                color_idx = math.floor( (distance_above_water / land_elevation_range) * len(gradient) )
                draw_region(ctx, region, gradient[color_idx])

        # Draw outlines
        for landform_id in [id for id in numpy.unique(world.cp_landform_id) if id != -1]:
            # Get all cells with the current landform_id
            cell_idxs = numpy.argwhere(world.cp_landform_id == landform_id)[:, 0]

            for outline in vd.outline(cell_idxs):
                start = transform(outline[0])
                end = transform(outline[1])

                draw_outline(ctx, start, end)

        # graph sample
        # for idx in random.choices(world.cell_idxs(), k=10):
        #     neighbors = world.graph.neighbors(idx)

        #     for n in neighbors:
        #         src = transform( (world.cp_latitude[idx], world.cp_longitude[idx]) )
        #         dest = transform( (world.cp_latitude[n], world.cp_longitude[n]) )

        #         draw_line_between(ctx, src, dest, (0, 0, 0, 1))

        close_surface(output_fmt, surface)