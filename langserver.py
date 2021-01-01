import random
import languages

from xmlrpc.client import ServerProxy
from xmlrpc.server import SimpleXMLRPCServer
from xmlrpc.server import SimpleXMLRPCRequestHandler

ServerHost = 'localhost'
ServerPort = 8050

reject_list = ['cock',]

def GetClient():
    return ServerProxy('http://%s:%d' % (ServerHost, ServerPort))

# Restrict to a particular path.
class RequestHandler(SimpleXMLRPCRequestHandler):
    rpc_paths = ('/RPC2',)

def valid_basename(base):
    def is_vowel(char):
        return char in ['a', 'e', 'i', 'o', 'u', 'y']

    vowels = ''.join( ['1' if is_vowel(char) else '0' for char in base] )

    # Name can't have three consonants in a rule; these are usually unpronounceable
    return '000' not in vowels

def start_server():
    def name_city(base, params):
        patterns = ['Fort %s', 'New %s', '%s']
        patterns_weight = [2, 3, 10]

        if 'near_water' in params and params['near_water']:
            patterns.append('%s Harbor')
            patterns_weight.append(2)

            patterns.append('%s\'s Cove')
            patterns_weight.append(1)

        pattern = random.choices(patterns, weights=patterns_weight)

        return pattern % (base,)
    
    def name_lake(base, params):
        return 'Lake %s' % (base,)
    
    def name_mountain(base, params):
        if random.random() < 0.50:
            return 'Mount %s' % (base,)
        
        if random.random() < 0.50:
            return '%s\'s Peak' % (base,)
        
        return base

    print('Loading languages...')

    # Create server
    with SimpleXMLRPCServer((ServerHost, ServerPort), requestHandler=RequestHandler) as server:
        server.register_introspection_functions()

        # Load all language models
        langs = languages.load()
        langmodels = {}

        for lang in langs:
            print('  Loaded language "{}"'.format(lang.name))
            # print('  Language "%s" examples: %s' % (lang.name, [lang.generate_name() for _ in range(8)]))
            langmodels[lang.name] = lang.generate_name

        entity_handlers = {
            'city':     name_city,
            'lake':     name_lake,
            'mountain': name_mountain,
        }

        def get_name(language, entity_type, params):
            '''
            Return a name in the specified language for the specified entity type.

            Example: get_name('english', 'city')
            '''

            if language in langmodels:
                base = langmodels[language]()

                while base in reject_list:
                    base = langmodels[language]()

                while not valid_basename(base):
                    print('  Rejecting: {}'.format(base))

                    base = langmodels[language]()

                try:
                    return entity_handlers[entity_type](base, params)
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