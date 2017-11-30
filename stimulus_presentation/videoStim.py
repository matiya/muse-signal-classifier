from time import time, strftime, gmtime
from optparse import OptionParser
from glob import glob
from random import choice

import numpy as np
from pandas import DataFrame
from psychopy import visual, core, event, sound, prefs, logging
from pylsl import StreamInfo, StreamOutlet, local_clock

prefs.general['audioLib'] = ['pygame']

parser = OptionParser()
# nombre para el logfile
fname = ("../logs/stimulus_%s.log" % strftime("%Y-%m-%d-%H.%M.%S", gmtime()))
logfile = logging.LogFile(fname, filemode='w')

parser.add_option(
    "-e",
    "--experimentos",
    dest="n_trials",
    type='int',
    default=3,
    help="Numero de experimentos")
parser.add_option(
    "-i",
    "--interval",
    dest="iti",
    type='int',
    default=7,
    help="Intervalo entre las pruebas")

(options, args) = parser.parse_args()

# Create markers stream outlet
info = StreamInfo('Markers', 'Markers', 1, 0, 'int32', 'myuidw43536')
outlet = StreamOutlet(info)
# 1 : Estimulo positivo
# 2 : Estimulo negativo
# 3 : Estimulo neutro
markernames = [1, 2, 3]

from psychopy import gui
# Feedback del usuario
feedback = []
# Sonido para debug
aud1 = sound.Sound('C', octave=5, sampleRate=44100, secs=0.3, bits=8)
aud1.setVolume(0.8)

start = time()
timestamp = time()

# Set up trial parameters
n_trials = np.float32(options.n_trials)
iti = np.float32(options.iti)
soa = 0.2
jitter = 0.2
record_duration = 1000
# Setup trial list
# cambiar para mostrar videos feos
movie_type = np.random.binomial(1, 0.5, n_trials)

trials = DataFrame(dict(movie_type=movie_type, timestamp=np.zeros(n_trials)))

mywin = visual.Window(
    [1366, 800], monitor='testMonitor', units='deg', fullscr=False)


def load_movie(filename):
    return visual.MovieStim3(
        mywin, filename, size=(800, 600), volume=1.0, noAudio=False)


# cargar las imagenes para evaluacion
sam_valence = visual.ImageStim(win=mywin, image='stim/sam_valence.jpg')
sam_arousal = visual.ImageStim(win=mywin, image='stim/sam_arousal.jpg')
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


def handle_eval_data(myDlg, uid="Info personal"):
    ok_data = myDlg.show()
    if myDlg.OK:  # or if ok_data is not None
        print("[I] %s: %s" % (uid, ok_data))
        if (uid != "Info personal"):
            feedback.append(ok_data[0])
            logging.log("Dato registrado %s: %s" % (uid, ok_data[0]), level=80)
        else:  # Info del sujeto
            logging.log("#### Nuevo experimento ####", level=80)
            logging.log("Edad sujeto: " + str(ok_data[0]), level=80)
            logging.log("Sexo sujeto: " + str(ok_data[1]), level=80)

    else:
        raise (RuntimeError, "El usuario se la mando")


# obtener info del sujeto
myDlg = gui.Dlg(title="Experimento emocionalidad")
myDlg.addText('Informacion del sujeto')
myDlg.addField('Edad:')
myDlg.addField('Sexo:', choices=["Masculino", "Femenino"])
handle_eval_data(myDlg)

for ii, trial in trials.iterrows():
    # intervalo entre videos
    message = visual.TextStim(
        mywin,
        text='En breve comenzara \
                          un nuevo video.')
    message.draw()
    mywin.flip()
    core.wait(iti + np.random.rand() * jitter)

    # Select and display image
    label = trials['movie_type'].iloc[ii]
    mov = choice(make_choice(label))
    # tiempo en el que aparece el estimulo
    onset = int(mov.filename.split('.')[0].split('_')[1])
    logging.log("Archivo: %s" % mov.filename, level=80)
    print("[I] Onset en: %s segundos" % onset)
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
            print("Se envia %s de tipo %s" % ([markernames[label]],
                                              type([markernames[label]])))
            outlet.push_sample([markernames[label]], timestamp)
            isAlreadySent = True

        if len(event.getKeys()) > 0:
            mov.stop()
            break

        event.clearEvents()

    # Comienza autoevaluacion de la prueba
    core.wait(1.0)
    sam_valence.draw()
    mywin.flip()
    core.wait(2.0)
    myDlg = gui.Dlg(title="Evaluacion valencia")
    myDlg.addText('Por favor, indique el impacto personal del\
    video anterior. Utilice la imagen como referencia.')
    myDlg.addField(
        'Puntuacion:', choices=['1', '2', '3', '4', '5', '6', '7', '8', '9'])
    handle_eval_data(myDlg, 'valence')
    sam_arousal.draw()
    mywin.flip()
    core.wait(2.0)
    myDlg = gui.Dlg(title="Evaluacion magnitud")
    myDlg.addText('Por favor, indique el impacto personal del\
    video anterior. Utilice la imagen como referencia.')
    myDlg.addField(
        'Puntuacion:', choices=['1', '2', '3', '4', '5', '6', '7', '8', '9'])
    handle_eval_data(myDlg, 'arousal')

    # envio la operacion del usuario
    dato = [int(''.join(feedback[-2:]))]
    print(dato)
    timestamp = local_clock()
    outlet.push_sample(dato, local_clock())
    event.clearEvents()

    if len(event.getKeys()) > 0 or (time() - start) > record_duration:
        break

# Cleanup
mywin.close()
