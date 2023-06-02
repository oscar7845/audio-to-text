import yaml
import os

#---------------------#
# Constants and fixed #
#---------------------#

# Store text file when done, params to empty dict if empty
app_params = "current_app_params.yaml"
params = yaml.safe_load(open(app_params, 'r')) if os.path.exists(app_params) else {}

# Constants
# PEAK_POW = 5000
AUDIO_SAMPLING_FREQ = 16000
FPB = 1024
LARGEST_SHORT_INT16 = 32767 #2**15

