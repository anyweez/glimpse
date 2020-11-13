import random, structs, numpy, datetime, sys, multiprocessing
import voronoi, civilization, graph, renderer

seed = round( datetime.datetime.now().timestamp() * 10000 )
random.seed(seed)

# Configuration variables
PointCount = 2000
NumCities = 2
NumWorlds = 1

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

    ## Render
    print('  [%s] Rendering world...' % (world.id,))

    render_opts = renderer.RenderOptions()

    renderer.render(world, cities, render_opts)
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

    with multiprocessing.Pool() as pool:
        pool.map(generate, range(NumWorlds))