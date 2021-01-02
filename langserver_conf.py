from xmlrpc.client import ServerProxy

ServerHost = 'localhost'
ServerPort = 8050

def GetClient():
    return ServerProxy('http://%s:%d' % (ServerHost, ServerPort))