# st2pkl.py
#
# Loads a scoring table from its .py file and dumps it to a .pkl with the same name
#
# Ex: python st2pkl.py -st st_ACT_123456.py

# UNTESTED

import pickle
import argparse 

ap = argparse.ArgumentParser()
ap.add_argument('--scoring_table', '-st', required=True, help='path/to/scoring/table/file.py')
args = vars(ap.parse_args())

inFile = args['scoring_table']
outFile = inFile.split('.')[0] + '.pkl'

exec( open(inFile).read() )  # loads the 'scoring_table' variable

with open(outfile, 'wb') as f:
    pickle.dump(scoring_table, f)

