
class Entity(object):
    def __init__(self, graph, name=None):
        self.graph = graph
        self.name = name

    def render(self, ctx, world, vd):
        raise NotImplementedError('render() not implemented on entity type')
    
    @staticmethod
    def _transform_pt(pt):
        return (pt[0], 1.0 - pt[1])