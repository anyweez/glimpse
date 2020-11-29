import random
import languages

from xmlrpc.client import ServerProxy
from xmlrpc.server import SimpleXMLRPCServer
from xmlrpc.server import SimpleXMLRPCRequestHandler

ServerHost = 'localhost'
ServerPort = 8050

def GetClient():
    return ServerProxy('http://%s:%d' % (ServerHost, ServerPort))

# Restrict to a particular path.
class RequestHandler(SimpleXMLRPCRequestHandler):
    rpc_paths = ('/RPC2',)

def start_server():
    def name_city(base):
        if random.random() < 0.2:
            return 'Fort %s' % (base,)

        if random.random() < 0.25:
            return '%s Harbor' % (base,)

        if random.random() < 0.35:
            return 'New %s' % (base,)
        
        return base
    
    def name_lake(base):
        return 'Lake %s' % (base,)
    
    def name_mountain(base):
        if random.random() < 0.50:
            return 'Mount %s' % (base,)
        
        return base

    # Create server
    with SimpleXMLRPCServer((ServerHost, ServerPort), requestHandler=RequestHandler) as server:
        server.register_introspection_functions()

        # Load all language models
        langs = languages.load()
        langmodels = {}

        for lang in langs:
            print('  Language "%s" examples: %s' % (lang.name, [lang.generate_name() for _ in range(8)]))
            langmodels[lang.name] = lang.generate_name

        entity_handlers = {
            'city':     name_city,
            'lake':     name_lake,
            'mountain': name_mountain,
        }

        def get_name(language, entity_type):
            '''
            Return a name in the specified language for the specified entity type.

            Example: get_name('english', 'city')
            '''
            if language in langmodels:
                base = langmodels[language]()

                try:
                    return entity_handlers[entity_type](base)
                except:
                    return base
            else:
                return ''


        server.register_function(get_name, 'get_name')

        print('Language server active')
        # Run the server's main loop
        server.serve_forever()

if __name__ == '__main__':
    start_server()