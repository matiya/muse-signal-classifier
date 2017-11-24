from time import time
from optparse import OptionParser
from glob import glob
from random import choice

import numpy as np
from pandas import DataFrame
from psychopy import visual, core, event, sound, prefs
from pylsl import StreamInfo, StreamOutlet, local_clock

prefs.general['audioLib'] = ['pygame']

parser = OptionParser()
parser.add_option(
    "-d",
    "--duration",
    dest="duration",
    type='int',
    default=10,
    help="duration of the recording in seconds.")

(options, args) = parser.parse_args()

# Create markers stream outlet
info = StreamInfo('Markers', 'Markers', 1, 0, 'int32', 'myuidw43536')
outlet = StreamOutlet(info)
# 1 : Estimulo positivo
# 2 : Estimulo negativo
# 3 : Estimulo neutro
markernames = [1, 2, 3]

# Sonido para debug
aud1 = sound.Sound('C', octave=5, sampleRate=44100, secs=0.3, bits=8)
aud1.setVolume(0.8)

start = time()
timestamp = time()

# Set up trial parameters
n_trials = 3
iti = 3.3
soa = 0.2
jitter = 0.2
record_duration = np.float32(options.duration)

# Setup trial list
# cambiar para mostrar videos feos
movie_type = np.random.binomial(1, 0.5, n_trials)

trials = DataFrame(dict(movie_type=movie_type, timestamp=np.zeros(n_trials)))

mywin = visual.Window(
    [900, 800], monitor='testMonitor', units='deg', fullscr=True)


def load_movie(filename):
    return visual.MovieStim3(
        mywin, filename, size=(800, 600), volume=1.0, noAudio=False)


# cargar los archivos de video
pos_mov = map(load_movie, glob('stim/pos*.webm'))
neg_mov = map(load_movie, glob('stim/neg*.webm'))
neu_mov = map(load_movie, glob('stim/neu*.webm'))


def make_choice(label):
    if label == 0:
        return neu_mov
    if label == 1:
        return pos_mov
    else:
        return neg_mov


for ii, trial in trials.iterrows():
    # intervalo entre videos
    message = visual.TextStim(
        mywin,
        text='Hola! En breve comenzara \
                          un nuevo video.')
    message.draw()  # automatically draw every frame
    mywin.flip()
    core.wait(iti + np.random.rand() * jitter)

    # Select and display image
    label = trials['movie_type'].iloc[ii]
    mov = choice(make_choice(label))
    # tiempo en el que aparece el estimulo
    onset = int(mov.filename.split('.')[0].split('_')[1])
    print("Onset en: %s" % onset)
    start = time()
    isAlreadySent = False
    while mov.status != visual.FINISHED:
        mov.draw()
        mywin.flip()
        if (abs((time() - start) - onset) < 0.05 and not isAlreadySent):
            aud1.play()
            timestamp = local_clock()
            print("[I] Evento con etiqueta %s enviado en %s: " %
                  (label, (time() - start)))
            outlet.push_sample([markernames[label]], timestamp)
            isAlreadySent = True
            #mywin.flip()

        if len(event.getKeys()) > 0:
            break

        event.clearEvents()
        # offset
        #core.wait(soa)
        #mywin.flip()

    if len(event.getKeys()) > 0 or (time() - start) > record_duration:
        break

# Cleanup
mywin.close()
