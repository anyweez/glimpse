import datetime, random, sys, numpy, pkgutil, importlib, time, os
import voronoi, graph, renderer, world
import langserver

import plugins

seed = round( datetime.datetime.now().timestamp() * 10000 )
random.seed(seed)

# Configuration variables
PointCount = 5000      # default = 3500
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
    
    # Generate the world
    print('  [%s] Generating world #%d...' % (w.id, world_idx + 1))
    generate_world(w, vd)

    ## Render
    print('  [%s] Rendering world...' % (w.id,))

    folder = 'gallery/%s' % (str(datetime.datetime.now()),)

    os.mkdir(folder)

    # Render 'clean' map without POIs
    render_opts = renderer.RenderOptions()
    render_opts.filename = 'sample.png'
    # render_opts.filename = '%s/%d.full.png' % (folder, world_idx,)

    renderer.simple_render(w, vd, render_opts)

    # render_opts_t = renderer.RenderOptions()
    # render_opts_t.filename = '%s/%d.temperature.png' % (folder, world_idx,)
    # renderer.heatmap(w, vd, render_opts_t, render_opts.filename, lambda idx: w.cp_temperature[idx])

    # render_opts_m = renderer.RenderOptions()
    # render_opts_m.filename = '%s/%d.moisture.png' % (folder, world_idx,)
    # renderer.heatmap(w, vd, render_opts_m, render_opts.filename, lambda idx: w.cp_moisture[idx])

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