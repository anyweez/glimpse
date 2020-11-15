from tensorflow.keras.layers import LSTM, Dense, Input, concatenate, Reshape, Dropout
from tensorflow.keras.models import Model, load_model
import numpy as np

import os
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'    # Hide tensorflow warnings

class Language(object):
    def __init__(self, name, example_names):
        self.name = name
        self.model, self.generator = train_model(example_names, verbose=False)

    def generate_name(self):
        return self.generator()


'''
Name generator pulled from Jupyter notebook from @tadeaspaule here:
https://github.com/tadeaspaule/universal-name-generator/blob/master/Universal%20RNN%20for%20name%20generation.ipynb

To use:

```
model, generate_name = train_model( ('Name 1', 'Name 2', 'Name 3') )

# Generate five names
names = [generate_name() for _ in range(5)]
```
'''

def process_names(names,*,unwanted=['(', ')', '-', '.', '/']):
    names = [name.lower() for name in names]
    chars = sorted(list(set(''.join(names))))

    def has_unwanted(word):
        for char in word:
            if char in unwanted:
                return True
        return False
    names = [name for name in names if not has_unwanted(name)]
    chars = [char for char in chars if char not in unwanted]
    
    # enchar indicates the end of the word
    # here it goes through unlikely-to-be-used characters to find one it can use
    endchars = '!£$%^&*()-_=+/?.>,<;:@[{}]#~'
    endchar = [ch for ch in endchars if ch not in chars][0]

    # ensures the character isn't already used & present in the training data
    assert(endchar not in chars)
    chars += endchar
    
    return names, chars

def make_sequences(names, seqlen, chars):
    sequences, lengths, nextchars = [],[],[] # To have the model learn a more macro understanding, 
                                             # it also takes the word's length so far as input
    for name in names:
        if len(name) <= seqlen:
            sequences.append(name + chars[-1]*(seqlen - len(name)))
            nextchars.append(chars[-1])
            lengths.append(len(name))
        else:
            for i in range(0,len(name)-seqlen+1):
                sequences.append(name[i:i+seqlen])
                if i+seqlen < len(name):
                    nextchars.append(name[i+seqlen])
                else:
                    nextchars.append(chars[-1])
                lengths.append(i+seqlen)

    # print(len(sequences),"sequences of length",seqlen,"made")
    
    return sequences,lengths,nextchars

def make_onehots(*,sequences,lengths,nextchars,chars):
    x = np.zeros(shape=(len(sequences),len(sequences[0]),len(chars)), dtype='float32') # sequences
    x2 = np.zeros(shape=(len(lengths),max(lengths))) # lengths

    for i, seq in enumerate(sequences):
        for j, char in enumerate(seq):
            x[i,j,chars.index(char)] = 1.

    for i, l in enumerate(lengths):
        x2[i,l-1] = 1.

    y = np.zeros(shape=(len(nextchars),len(chars)))
    for i, char in enumerate(nextchars):
        y[i,chars.index(char)] = 1.
    
    return x,x2,y

def get_dictchars(names,seqlen):
    dictchars = [{} for _ in range(seqlen)]

    for name in names:
        if len(name) < seqlen:
            continue
        dictchars[0][name[0]] = dictchars[0].get(name[0],0) + 1
        for i in range(1,seqlen):
            if dictchars[i].get(name[i-1],0) == 0:
                dictchars[i][name[i-1]] = {name[i]: 1}
            elif dictchars[i][name[i-1]].get(name[i],0) == 0:
                dictchars[i][name[i-1]][name[i]] = 1
            else:
                dictchars[i][name[i-1]][name[i]] += 1
    return dictchars

def generate_start_seq(dictchars):
    res = "" # The starting sequence will be stored here
    p = sum([n for n in dictchars[0].values()]) # total amount of letter occurences
    r = np.random.randint(0,p) # random number used to pick the next character
    tot = 0
    for key, item in dictchars[0].items():
        if r >= tot and r < tot + item:
            res += key
            break
        else:
            tot += item

    for i in range(1,len(dictchars)):
        ch = res[-1]
        if dictchars[i].get(ch,0) == 0:
            l = list(dictchars[i].keys())
            ch = l[np.random.randint(0,len(l))]
        p = sum([n for n in dictchars[i][ch].values()])
        r = np.random.randint(0,p)
        tot = 0
        for key, item in dictchars[i][ch].items():
            if r >= tot and r < tot + item:
                res += key
                break
            else:
                tot += item
    return res

def sample(preds,temperature=0.4):
    preds = np.asarray(preds).astype('float64')
    if temperature == 0:
        # Avoiding a division by 0 error
        return np.argmax(preds)
    preds = np.log(preds) / temperature
    exp_preds = np.exp(preds)
    preds = exp_preds / np.sum(exp_preds)
    probas = np.random.multinomial(1,preds,1)
    return np.argmax(probas)

def generate_name(model,start,*,chars,temperature=0.4):
    maxlength = model.layers[3].input.shape[1]
    seqlen = int(model.layers[0].input.shape[1])
    result = start
    
    sequence_input = np.zeros(shape=(1,seqlen,len(chars)))
    for i, char in enumerate(start):
        sequence_input[0,i,chars.index(char)] = 1.
    
    length_input = np.zeros(shape=(1,maxlength))
    length_input[0,len(result)-1] = 1.
    
    prediction = model.predict(x=[sequence_input,length_input])[0]
    char_index = sample(prediction,temperature)
    while char_index < len(chars)-1 and len(result) < maxlength:
        result += chars[char_index]
        
        sequence_input = np.zeros(shape=(1,seqlen,len(chars)))
        for i, char in enumerate(result[(-seqlen):]):
            sequence_input[0,i,chars.index(char)] = 1.
        
        length_input[0,len(result)-2] = 0.
        length_input[0,len(result)-1] = 1.
        
        prediction = model.predict(x=[sequence_input,length_input])[0]
        char_index = sample(prediction,temperature)
    
    return result.title()

def generate_random_name(model, *, chars, dictchars, temperature=0.4):
    start = generate_start_seq(dictchars)
    return generate_name(model,start,chars=chars,temperature=temperature)

def make_model(x,x2,chars):
    inp1 = Input(shape=x.shape[1:]) # sequence input
    inp2 = Input(shape=x2.shape[1:]) # length input
    lstm = LSTM(len(chars),activation='relu',dropout=0.3)(inp1)
    lstm2 = LSTM(len(chars),dropout=0.3,go_backwards=True)(inp1)
    concat = concatenate([lstm,lstm2,inp2])
    dense = Dense(len(chars),activation='softmax')(concat)

    model = Model([inp1,inp2],dense)
    model.compile(optimizer='adam',loss='binary_crossentropy')
    return model

def try_model(model, *, x, x2, y, chars, dictchars, total_epochs=180, print_every=60, temperature=0.4, verbose=True):
    for i in range(total_epochs//print_every):
        history = model.fit([x,x2],y,
                            epochs=print_every,
                            batch_size=64,
                            validation_split=0.05,
                            verbose=0)
        if verbose:
            print("\nEpoch",(i+1)*print_every)
            print("First loss:            %1.4f" % (history.history['loss'][0]))
            print("Last loss:             %1.4f" % (history.history['loss'][-1]))
            print("First validation loss: %1.4f" % (history.history['val_loss'][0]))
            print("Last validation loss:  %1.4f" % (history.history['val_loss'][-1]))
            print("\nGenerating random names:")
            for _ in range(10):
                print(generate_random_name(model,chars=chars,dictchars=dictchars,temperature=temperature)) 
    # if not verbose:
    #     print("Model training complete, here are some generated names:")
    #     for _ in range(20):
    #         print(generate_random_name(model,chars=chars,dictchars=dictchars,temperature=0.4))

def train_model(names,*, seqlen=4,unwanted=['(', ')', '-', '.', '/'],verbose=True):
    names,chars = process_names(names,unwanted=unwanted)
    
    sequences,lengths,nextchars = make_sequences(names, seqlen, chars)
    
    x,x2,y = make_onehots(sequences=sequences,
                          lengths=lengths,
                          nextchars=nextchars,
                          chars=chars)
        
    dictchars = get_dictchars(names,seqlen)
    
    model = make_model(x,x2,chars)  
    
    try_model(model,x=x,x2=x2,y=y,chars=chars,dictchars=dictchars,verbose=verbose)
    
    def generate():
        return generate_random_name(model,chars=chars,dictchars=dictchars,temperature=0.4)
    
    return model, generate
