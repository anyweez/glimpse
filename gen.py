import random, structs, numpy, datetime, sys, multiprocessing, pprint, pkgutil
import voronoi, civilization, graph, renderer, poi, cultures, river
# import languages

import plugins

seed = round( datetime.datetime.now().timestamp() * 10000 )
random.seed(seed)

# Configuration variables
PointCount = 3500
NumCities = 8
NumWorlds = 1
NumForests = 14

def generate(world_idx, language_list):
    def point_cloud(n):
        return [(random.random(), random.random()) for _ in range(n)]

    # def initialize_plugins(world, stack):
    #     pass

    def generate_world(world, vd, stack):
        for plugin in stack:
            plugin.generate(world, vd)

    # def render_world(world, stack):
    #     pass

    # From https://packaging.python.org/guides/creating-and-discovering-plugins/#using-namespace-packages
    # p = pkgutil.iter_modules(plugins.__path__, plugins.__name__ + '.')
    # for pl in p:
    #     print(pl)

    points = numpy.array(point_cloud(PointCount))
    vor = voronoi.generate(points)

    cell_idxs = [idx for idx in range(PointCount)]
    cell_mapping = {}
    for cell_idx, v_idx in enumerate( sorted(vor.point_region) ):
        cell_mapping[cell_idx] = v_idx

    worldgraph = graph.BuildGraph(cell_idxs, vor, cell_mapping)

    world = structs.World(cell_idxs, vor, worldgraph)
    vd = structs.VoronoiDiagram(vor, cell_mapping)

    ###
    gen_stack = [
        plugins.init_cells,
        plugins.tectonics,
        plugins.terrain,
        plugins.form_lakes,
        plugins.forest,
        plugins.mark_landforms,
        plugins.form_rivers,
    ]

    render_stack = []
    
    # Initialize all plugins
    # initialize_plugins(world, gen_stack)
    # Generate the world
    generate_world(world, vd, gen_stack)

    # print( 'World params: %s' % (str(world.__worldparams)) )

    # Render the world
    # render_world(world, render_stack)

    ###

    print('  [%s] Generating world #%d...' % (world.id, world_idx + 1))

    # world.build()

    print('  [%s] Establishing civilization...' % (world.id,))

    # Eventually we can represent multiple cultures; for now this is a single world-wide culture.
    # english = [lang for lang in language_list if lang.name == 'english'][0]
    # first_culture = cultures.HumanCulture(world.cells, world.vor, world.graph, english)
 
    # cities = []
    # for _ in range(NumCities):
    #     city = civilization.PlaceCity(world, first_culture, cities)

    #     cities.append(city)
    
    # print('  [%s] Growing forests...' % (world.id,))

    # forests = []
    # for _ in range(NumForests):
    #     f = forest.PlaceForest(world, forests)

    #     forests.append(f)

    ## Generate rivers
    # print('  [%s] Forming rivers...' % (world.id,))
    # rivers = river.FormRivers(world)

    ## Find points of interest
    # print('  [%s] Identifying points of interest...' % (world.id,))
    # poi_lib = poi.DetectAll(world)

    ## Generate names
    # names = {}

    # for city in cities:
    #     names[city] = first_culture.name_place(city)

    # for poi_type in poi_lib.list_types():
    #     for poi_inst in poi_lib.get_type(poi_type):
    #         names[poi_inst] = first_culture.name_place(poi_inst)

    # pprint.pprint(names)

    ## Render
    print('  [%s] Rendering world...' % (world.id,))

    # Render 'clean' map without POIs
    render_opts = renderer.RenderOptions()
    render_opts.filename = 'plugin-test.png'
    # render_opts.filename = 'world-%s.png' % (world.id,)

    renderer.simple_render(world, vd, render_opts)

    # renderer.render(
    #     world, 
    #     cities=cities, 
    #     forests=forests,
    #     rivers=rivers,
    #     opts=render_opts,
    # )

    # Render map with POIs highlighted
    # render_opts_poi = renderer.RenderOptions()
    # render_opts_poi.filename = 'world-%s_poi.png' % (world.id,)
    # render_opts_poi.highlight_poi = True

    # renderer.render(
    #     world, 
    #     cities=cities, 
    #     forests=forests,
    #     rivers=rivers,
    #     poi_lib=poi_lib,
    #     opts=render_opts_poi,
    # )

    # Render map with print theme
    # render_opts_print = renderer.RenderOptions()
    # render_opts_print.filename = 'world_print.png' # % (world.id,)
    # render_opts_print.theme = 'print'

    # renderer.render(
    #     world, 
    #     cities=cities, 
    #     forests=forests,
    #     rivers=rivers,
    #     opts=render_opts_print,
    # )

    # Render SVG
    # render_opts_svg = renderer.RenderOptions()
    # render_opts_svg.filename = 'gallery/maps/world-%s.svg' % (world.id,)

    # renderer.render(
    #     world, 
    #     cities=cities, 
    #     forests=forests,
    #     rivers=rivers,
    #     names=names,
    #     poi_lib=poi_lib,
    #     opts=render_opts_svg,
    # )

if __name__ == '__main__':
    print('seed=%d, num_points=%d' % (seed, PointCount))
    if len(sys.argv) > 1:
        NumWorlds = int(sys.argv[1])

    print('')

    print('Building language models...')
    # langs = languages.load()

    # for lang in langs:
    #     print('  Language "%s" examples: %s' % (lang.name, [lang.generate_name() for _ in range(8)]))
    langs = None

    print('Generating %d world(s)...' % (NumWorlds,))
    for idx in range(NumWorlds):
        generate(idx, langs)