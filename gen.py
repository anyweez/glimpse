import datetime, random, sys, numpy, pkgutil, importlib, time, os
import voronoi, graph, renderer, world

import plugins

# Configuration variables
PointCount = 8000      # default = 3500
NumWorlds = 1

def generate(world_idx):
    def point_cloud(n):
        '''
        Generate a series of `n` random latlong points, returned as a single ndarray
        '''
        return numpy.array( [(
            numpy.random.uniform(-90.0, 90.0),          # latitude
            numpy.random.uniform(-180.0, 180.0),        # longitude
        ) for _ in range(n)] )

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
                print('   * [{} / {}] Running {}...\t'.format(
                        plugin_count - len(plugin_queue) + 1,
                        plugin_count,
                        pl.__name__
                    ),
                    end='',
                    flush=True,
                )

                start_ts = time.time() * 1000
                pl.generate(world, vd)
                end_ts = time.time() * 1000

                print( '[%.1fms]' % (round(end_ts - start_ts, 1)) )

                # Once run, remove the plugin from the queue
                plugin_queue.remove(pl)
            
            available_cellprops = list( map(lambda k: k[3:], filter(lambda k: k.startswith('cp_'), world.__dict__.keys())) )
            available_worldparams = world.list_params()

    # Seed RNG once per iteration
    seed = round( datetime.datetime.now().timestamp() * 10000 )
    random.seed(seed)

    print('  [------] Generating Voronoi points for world...')
    points = point_cloud(PointCount)
    vor = voronoi.generate(points)

    cell_idxs = [idx for idx in range(PointCount)]
    cell_mapping = {}

    # NOTE: I believe the spherical voronoi surface removes the need for this mapping;
    # the version below is clearly not very important and assuming no new bugs emerge
    # it should be possible to remove the mapping entirely.
    for cell_idx in cell_idxs:
        cell_mapping[cell_idx] = cell_idx

    print('  [------] Building world graph...')
    worldgraph = graph.BuildGraph(cell_idxs, vor, cell_mapping)

    w = world.World(cell_idxs, vor, worldgraph)
    vd = voronoi.VoronoiDiagram(vor, cell_mapping)
    
    # Generate the world
    print('  [{}] Generating world #{}...'.format(w.id, world_idx + 1))
    generate_world(w, vd)

    ## Render one or more images
    print('  [{}] Rendering world...'.format(w.id))

    folder = 'gallery/%s' % (str(datetime.datetime.now()),)
    os.mkdir(folder)

    render_opts = renderer.RenderOptions()
    render_opts.filename = 'batch/{}.png'.format(w.id)

    # print('   * Rendering png ({})...'.format(render_opts.filename))
    # renderer.print_render(w, vd, render_opts)

    print('Calculating geographic representations (PostGIS)....')
    renderer.geo(w, vd, None)
    print('\rdone')

    # print_render_opts = renderer.RenderOptions()
    # print_render_opts.filename = 'print.svg'

    # print('    * Rendering svg...')
    # renderer.print_render(w, vd, print_render_opts)

if __name__ == '__main__':
    if len(sys.argv) > 1:
        NumWorlds = int(sys.argv[1])

    print('num_worlds={}, num_points={}'.format(NumWorlds, PointCount))
    print('')

    print('Generating world(s)...')
    for idx in range(NumWorlds):
        generate(idx)