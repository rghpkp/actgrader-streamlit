#

import os
import pickle
import argparse 

ap = argparse.ArgumentParser()
ap.add_argument('--inFile', '-i', required=False, help='path/to/input/file')
args = vars(ap.parse_args())

if args['inFile']: # if a scoring table is specified, pickle it
    inFile = args['inFile']
    outfile = inFile.split('.')[0] + '.pkl'
    
    exec( open(inFile).read() )  # loads the 'scoring_table' variable

    with open(outfile, 'wb') as f:
        pickle.dump(scoring_table, f)

else:  # pickle all scoring tables in 'scoring_table' dir
    for st in os.listdir('scoring_tables'):
            if st.endswith('.py'):
                    name = st.split('.')[0] + '.pkl'
                    name = 'scoring_tables/' + name

                    exec( open('scoring_tables/'+st).read() )

                    with open(name, 'wb') as f:
                            pickle.dump(scoring_table, f)

print(f"\n{outfile} written \n")
