# coding: utf-8

# In[1]:

# Importaciones iniciales
import sys
from collections import OrderedDict

from mne import create_info, concatenate_raws
from mne.io import RawArray
from mne.channels import read_montage

import pandas as pd
import numpy as np

from glob import glob
import seaborn as sns
from matplotlib import pyplot as plt

# importar utilidades de muse-lsl
sys.path.append('../muse')
import utils

#get_ipython().magic(u'matplotlib inline')

# ## Cargar datos desde muse
# Se pueden leer datos del dispositivo y guardarlos en un .csv con la utilidad de `lsl-record.py.`
#
# Ejemplo: `python stimulus_presentation/generate_Visual_P300.py & python lsl-record.py -d 60`
#
# Un problema de esta utilidad es que espera un canal de eventos (markers). En este ejemplo dicho canal es provisto por generate_Visual_P300.py que es un evento propio del repositorio original

# ## Cargar datos CSV
# muse-lsl tiene una utilidad propia para cargar los datos de un .csv. Para utilizarla primero se deben guardar los datos bajo el directorio "data/<nombre>" e invocar la función utils.load_data(). La misma leerá todos los .csv bajo el directorio pasado como argumento y devolverá un objeto del tipo mne.raw.

# In[10]:

subject = 1
session = 1

raw = utils.load_data(
    'Test_EEG',
    sfreq=256.,
    subject_nb=subject,
    session_nb=session,
    ch_ind=[0, 1, 2, 3])
raw

# In[11]:

#raw.plot_psd(tmax=np.inf)

# Como puede verse, existe un pico en 50Hz y un armónico en 100Hz.
# ## Filtrado
#
# Para eliminar información que no necesitamos, filtramos entre 1 y 40Hz

# In[12]:

raw.filter(1, 40, method='iir')
#raw.plot_psd(tmax=np.inf)

# ## Epoching
# Se dividen los registros en Epochs entre -100ms y 800ms luego del evento. No se hace corrección a la baseline y se rechazan los eventos mayores a 100uV (mayormente parpadeos)

# In[65]:

from mne import Epochs, find_events

events = find_events(raw, output='offset')
#elimino el último porque puede quedar cortado
#events = events[5:6]
event_id = {'Parpadeo': 1}
#normalmente la función de abajo toma otro comando reject = {eeg=some_value} para eliminar los epochs con ruido.
epochs = Epochs(
    raw,
    events=events,
    event_id=event_id,
    tmin=-0.14,
    tmax=0.4,
    baseline=None,
    preload=True,
    verbose=True)  #, picks=[0,1,2,3])

# In[66]:

epochs.plot(block=True)

# In[35]:

events[2:-1]

# In[33]:

events

# In[ ]:
