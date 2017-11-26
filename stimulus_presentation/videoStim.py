from time import time, strftime, gmtime
from optparse import OptionParser
from glob import glob
from random import choice

import numpy as np
from pandas import DataFrame
from psychopy import visual, core, event, sound, prefs, gui, logging
from pylsl import StreamInfo, StreamOutlet, local_clock

prefs.general['audioLib'] = ['pygame']

parser = OptionParser()
# nombre para el logfile
fname = ("stimulus_%s.log" % strftime("%Y-%m-%d-%H.%M.%S", gmtime()))
logfile = logging.LogFile(fname)

parser.add_option(
    "-d",
    "--duration",
    dest="duration",
    type='int',
    default=10,
    help="Duracion del experimento.")
parser.add_option(
    "-i",
    "--interval",
    dest="iti",
    type='int',
    default=7,
    help="Intervalo entre las pruebas.")

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
iti = np.float32(options.iti)
soa = 0.2
jitter = 0.2
record_duration = np.float32(options.duration)
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


myDlg = gui.Dlg(title="Experimento emocionalidad")
myDlg.addText('Informacion del sujeto')
myDlg.addField('Edad:')
myDlg.addField('Sexo:', choices=["Masculino", "Femenino"])
ok_data = myDlg.show()  # show dialog and wait for OK or Cancel
if myDlg.OK:  # or if ok_data is not None
    print("Data usuario: %s" % ok_data)
else:
    raise (RuntimeError, "El usuario se la mando")

# imprimir informacion al logfile
logging.log("#### Nuevo experimento ####", level=80)
logging.log("Edad sujeto: " + str(ok_data[0]), level=80)
logging.log("Sexo sujeto: " + str(ok_data[1]), level=80)

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

        if len(event.getKeys()) > 0:
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
    ok_data = myDlg.show()  # show dialog and wait for OK or Cancel
    if myDlg.OK:  # or if ok_data is not None
        print(ok_data)
    else:
        print('user cancelled')
    sam_arousal.draw()
    mywin.flip()
    core.wait(2.0)
    myDlg = gui.Dlg(title="Evaluacion magnitud")
    myDlg.addText('Por favor, indique el impacto personal del\
    video anterior. Utilice la imagen como referencia.')
    myDlg.addField(
        'Puntuacion:', choices=['1', '2', '3', '4', '5', '6', '7', '8', '9'])
    ok_data = myDlg.show()  # show dialog and wait for OK or Cancel
    if myDlg.OK:  # or if ok_data is not None
        print(ok_data)
    else:
        print('user cancelled')

    event.clearEvents()

    if len(event.getKeys()) > 0 or (time() - start) > record_duration:
        break

# Cleanup
mywin.close()
