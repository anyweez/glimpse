import langserver_conf as lsc

lc = lsc.GetClient()

class Entity(object):
    def __init__(self, graph, name=None):
        self.graph = graph
        self.name = name

    def render_stage1(self, ctx, world, vd, theme):
        '''
        Immediately after land is drawn. Land and other stage 1 entities will be the only
        rendered elements.

        Ex: rivers
        '''
        raise NotImplementedError('Entity does not leverage stage 1 for rendering')
    
    def render_stage2(self, ctx, world, vd, theme):
        '''
        Immediately after all other elements are rendered.
        '''
        raise NotImplementedError('Entity does not leverage stage 2 for rendering')

    def fetch_name(self, language, entity_type, params):
        self.name = lc.get_name(language, entity_type, params)

    @staticmethod
    def _transform_pt(pt):
        return (pt[0], 1.0 - pt[1])