
import os


CHECKSUMLEN = 10
WORKFOLDER = 'fluf'


FLUFCACHEFOLDER = os.path.join(os.path.expanduser('~'), '.cache', 'fluf')
if not os.path.exists(FLUFCACHEFOLDER):
    os.makedirs(FLUFCACHEFOLDER)
