from renderer.hill import draw_hill
from renderer.mountain import draw_mountain
from shapely.geometry import Point, Polygon, LineString
from shapely import affinity, ops
from sqlalchemy import create_engine
from osgeo import gdal, osr

# import matplotlib.pyplot as plt

import enum, cairo, colour, math, random, numpy, random, geopandas
from plugins.identify_poi import PointOfInterest

from scipy import interpolate
from world import Cell
from plugins.build_cities import City
from plugins.mark_biome import biomes

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
    def __init__(self, anchor, dim, text, font_scale):
        self.anchor = anchor    # The point the label is labeling
        self.dim = dim          # The size of the label
        self.text = text
        self.font_scale = font_scale

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

def render_text(ctx, top_left, text, font_scale=1.0):
    ctx.move_to(*top_left)

    ctx.select_font_face(PrintTheme.LabelFont, 
        cairo.FONT_SLANT_NORMAL,
        cairo.FONT_WEIGHT_NORMAL
    )
    ctx.set_font_size(PrintTheme.LabelFontSize * font_scale)

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
    '''
    Interpolate the corner points into a smoother line.
    '''
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

        if dist > world.std_density(0.6):
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

                    font_scale = 1.0

                    if isinstance(entity, City):
                        font_scale -= ((entity.MaxSize - entity.size()) / entity.MaxSize) * 0.3

                    labels.append( Label((x, y), (w, h), entity.name, font_scale) )

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
            render_text(ctx, top_left, label.text, label.font_scale)

        close_surface(output_fmt, surface)

GIS_CRS = 'EPSG:4326'

def proj_x(base_x):
    return (base_x * 360.0) - 180

def proj_y(base_y):
    return (base_y * 180.0) - 90.0

# def elevation_map(world, vd):
#     '''
#     Generate a GeoTIFF elevation map (`resolution` x `resolution`) based on the
#     elevation of the closest cell.

#     '''
#     resolution = int( math.sqrt(world.get_cellcount()) ) * 2

#     elevation = numpy.zeros((resolution, resolution), dtype=numpy.float)
#     dx = 1.0 / resolution   # divide full width by resolution
#     dy = 1.0 / resolution   # divide full height by resolution

#     for y_idx in range(resolution):
#         for x_idx in range(resolution):
#             x = dx * x_idx
#             y = dy * y_idx

#             cell_idx = vd.find_cell(x, y)
#             elevation[y_idx, x_idx] = 7000 * world.cp_elevation[cell_idx] # int( world.cp_elevation[cell_idx] * 255 )

#     img = gdal.GetDriverByName('GTiff').Create('world.tiff', resolution, resolution, 1, gdal.GDT_Float32)
#     img.SetGeoTransform( (-180, 360.0 / resolution, 0, 90, 0, -1 * 180.0 / resolution) )

#     srs = osr.SpatialReference()
#     srs.ImportFromEPSG(4326)

#     img.SetProjection(srs.ExportToWkt())
#     img.GetRasterBand(1).WriteArray(elevation)
#     img.FlushCache()    # write image to disk

# FROM https://towardsdatascience.com/around-the-world-in-80-lines-crossing-the-antimeridian-with-python-and-shapely-c87c9b6e1513
import math
import copy
import json
from typing import Union, List
from shapely.geometry import Polygon, LineString, GeometryCollection
from shapely.ops import split

from typing import Union, List
from shapely.geometry import mapping, Polygon, GeometryCollection
from shapely import affinity

def check_crossing(lon1: float, lon2: float, validate: bool = True):
    """
    Assuming a minimum travel distance between two provided longitude coordinates,
    checks if the 180th meridian (antimeridian) is crossed.
    """
    if validate and any(abs(x) > 180.0 for x in [lon1, lon2]):
        raise ValueError("longitudes must be in degrees [-180.0, 180.0]")   
    return abs(lon2 - lon1) > 180.0

def translate_polygons(geometry_collection: GeometryCollection, 
                       output_format: str = "geojson") -> Union[List[dict], List[Polygon]]:
    
  for polygon in geometry_collection:
      (minx, _, maxx, _) = polygon.bounds
      if minx < -180: geo_polygon = affinity.translate(polygon, xoff = 360)
      elif maxx > 180: geo_polygon = affinity.translate(polygon, xoff = -360)
      else: geo_polygon = polygon

      yield json.dumps(mapping(geo_polygon)) if (output_format == "geojson") else geo_polygon


# https://gist.github.com/PawaritL/ec7136c0b718ca65db6df1c33fd1bb11
# from geopolygon_utils import check_crossing, translate_polygons

def split_polygon(poly: Polygon, output_format: str = "geojson") -> Union[
    List[dict], List[Polygon], GeometryCollection
    ]:
    """
    Given a GeoJSON representation of a Polygon, returns a collection of
    'antimeridian-safe' constituent polygons split at the 180th meridian, 
    ensuring compliance with GeoJSON standards (https://tools.ietf.org/html/rfc7946#section-3.1.9)
    Assumptions:
      - Any two consecutive points with over 180 degrees difference in
        longitude are assumed to cross the antimeridian
      - The polygon spans less than 360 degrees in longitude (i.e. does not wrap around the globe)
      - However, the polygon may cross the antimeridian on multiple occasions
    Parameters:
        geojson (dict): GeoJSON of input polygon to be split. For example:
                        {
                        "type": "Polygon",
                        "coordinates": [
                          [
                            [179.0, 0.0], [-179.0, 0.0], [-179.0, 1.0],
                            [179.0, 1.0], [179.0, 0.0]
                          ]
                        ]
                        }
        output_format (str): Available options: "geojson", "polygons", "geometrycollection"
                             If "geometrycollection" returns a Shapely GeometryCollection.
                             Otherwise, returns a list of either GeoJSONs or Shapely Polygons
      
    Returns:
        List[dict]/List[Polygon]/GeometryCollection: antimeridian-safe polygon(s)
    """
    orig_coords = [ list(map(lambda pt: [pt[0], pt[1]], poly.exterior.coords)), ]

    output_format = output_format.replace("-", "").strip().lower()
    coords_shift = copy.deepcopy( orig_coords )
    shell_minx = shell_maxx = None
    split_meridians = set()
    splitter = None

    for ring_index, ring in enumerate(coords_shift):
        if len(ring) < 1: 
            continue
        else:
            ring_minx = ring_maxx = ring[0][0]
            crossings = 0

        for coord_index, (lon, _) in enumerate(ring[1:], start=1):
            lon_prev = ring[coord_index - 1][0]
            if check_crossing(lon, lon_prev, validate=False):
                direction = math.copysign(1, lon - lon_prev)
                coords_shift[ring_index][coord_index][0] = lon - (direction * 360.0)
                crossings += 1

            x_shift = coords_shift[ring_index][coord_index][0]
            if x_shift < ring_minx: ring_minx = x_shift
            if x_shift > ring_maxx: ring_maxx = x_shift

        # Ensure that any holes remain contained within the (translated) outer shell
        if (ring_index == 0): # by GeoJSON definition, first ring is the outer shell
            shell_minx, shell_maxx = (ring_minx, ring_maxx)
        elif (ring_minx < shell_minx):
            ring_shift = [[x + 360, y] for (x, y) in coords_shift[ring_index]]
            coords_shift[ring_index] = ring_shift
            ring_minx, ring_maxx = (x + 360 for x in (ring_minx, ring_maxx))
        elif (ring_maxx > shell_maxx):
            ring_shift = [[x - 360, y] for (x, y) in coords_shift[ring_index]]
            coords_shift[ring_index] = ring_shift
            ring_minx, ring_maxx = (x - 360 for x in (ring_minx, ring_maxx))

        if crossings: # keep track of meridians to split on
            if ring_minx < -180: split_meridians.add(-180)
            if ring_maxx > 180: split_meridians.add(180)

    n_splits = len(split_meridians)
    if n_splits > 1:
        raise NotImplementedError(
            """Splitting a Polygon by multiple meridians (MultiLineString) 
               not supported by Shapely"""
        )
    elif n_splits == 1:
        split_lon = next(iter(split_meridians))
        meridian = [[split_lon, -90.0], [split_lon, 90.0]]
        splitter = LineString(meridian)

    shell, *holes = coords_shift if splitter else orig_coords
    if splitter: split_polygons = split(Polygon(shell, holes), splitter)
    else: split_polygons = GeometryCollection([Polygon(shell, holes)])
        
    geo_polygons = list(translate_polygons(split_polygons, output_format))  
    if output_format == "geometrycollection": return GeometryCollection(geo_polygons)
    else: return geo_polygons

#########

_SPLITSTRING = LineString([ Point(0, 90), Point(0, -90) ])

def geo(world, vd, opts):
    polygons = []

    # for cell_idx in [i for i in world.cell_idxs() if world.cp_celltype[i] == Cell.Type.LAND]:
    #     outline_x = []
    #     outline_y = []

    #     for (latitude, longitude) in vd.get_region(cell_idx):
    #         outline_x.append(longitude)
    #         outline_y.append(latitude)
        
    #     geometry = geopandas.points_from_xy(x=outline_x, y=outline_y)
    #     polygon = Polygon(geometry)

    #     # Check to see if this polygon crosses the anti-meridian. If it does, we need to split it
    #     # into two polygons (one for each side), otherwise Shapely and PostGIS will assume we want
    #     # to connect the far west coords to the far right coords vs just crossing the antimeridian.
    #     split_polys = split_polygon(polygon, 'polygons')

    #     for poly in split_polys:
    #         polygons.append(poly)

    # Calculate polygons for each landform
    for landform_id in [id for id in numpy.unique(world.cp_landform_id) if id != -1]:
        # Get all cells with the current landform_id
        cell_idxs = numpy.argwhere(world.cp_landform_id == landform_id)[:, 0]

        print('landform_size={}'.format( len(cell_idxs) ))

        # outline_x = [] 
        # outline_y = []

        for cell_idx in cell_idxs:
            outline_x = [] 
            outline_y = []

            for (latitude, longitude) in vd.get_region(cell_idx):
                outline_x.append(longitude)
                outline_y.append(latitude)
            
            geometry = geopandas.points_from_xy(x=outline_x, y=outline_y)
            polygon = Polygon(geometry)

            split_polys = split_polygon(polygon, 'polygons')
            for poly in split_polys:
                polygons.append(poly)

        # break

        # Each landform should be a single polygon. Iterate over the coordinates in order.
        # for (x, y) in vd.outline_polygon(cell_idxs):
        #     outline_x.append(x)
        #     outline_y.append(y)

        # geometry = geopandas.points_from_xy(x=outline_x, y=outline_y)
        # polygon = Polygon(geometry)

        # split_polys = split_polygon(polygon, 'polygons')
        # for poly in split_polys:
        #     polygons.append(poly)

        # break

        # polygons.append(Polygon(geometry))

        # for polygon in vd.outline_polygons(cell_idxs):
        #     outline_x = []
        #     outline_y = []

        #     print(polygon)

        #     for segment in polygon:
        #         outline_x.append(segment[0][0])
        #         outline_y.append(segment[0][1])

        #     outline_x.append(outline_x[0])
        #     outline_y.append(outline_y[0])

        #     # _, outline_x = inter(outline_x)
        #     # _, outline_y = inter(outline_y)
    
        #     # Naive scale to lat/long
        #     outline_x = [proj_x(x) for x in outline_x]
        #     outline_y = [proj_y(y) for y in outline_y]

        #     geometry = geopandas.points_from_xy(x=outline_x, y=outline_y)
        #     polygons.append(Polygon(geometry))

    # Prep PostGIS for continents
    engine = create_engine('postgres://localhost:5432/glimpse')
    engine.execute('drop table if exists continents')
    engine.execute('drop table if exists lakes')

    for polygon in polygons:
        series = geopandas.GeoSeries(polygon, crs=GIS_CRS)
        gdf = geopandas.GeoDataFrame(geometry=series, crs=GIS_CRS)

        # Check if `polygon` is a continent or lake; the polygon is a lake if its
        # fully contained within another polygon.
        # TODO: can we use existing entities to identify lakes instead of re-deriving?
        is_continent = True
        # for target in [p for p in polygons if p != polygon]:
        #     if target.contains(polygon):
        #         is_continent = False # lake, not continent

        
        # if abs( polygon.bounds[0] - polygon.bounds[2] ) > 180.0:
        #     gdf['name'] = 'Lake'
        #     gdf.to_postgis(name='lakes', con=engine, if_exists='append')
        # else:
        #     gdf['name'] = 'abc-{}'.format(random.randint(1000, 10000))
        #     gdf.to_postgis(name='continents', con=engine, if_exists='append')

        if is_continent:
            gdf['name'] = 'abc-{}'.format(random.randint(1000, 10000))
            gdf.to_postgis(name='continents', con=engine, if_exists='append')
        else:
            gdf['name'] = 'Lake'
            gdf.to_postgis(name='lakes', con=engine, if_exists='append')

    return

    # Prep PostGIS for cities
    engine.execute('drop table if exists cities')

    for entity in [e for e in world.entities() if isinstance(e, City)]:
        city_loc = Point(
            proj_x( world.cp_longitude[entity.cell_idx] ), 
            proj_y( world.cp_latitude[entity.cell_idx] ),
        )

        series = geopandas.GeoSeries(city_loc, crs=GIS_CRS)
        gdf = geopandas.GeoDataFrame(geometry=series, crs=GIS_CRS)
        gdf['name'] = entity.name
        gdf['pop_size'] = entity.size()

        gdf.to_postgis(name='cities', con=engine, if_exists='append')

    # Prep PostGIS for biomes
    engine.execute('drop table if exists biomes')

    for cell_idx in [idx for idx in world.cell_idxs() if world.cp_celltype[idx] == Cell.Type.LAND]:
        region = [ (proj_x(x), proj_y(y)) for (x, y) in vd.get_region(cell_idx) ]

        # vd.get_region() returns an empty list if the cell is out of bounds
        if len(region) > 0:
            biome = biomes[world.cp_biome[cell_idx]].name

            polygon = Polygon(region)
            series = geopandas.GeoSeries(polygon, crs=GIS_CRS)
            gdf = geopandas.GeoDataFrame(geometry=series, crs=GIS_CRS)
            gdf['biome'] = biome

            gdf.to_postgis(name='biomes', con=engine, if_exists='append')


    # elevation_map(world, vd)
    # print('Wrote elevation map to world.tiff')