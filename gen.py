import random, world, numpy, datetime, sys, multiprocessing, pprint, pkgutil, importlib, time
import voronoi, civilization, graph, renderer, poi, cultures
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

    def generate_world(world, vd):
        available_cellprops = []
        available_worldparams = []

        def is_ready(plugin):
            '''
            Determine whether all pre-requisites are satisfied. If yes, its safe to run this plugin
            given the current state of the world.
            '''
            genfunc = plugin.generate

            if hasattr(genfunc, 'cellprops'):
                for cp in genfunc.cellprops:
                    if cp not in available_cellprops:
                        return False

            if hasattr(genfunc, 'worldparams'):
                for wp in genfunc.worldparams:
                    if wp not in available_worldparams:
                        return False

            return True

        def all_plugins():
            '''
            Dynamically load all plugins from the `plugins/` directory.
            '''
            plugin_list = pkgutil.iter_modules(plugins.__path__, plugins.__name__ + '.')
            
            modules = []
            for _, name, __ in plugin_list:
                pl = importlib.import_module(name)
                modules.append(pl)
            
            return modules

        plugin_queue = all_plugins()
        plugin_count = len(plugin_queue)

        while len(plugin_queue) > 0:
            available_plugins = list( filter(is_ready, plugin_queue) )

            for pl in available_plugins:
                print('   * [%d / %d] Running %s...\t' % (plugin_count - len(plugin_queue) + 1, plugin_count, pl.__name__), end='', flush=True)

                start_ts = time.time() * 1000
                pl.generate(world, vd)
                end_ts = time.time() * 1000

                print( '[%.1fms]' % (round(end_ts - start_ts, 1)) )

                # Once run, remove the plugin from the queue
                plugin_queue.remove(pl)
            
            available_cellprops = list( map(lambda k: k[3:], filter(lambda k: k.startswith('cp_'), world.__dict__.keys())) )
            available_worldparams = world.list_params()

    points = numpy.array(point_cloud(PointCount))
    vor = voronoi.generate(points)

    cell_idxs = [idx for idx in range(PointCount)]
    cell_mapping = {}
    for cell_idx, v_idx in enumerate( sorted(vor.point_region) ):
        cell_mapping[cell_idx] = v_idx

    worldgraph = graph.BuildGraph(cell_idxs, vor, cell_mapping)

    w = world.World(cell_idxs, vor, worldgraph)
    vd = voronoi.VoronoiDiagram(vor, cell_mapping)

    render_stack = []
    
    # Generate the world
    print('  [%s] Generating world #%d...' % (w.id, world_idx + 1))
    generate_world(w, vd)

    # print('  [%s] Establishing civilization...' % (world.id,))

    # Eventually we can represent multiple cultures; for now this is a single world-wide culture.
    # english = [lang for lang in language_list if lang.name == 'english'][0]
    # first_culture = cultures.HumanCulture(world.cells, world.vor, world.graph, english)
 
    # cities = []
    # for _ in range(NumCities):
    #     city = civilization.PlaceCity(world, first_culture, cities)

    #     cities.append(city)

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
    print('  [%s] Rendering world...' % (w.id,))

    # Render 'clean' map without POIs
    render_opts = renderer.RenderOptions()
    render_opts.filename = 'plugin-test.png'
    # render_opts.filename = 'world-%s.png' % (world.id,)

    renderer.simple_render(w, vd, render_opts)

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