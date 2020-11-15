import os
from languages import language

def load():
    '''
    Builds a naming model for each of the language datasets available.
    '''
    filenames = [filename for filename in os.listdir('languages') if filename.endswith('.txt')]

    langs = []

    for filename in filenames:
        lang_name = filename.split('.')[0]

        with open('languages/%s' % (filename,)) as fp:
            examples = fp.read().split('\n')

            lang = language.Language(lang_name, examples)
            langs.append(lang)


    return langs