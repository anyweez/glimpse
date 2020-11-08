import numpy

from scipy.spatial import Voronoi

def generate(points, n_smooth=3):
    vor = None

    for _ in range(n_smooth):
        vor = Voronoi(points)
        new_points = numpy.zeros(points.shape)

        for point_idx, region_id in enumerate(vor.point_region):
            region = vor.regions[region_id]

            if -1 in region:
                new_points[point_idx] = points[point_idx]

            vertices = [vor.vertices[idx] for idx in region]
            new_points[point_idx] = numpy.mean(vertices, 0)

        points = new_points
    
    return vor

def prebuilt_vor1():
    points = numpy.array([
        [0.40262444, 0.89010797],
        [0.46321667, 0.38315214],
        [0.44349672, 0.18688911],
        [0.68745787, 0.69143624],
        [0.81944654, 0.15131946],
        [0.72458714, 0.22609854],
        [0.09813275, 0.10948937],
        [0.70126296, 0.75512688],
        [0.94840268, 0.1245352 ],
        [0.67502909, 0.67320131],
        [0.51403338, 0.19046477],
        [0.50371745, 0.11135518],
        [0.82637509, 0.8662734 ],
        [0.73357888, 0.17471943],
        [0.03979779, 0.03844015],
        [0.98681669, 0.93202815],
        [0.37459058, 0.38567779],
        [0.97938578, 0.79391543],
        [0.72289236, 0.1089072 ],
        [0.78337802, 0.73216984],
        [0.19575816, 0.81631711],
        [0.97356313, 0.82395971],
        [0.10195127, 0.01111625],
        [0.78762842, 0.95231354],
        [0.4559196 , 0.01983087],
        [0.94214394, 0.19983331],
        [0.80805499, 0.75741924],
        [0.01387654, 0.4010178 ],
        [0.29149957, 0.11556165],
        [0.66567361, 0.92751248],
        [0.59049409, 0.32640914],
        [0.38291789, 0.92962468],
        [0.10056959, 0.56028808],
        [0.78515087, 0.86267363],
        [0.71865541, 0.22180088],
        [0.05040245, 0.7702802 ],
        [0.37084486, 0.36057732],
        [0.64849443, 0.40721157],
        [0.15563548, 0.90238154],
        [0.58745176, 0.90352623],
        [0.12489829, 0.32289921],
        [0.34419703, 0.86792104],
        [0.50676785, 0.40017397],
        [0.50834899, 0.65523267],
        [0.36487756, 0.62471309],
        [0.39764789, 0.2181109 ],
        [0.3011823 , 0.0222423 ],
        [0.2143103 , 0.60207535],
        [0.13990504, 0.17716391],
        [0.90438299, 0.66031845],
        [0.40423086, 0.56533161],
        [0.79536783, 0.37672868],
        [0.43392892, 0.32567715],
        [0.17528278, 0.05660193],
        [0.21399672, 0.68699174],
        [0.47474729, 0.35745426],
        [0.29068082, 0.59539884],
        [0.36700722, 0.13542221],
        [0.79564283, 0.95248314],
        [0.68364939, 0.60702048],
        [0.57251765, 0.6317786 ],
        [0.21822423, 0.7171864 ],
        [0.6573202 , 0.65521942],
        [0.08380973, 0.23864449],
        [0.73907708, 0.78899286],
        [0.24951666, 0.50910092],
        [0.48166857, 0.93009483],
        [0.52880764, 0.76343148],
        [0.14900537, 0.81545771],
        [0.63578057, 0.69103053],
        [0.66096026, 0.51938303],
        [0.17768932, 0.78702168],
        [0.89266581, 0.2582247 ],
        [0.52915596, 0.67159946],
        [0.6047453 , 0.26361231],
        [0.76748022, 0.45862889],
        [0.86477637, 0.44603271],
        [0.82338454, 0.98428034],
        [0.20278993, 0.06884434],
        [0.15602841, 0.8087541 ],
        [0.99733613, 0.98585632],
        [0.23368683, 0.65465301],
        [0.24976235, 0.38553243],
        [0.76690454, 0.78862475],
        [0.15056952, 0.96460832],
        [0.23950245, 0.28971527],
        [0.74287355, 0.06861326],
        [0.63059252, 0.7292568 ],
        [0.28497952, 0.94096798],
        [0.29997593, 0.31476221],
        [0.34970587, 0.84843535],
        [0.09496377, 0.31222525],
        [0.82098736, 0.52918112],
        [0.92285489, 0.15623229],
        [0.19687324, 0.55516564],
        [0.45493029, 0.02460928],
        [0.55018825, 0.75980363],
        [0.33457664, 0.21343718],
        [0.20419116, 0.13904349],
        [0.27995101, 0.04775983],
    ])

    return generate(points)