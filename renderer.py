import enum, cairo, colour, math, random, json, functools, numpy, random
from plugins.identify_poi import PointOfInterest

import xml.etree.ElementTree as ET
from PIL import Image
from scipy import interpolate
from scipy.spatial import distance
from world import Cell
from plugins.build_cities import City

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

def draw_outline(ctx, start_pt, end_pt, stroke=True):
    ctx.move_to(*start_pt)

    ctx.line_to(*end_pt)

    # ctx.set_source_rgb(0.0, 0.0, 0.0)
    ctx.set_source_rgba(*FullColorTheme.WaterShore)
    ctx.set_line_width(0.0015)
    ctx.set_line_join(cairo.LINE_JOIN_BEVEL)
    ctx.set_line_cap(cairo.LINE_CAP_ROUND)

    if stroke:
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

def draw_tree(ctx, top):
    tree_height = 0.015
    # top = transform(point)

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

class Theme(object):
    def __init__(self):
        pass

class FullColorTheme(Theme):
    WaterShallow    = rgba(1, 133, 209)
    WaterDeep       = rgba(1, 59, 94) #rgba(3, 119, 188)
    WaterRiver      = rgba(0, 96, 152)
    WaterShore      = rgba(0, 7, 12)

    CityFill        = rgba(255, 255, 255)
    CityBorder      = rgba(0, 0, 0)
    CityBorderWidth = 0.004
    CityRadius      = 0.01
    
    @staticmethod
    def add_alpha(colors):
        return list( map(lambda c: (*c, 1.0), colors) )

class PrintTheme(Theme):
    WaterOcean      = (0.72, 0.72, 0.72, 1.0)
    WaterRiver      = rgba(40, 40, 40)
    WaterShore      = rgba(0, 7, 12)

    CityFill        = rgba(210, 210, 210)
    CityBorder      = rgba(0, 0, 0)
    CityBorderWidth = 0.0035
    CityRadius      = 0.005

    @staticmethod
    def add_alpha(colors):
        return list( map(lambda c: (*c, 1.0), colors) )

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

        c_desert_low = colour.Color('#f5ffba')
        c_desert_hi = colour.Color('#666b4d')

        c_biomes = theme.add_alpha([
            colour.Color('#d4e4d3').rgb,
            colour.Color('#3a8381').rgb,
            colour.Color('#ffe07f').rgb,
            colour.Color('#228855').rgb,
            colour.Color('#228855').rgb,
            colour.Color('#f5ffba').rgb,
            colour.Color('#f5ffba').rgb,
            colour.Color('#534239').rgb,
        ])

        num_colors = 25

        gradients = (
            theme.add_alpha( list( map(lambda c: c.rgb, color_sealevel.range_to(color_peak, num_colors)) ) ),
            theme.add_alpha( list( map(lambda c: c.rgb, color_sealevel.range_to(color_peak, num_colors)) ) ),
            theme.add_alpha( list( map(lambda c: c.rgb, color_sealevel.range_to(color_peak, num_colors)) ) ),
            theme.add_alpha( list( map(lambda c: c.rgb, color_sealevel.range_to(color_peak, num_colors)) ) ),
            theme.add_alpha( list( map(lambda c: c.rgb, color_sealevel.range_to(color_peak, num_colors)) ) ),
            theme.add_alpha( list( map(lambda c: c.rgb, color_sealevel.range_to(color_peak, num_colors)) ) ),
            theme.add_alpha( list( map(lambda c: c.rgb, color_sealevel.range_to(color_peak, num_colors)) ) ),
            theme.add_alpha( list( map(lambda c: c.rgb, color_sealevel.range_to(color_peak, num_colors)) ) ),
        )

        land_elevation_range = 1.0 - world.get_param('WaterlineHeight')

        # Draw land
        for idx in numpy.argwhere(world.cp_celltype == Cell.Type.LAND)[:, 0]:
            biome_id = world.cp_biome[idx]
            region = list( map(lambda pt: transform(pt), vd.get_region(idx)) )

            # How far is this cell above sea level?
            distance_above_water = world.cp_elevation[idx] - world.get_param('WaterlineHeight')

            color_idx = math.floor( (distance_above_water / land_elevation_range) * len(gradients[biome_id]) )
            # Elevation-based color scheme
            draw_region(ctx, region, gradients[biome_id][color_idx])
            # Biome color scheme
            # draw_region(ctx, region, c_biomes[biome_id])

        # Draw entities (stage 1)
        for entity in world.entities():
            try:
                entity.render_stage1(ctx, world, vd, theme)
            except NotImplementedError:
                pass

        # Draw water
        water_color_shallow = colour.Color(rgb=theme.WaterShallow[:3])
        water_color_deep = colour.Color(rgb=theme.WaterDeep[:3])
        water_gradient = theme.add_alpha( [c.rgb for c in water_color_shallow.range_to(water_color_deep, 6)] )
        for idx in numpy.argwhere(world.cp_celltype == Cell.Type.WATER)[:, 0]:
            region = list( map(lambda pt: transform(pt), vd.get_region(idx)) )

            color_idx = math.floor( world.cp_depth[idx] / world.get_param('WaterlineHeight') * len(water_gradient) )
            draw_region(ctx, region, water_gradient[color_idx])

        # Draw outlines
        for landform_id in [id for id in numpy.unique(world.cp_landform_id) if id != -1]:
            # Get all cells with the current landform_id
            cell_idxs = numpy.argwhere(world.cp_landform_id == landform_id)[:, 0]

            for outline in vd.outline(cell_idxs):
                start = transform(outline[0])
                end = transform(outline[1])

                draw_outline(ctx, start, end)

        # Draw forests
        biome_density = (0.05, 0.1, 0.04, 0.10, 0.10, 0.02, 0.02, 0.15)
        for idx in numpy.argwhere(world.cp_celltype == Cell.Type.LAND)[:, 0]:
            density = biome_density[world.cp_biome[idx]]

            # Forests have a boosted chance of showing a tree.
            if world.cp_forest_id[idx] != -1 and random.random() > 0.3:
                pt = transform( (world.cp_longitude[idx], world.cp_latitude[idx]) )
                draw_tree(ctx, pt)

            elif random.random() < density and world.cp_elevation[idx] < 0.8:
                pt = transform( (world.cp_longitude[idx], world.cp_latitude[idx]) )
                draw_tree(ctx, pt)

        # Draw forests
        if hasattr(world, 'cp_forest_id'):
            for forest_id in [id for id in numpy.unique(world.cp_forest_id) if id != -1]:
                cell_idxs = numpy.argwhere(world.cp_forest_id == forest_id)[:, 0]

                for idx in cell_idxs:
                    pt = transform( (world.cp_longitude[idx], world.cp_latitude[idx]) )
                    draw_tree(ctx, pt)

        # Draw entities (stage 2)
        for entity in world.entities():
            try:
                entity.render_stage2(ctx, world, vd, theme)
            except NotImplementedError:
                pass
        
        print('   * Optimizing label placement...')
        labels = []
        for entity in world.entities():
            if isinstance(entity, City):
                x, y = world.cp_longitude[entity.cell_idx], world.cp_latitude[entity.cell_idx]
                w, h = label_dim(ctx, entity.name)

                labels.append( Label((x, y), (w, h), entity.name) )

        # Optimize label positions
        iter_count = 0
        conflicts = find_conflicts(labels)

        while len(conflicts) > 0 and iter_count < 100:
            # Shift one of the conflicting labels
            random.choice(conflicts).shift()

            conflicts = find_conflicts(labels)
            iter_count += 1

        # Render optimized labels
        for label in labels:
            top_left = transform( (label.position()[0], label.position()[1]) )
            render_text(ctx, top_left, label.text)

        # graph sample
        # for idx in random.choices(world.cell_idxs(), k=10):
        #     neighbors = world.graph.neighbors(idx)

        #     for n in neighbors:
        #         src = transform( (world.cp_latitude[idx], world.cp_longitude[idx]) )
        #         dest = transform( (world.cp_latitude[n], world.cp_longitude[n]) )

        #         draw_line_between(ctx, src, dest, (0, 0, 0, 1))

        close_surface(output_fmt, surface)

def label_dim(ctx, text):
    # ctx.select_font_face('Avenir Next', 
    #     cairo.FONT_SLANT_NORMAL,
    #     cairo.FONT_WEIGHT_NORMAL
    # )
    # ctx.set_font_size(0.02)

    ctx.select_font_face('Gill Sans', 
        cairo.FONT_SLANT_NORMAL,
        cairo.FONT_WEIGHT_NORMAL
    )
    ctx.set_font_size(0.014)

    (x, y, width, height, dx, dy) = ctx.text_extents(text)

    # Add padding for the white box
    return (width + 0.01, height + 0.02)

class Label(object):
    def __init__(self, anchor, dim, text):
        self.anchor = anchor    # The point the label is labeling
        self.dim = dim          # The size of the label
        self.text = text

        x, y = self.anchor
        w, h = self.dim

        x_pad = 0.01

        self.pos = [
            (x + x_pad, y, w, h),
            (x - w - x_pad, y, w, h),

            (x + x_pad, y - (2 * h), w, h),
            (x - w - x_pad, y - (2 * h), w, h),
        ]

        self.pos_idx = 0

    def position(self):
        return self.pos[self.pos_idx]

    def shift(self):
        self.pos_idx = (self.pos_idx + 1) % len(self.pos)

        return self.position()

def find_conflicts(labels):
    conflicts = set()

    for idx, first in enumerate(labels):
        # If this label hangs off the edge of the map, we need to rotate it.
        if is_offworld(first.position()):
            conflicts.add(first)

        # If two labels overlap, we need to rotate one of them.
        for second in labels[idx+1:]:
            if rectangles_conflict(first.position(), second.position()):
                conflicts.add(first)
                conflicts.add(second)

    return list(conflicts)

def is_offworld(rect):
    if rect[0] < 0:
        return True
    
    if rect[0] + rect[2] > 1.0:
        return True
    
    if rect[1] < 0:
        return True

    if rect[1] + rect[3] > 1.0:
        return True

    return False

def rectangles_conflict(r1, r2):
    # r1 is to the right of r2
    if r1[0] > r2[0] + r2[2]:
        return False
    
    # r1 is to the left of r2
    if r2[0] > r1[0] + r1[2]:
        return False
    
    if r1[1] > r2[1] + r2[3]:
        return False
    
    if r2[1] > r1[1] +r1[3]:
        return False

    return True 

def render_text(ctx, top_left, text, font_size=12):
    ctx.move_to(*top_left)

    ctx.select_font_face('Gill Sans', 
        cairo.FONT_SLANT_NORMAL,
        cairo.FONT_WEIGHT_NORMAL
    )
    ctx.set_font_size(0.014)

    (x, y, width, height, dx, dy) = ctx.text_extents(text)

    ctx.set_source_rgba(1, 1, 1, 0.6)
    ctx.rectangle(
        top_left[0] - 0.005, top_left[1] - height - 0.005, 
        width + 0.01, height + 0.01
    )
    ctx.fill()

    ctx.move_to(*top_left)
    ctx.set_source_rgb(0, 0, 0)
    ctx.show_text(text)


def heatmap(world, vd, opts, base_img_path, cellfunc):
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

        color_cold = colour.Color('blue')
        color_hot = colour.Color('red')

        num_colors = 25
        gradient = FullColorTheme.add_alpha( list( map(lambda c: c.rgb, color_cold.range_to(color_hot, num_colors)) ) )
        gradient = [ (c[0], c[1], c[2], 0.5) for c in gradient ] # heatmap layers should be somewhat transparent (to overlay)

        for idx in world.cell_idxs():
            magnitude = cellfunc(idx)

            color_idx = math.floor( magnitude * len(gradient) )
            region = list( map(lambda pt: transform(pt), vd.get_region(idx)) )

            draw_region(ctx, region, gradient[color_idx])

        close_surface(output_fmt, surface)

    base_img = Image.open(base_img_path).convert('RGBA')
    overlay_img = Image.open(opts.filename).convert('RGBA')

    base_img.paste(overlay_img, (0,0), overlay_img)
    base_img.save(opts.filename, 'png')


def inter(vals):
    x_axis = list( range(0, len(vals)) )

    f = interpolate.interp1d(x_axis, vals, kind='quadratic')
    x_axis_new = numpy.arange(0, len(vals) - 1, 0.5)

    return x_axis_new, f(x_axis_new)

def render_tree(ctx, top):
    tree_height = 0.012
    trunk_height = 0.003

    top = (top[0], top[1] - tree_height)
    
    bottom_left = (top[0] - (tree_height / 3.5), 1 - (top[1] + tree_height))
    bottom_right = (top[0] + (tree_height / 3.5), 1 - (top[1] + tree_height))
    bottom_center = (top[0], 1 - (top[1] + tree_height))
    bottom_trunk = (top[0], 1 - (top[1] + tree_height + trunk_height))

    # Draw trunk
    # ctx.set_source_rgba(*rgba(0, 0, 0, 1))
    ctx.set_source_rgba(*rgba(60, 60, 60, 0.6))
    ctx.set_line_width(0.002)

    ctx.move_to(*transform(bottom_center))
    ctx.line_to(*transform(bottom_trunk))
    ctx.stroke()

    # Draw outline of tree

    ctx.move_to(*top)
    ctx.line_to(*transform(bottom_left))
    ctx.line_to(*transform(bottom_right))
    ctx.close_path()

    # Fill in white background
    ctx.set_source_rgba(1, 1, 1, 1)
    ctx.fill_preserve()

    # Draw border
    ctx.set_source_rgba(*rgba(60, 60, 60, 0.6))
    ctx.set_line_width(0.002)
    ctx.stroke_preserve()

    # Fill tree
    ctx.set_source_rgba(*rgba(220, 220, 220, 0.8))
    ctx.fill()

def render_hill(ctx, point):
    hill_width = 0.004

    transformed = transform(point)

    ctx.arc(transformed[0] - (hill_width / 2), transformed[1], hill_width, math.pi, math.pi * 2)

    # Fill in white background
    ctx.set_source_rgba(1, 1, 1, 1)
    ctx.fill_preserve()

    # Draw border
    ctx.set_source_rgba(*rgba(60, 60, 60, 0.6))
    ctx.stroke_preserve()

    # Draw final fill color
    ctx.set_source_rgba(*rgba(60, 60, 60, 0.20))
    ctx.fill()

def render_landform(ctx, outline_x, outline_y):
    start_pt = transform( (outline_x[0], outline_y[0]) )

    ctx.move_to(*start_pt)

    for idx in range(1, len(outline_x)):
        next_loc = transform( (outline_x[idx], outline_y[idx]) )

        ctx.line_to(*next_loc)

    ctx.close_path()

def add_water_shading(ctx, world, vd, theme):
    '''
    Add horizontal lines to mark shores. This needs to be done prior to drawing
    landforms.
    '''
    n_lines = 160

    ctx.push_group()

    for i in range(n_lines):
        ctx.move_to(0, i * (1 / n_lines))
        ctx.line_to(1, i * (1 / n_lines))

    ctx.set_line_width(0.001)
    ctx.set_source_rgba(0, 0, 0, 1)

    ctx.stroke()

    for cell_idx in numpy.argwhere(world.cp_celltype == Cell.Type.WATER)[:, 0]:
        # All cells beyond a configured radius get cleared
        (_, dist) = world.graph.distance(cell_idx, lambda idx: world.cp_celltype[idx] == Cell.Type.LAND)

        if dist > world.std_density(1.2):
            region = list( map(lambda pt: transform(pt), vd.get_region(cell_idx)) )

            draw_region(ctx, region, theme.WaterOcean)

    ctx.set_operator(cairo.OPERATOR_CLEAR)
    ctx.fill()

    ctx.pop_group_to_source()
    ctx.paint()

def print_render(world, vd, opts):
    def create_surface(fmt):
        if fmt == 'svg':
            return cairo.SVGSurface(opts.filename, opts.scale_x, opts.scale_y)

        if fmt == 'png':
            return cairo.ImageSurface(cairo.FORMAT_ARGB32, opts.scale_x, opts.scale_y)

        return Exception('Unknown image type requested: %s' % (fmt,))

    def close_surface(format, cairo_surface):
        if format == 'png':
            surface.write_to_png(opts.filename)

    output_fmt = opts.filename[-3:]

    with create_surface(output_fmt) as surface:
        ctx = cairo.Context(surface)
        ctx.scale(opts.scale_x, opts.scale_y)

        theme = PrintTheme()

        ctx.rectangle(0, 0, 1, 1)
        ctx.set_source_rgba(*theme.WaterOcean)
        ctx.fill()

        add_water_shading(ctx, world, vd, theme)

        # Draw landforms, including lakes
        for landform_id in [id for id in numpy.unique(world.cp_landform_id) if id != -1]:
            # Get all cells with the current landform_id
            cell_idxs = numpy.argwhere(world.cp_landform_id == landform_id)[:, 0]

            for polygon in vd.outline_polygons(cell_idxs):
                outline_x = []
                outline_y = []

                for segment in polygon:
                    outline_x.append(segment[0][0])
                    outline_y.append(segment[0][1])

                outline_x.append(outline_x[0])
                outline_y.append(outline_y[0])

                _, outline_x = inter(outline_x)
                _, outline_y = inter(outline_y)

                render_landform(ctx, outline_x, outline_y)

            # Render background
            ctx.set_source_rgba(1, 1, 1, 1)
            ctx.set_fill_rule(cairo.FILL_RULE_EVEN_ODD)
            landform_path = ctx.copy_path()
            ctx.fill_preserve()

            # Render elevation shading
            ctx.save()
            ctx.clip()

            color_sealevel = colour.Color('#fff')
            color_peak = colour.Color('#aaa')
            num_colors = 10
            gradient = theme.add_alpha( list( map(lambda c: c.rgb, color_sealevel.range_to(color_peak, num_colors)) ) )

            waterline_range = 1.0 - world.get_param('WaterlineHeight')
            for cell_idx in cell_idxs:
                region = list( map(lambda pt: transform(pt), vd.get_region(cell_idx)) )

                color_pct = (world.cp_elevation[cell_idx] - world.get_param('WaterlineHeight')) / waterline_range
                color_idx = math.floor(num_colors * color_pct)

                if color_idx != 0:
                    color = gradient[color_idx]
                    draw_region(ctx, region, color)

            ctx.restore()

            # Render border
            ctx.append_path(landform_path)
            ctx.set_source_rgba(*PrintTheme.WaterShore)
            ctx.set_line_width(0.0015)
            ctx.set_line_join(cairo.LINE_JOIN_BEVEL)
            ctx.set_line_cap(cairo.LINE_CAP_ROUND)

            ctx.stroke()

        # Draw entities (stage 1)
        for entity in world.entities():        
            try:
                entity.render_stage1(ctx, world, vd, theme)
            except NotImplementedError:
                pass

        # Draw land iconography
        idx_latsort = sorted(
            numpy.argwhere(world.cp_celltype == Cell.Type.LAND)[:, 0], 
            key=lambda idx: world.cp_latitude[idx], 
            reverse=True,
        )

        def between(val, lower, upper):
            return val >= lower and val <= upper

        for idx in idx_latsort:
            if world.cp_forest_id[idx] != -1 and random.random() < 2.0 / world.std_density(2):
                pt = transform( (world.cp_longitude[idx], world.cp_latitude[idx]) )
                render_tree(ctx, pt)
            
            elif between( world.cp_elevation[idx], 0.6, 0.75 ) and random.random() < 1.0 / world.std_density(2):
                render_hill(ctx, (world.cp_longitude[idx], world.cp_latitude[idx]))

        # Draw entities (stage 2)
        for entity in world.entities():
            try:
                entity.render_stage2(ctx, world, vd, theme)
            except NotImplementedError:
                pass
                
        # Place labels
        labels = []
        for entity in world.entities():
            # TODO: remove once we want to render mountain labels (once they're being rendered)
            if isinstance(entity, City) or (isinstance(entity, PointOfInterest) and entity.type == PointOfInterest.Type.LAKE):
                if hasattr(entity, 'cell_idx') and hasattr(entity, 'name'):
                    x, y = world.cp_longitude[entity.cell_idx], world.cp_latitude[entity.cell_idx]
                    w, h = label_dim(ctx, entity.name)

                    labels.append( Label((x, y), (w, h), entity.name) )

        # Optimize label positions
        iter_count = 0
        conflicts = find_conflicts(labels)

        while len(conflicts) > 0 and iter_count < 100:
            # Shift one of the conflicting labels
            random.choice(conflicts).shift()

            conflicts = find_conflicts(labels)
            iter_count += 1

        # Render optimized labels
        for label in labels:
            top_left = transform( (label.position()[0], label.position()[1]) )
            render_text(ctx, top_left, label.text)

        close_surface(output_fmt, surface)