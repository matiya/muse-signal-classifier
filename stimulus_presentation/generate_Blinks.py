"""
Generate Auditory P300
======================

Auditory oddball paradigm stimulus presentation.

"""

from time import time
from optparse import OptionParser

import numpy as np
#from pandas import DataFrame
from psychopy import visual, core, event, sound, prefs
from pylsl import StreamInfo, StreamOutlet, local_clock

#prefs.general['audioDevice']=['HDA Intel PCH']
#prefs.general['audioDriver'] = [u'jack']
prefs.general['audioLib'] = ['pygame']

parser = OptionParser()
parser.add_option(
    "-d",
    "--duration",
    dest="duration",
    type='int',
    default=30,
    help="duration of the recording in seconds.")

(options, args) = parser.parse_args()

# Create markers stream outlet
info = StreamInfo('Markers', 'Markers', 1, 0, 'int32', 'myuidw43536')
outlet = StreamOutlet(info)
# 1 : No Parpadeo
# 2 :  Parpadeo
markernames = [1, 2]
start = time()

# Set up trial parameters
n_trials = 2010
iti = 0.3
soa = 0.2
jitter = 0.2
record_duration = np.float32(options.duration)

# Setup graphics
mywin = visual.Window(
    [900, 800], monitor='testMonitor', units='deg', fullscr=False)
# Initialize stimuli
aud1 = sound.Sound('C', octave=5, sampleRate=44100, secs=0.3, bits=8)
aud1.setVolume(0.8)
path_to_stimulus = '/home/default/Workspace/pfinal//stimulus_presentation/stim/timer.webm'
mov = visual.MovieStim3(
    mywin, path_to_stimulus, size=(800, 600), volume=1.0, noAudio=True)
start = time()
timestamp = time()

while mov.status != visual.FINISHED:
    mov.draw()
    mywin.flip()

    # Send blink marker every 3 seconds
    if ((round(time() - start, 2) % 3) <= 0.015
            and (abs(local_clock() - timestamp)) > 1):
        timestamp = local_clock()
        print("Blink", time() - start)
        aud1.play()
        outlet.push_sample([markernames[1]], timestamp)
    else:
        if ((round(time() - start, 2) % 2) <= 0.015
                and (abs(local_clock() - timestamp)) > 1):
            timestamp = local_clock()
            print("Non blink: ", time() - start)
            outlet.push_sample([markernames[0]], timestamp)
    if len(event.getKeys()) > 0 or (time() - start) > record_duration:
        break
    event.clearEvents()

mywin.close()
#core.quit()
