import random, structs, numpy, datetime, sys, multiprocessing, pprint
import voronoi, civilization, graph, renderer, forest, poi, languages, cultures

seed = round( datetime.datetime.now().timestamp() * 10000 )
random.seed(seed)

# Configuration variables
PointCount = 2000
NumCities = 8
NumWorlds = 1
NumForests = 14

def generate(world_idx, language_list):
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

    # Eventually we can represent multiple cultures; for now this is a single world-wide culture.
    english = [lang for lang in language_list if lang.name == 'english'][0]
    first_culture = cultures.HumanCulture(world.cells, world.vor, world.graph, english)
 
    cities = []
    for _ in range(NumCities):
        city = civilization.PlaceCity(world, first_culture, cities)

        cities.append(city)
    
    print('  [%s] Growing forests...' % (world.id,))

    forests = []
    for _ in range(NumForests):
        f = forest.PlaceForest(world, forests)

        forests.append(f)

    ## Find points of interest
    print('  [%s] Identifying points of interest...' % (world.id,))
    poi_lib = poi.DetectAll(world)

    ## Generate names
    names = {}

    for city in cities:
        names[city] = first_culture.name_place(city)

    for poi_type in poi_lib.list_types():
        for poi_inst in poi_lib.get_type(poi_type):
            names[poi_inst] = first_culture.name_place(poi_inst)

    pprint.pprint(names)

    ## Render
    print('  [%s] Rendering world...' % (world.id,))

    # Render 'clean' map without POIs
    render_opts = renderer.RenderOptions()

    renderer.render(
        world, 
        cities=cities, 
        forests=forests,
        opts=render_opts,
    )

    # Render map with POIs highlighted
    render_opts_poi = renderer.RenderOptions()
    render_opts_poi.filename = 'world_poi.png'

    renderer.render(
        world, 
        cities=cities, 
        forests=forests,
        poi_lib=poi_lib,
        opts=render_opts_poi,
    )

    # Render SVG
    render_opts_svg = renderer.RenderOptions()
    render_opts_svg.filename = 'world-%s.svg' % (world.id,)

    renderer.render(
        world, 
        cities=cities, 
        forests=forests,
        names=names,
        # poi_lib=poi_lib,
        opts=render_opts_svg,
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
    if len(sys.argv) > 1:
        NumWorlds = int(sys.argv[1])

    print('')

    print('Building language models...')
    langs = languages.load()

    for lang in langs:
        print('  Language "%s" examples: %s' % (lang.name, [lang.generate_name() for _ in range(8)]))

    print('Generating %d world(s)...' % (NumWorlds,))
    for idx in range(NumWorlds):
        generate(idx, langs)
    # with multiprocessing.Pool() as pool:
    #     for idx in range(NumWorlds):
    #         pool.apply_async(generate, args=(idx,langs))
        
        # pool.close()
        # pool.join()