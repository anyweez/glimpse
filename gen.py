import random, structs, numpy, datetime, sys, multiprocessing
import voronoi, civilization, graph

seed = round( datetime.datetime.now().timestamp() * 10000 )
random.seed(seed)

# Configuration variables
PointCount = 2000
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

    print('  Generating world #%d [%s]...' % (world_idx + 1, world.id,))

    world.build()
    world.label()

    print('  Establishing civilization [%s]...' % (world_idx,))

    cities = []
    # for _ in range(5):
    #     city = civilization.PlaceCity(world, cities)

    #     print(city.location)
    #     cities.append(city)

    ## Render
    world.render(
        cities=cities,
        cell_labels=False, 
        color_boundaries=True, 
        cell_elevation=True, 
        show_graph=False, 
        tectonics=False,
        outline_landforms=True,
        heightmap=True
    )

if __name__ == '__main__':
    print('seed=%d, num_points=%d' % (seed, PointCount))
    print('Generating %d world(s)...' % (NumWorlds,))

    with multiprocessing.Pool() as pool:
        pool.map(generate, range(NumWorlds))