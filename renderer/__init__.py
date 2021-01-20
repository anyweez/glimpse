from renderer.hill import draw_hill
from renderer.mountain import draw_mountain

import enum, cairo, colour, math, random, numpy, random
from plugins.identify_poi import PointOfInterest

# import xml.etree.ElementTree as ET
# from PIL import Image
from scipy import interpolate
# from scipy.spatial import distance
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

    LabelFont       = 'Optima'
    LabelFontSize   = 0.014

    @staticmethod
    def add_alpha(colors):
        return list( map(lambda c: (*c, 1.0), colors) )

def label_dim(ctx, text):
    ctx.select_font_face(PrintTheme.LabelFont, 
        cairo.FONT_SLANT_NORMAL,
        cairo.FONT_WEIGHT_NORMAL
    )
    ctx.set_font_size(PrintTheme.LabelFontSize)

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

    ctx.select_font_face(PrintTheme.LabelFont, 
        cairo.FONT_SLANT_NORMAL,
        cairo.FONT_WEIGHT_NORMAL
    )
    ctx.set_font_size(PrintTheme.LabelFontSize)

    (x, y, width, height, dx, dy) = ctx.text_extents(text)

    ctx.set_source_rgba(1, 1, 1, 0.8)
    ctx.rectangle(
        top_left[0] - 0.005, top_left[1] - height - 0.005, 
        width + 0.01, height + 0.01
    )
    ctx.fill()

    ctx.move_to(*top_left)
    ctx.set_source_rgb(0, 0, 0)
    ctx.show_text(text)

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

        print('   * [1 / X] Adding water shading...')
        add_water_shading(ctx, world, vd, theme)

        cell_colors = {} # idx => color

        # Draw landforms, including lakes
        print('   * [2 / X] Drawing landforms...')
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

            def cell_color(idx):
                color_pct = (world.cp_elevation[idx] - world.get_param('WaterlineHeight')) / waterline_range
                color_idx = math.floor(num_colors * color_pct)

                return gradient[color_idx]

            for cell_idx in cell_idxs:
                region = list( map(lambda pt: transform(pt), vd.get_region(cell_idx)) )

                # color_pct = (world.cp_elevation[cell_idx] - world.get_param('WaterlineHeight')) / waterline_range
                # color_idx = math.floor(num_colors * color_pct)

                cell_colors[cell_idx] = cell_color(cell_idx)

                if cell_colors[cell_idx] != gradient[0]:
                    # color = gradient[color_idx]
                    draw_region(ctx, region, cell_colors[cell_idx])

            ctx.restore()

            # Render border
            ctx.append_path(landform_path)
            ctx.set_source_rgba(*PrintTheme.WaterShore)
            ctx.set_line_width(0.0015)
            ctx.set_line_join(cairo.LINE_JOIN_BEVEL)
            ctx.set_line_cap(cairo.LINE_CAP_ROUND)

            ctx.stroke()

        # Draw entities (stage 1)
        print('   * [3 / X] Rendering iconography...')
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
            
            elif between( world.cp_elevation[idx], 0.6, 0.75 ) and random.random() < 1.0 / world.std_density(3):
                # render_hill(ctx, (world.cp_longitude[idx], world.cp_latitude[idx]))

                pos = transform((world.cp_longitude[idx], world.cp_latitude[idx]))

                draw_hill(ctx, pos, {
                    'fill_color': cell_colors[idx],
                })

            elif between( world.cp_elevation[idx], world.get_param('MountainMinHeight'), 1.0 ) and random.random() < 1.0 / world.std_density(2):
                # Don't render hills near water
                _, distance = world.graph.distance(
                    idx,
                    lambda d_idx: world.cp_celltype[d_idx] == Cell.Type.WATER, 
                    max_distance=4,
                )

                if distance > 3:
                    pos = transform((world.cp_longitude[idx], world.cp_latitude[idx]))

                    ctx.save()
                    draw_mountain(ctx, pos, {
                        'fill_color': (0.90, 0.90, 0.90),
                        'width': 0.03,
                    })
                    ctx.restore()

        # Draw entities (stage 2)
        for entity in world.entities():
            try:
                entity.render_stage2(ctx, world, vd, theme)
            except NotImplementedError:
                pass
                
        # Place labels
        print('   * [4 / X] Placing labels...')
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