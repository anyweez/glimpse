import random, structs, numpy, datetime, sys, multiprocessing
import voronoi, civilization, graph, renderer, forest, poi

seed = round( datetime.datetime.now().timestamp() * 10000 )
random.seed(seed)

# Configuration variables
PointCount = 2000
NumCities = 2
NumWorlds = 1
NumForests = 14

if len(sys.argv) > 1:
    NumWorlds = int(sys.argv[1])

def generate(world_idx):
    def point_cloud(n):
        return [(random.random(), random.random()) for _ in range(n)]

    points = numpy.array(point_cloud(PointCount))

    vor = voronoi.generate(points)
    cells = structs.Cell.FormCells(vor)
    worldgraph = graph.BuildGraph(cells, vor)

    world = structs.World(cells, vor, worldgraph)

    print('  [%s] Generating world #%d...' % (world.id, world_idx + 1))

    world.build()
    world.label()

    print('  [%s] Establishing civilization...' % (world.id,))

    cities = []
    for _ in range(NumCities):
        city = civilization.PlaceCity(world, cities)

        cities.append(city)
    
    print('  [%s] Growing forests...' % (world.id,))

    forests = []
    for _ in range(NumForests):
        f = forest.PlaceForest(world, forests)

        forests.append(f)

    ## Find points of interest
    print('  [%s] Identifying points of interest...' % (world.id,))
    poi_lib = poi.DetectAll(world)

    ## Render
    print('  [%s] Rendering world...' % (world.id,))

    render_opts = renderer.RenderOptions()

    renderer.render(
        world, 
        cities=cities, 
        forests=forests,
        # poi_lib=poi_lib,
        opts=render_opts,
    )

    render_opts_poi = renderer.RenderOptions()
    render_opts_poi.filename = 'world_poi.png'

    renderer.render(
        world, 
        cities=cities, 
        forests=forests,
        poi_lib=poi_lib,
        opts=render_opts_poi,
    )

    # world.render(
    #     cities=cities,
    #     cell_labels=False, 
    #     color_boundaries=True, 
    #     cell_elevation=True, 
    #     show_graph=False, 
    #     tectonics=False,
    #     outline_landforms=True,
    #     heightmap=True
    # )

if __name__ == '__main__':
    print('seed=%d, num_points=%d' % (seed, PointCount))
    print('Generating %d world(s)...' % (NumWorlds,))

    generate(0)
    # with multiprocessing.Pool() as pool:
    #     pool.map(generate, range(NumWorlds))