import enum, cairo, colour, math, random, json, functools, numpy, random

import xml.etree.ElementTree as ET
from PIL import Image
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
    
    @staticmethod
    def add_alpha(colors):
        return list( map(lambda c: (*c, 1.0), colors) )

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
            # theme.add_alpha( list( map(lambda c: c.rgb, c_desert_low.range_to(c_desert_hi, num_colors)) ) ),
            theme.add_alpha( list( map(lambda c: c.rgb, color_sealevel.range_to(color_peak, num_colors)) ) ),
            theme.add_alpha( list( map(lambda c: c.rgb, color_sealevel.range_to(color_peak, num_colors)) ) ),
        )

        # gradient = theme.add_alpha( list( map(lambda c: c.rgb, color_sealevel.range_to(color_peak, num_colors)) ) )

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

    # Biome('Tundra', t=(0.0, 0.2), m=(0.0, 0.4)),            # cold and dry. do not go here.
    # Biome('Boreal forest', t=(0.0, 0.3), m=(0.4, 1.0)),
    # Biome('Temperate grassland', t=(0.2, 0.6), m=(0.0, 0.3)),
    # Biome('Temperate forest', t=(0.2, 0.8), m=(0.3, 0.4)),
    # Biome('Temperate forest', t=(0.3, 0.8), m=(0.4, 1.0)),
    # Biome('Desert', t=(0.6, 1.0), m=(0.0, 0.3)),
    # Biome('Desert', t=(0.8, 1.0), m=(0.3, 0.4)),
    # Biome('Rainforest', t=(0.8, 1.0), m=(0.4, 1.0)),

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
    ctx.select_font_face('Avenir Next', 
        cairo.FONT_SLANT_NORMAL,
        cairo.FONT_WEIGHT_NORMAL
    )
    ctx.set_font_size(0.02)

    (x, y, width, height, dx, dy) = ctx.text_extents(text)

    return (width, height)

class Label(object):
    def __init__(self, anchor, dim, text):
        self.anchor = anchor    # The point the label is labeling
        self.dim = dim          # The size of the label
        self.text = text

        x, y = self.anchor
        w, h = self.dim

        self.pos = [
            (x + 0.02, y, w, h),
            (x - w - 0.02, y, w, h),

            (x + 0.02, y - (2 * h), w, h),
            (x - w - 0.02, y - (2 * h), w, h),
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

    ctx.select_font_face('Avenir Next', 
        cairo.FONT_SLANT_NORMAL,
        cairo.FONT_WEIGHT_NORMAL
    )
    ctx.set_font_size(0.02)

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