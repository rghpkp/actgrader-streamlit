import os, sys
import numpy as np
from sklearn.cluster import KMeans
from collections import namedtuple

sys.path.append('./classes')



class SheetUtilities():
    """
    Non-Image methods for working with ACT answer sheets. Contains methods
    for comparing numbers, converting lists to dicts, etc.
    """

    Point = namedtuple('Point', ['x', 'y'])



    def __init__(self):
        pass


    def listToDict(self, aList):
        """
        Stores list values in a dict with: key = (index+1)

        Parameters
        ----------
        aList : list
            A list of anything

        Returns
        -------
        dict
            A dict compatible with the 'ACT Scorer module'. 
            Keys are 1-indexed to match question numbers.
        """
        d = {}

        for i,v in enumerate(aList):
            k = i+1
            d[k] = v

        return d



    def within(self, element, minimum, maximum, inclusive=False):
        """
        Checks whether a target element is within the given range.
        Used primarily for filtering aspect ratios. Non-numeric types
        are implicitly cast to numerics in the LLVM.

        Parameters
        ----------
        element : any
            The element (primitive type) to check
        minimum : any
            The lower boundary
        maximum : any
            The upper boundary
        inclusive : bool 
            Whether the target can be equal to the min and max

        Returns
        -------
        bool
            True if the element is in between the maximum and minimum
            False otherwise

        """
        if inclusive == False:
            if minimum < element and element < maximum:
                return True
        elif inclusive == True:
            if minimum <= element and element <= maximum:
                return True
        
        return False



    def close_to(self, element, target, delta, inclusive=False):
        """
        Checks whether an element is within one delta of the target.
        Primarily used for filtering aspect ratios.

        Parameters
        ----------
        element : int, float 
            The number that will be checked against the target
        target : int, float 
            The target value
        delta : int, float
            The distance between the element and target (full domain = 2*delta)
        inclusive : bool
            Whether to include the domain boundaries (target +/- delta)

        Returns
        -------
        bool 
            True if the element is within 1 delta of the target
            False otherwise

        Examples
        --------
        >>> self.close_to( 5, target=7, delta=2, inclusive=False )
            False

        >>> self.close_to( 5, target=7, delta=2, inclusive=True )
            True
        """
        minimum = target - delta
        maximum = target + delta

        return self.within(element, minimum, maximum, inclusive)



    def kmeans_centers(self, values, clusters, iterations=4):
        """
        Groups all values into 'clusters' number of clusters and returns the 
        centroids of all the clusters, each rounded to the nearest integer. 

        Parameters
        ----------
        values : list, int
            The values to group into clusters
        clusters : int  
            The number of clusters to force the values into
        iterations : int  
            The number of iterations of the KMeans algorithm.
            More iterations is slower but more accurate.

        Returns
        -------
        list, int 
            The median value of each cluster, rounded to the nearest integer

        Examples
        --------
        # Group 4 values into 2 clusters
        >>> self.kmeans_centers( values=[23.1, 23.3, 100.8, 100.9] , clusters=2) 
        [23, 101]
        """
        V = np.unique(np.array(values))
        vArray = np.array(list(zip( V, list(range(0, len(V))) )))
        model = KMeans(init="k-means++", n_clusters=clusters, n_init=iterations, random_state=0).fit(vArray)
        vCentroids = sorted([ int(c + 0.5) for c in model.cluster_centers_[:,0] ])

        return vCentroids



    def xCoordinates_to_groups(self, xCoords, row_length):
        """
        Receives a flat list of values and returns a list of lists of values.
        The inner list has length 'row_length' and represents 
        (the x-coordinates) of a single row of exam answer bubbles. 

        Parameters
        ----------
        xCoords : list, int 
            A flat list of integers representing x-coordinates

        row_length : int 
            The number of bubbles in a single row/group; also the length of the
            inner lists that are returned.

        Returns
        -------
        list[list, list, ...] 
            A list of lists. The inner list has length 'row_length', and represents
            some group of numbers: typically the x-coordinates of the 4 bubbles in a
            single ACT question.

        Examples
        --------
        # Segment 6 sorted values into groups of length 3
        >>> self.xCoordinates_to_groups( values=[1,2,3,4,5,6], row_length=3)
        [[1,2,3], [4,5,6]]
        """
        groups = []
        i = 0
        while i < len(xCoords):
            row = []    
            # iterate along each row
            for offset in range(0, row_length):
                row.append( xCoords[i + offset] )
            groups.append(row)
            i += row_length

        return groups



    def coordinates_to_points(self, xGroups, yCoords, num_questions):
        """
        Generates a map of bubble positions for an exam indices. A bubble 
        position is defined as the (x,y) location of the center of the 
        bubble contour's bounding box. Each location is stored in the named
        tuple: Point(x,y). Each dict key contains a list of Points, length 
        determined by the group length in 'xGroups'

        The parameter xGroups contains lists of x-coordinates; yCoords contains
        y-coordinates. The returned map is created by combining all the 
        x and y coordinates to generate a grid of unique Point objects 
        representing all the answer bubbles for an ACT indices of length
        'num_questions'.

        Parameters
        ----------
        xGroups : list[list, list, ...], int 
            A nested list of rows of x-coordinates representing all column groups 
            in a indices.

        yCoords : list, int
            A flat list of y-coordinates representing all rows in a indices

        num_questions : int
            The total number of questions in a test indices

        Returns
        ------- 
        dict
            Key = question number
            Value = list of Point tuples; list has same length as inner lists
            of 'xGroups'
            { 1:[Point(x,y), Point(x,y) ...], 2:[Point(x,y), ... ], ... }

        See Also
        --------
        kmeans_centers
        xCoordinates_to_groups
        """
        sMap = {}

        q = 1
        for group in xGroups:
            for y in yCoords:
                if q > num_questions: break
                row = []
                for x in group:
                    p = self.Point(x,y)
                    row.append(p)
                sMap[q] = row
                q += 1

        return sMap



    def indices_to_json(self, indices, flag):
        """
        Receives a flat dict of answer indices and converts it to a string of
        valid json suitable for writing to a json file.

        Parameters
        ----------
        indices : dict
            A dictionary of submitted answers (filled-in bubbles) to multiple
            choice questions.
            Key = int   # The question number
            Val = list, int/None  IF flag == numbers
            Val = string          IF flag == letters

        flag : string 
            Determines which kind of input to accept.
            Values = {'numbers', 'letters'}
            Ex: 'numbers' -->  indices = {1:[None], 2:[4], 3:[1,3]}  
            Ex: 'letters' -->  indices = {1:'', 2:'J', 3:'AC'}

        Returns 
        -------
        str
            A string of valid json

        Examples
        --------
        >>> self.indices_to_json(indices={1:[None], 2:[4], 3:[1,3]}, flag='numbers')
        '\t   "1":  "",\n\t   "2":  "4",\n\t   "3":  "1 3"\n'

        >>> self.indices_to_json(indices={1:'', 2:'J', 3:'AC'}, flag='letters')
        '\t   "1":  "",\n\t   "2":  "J",\n\t   "3":  "AC"\n'
        """
        m = ""
        if flag == 'numbers':
            for q, row in indices.items():
                m += f'\t   "{q}": '
                if q < 10: m += ' '
                m += '"'
                if row[0] == None:
                    pass
                else:
                    ctr = 1  # counter for handling multiple answers
                    for index in row:  # iterate through the row
                        m += f'{index}'
                        if ctr < len(row): 
                            m += ' '  # intermediate space
                        ctr += 1
                    # end row iteration

                if q == len(indices):  # final question
                    m += '"\n'  # closing double quote, no trailing comma
                else:  # not final question
                    m += '",\n'  # closing double quote, trailing comma

        elif flag == 'letters':
            for q, string in indices.items():
                m += f'\t   "{q}": '
                if q < 10: m += ' '
                m += f'"{string}"'
                if q < len(indices):  # final question
                    m += ','  # trailing comma
                m += '\n'  # closing double quote, trailing comma

        return m



    

    















