import cv2
import imutils
import numpy as np
from collections import namedtuple

from sheetScanner import Bubble, Sheet


class ActSection():
	"""
	Attributes and methods relating to a single ACT section. During processing,
	one of these classes will be instantiated for each section and will be used
	to process the bounding contours and enclosed bubbles.

	Expected values should be taken from a reference answer sheet and heuristic
	experimentation.

	
	Attributes
	----------
	code : str
		The section code. Should be one of 'e', 'm', 'r', 's'.

	expected : tuple
		Reference values pertaining to a section contour. The expected values
		are used to construct filters for extracting section contours.

		Fields
		------
		area : int 
			The expected area in pixels of the enclosing contour
		area_fraction : float
			A percentage from 0 to 1.0, used to determine a size threshold for
			distinguishing section contours from other contours.
			threshold = area_fraction * area
		aspect_delta : float
			An absolute deviation from an aspect ratio, usually a number 
			between 0 and 1.0. The delta is used to determine a threshold for
			distinguishing section contours.
			threshold = target +/- aspect_delta
		aspect_ratio : float
			The expected aspect ratio of the enclosing contour.
		x_bounds : tuple, (int, int)
			The expected domain where we expect to find the upper left corner
			of the section contour. Ex: x_bounds = (10, 120)
		y_bounds : tuple, (int, int)
			The expected range where we expect to find the upper left corner
			of the section contour. Ex: y_bounds = (300, 350)

	enclosing_contour : ndarray
		The contour enclosing a section. Contour attributes can be calculated
		and compared to expected values.

	sheet : Sheet
		A Sheet object storing the section's portion of the answer sheet. The
		section's sheet is a subset of the answer sheet image that will undergo
		further image processing. See class Sheet.

	bubble_contours : list, ndarray
		A list of opencv contours of answer bubbles

	bubble_params : tuple  
		((int,int), (int,int), (float,float), float)
		((wMin, wMax), (hMin, hMax), (arMin, arMax), circMin)
		Contains the expected min and max values of width, height, 
		aspect ratio, and min circularity of bubble contours

	bubbles : list, Bubble
		List of valid answer bubbles. See class Bubble.

	sectionMap : dict
		Key = (int) The question numbers
		Val = (list, Point)
		The coordinates of bubble centers for all questions
		Ex:	{q:[ Point(x,y), ... ], q:[...], ... } 

	num_questions : int
		The number of questions in the section

	group_length : int
		The number of answer choices for the questions.
		Ex: The choices A,B,C,D result in a group_length of 4

	grid : tuple, (int, int)
		The numbers of unique rows and columns for all answer bubbles in the 
		section. Each row/column aligns with the geometric centers of the 
		bubbles on that row/column.

	mask_shape : tuple,  (str, list[int]) 
		(shape, [dimensions])
		Ex 1: ('rectangle', [width, height])
		Ex 2: ('circle', [radius])

		A shape and its dimensions; used to mask answer bubbles when counting
		black and white pixels.

	white_epsilon : float 
		The fraction of white pixels at which to set the white suppression
		threshold. See SheetScanner.suppress_white()
			threshold = max_white * white_epsilon

	filter_params : tuple,  (float, float, int)
		(adaptive_epsilon, maximum_epsilon, black_threshold)
		adaptive_epsilon : float
			The % deviation from the average of black pixel counts
		maximum_epsilon : float
			The % deviation from the average of black pixel counts
		black_threshold : int
			The minimum number of black pixels required to consider a bubble
			filled.
		
		These parameters are used to compute 'filled' thresholds of the
		'adaptive', 'maximum', and 'threshold' filters. All 3 parameters are 
		required. See SheetScanner.extract_filled()

	answer_indices : dict
		Key = (str) One of 'adaptive', 'maximum', 'threshold'
		Val = dict
			K = (int)  The question numbers
			V = list, int/None
				The zero-based index of the filled-in bubbles

	confirmation_points : dict
		Key = (str) A filter label like 'adaptive', 'maximum', 'threshold'
		Val = (list, Point) The list of center points of the filled-in bubbles 

	"""

	Point = namedtuple('Point', ['x', 'y'])

	Expected = namedtuple('Expected', ['code', 'area', 'area_fraction', 
									   'aspect_delta', 'aspect_ratio', 
									   'x_bounds', 'y_bounds'])

	def __init__(self, expected_attributes=None, code=None, area=None, 
					area_fraction=None, aspect_delta=None, aspect_ratio=None, 
					x_bounds=(None, None), y_bounds=(None, None)):
		"""
		The constructor

		Parameters
		----------
		expected_attributes : dict
			For convenience, all of the following keyword args may be passed in 
			this dict. Keys are identical to parameter names. If this parameter
			is None, the dict is ignored and values are taken from the keyword
			args 

		code : str
			The section code, one of 'e', 'm', 'r', 's'

		area : int 
			The expected area in pixels of the enclosing contour

		area_fraction : float
			A percentage from 0 to 1.0, used to determine a size threshold for
			distinguishing section contours from other contours.
			threshold = area_fraction * area

		aspect_delta : float
			An absolute deviation from an aspect ratio, usually a number 
			between 0 and 1.0. The delta is used to determine a threshold for
			distinguishing section contours.
			threshold = target +/- aspect_delta
		
		aspect_ratio : float
			The expected aspect ratio of the enclosing contour.
		
		x_bounds : tuple, (int, int)
			The domain in which we expect to find the upper left corner
			of the section contour.
		
		y_bounds : tuple, (int, int)
			The range in which we expect to find the upper left corner
			of the section contour.
		"""
		if isinstance(expected_attributes, dict):  # pass args in dict
			d = expected_attributes
			self.code = d['code']
			self.expected = self.Expected(d['code'], d['area'], d['area_fraction'],
										  d['aspect_delta'], d['aspect_ratio'],
										  d['x_bounds'], d['y_bounds'])
		else:  # pass args as parameters
			self.code = code
			self.expected = self.Expected(code, area, area_fraction, aspect_delta, 
											aspect_ratio, x_bounds, y_bounds)

		self.enclosing_contour = None
		self.sheet = None
		self.bubble_contours = None
		self.bubble_params = [(14,16), (14,16), (0.9,1.1), 0.7]
		self.bubbles = []
		self.sectionMap = {}
		self.num_questions = None
		self.group_length = None
		self.grid = (None, None)
		self.mask_shape = (None,[])
		self.white_epsilon = None
		self.filter_params = (None, None, None)
		self.answer_indices = { 'adaptive':{}, 'maximum':{}, 'threshold':{} }
		self.confirmation_points = {}	

	pass


class ActSheet(Sheet, ActSection):
	"""
	Attributes and methods specific to ACT answer sheets.

	Attributes
	----------
	expected_section_attributes : dict
		Key = str : 'e', 'm', 'r', 's'
		Val = dict
			K = str : 'code', 'area', 'area_fraction', 'aspect_delta', 'aspect_ratio', 'x_bounds', 'y_bounds'
			V = str, int, float, float, float, tuple:(int, int), tuple(int, int)
		Contains reference sizes for the enclosing contours of each answer 
		sheet section. These sizes are used to instantiate ActSection objects.

	sections : dict
		Key = str : 'e', 'm', 'r', 's' 
		Val = ActSection
		Contains ActSection objects for each answer sheet section. Each object
		should be self contained and able to be processed solely with its own
		data. Each ActSection will contain a subset of the answer sheet image
		with which further processing will be done.

	submission : dict
		An encoded exam submission in the same format as ACT.submission
		Key = 'first', 'last', 'test_code', 'e', 'm', 'r', 's'
		Val = str*3, dict*4

	"""

	ASPECT_E = 3.596
	ASPECT_M = 3.896
	ASPECT_R = 5.500
	ASPECT_S = 5.500

	Point = namedtuple('Point', ['x', 'y'])

	def __init__(self, image):
		"""
		The constructor
		Parameter can be an opencv image (ndarray) or path to an image file

		Parameters
		----------
		image : str or ndarray 
			str = path/to/image.file
			ndarray = A numpy ndarray of depth 0, 1, or 3
		"""

		self.submission = {}
		self.mask_shape = ('circle', [6])
		self.white_epsilon = 0.65
		self.filter_params = (0.1, 0.1, 90)

		Sheet.__init__(self, image)
		
		e = {'code':'e', 'area':143386, 'area_fraction':0.95, 'aspect_delta':0.5, 'aspect_ratio':3.596, 'x_bounds':(30,70), 'y_bounds':(200,250)}
		m = {'code':'m', 'area':132356, 'area_fraction':0.95, 'aspect_delta':0.5, 'aspect_ratio':3.896, 'x_bounds':(30,70), 'y_bounds':(455,495)}
		r = {'code':'r', 'area':93752,  'area_fraction':0.95, 'aspect_delta':0.5, 'aspect_ratio':5.500, 'x_bounds':(30,70), 'y_bounds':(680,720)}
		s = {'code':'s', 'area':93752,  'area_fraction':0.95, 'aspect_delta':0.5, 'aspect_ratio':5.500, 'x_bounds':(30,70), 'y_bounds':(860,900)}
		self.expected_section_attributes = {'e':e, 'm':m, 'r':r, 's':s}

		e = ActSection(e)
		e.num_questions = 75; e.group_length = 4; e.grid = (11,28)
		e.mask_shape = self.mask_shape; e.white_epsilon = self.white_epsilon; e.filter_params = self.filter_params
		m = ActSection(m)
		m.num_questions = 60; m.group_length = 5; m.grid = (10,30)
		m.mask_shape = self.mask_shape; m.white_epsilon = self.white_epsilon; m.filter_params = self.filter_params
		r = ActSection(r)
		r.num_questions = 40; r.group_length = 4; r.grid = (7,24)
		r.mask_shape = self.mask_shape; r.white_epsilon = self.white_epsilon; r.filter_params = self.filter_params
		s = ActSection(s)
		s.num_questions = 40; s.group_length = 4; s.grid = (7,24)
		s.mask_shape = self.mask_shape; s.white_epsilon = self.white_epsilon; s.filter_params = self.filter_params

		self.sections = {'e':e, 'm':m, 'r':r, 's':s}
		self.section_labels = {'e':'ENGLISH', 'm':'MATH', 'r':'READING', 's':'SCIENCE'}


		pass


	def indices_to_answers(self, groups):
		"""
		Receives a dict or nested list of filled bubble indices representing a full section 
		and returns a json-formatted dict of letter answers with question numbers 
		as keys. Accepts ints 1-5

		Parameters
		----------
		groups : dict or list[list[int]] 
			Indices 1-5 of filled question bubbles
			Key = (int) question numbers
			Val = (list[int]) index of filled bubble

		Returns
		-------
		dict 
			Ex.  {1:"A", 2:"F", 3:"", 4:"GH", etc.}
		"""
		section = {}

		dOdd  = {1:'A', 2:'B', 3:'C', 4:'D', 5:'E'}
		dEven = {1:'F', 2:'G', 3:'H', 4:'J', 5:'K'}

		if type(groups) == list:
			for q, g in enumerate(groups):
				if g == [None]:  # if no bubbles filled
					section[q+1] = ""  # assign empty string
				else:  # if any bubbles are filled
					d = dOdd if (q+1)%2 == 1 else dEven
					tmp = ""  # empty string
					for i in g:
						tmp += d[i]  # append all letters
					section[q+1] = tmp
		elif type(groups) == dict:
			for q, g in groups.items():
				if g == [None]:  # if no bubbles filled
					section[q] = ""  # assign empty string
				else:  # if any bubbles are filled
					d = dOdd if (q)%2 == 1 else dEven
					tmp = ""  # empty string
					for i in g:
						tmp += d[i]  # append all letters
					section[q] = tmp

		return section


	def extract_section_area(self, section, contour, show_counts=False, show_contours=False):
		"""
		Identifies a single answer sheet section by its expected attributes and
		returns its bounding contour along with a Sheet object of the section
		area. If the expected contour is not found. Nothing is returned or 
		stored.

		In addition to returning the contour and Sheet, this method stores
		them in the ActSection object by default.

		This method accesses Sheet.all_contours and sorts those contours by 
		descending size, then subsets the 5 largest contours as section
		candidates. If this method fails to find the desired section area, 
		then either
		(1) The area_threshold and aspect_ratio filters need to be relaxed
		(2) There is a problem finding the contours in the first place --
			try running Sheet.extract_contours() with different binarization
			thresholds.


		Parameters
		----------
		section : ActSection
			An ActSection object containing the expected attributes that will
			identify the specific section contour.

		contour : ndarray
			The OpenCV contour that will be checked against the expected 
			attributes.

		Returns
		-------
		ndarray
			The bounding contour of the section

		Sheet
			A Sheet object of the section's subset of the answer sheet image
		"""
		esa = section.expected
		label = self.section_labels[section.code] 

		c = contour

		x,y,w,h = cv2.boundingRect(c)
		area = cv2.contourArea(c)
		ratio = float(w)/float(h)

		area_thresh = esa.area_fraction * area
		expected_aspect = esa.aspect_ratio
		delta = esa.aspect_delta
		xMin, xMax = esa.x_bounds
		yMin, yMax = esa.y_bounds

		if show_counts:
			print(f"x = {x}\t y = {y}\t w = {w}  h = {h}\t area = {area}   aspect = {round(ratio,5)}")

		if (self.within(y, yMin, yMax) and 
			area >= area_thresh and 
			self.close_to(ratio, expected_aspect, delta) and 
			self.within(x, xMin, xMax)
			):
			enclosing_contour = c
			sheet = Sheet(self.image[y:y+h, x:x+w])
			section.enclosing_contour = enclosing_contour
			section.sheet = sheet
			# print(f"Found {self.section_labels[esa.code]} \n")

			if show_contours:
				self.show_contours(self.image, f"{label} Contour", [c], 2)

			return enclosing_contour, sheet

		return None

	
	def indices_to_submission(self, sections=None, test_code=None, first=None, last=None):
		"""
        Converts the answer indices of all sections to an ACT submission
        suitable for passing to the ACT grader. If 'sections' == None, 
        this method automatically reads the indices from 

        self.sections[code].answer_indices['maximum']

        See Parameters --> sections for the correct format of this input parameter

        If any other params are None, the None value will be inserted into the 
        output dict. This allows the ActSheet class to remain independent of
        any specific person or exam. Identifying information may be passed to 
        this method or inserted later in the pipeline before the submission
        is passed to the Act (Grader) class.

        At this point, indices are taken from the 'maximum' filter. In the 
        future, this may be replaced by a heuristic method that calculates the 
        most likely candidate based on all the filters. 

        Parameters
        ----------
		sections : dict
			Key = (str) : 'e', 'm', 'r', 's'
			Val = ActSection*4

			The ActSection object contains the dict 'answer_indices' as an
			attribute.
				K = (str) : 'adaptive', 'maximum', 'threshold'
				V = dict*3

				Each dict contains question nums & lists of filled bubbles
					K = (int)  The question numbers
					V = list, int/None
					The zero-based index of the filled-in bubbles

        test_code : str
        	An ACT test code of format yyyymm

        first : str
		A student's first name

		last : str
			A student's last name


        Returns
        -------
        dict
        	Key = (str) : 'first', 'last', 'test_code', 'e', 'm', 'r', 's'
			Val = str*3, dict*4
			The emrs keys contain dict values:
				K = int  # question number
				V = str  # 'ABCDE' or '12345' representing submitted answers


		Examples
		--------

        """
		if not sections:
			sections = self.sections

		sub = {"first":"", "last":"", "test_code":"", "e":{}, "m":{}, "r":{}, "s":{}}

		if test_code:
			sub['test_code'] = test_code 
		else: 
			sub['test_code'] = ''

		if first:
			sub['first'] = first 
		else: 
			sub['first'] = ''

		if last:
			sub['last'] = last 
		else: 
			sub['last'] = ''


		for code, section in sections.items():
			assert code in ('e', 'm', 'r', 's')

			indices = section.answer_indices['maximum']
			answers = self.indices_to_answers(indices)

			sub[code] = answers

		return sub
		

	def build_submission(self, image=None, test_code=None, first=None, last=None):
		"""
		Wrapper method - accepts an image parameter and returns a json-formatted
		dict of all answers to an entire ACT exam. If the image param is None,
		this method automatically reads it from self.image

		Parameters
		----------
		image : ndarray

		test_code : str
        	An ACT test code of format yyyymm

        first : str
		A student's first name

		last : str
			A student's last name


		Returns
		-------
		dict
        	Key = (str) : 'first', 'last', 'test_code', 'e', 'm', 'r', 's'
			Val = str*3, dict*4
			The emrs keys contain dict values:
				K = int  # question number
				V = str  # 'ABCDE' or '12345' representing submitted answers

		"""
		try:
			len(image)
		except TypeError:
			image = self.image

		# process the answer sheet
		for c in self.all_contours[0:5]:
			for code in self.sections.keys():
				self.extract_section_area(self.sections[code], c)

		for code, section in self.sections.items():
			s = self.sections[code].sheet
			contours = s.contours_from_section(s.image, s.all_contours[0])
			contours = s.extract_circles(contours, 100, 0.5)

			bp = section.bubble_params
			bubbles = s.contours_to_bubbles(contours, bp[0], bp[1], bp[2], bp[3])
			section.bubbles = bubbles

			sMap = s.build_sectionMap(bubbles, section.grid, section.num_questions, 
                                        section.group_length)
			section.sectionMap = sMap
			indices = s.generate_filled_indices(sMap, section.mask_shape, 
                                              section.white_epsilon, 
                                              section.filter_params, False)
			section.answer_indices = indices

		sub = self.indices_to_submission(None, test_code, first, last)
		
		return sub


	def submission_to_json(self, submission):
		"""
		Converts an ACT submission to a json-compliant string formatted 
		according to my idiosyncratic preferences.

		Parameters
		----------
		submission : dict
			An ACT exam submission
			Keys = 'first', 'last', 'test_code', 'e', 'm', 'r', 's'
			Vals =  str * 3, dict * 4
				K = int
				V = str

		Returns
		-------
		str
			The submission as a json-compliant string

		"""
		assert isinstance(submission, dict)

		sub = submission
		first, last, tc = sub['first'], sub['last'], sub['test_code']

		# print(sub)

		# Write the json
		m = '{\n'
		m += f'  "first": "{first}",\n'
		m += f'  "last": "{last}",\n'
		m += f'  "test_code": "{tc}",\n\n'
		
		# add questions + answers for all sections
		for code in ('e', 'm', 'r', 's'):
			m += f'   "{code}": ' + '{\n'

			for q, a in sub[code].items():
				m += f'\t   "{q}":'

				# insert spaces for single or double digit rows
				if q < 10: 
					m += f'  '  
				else:
					m += f' '
				m += f' "{a}"'

				if q < len(sub[code]): # not final question, trailing comma
					m +=  ',\n'
				else:  # final question, no trailing comma
					m +=  '\n'

			# add closing braces
			if code != 's':  # not final section
				m += '\t},\n\n'
			else:
				m += '\t}\n}\n\n' # final section (science)

		return m


	def get_sheet_confirmation(self, filter_name: str, sections: dict=None) -> list:
		"""
		Kind of a wrapper method. Transforms the bubble coordinates from section
		coordinates to sheet coordinates by adding the (x,y) coordinates of the
		enclosing contour's bounding box to each point in the section confirmation.

		This method will first try to find existing confirmation points in 
		self.sections[section_code].confirmation_points. If that fails, then
		get_section_confirmation() will be called on each section.

		Parameters
		----------
		filter_name : str
			One of 'adaptive', 'maximum', 'threshold'.
			The section

		sections : dict
			Key = any
			Val = dict
				K = (str) 'enclosing_contour', 'section_map', 'answer_indices'
				V = ndarray, dict, dict

			If 'sections' is None, this method will iterate through everything 
			in self.sections. If 'sections' is specified, it must contain the
			keys 'enclosing_contour' : opencv contour, 
				 'sectionMap' : a valid section map
				 'answer_indices' : {filter_name : list[Point]}
				 'confirmation_points' : dict
			For more information, see the ActSection class. If 
			'confirmation' points exists and is valid, then 
			'enclosing_contour' is used, but the remaining keys are never 
			accessed and may be (un)safely omitted.


		Returns
		-------
		list[Point]
			The list of x,y coordinates of the filled-in bubbles, with respect
			to the entire exam answer sheet, for all sections.

		"""
		# cv2.imshow("Sheet Confirmation By Method", self.image)
		# cv2.waitKey(0)
		# cv2.destroyAllWindows()
		if sections is None: sections = self.sections

		sheet_confirmation = []

		for sec in sections.values():

			if filter_name in sec.confirmation_points.keys():
				sec_conf = sec.confirmation_points[filter_name].copy()

				if not 'Point' in repr(sec_conf[0]):
					sec_conf = self.get_section_confirmation(sec.sectionMap, sec.answer_indices)

			else:
				sec_conf = self.get_section_confirmation(sec.sectionMap, sec.answer_indices)
				sec_conf = sec_conf[filter_name]


			x0, y0, _, _ = cv2.boundingRect(sec.enclosing_contour)
			for i, p in enumerate(sec_conf):
				sec_conf[i] = self.Point(p.x+x0, p.y+y0)

			sheet_confirmation += sec_conf

		return sheet_confirmation


	def show_sheet_confirmation(self, image, confirmation_points: list, rect_dims: tuple, show_image: bool=False, title: str=""):
		"""
		Wrapper method. 
		Generates a confirmation image by drawing red rectangles around each
		filled-in bubble. Returns the confirmation image by default in BGR 
		format (3 color channels), but can also display the confirmation image
		if show_image is True.

		NOTE: The input image is copied, not modified in place.

		Parameters
		----------
		image : ndarray
			An image of the exam sheet showing question numbers and answer 
			bubbles.

		confirmation_points : list, Point
			The center points of the filled-in bubbles.

		rect_dims : tuple, (int,int) 
			Dimensions of the rectangles (w,h) to draw. Both dims must be 
			even numbers.

		show_image : bool
			If True, show the confirmation image

		title : str
			The title of the image to be displayed; only used if show_image is
			True.

		Returns
		-------
		ndarray
			The sheet image with red rectangles drawn around each filled
			bubble that was detected. 
		"""

		conf = self.show_section_confirmation(image, confirmation_points, rect_dims, show_image, title)
		return conf


	
##########################################
	