import cv2
import imutils
import numpy as np
from sklearn.cluster import KMeans
from collections import namedtuple

from sheetUtilities import SheetUtilities






class Bubble():
	"""
	Assumes that any contour is a test bubble and computes the
	bounding rectangle, Moments, center, aspect ratio, and polar
	coordinates of its center.
	"""
	def __init__(self, contour):
		self.contour = contour

		self.area = cv2.contourArea(contour)
		self.perimeter = cv2.arcLength(contour, closed=True)
		self.circularity = 4*np.pi*self.area * self.perimeter**(-2) 

		x,y,w,h = cv2.boundingRect(contour)
		M = cv2.moments(contour)
		cX = int( M["m10"] // M["m00"] )
		cY = int( M["m01"] // M["m00"] )
		self.x = x
		self.y = y
		self.w = w
		self.h = h
		self.aspect_ratio = w/h
		self.center = (cX,cY)
		self.moments = M
		# polar is (r, theta) coordinates
		self.polar = ( np.linalg.norm( (cX, cY) ) , np.degrees( np.arctan(cY/cX) ) )
		self.pixel_count = None



class Sheet(Bubble, SheetUtilities):
	"""
	Methods for processing any answer sheet. Assumes that the sheet contains
	answer bubbles.
	"""

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
		if isinstance(image, str):
			self.image = cv2.imread(image)
		if isinstance(image, np.ndarray):
			self.image = image

		p = self.preprocess()
		self.gray = p[0]
		self.edges = p[1]
		self.binary = p[2]
		self.inverted = p[3]
		self.all_contours = self.extract_contours()
		self.all_contours = self.sort_contours_by_size(self.all_contours)


	def preprocess(self, image=None, binary_threshold=225):
		"""
		Creates some helper images. The same threshold is used to create both
		the binary and inverted images.
		(1) Grayscale image
		(2)	Edges via the Canny algorithm
		(3) Binary image
		(4) Inverted binary image.

		Parameters
		----------
		image : ndarray, None
			Any image. If an image is not passed, the original image from the
			instance members is used.

		binary_threshold : int
			Value (0 to 255) used to threshold the image. The same value is
			used for both binary and inverted binary thresholding.

		Returns
		-------
		ndarray
			A grayscale image.

		ndarray
			An image with edges emphasized via the Canny algorithm.

		ndarray
			A binary black and white image.

		ndarray
			An inverted binary white and black image.
		"""
		try:
			len(image)
		except TypeError:
			image = self.image

		# If RGB, convert to gray
		if len(image.shape) == 3:
			gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
		else:
			gray = image

		edges = cv2.Canny(gray, 30, 150)
		binary = cv2.threshold(gray, 225, 255, cv2.THRESH_BINARY)[1]
		inverted = cv2.threshold(gray, 225, 255, cv2.THRESH_BINARY_INV)[1]
		return gray, edges, binary, inverted


	def get_circularity(self, contour):
		"""
		Computes the circularity (a.k.a. roundness) of a contour according to 

			circularaity = 4*pi*area / (perimeter**2)

		Parameters
		----------
		contour : ndarray
			An OpenCV contour

		Returns
		-------
		float
			The circularity of the contour
		"""
		area = cv2.contourArea(contour)
		perimeter = cv2.arcLength(contour, closed=True)
		circularity = 4*np.pi*area * perimeter**(-2)
		return circularity


	def extract_contours(self, image=None, threshold=0, maxval=255):
		"""
		Finds all external contours in an image. The inverted binary of the
		input image will be computed using the given threshold and maxval
		parameters

		Parameters
		----------
		image : ndarray
			The image in which to find the contours. If the image is BGR, it 
			will be converted to grayscale. If image is None, self.gray will be
			used.

		threshold : int
			The binary threshold. This param will be passed to cv2.threshold()

		maxval : int
			The maximum white value (Default is 255). This param will be passed 
			to cv2.threshold()

		"""
		if image is None:
			gray = self.gray
		elif len(image.shape) == 3:  # convert img to grayscale if it isn't already
			gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
		elif len(image.shape) == 2:
			gray = image
		else:
			# something has gone horribly wrong
			pass	

		inverted = cv2.threshold(gray, threshold, maxval, cv2.THRESH_BINARY_INV | cv2.THRESH_OTSU)[1] # doesn't work on BW test shapes, use binary from self.preprocess() instead
		all_contours = cv2.findContours(inverted, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
		all_contours = imutils.grab_contours(all_contours)
		
		return all_contours


	def extract_circles(self, contours, min_area=1, min_circularity=0):
		"""
		Receives a list of contours and returns a list of contours that are 
		circles. Unfiltered lists of contours can contain contours of single
		points, which have areas and perimeters of zero. These point contours
		will cause division by zero errors in the circularity calculation, so
		this method implicitly filters them out. Judiciously setting the 
		minimum area threshold also helps identify nice circular contours.

		Note 1: Setting min_area=0 will probably crash this method. 
		Note 2: Using the default parameters will filter out single pixel 
				points and retain all larger contours.

		Parameters
		----------
		contours : list, ndarray
			A list of OpenCV contours from which to extract the circular
			contours

		min_area : int
			The minimum area (in pixels) that a contour must have in order to 
			be a candidate for being a circle. 
			Note: Setting min_area=0 will probably cause a division-by-zero
			error.

		min_circularity : float
			The minimum roundness in order to consider a contour a circle. The
			circularity will always be a number between 0 and 1. Due to 
			rasterization of png images, circular contours rarely have a 
			circularity approaching 1.0; the circularity of a circle contour 
			decreases as its radius decreases. 

			Ex: A good threshold for 15x15 pixel circles is 0.7. 

		Returns
		-------
		list, ndarray
			A list of contours representing (approximately) perfect circles. If
			no circles are found, an empty list is returned.
		"""

		# It's efficient to process this list in place, so reverse-traverse it.
		for i in range( len(contours)-1, -1, -1 ):
			c = contours[i]

			if cv2.contourArea(c) < min_area:
				del contours[i]  # Remove the contour if it's too small
				continue	     # Skip to the next loop iteration
			else:
				circ = self.get_circularity(c)

			if  circ < min_circularity:
				del contours[i]  # Remove the contour if it isn't a circle

		return contours


	def sort_contours_by_size(self, all_contours, descending=True):
		"""
		Sorts contours by size. Default is descending order.

		Parameters
		----------
		all_contours : list, ndarray
			A list of OpenCV contours. Ideally all the external contours on an
			ACT answer sheet.

		descending : bool
			If True  --> sorts in descending size order
			If False --> sorts in ascending  size order

		Returns
		-------
		list, ndarray
			The input list of contours, sorted by size
		"""
		return sorted(all_contours, key=cv2.contourArea, reverse=descending)


	def show_contours(self, image, title, contours, line=-1):
		"""
		Draws contours for visual inspection. Exits on Esc.

		Parameters
		----------
		image : ndarray 
			The image to draw on

		title : str 
			A title for the display window

		contours : list, ndarray 
			The list of contours to draw

		line : int 
			The line weight. -1 == filled
		"""
		if len(image.shape) == 2:  # grayscale
			image = cv2.cvtColor(image, cv2.COLOR_GRAY2BGR)

		for c in contours:
			img = image.copy()
			cv2.drawContours(img, [c], -1, (0,0,255), line)
			cv2.imshow(title, img)

			# DEBUGGING CODE
			# x,y,w,h = cv2.boundingRect(c)
			# area = w*h
			# ratio = w/h
			# print(f"x = {x}\t y = {y}\t w = {w}  h = {h}\t area = {area}   aspect = {round(ratio,5)}")

			if cv2.waitKey(0) == 27:  # Esc will kill the method
				break
		cv2.destroyAllWindows()
		return True


	def show_bubbles(self, image, title, bubbles, individual=False):
		"""
		Displays bubble contours for visual inspection, exits on Esc

		Parameters
		----------
		image : ndarray 
			The image to draw on

		title : str 
			A title for the display window

		bubbles : list, Bubble
			The list of Bubble objects to draw

		individual : bool 
			If True, shows the bubbles one-at-a-time
			If False, shows them all at once (faster)
		"""
		if len(image.shape) == 2:  # grayscale
			image = cv2.cvtColor(image, cv2.COLOR_GRAY2BGR)

		if individual:
			for b in bubbles:
				print("w =", b.w, "  h =", b.h, "  aspect =", b.w/b.h)
				img = image.copy()
				cv2.drawContours(img, [b.contour], -1, (0,0,255), -1)
				cv2.imshow(title, img)
				if cv2.waitKey(0) == 27:  # exit on Esc
					break
		elif not individual:
			img = image.copy()
			for b in bubbles:
				cv2.drawContours(img, [b.contour], -1, (0,0,255), -1)
			cv2.imshow(title, img)
			cv2.waitKey(0)
			cv2.destroyAllWindows()
		else:
			return False

		return True


	def show_rectangles(self, image, title, coordinates, rect_dims, individual=False):
		"""
		Displays bounding box-ish rectangles at the locations of exam bubbles,
		exits on Esc.
		
		Parameters
		----------
		image : ndarray 
			The image to draw on

		title : str 
			A title for the display window

		coordinates : list, dict - Point(x,y)) 
			The center Points of the bubble contours. The coordinates must be
			in a list or dict, otherwise a TypeError will be raised.

		rect_dims : tuple, (int,int) 
			Dimensions of the rectangles (w,h) to draw. Both dims must be 
			even numbers.

		individual : bool 
			If True, shows the bubbles one-at-a-time
			If False, shows them all at once (faster)

		returns : ndarray
			The image with the rectangles drawn on it.
		"""
		if (not isinstance(coordinates, list)) and (not isinstance(coordinates, dict)):
			raise TypeError("The coordinates must be a list or dict")

		if len(image.shape) == 2:  # if image is grayscale
			image = cv2.cvtColor(image, cv2.COLOR_GRAY2BGR)

		w, h = rect_dims[0], rect_dims[1]

		if (w%2 != 0) or (h%2 != 0):
			raise ValueError("The width and height must both be even numbers.")
		else:
			pass

		dx = int(w/2); dy = int(h/2);
		img = image.copy()

		# Convert the coordinates to a list and drop Nones if necessary
		if isinstance(coordinates, dict):
			boxes = []
			for row in coordinates.values():
				for point in row:
					if point is not None:
						boxes.append(point)
			coordinates = boxes

		if individual:
			for b in coordinates:
				cv2.rectangle(img, (b.x-dx,b.y-dy), (b.x+dx,b.y+dy), (0,0,255), 1)
				cv2.imshow(title, img)
				if cv2.waitKey(0) == 27:  # exit on Esc
					break
			cv2.destroyAllWindows()
		elif not individual:
			for b in coordinates:
				cv2.rectangle(img, (b.x-dx,b.y-dy), (b.x+dx,b.y+dy), (0,0,255), 1)
				cv2.imshow(title, img)

			if cv2.waitKey(0) == 27: 
				cv2.destroyAllWindows()
		else:
			return False

		return img


	def show_sectionMap(self, image, title, sMap, bubble_dims, individual=False):
		"""
		Displays rectangles at the bubble positions stored in the section map.
		Used to check that the sectionMap is accurate.

		Parameters
		----------
		image : ndarray 
			The image to draw on

		title : str 
			A title for the display window

		sMap : dict, list, Point(x,y) 
			The coordinates of all bubble locations (centers) within a section.
			key : int
				A question number
			val : list, Point(x,y)
				The list of bubble centers of the answer choice options.
			Ex: {1:[Point(x,y), ...],  .... n:[Point(x,y), ...]}


		bubble_dims : tuple, (w,h) 
			The pixel width and height of the bubble rectangles to draw (w,h)

		individual : bool 
			If True, shows the bubbles one-at-a-time
			If False, shows them all at once (faster)							
		"""
		points = []
		for group in sMap.values():
			for p in group:
				points.append(p)
		self.show_rectangles(image, title, points, bubble_dims, individual=individual)

		return True


	# @TODO write this method
	def show_section_confirmation(self, image, section_label, filter_label, destroy_window=False):
		"""
		Displays the confirmation image(s)

		Parameters
		----------
		image : ndarray
			The section image with red rectangles drawn around each filled
			bubble that was detected. 

		section_label : str
			The name of the exam section, one of 'ENGLISH', 'MATH', 'READING', 
			'SCIENCE'.

		filter_label : str
			The name of the filter that was used to identify the filled bubbles.
			One of 'adaptive', 'maximum', 'threshold'.
			See self.generate_filled_indices()

		destroy_window : bool
			Whether to destroy or retain the window after function exit

		Returns
		-------
		bool
			True if the function executes properly (displays an image),
		"""
		conf_label = str.join(' ', (section_label, filter_label))
		cv2.imshow(conf_label, image)
		cv2.waitKey(0)

		if destroy_window:
		    cv2.destroyWindow(conf_label)

		return True


	def contours_to_bubbles(self, all_contours, width=(12,13), height=(8,9), aspect=(1.3,1.5), circularity=0):
		"""
		Converts contours to Bubble objects IF the contour falls within a
		particular size, aspect ratio, and circularity. The default parameter
		values correspond to a bubble image used in early unit testing. There
		is nothing special about them.

		Parameters
		----------
		all_contours : list, ndarray 
			Closed contours (numpy arrays)

		width : tuple, int 
			Min and max widths in pixels: (w1, w2) --> w1 <= w <= w2

		height : tuple, int
			Min and max heights in pixels: (h1, h2) --> h1 <= h <= h2

		aspect : tuple, float
			Min and max aspect ratios: (a1, a2) --> a1 <= ar <= a2
			An aspect ratio is width/height. 
			The aspect ratio of a perfect circle is 1.0	

		circularity : float
			The minimum threshold for circularity. 
			Circularity = 4π*area/perimeter^2
			A perfect circle has circularity of 1.0. The lower the circularity,
			the more deformed a shape can be. Setting circularity equal to 0
			essentially deactivates this filter.


		Returns
		-------
		list, Bubble
			A list of Bubble objects, representing answer sheet bubbles. 
			See class 'Bubble'
		"""
		w1, w2 = width
		h1, h2 = height
		a1, a2 = aspect
		bubbles = []

		for c in all_contours:
			area = cv2.contourArea(c)
			perimeter = cv2.arcLength(c, closed=True)
			roundness = 4*np.pi*area * perimeter**(-2) # circularity by a different name

			(x,y,w,h) = cv2.boundingRect(c)
			ar = w / h  # aspect ratio
			# print("Area", area, "\tPerimeter", perimeter)
			# print("Roundness", roundness)
			if (w1 <= w <= w2) and (h1 <= h <= h2) and (a1 <= ar <= a2) and (circularity < roundness):
				b = Bubble(c)
				bubbles.append(b)

		return bubbles


	def contours_from_section(self, image, section_contour):
		"""
		Returns all contours within a bounding contour

        Parameters
        ----------
		image : ndarray
			An OpenCV image, usually a the full answer sheet. A portion of the
			full answer sheet image is masked off and contours are extracted
			from the remaining portion.

		section_contour : ndarray 
			A bounding contour representing an exam section. Answer bubble
			contours are extracted from the portion of the answer sheet image
			within the section contour.

		Returns
		-------
		list, ndarray 
			A list of all the contours residing inside the bounding contour.
			The list must still be filtered to distinguish answer bubble
			contours from extraneous contours.

		"""
		c = section_contour
		x,y,w,h = cv2.boundingRect(c)
		mask = np.zeros(self.image.shape[:2], dtype="uint8")

		# masked area will be 2 pixels smaller than bounding contour on each side
		cv2.rectangle(mask, (x+2, y+2), (x+w-4, y+h-4), 255, -1)
		masked = cv2.bitwise_and(self.inverted.copy(), self.inverted.copy(), mask=mask)

		interior_contours = cv2.findContours(masked, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
		interior_contours = imutils.grab_contours(interior_contours)
		if not isinstance(interior_contours, list):
			interior_contours = list(interior_contours)

		return interior_contours


	def bubbles_from_section(self, image, section_contour, width, height, aspect_ratio, circularity):
		"""
		Wrapper method. Returns all answer bubbles within a bounding contour as
		Bubble objects by calling contours_from_section() and 
		contours_to_bubbles().

		Parameters
		----------
		image : ndarray
			An OpenCV image, usually a the full answer sheet. A portion of the
			full answer sheet image is masked off and contours are extracted
			from the remaining portion.

		section_contour : ndarray 
			A bounding contour representing an exam section. Answer bubble
			contours are extracted from the portion of the answer sheet image
			within the section contour.

		width : tuple, int 
			Min and max widths in pixels: (w1, w2) --> w1 <= w <= w2

		height : tuple, int
			Min and max heights in pixels: (h1, h2) --> h1 <= h <= h2

		aspect : tuple, float
			Min and max aspect ratios: (a1, a2) --> a1 <= ar <= a2
			An aspect ratio is width/height. 
			The aspect ratio of a perfect circle is 1.0	

		circularity : float
			The threshold for minimum circularity. 
			Circularity = 4π*area/perimeter^2
			A perfect circle has circularity of 1.0. The lower the circularity,
			the more deformed a shape can be. Setting circularity equal to 0
			essentially deactivates this filter.

		Returns
		-------
		list, Bubble 
			A list of Bubble objects representing answer choice bubbles from
			a single test section. See class 'Bubble'
		"""
		contours = self.contours_from_section(image, section_contour)
		bubbles = self.contours_to_bubbles(contours, width, height, aspect_ratio)

		return bubbles


	def segment_bubbles(self, bubbles, y1, y2):
		"""
			Filters bubbles based on their y-coordinates. An alternate method
			of grabbing the answer bubbles from a specific test section.

			A Bubble passes the filter if y1 < y < y2, exclusive

			Parameters
			----------
			bubbles : list, Bubble 
				A list of Bubble objects representing answer bubbles

			y1 : int 
				A y-coordinate, y1 < y2

			y2 : int 
				A y-coordinate, y2 > y1

			Returns
			-------
			list, Bubble 
				The list of answer bubbles within the range [y1, y2]
		"""
		segmented = [ b for b in bubbles if y1 < b.y < y2 ]
		return segmented


	def align_bubbles(self, bubbles, delta):
		"""
			The method checks for small coordinate deviations and overwrites
			the coordinate with the smallest value within 'delta' pixels.

			Clamps misaligned bubbles to a single x or y coordinate by updating
			the (x,y) bounding box corner coordinates of a Bubble object. This
			does not update the location of the contour or contour centroids --
			only the Bubble.x and Bubble.y labels. This can improve sorting of 
			Bubble objects without altering the source contours. 

			This method is NOT compatible with section maps.

			WARNING: This method might fail when 
			(1) Delta is not small compared to the bubble size 
			(2) Many bubbles within delta deviate in the same direction 
			    Ex: 10, 12, 14, 16, etc.
			(3) A deviated bubble is very close to another row or col

			Parameters
			----------
			bubbles : list, Bubble
				A list of Bubble objects

			delta : int 
				The maximum pixel deviation to overwrite
		"""

		# grab unique bounding box y-values
		sb = sorted(list(set([ b.y for b in bubbles ]))) # gets all unique values
		true_y = [sb[0]]  # container for the true y-values
		# print("\ny: ", sb)

		# appends to true y list if the value is in a different row
		for i in range(1, len(sb)):
			epsilon = sb[i] - sb[i-1]
			if epsilon > delta: true_y.append(sb[i])
		# print(true_y)

		# grab unique bounding box x-values
		sb = sorted(list(set([ b.x for b in bubbles ]))) # gets all unique values
		true_x = [sb[0]] # container for the true x-values
		# print("\nx: ", sb)

		# appends to true x list if the value is in a different row
		for i in range(1, len(sb)):
			epsilon = sb[i] - sb[i-1]
			if epsilon > delta: true_x.append(sb[i])
		# print(true_x)


		# overwrite a deviated coordinate with the true value
		for b in bubbles:
			for y in true_y:
				if self.close_to(b.y, y, delta, True):
					b.y = y
			for x in true_x:
				if self.close_to(b.x, x, delta, True):
					b.x = x	

		return bubbles
		

	def sort_bubbles(self, bubbles, row_length):
		"""
		Sorts bubbles into question-major, answer choice minor order,
		corresponding to columns of questions, each with 4-5 answer choices.
		After R rows of questions, a new column is begun with some question
		back on the first row, with 4-5 answer choices. See the example.

		Parameters
		----------
		bubbles : list, Bubble
			An unordered list of Bubble objects representing all the answer 
			choices for each question.
			Ex: [ Q1A, Q1B, Q1C, Q1D, Q2A, Q2B . . . ]

		row_length : int
			The number of answer choices per question 
			(usually equal to 4 or 5).

		Returns
		-------
		list, Bubble
			A list of answer bubbles sorted into row-major, group-minor
			order. See examples.

		Examples
		--------

		>>> sort_bubbles(bubbles=[9, 11, 7, 4, 12, 6, 3, 8, 1, 10, 2, 5], row_length=3)
		# 1  2  3 	  7   8   9
		# 4  5  6 	 10  11  12

		"""
		# first 2 sorts achieve col-major, top to bottom order
		bubbles.sort(key = lambda b:b.y)
		bubbles.sort(key = lambda b:b.x)

		# next, sort row major by column, to get:
		#
		#  1  2  3 		 7   8   9
		#  4  5  6 		10  11  12

		num_bubbles = len(bubbles)
		ordered = []

		i = 0  # index for traversing list of bubbles
		while len(ordered) < num_bubbles:
			y_line = bubbles[i].center[1]  # y-coord of first bubble in row (bounding rectangle)
			row_index = 0  # counts how many bubbles in the current row have been extracted

			while row_index < row_length:
				while abs(bubbles[i].center[1] - y_line) > 3 :  # until we find next bubble in the row, keep traversing
					i += 1
				ordered.append(bubbles.pop(i))  # when we do find that bubble, pop it into the output list
				row_index += 1
			row_counter = 0  # when we've filled an entire row, reset the row index
			i = 0			 # and return to the beginning of the bubble list

		return ordered


	def bubbles_to_groups(self, bubbles, group_length):
		"""
		Rearranges a flat list of sorted bubbles into a 2D array (nested list) 
		of groups of bubbles. Each group represents the answer choice 
		bubbles for a single question. 

		Parameters
		----------
		group_length : int
			The number of bubbles per group (choices per question), usually
			4-5, i.e. A-D or A-E

		bubbles : list
			A SORTED list of Bubble objects or OpenCV contours. The list must
			be sorted in row-major, group-minor order, a.k.a. question-major,
			answer choice minor order.

		Returns
		-------
		list 
			A 2D list of shape (num_groups, group_length). Each inner list
			represents the answer bubbles for a single question. The outer
			list should represent some number of questions

		"""
		assert( len(bubbles)%group_length == 0 ) # same num of choices in each group

		nRows = len(bubbles)//group_length
		groups = []

		for i in range(0, len(bubbles), group_length):
			ixRow = i%group_length
			row = bubbles[i:i+group_length]
			groups.append(row)

		return groups


	def segment_section(self, bubbles, y1, y2, group_length):
		"""
		Wrapper function - extracts all bubbles within a range y1, y2 and sorts
		them in row-major, multiple column minor order by calling
		segment_bubbles(), sort_bubbles(), and bubbles_to_groups().

		Sorts bubbles into question-major, answer choice minor order,
		corresponding to columns of questions, each with 4-5 answer choices.
		After R rows of questions, a new column is begun with some question
		back on the first row, with 4-5 answer choices. See the example.

		Parameters
			----------
			bubbles : list, Bubble
				An unordered list of Bubble objects representing all the answer 
				choices for each question.
				Ex: [ Q1A, Q1B, Q1C, Q1D, Q2A, Q2B . . . ]

			y1 : int 
				A y-coordinate, y1 < y2

			y2 : int 
				A y-coordinate, y2 > y1

			row_length : int
				The number of answer choices per question 
				(usually equal to 4 or 5).

		Returns
		-------
		list, Bubble
			A list of answer bubbles sorted into row-major, group-minor
			order. See examples.

		Examples
		--------

		>>> sort_bubbles(bubbles=[9, 11, 7, 4, 12, 6, 3, 8, 1, 10, 2, 5], row_length=3)
		# 1  2  3 	  7   8   9
		# 4  5  6 	 10  11  12

		"""
		section = self.segment_bubbles(bubbles, y1, y2)
		section = self.sort_bubbles(section, group_length)
		section = self.bubbles_to_groups(section, group_length)
		return section


	def count_pixels_of_contours(self, contours, show_counts=False):
		"""
		Receives a 1D list of contours and returns both the black and white  
		pixel counts within each contour's region of the B & W binarized image
		(self.binary) The list typically represents the group of answer 
		bubbles for a single question.

		Parameters
		----------
		contours : list, ndarray 
			A list of opencv contours representing a group of test answer 
			bubbles for a single question

		show_counts : bool
			If true, prints white & black counts to console. Used for 
			debugging.

		Returns
		------- 
		dict  
			Key = 'b', 'w': black or white 
			Value = list of integers - pixel counts
			{'b':[int, ... int], 'w':[int, ... int]}

			The black and white pixel counts for each bubble in the group. The 
			index of a count corresponds to the position of a bubble:
			The zeroth count = choice A,
			The  first count = choice B, etc.

		"""
		binr = self.binary # the bw image``
		inv = self.inverted # the inverted binary image: black <--> white

		counts = {'b':[], 'w':[]} 
		counts['b'] = [None for c in contours] # holds the black pixel count of each bubble
		counts['w'] = [None for c in contours] # holds the white pixel count of each bubble

		for i,c in enumerate(contours):
			# count black pixels
			mask = np.zeros(inv.shape, dtype="uint8")
			cv2.drawContours(mask, [c], -1, 255, -1)
			invMask = cv2.bitwise_and(inv, inv, mask=mask)
			counts['b'][i] = cv2.countNonZero(invMask)

			# count white pixels
			mask = np.zeros(binr.shape, dtype="uint8")
			cv2.drawContours(mask, [c], -1, 255, -1)
			binMask = cv2.bitwise_and(binr, binr, mask=mask)
			counts['w'][i] = cv2.countNonZero(binMask)

			if show_counts:
				print(f"{i}: The black pixel count is {counts['b'][i]}")
				print(f"{i}: The white pixel count is {counts['w'][i]}")
		# 		cv2.imshow("Inverted Masked", invMask.copy())
		# 		cv2.imshow("Binary Masked", binMask.copy())
		# 		if cv2.waitKey(0) == 27: 
		# 			cv2.destroyAllWindows()
		# 			break
		# cv2.destroyAllWindows()

		return counts


	def count_pixels_of_bubbles(self, bubbles, show_counts=False):
		"""
		Receives a 1D list of Bubbles and returns both the black and white 
		pixel counts within each contour's region of the B & W binarized image
		(self.binary) The list typically represents the group of answer 
		bubbles for a single question.

		Parameters
		----------
		bubbles : list, ndarray 
			A list of Bubble objects representing a group of test answer 
			bubbles for a single question

		show_counts : bool
			If true, prints white & black counts to console. Used for 
			debugging.

		Returns
		------- 
		dict  
			Key = 'b', 'w': black or white 
			Value = list of integers - pixel counts
			{'b':[int, ... int], 'w':[int, ... int]}

			The black and white pixel counts for each bubble in the group. The 
			index of a count corresponds to the position of a bubble:
			The zeroth count = choice A,
			The  first count = choice B, etc.

		"""
		contours = [b.contour for b in bubbles]

		return self.count_pixels_of_contours(contours, show_counts)


	def count_pixels_at_points(self, points, shape, dimensions, show_counts=False):
		"""
		Receives a 1D list of Points and returns both the black and white 
		pixel counts within each contour's region of the B & W binarized image
		(self.binary) The list typically represents the group of answer 
		bubbles for a single question.

		Point objects represent the center of each bubble. Pixels are counted
		by masking the binary with the given 'shape' of 'dimensions'.

		Parameters
		----------
		points : list, Point 
			A list of Point namedtuple objects representing a group of test 
			answer bubbles for a single question

		shape : str 
			The shape to use when masking the binary image, must be
			'rectangle' or 'circle'

		dimensions : list, int 
			The dimensions of the shape passed in the 'shape' parameter
			If 'rectangle'  |  [width, height]
			If 'circle'	 |  [radius]

		show_counts : bool
			If true, prints white & black counts to console. Used for 
			debugging.

		Returns
		------- 
		dict  
			Key = 'b', 'w': black or white 
			Value = list of integers - pixel counts
			{'b':[int, ... int], 'w':[int, ... int]}

			The black and white pixel counts for each bubble in the group. The 
			index of a count corresponds to the position of a bubble:
			The zeroth count = choice A,
			The  first count = choice B, etc.
			
		"""
		binr = self.binary # the bw image``
		inv = self.inverted # the inverted binary image: black <--> white

		counts = {'b':[], 'w':[]} 
		counts['b'] = [None for c in points] # holds the black pixel count of each bubble
		counts['w'] = [None for c in points] # holds the white pixel count of each bubble

		# for display purposes only
		if show_counts: 
			print('')
			# cv2.imshow('bin', self.binary)
			# cv2.imshow('inv', self.inverted)
			pass

		# Set shape parameters
		if shape == 'rectangle':
			w, h = dimensions[0], dimensions[1]
			dw = int(w/2); dh = int(h/2);
		elif shape == 'circle':
			r = dimensions[0]

		for i,c in enumerate(points):
			
			mask_inv = np.zeros(inv.shape, dtype="uint8")
			mask_bin = np.zeros(binr.shape, dtype="uint8")

			if shape == 'rectangle':
				cv2.rectangle(mask_inv, (c.x-dw, c.y-dh), (c.x+dw, c.y+dh), 255, -1)
				cv2.rectangle(mask_bin, (c.x-dw, c.y-dh), (c.x+dw, c.y+dh), 255, -1)
			elif shape == 'circle':
				cv2.circle(mask_inv, (c.x, c.y), r, 255, -1)
				cv2.circle(mask_bin, (c.x, c.y), r, 255, -1)

			# count black pixels
			invMask = cv2.bitwise_and(inv, inv, mask=mask_inv)
			counts['b'][i] = cv2.countNonZero(invMask)

			# count white pixels
			binMask = cv2.bitwise_and(binr, binr, mask=mask_bin)
			counts['w'][i] = cv2.countNonZero(binMask)


			if show_counts:
				print(f"{i}: The black pixel count is {counts['b'][i]}")
				print(f"{i}: The white pixel count is {counts['w'][i]}")
				# cv2.imshow("Inverted Masked", invMask.copy())
				# cv2.imshow("Binary Masked", binMask.copy())
				# if cv2.waitKey(0) == 27: 
				# 	cv2.destroyAllWindows()
				# 	break
			# cv2.destroyAllWindows()

		return counts


	def count_pixels(self, elements, el_mode, mask_shape=None, show_counts=False):
		"""
		Wrapper method, calls one of 
			count_pixels_of_contours(),
			count_pixels_of_bubbles(),
			count_pixels_at_points()

		Receives a 1D list of elements and returns both the black and white 
		pixel counts within each contour's region of the B & W binarized image
		(self.binary) The list typically represents the group of answer 
		bubbles for a single question.


		Parameters
		----------
		elements : list
			A list of contours, Bubbles, or Points

		el_mode : str
			The element mode.
			One of 'contours', 'bubbles', 'points'. (Not case sensitive)
			The mode must match the types of elements passed in 'elements'.

		mask_shape : tuple
			el_mode='contours' | None
			el_mode= 'bubbles' | None
			el_mode='points'   | (shape, [dimensions])
							     ('rectangle', [width, height])
							     ('circle', [radius])
			The param holds shape and dimension arguments required when passing
			a list of Point objects (a.k.a. a section map). It is not needed
			when passing contours or Bubbles; its default value is None.

		show_counts : bool
			If true, prints white & black counts to console. Used for 
			debugging.

		Returns
		------- 
		dict  
			Key = 'b', 'w': black or white 
			Value = list of integers - pixel counts
			{'b':[int, ... int], 'w':[int, ... int]}

			The black and white pixel counts for each bubble in the group. The 
			index of a count corresponds to the position of a bubble:
			The zeroth count = choice A,
			The  first count = choice B, etc.
		"""

		if 'contour' in el_mode.lower() and isinstance(elements[0], np.ndarray):
			return self.count_pixels_of_contours(elements, show_counts)

		elif 'bubble' in el_mode.lower() and isinstance(elements[0], Bubble):
			return self.count_pixels_of_bubbles(elements, show_counts)

		elif 'point' in el_mode.lower() and isinstance(elements[0], self.Point):
			shape = mask_shape[0]
			dimensions = mask_shape[1]
			return self.count_pixels_at_points(elements, shape, dimensions, show_counts)

		else:
			raise ValueError("The mode must be one of: 'contours', 'bubbles', or 'points'.",
							 "\n",
							 "The 'elements' arg must contain either contours, Bubbles, or Points.")

		return counts


	def suppress_white(self, counts, epsilon):
		"""
		Excludes bubbles that contain any white pixels.
		When the ACT answer sheets are printed, photographed, and converted to
		a raster image, the resulting pixelation can create artifacts of dark 
		gray pixels	inside empty answer bubbles. Those artifacts can cause 
		false positives in the methods that find filled bubbles by counting
		black pixels ( extract_filled(...) ).

		This method suppresses those artifacts, ensuring that empty bubbles 
		not counted as filled. Suppression is accomplished by

		1) Storing the maximum number of white pixels among the bubbles
		2) Computing a threshold of white pixels:
			threshold = max_white_count * epsilon
		3) Exclude a bubble if its white count is over the threshold:
			set its black count to zero & set its white count to the maximum
		4) Include a bubble if its white count is under the threshold:
			retain its existing black count & set its white count to zero

		Parameters
		----------
		counts : dict 
			Key = 'b', 'w'
			Value = list of integer pixel counts

			The black and white pixel counts of a group of bubbles. The 
			position of a count corresponds to the position within the group of
			its bubble.

			Ex:	{'b':[12, 120, 13, 28], 'w':[108, 0, 107, 92]}

		epsilon : float 
			The fraction of white pixels at which to set the threshold.
				threshold = max_white * epsilon

		Returns
		-------
		counts : dict 
			Key = 'b', 'w'
			Value = list of integer modified pixel counts
			
			The dict of pixel counts with 
				black = zero or original
				white = zero or maximum
									
			Ex:	{'b':[0, 120, 0, 0], 'w':[108, 0, 108, 108]}

		Examples
		--------
		>>> suppress_white( counts={'b':[12, 120, 13, 28], 'w':[108, 0, 107, 92]}, epsilon=0.3 )

			{'b':[0, 120, 0, 0], 'w':[108, 0, 108, 108]}
		"""
		blk = counts['b']
		wht = counts['w']
		max_white = max(wht)
		threshold = epsilon * max_white

		for i in range(len(blk)):
			if wht[i] > 0 and wht[i] > threshold:
				blk[i] = 0
				wht[i] = max_white
			else:
				wht[i] = 0

		counts = {'b':blk, 'w':wht}

		return counts


	def find_darkest_from_contours(self, contours):
		"""
		Returns the index of the darkest bubble. Intended for use when an
		answer has been erased and its bubble is no longer white. If multiple
		bubbles are equivalently dark, returns the index of the first one.
		This method implicitly sorts the contours left-to-right. 

		Parameters
		----------
		contours : list, ndarray 
			A list of OpenCV contours representing 1 group of answer bubbles

		Returns
		------- 
		index : int
			The list index of the darkest bubble
		"""
		gray = self.gray

		# init large value for the sum of pixel values in the darkest bubble
		darkest = gray.shape[0]*gray.shape[1] 
		ix_darkest = 0  # counter for min_shade position

		contours = imutils.contours.sort_contours(contours, 'left-to-right')[0]

		for i,c in enumerate(contours):
			mask = np.zeros(gray.shape, dtype='uint8')
			cv2.drawContours(mask, [c], -1, 255, -1)
			masked = cv2.bitwise_and(gray, gray, mask=mask)
			sum_pixels = np.sum(masked)	
			if sum_pixels < darkest:
				darkest = sum_pixels
				ix_darkest = i

		return ix_darkest


	def find_darkest_from_bubbles(self, bubbles):
		"""
		Returns the index of the darkest bubble. Intended for use when an
		answer has been erased and its bubble is no longer white. If multiple
		bubbles are equivalently dark, returns the index of the first one.
		This method calls find_darkest_from_contours(...)

		Parameters
		----------
		contours : list, Bubble
			Bubble objects representing 1 group of bubbles

		Returns
		------- 
		index : int
			The list index of the darkest bubble
		"""
		contours = [b.contour for b in bubbles]

		return self.find_darkest_from_contours(contours)


	def find_darkest_from_points(self, points, shape, dimensions):
		"""
		Returns the index of the darkest bubble. Intended for use when an
		answer has been erased and its bubble is no longer white. If multiple
		bubbles are equivalently dark, returns the index of the first one.
		This method assumes the points are presorted left-to-right

		Points represent the center of each bubble. Pixel values are 
		counted by masking the binary with the given 'shape' of 'dimensions'.

		Parameters
		----------
		points : list, Point
			A list of Point namedtuple objects representing a group of answer
			bubble centers

		shape : str
			The shape to use when masking the binary image, can be
				'rectangle' or 'circle'

		dimensions : list, int
			The dimensions of the masking shape to draw on the binary 
				If 'rectangle'  |  [width, height]
				If 'circle'	    |  [radius]

		Returns
		-------
		index : int
			The list index of the darkest bubble
		"""
		gray = self.gray

		# init large value for the sum of pixel values in the darkest bubble
		darkest = gray.shape[0]*gray.shape[1] 
		ix_darkest = 0  # index of 'darkest' bubble position	

		if shape == 'rectangle':
			w, h = dimensions[0], dimensions[1]
			dw = int(w/2); dh = int(h/2);
		elif shape == 'circle':
			r = dimensions[0]

		for i,c in enumerate(points):
			mask = np.zeros(gray.shape, dtype="uint8")

			if shape == 'rectangle':
				cv2.rectangle(mask, (c.x-dw, c.y-dh), (c.x+dw, c.y+dh), 255, -1)
			elif shape == 'circle':
				cv2.circle(mask, (c.x, c.y), r, 255, -1)

			masked = cv2.bitwise_and(gray, gray, mask=mask)

			sum_pixels = np.sum(masked)	
			if sum_pixels < darkest:
				darkest = sum_pixels
				ix_darkest = i

		return ix_darkest


	def suppress_lighter(self, elements, counts, el_mode, param=None, show_counts=False):
		"""
		Used to exclude erased answer choices. Finds the darkest bubble, 
		then sets all other black pixel counts to zero and white counts to the
		maximum white pixel count.

		Note: If passing Points, the list must be presorted left-to-right

		Note: This method is NOT COMPATIBLE with finding multiple bubbles 
			  because it "removes" pixels counts for all but 1 bubble in a row.

		Parameters
		----------
		elements : list 
			The elements representing answer bubbles. Must be a list of
			opencv contours, Bubbles, or Points

		counts : dict 
			Key = 'b', 'w'
			Value = list of integer pixel counts

			The black and white pixel counts of a group of bubbles. The 
			position of a count corresponds to the position of its bubble
			within the group .

			Ex:	{'b':[12, 120, 13, 28], 'w':[108, 0, 107, 92]}

		el_mode : string 
			The element mode.
			A description of the type of element passed to the 'elements' arg.
			Must be one of 'contours', 'bubbles', or 'points' and correctly
			match the type of element passed to the 'elements' arg.

		mask_shape : tuple 
					(shape, [dimensions])
			Ex 1:	('rectangle', [width, height])
			Ex 2:	('circle', [radius])
			Default = None. This arg is only needed when the elements are Points.
			The mask_param holds shape and dimension arguments that determine
			the shape of the mask used when counting pixels in the binary
			image. 

		show_counts : bool 
			If true, prints white & black counts to console. Used for debugging.

		Returns
		-------
		counts : dict 
			Key = 'b', 'w'
			Value = list of integer modified pixel counts

			The black and white pixel counts. The darkest bubble retains its 
			black count and has white count set to zero. All other bubbles have 
			black counts set to zero and white counts set to max.
			
			Ex:	{'b':[int, ... int], 'w':[int, ... int]}
		"""
		gray = self.gray.copy()
		el_mode = el_mode.lower()
		max_count = max(max(counts['b'], counts['w']))

		# init large value for the sum of pixel values in the darkest bubble
		darkest = gray.shape[0]*gray.shape[1] 
		ix_darkest = 0  # counter for min_shade position

		if el_mode == 'contours':
			ix_darkest = self.find_darkest_from_contours(elements)
		elif el_mode == 'bubbles':
			ix_darkest = self.find_darkest_from_bubbles(elements)
		elif el_mode == 'points':
			ix_darkest = self.find_darkest_from_points(elements, param[0], param[1])

		counts['b'] = [0 if i!=ix_darkest else value for i,value in enumerate(counts['b'])]
		counts['w'] = [max_count if i!=ix_darkest else value for i,value in enumerate(counts['w'])] 
		if show_counts: print(counts)

		return counts


	def extract_filled(self, counts, filter_mode, filter_param, show_counts=False):
		"""
		Receives a 1D list of black pixel counts representing a single 
		row/group of answer bubbles and returns the indices of all filled-in 
		bubbles

		Parameters
		----------
		counts : list, int 
			A 1D list of black pixel counts

		filter_mode : string 
			Determines the condition by which to consider a bubble "filled".
			Must be one of 'threshold', 'adaptive', 'maximum'

            'threshold': Returns all bubbles with pixel counts over the 
            			 threshold.
            'adaptive': Computes the average pixel count in a group, then 
            			threshold = avg * (1 + epsilon). 
            			Needs white suppression to detect more than half filled.
            'maximum': An Adaptive Max, returns the bubble with the highest
            	   	   pixel count over the adaptive threshold. Can't return 
            	   	   multiple bubbles

		filter_param : int or float
			Contains the threshold or epsilon value, depends on mode
			   'threshold': param is an integer representing the pixel threshold 
			   'adaptive': param is a float epsilon representing the % deviation 
			   			   from average
			   'maximum': param is a float epsilon representing the % deviation 
			   			   from average
			 		 
		show_counts : bool 
			If true, print the pixel counts of each bubble 
			-- useful for determining the threshold
		

		Returns
		------- 
		list
			The one-based indices of all the filled-in contours. The list will 
			be the same length as the number of filled-in contours. If the row
			doesn't contain a filled-in contour, its index is None. 
		"""
		any_filled = False  # flag - have we found any filled bubbles?
		indices = []  # will hold the indices of bubbles passing the threshol

		# Set parameters based on the mode
		if filter_mode == 'threshold': 
			threshold = filter_param
		elif filter_mode in ('adaptive', 'maximum'):
			epsilon = filter_param
			threshold = (1+epsilon) * sum(counts)/len(counts)
		else:
			pass

		if show_counts: print(counts, "\nThreshold =", threshold)

		if filter_mode in ('threshold', 'adaptive'):
			for i in range(0, len(counts)):
				if counts[i] > threshold:
					any_filled = True
					indices.append(i+1)
		elif filter_mode == 'maximum':  # max mode -- keep only the maximum
			m = 0  # var to hold the max value
			for i in range(0, len(counts)):
				if counts[i] > threshold:
					any_filled = True
					if counts[i] > m:
						m = counts[i]
						indices = [i+1]

		if any_filled == False: indices = [None]

		return indices


	def extract_filled_bubbles_from_section(self, sMap, filter_mode, filter_param, mask_shape, suppress_white=True, white_epsilon=0.5, show_counts=False):
		"""
		Wrapper method.
		Receives a section map representing multiple groups and returns a dict
		of the indices of the filled-in bubbles for each question.

		Using this method is not recommended. It is better to write an 
		extraction pipeline using lower level methods to confer greater
		granularity and flexibiity.

		Parameters
		----------
		sMap : dict 
			Key = 1, 2, 3 . . . (question numbers)
			Value = list of Point objects
			Ex:	{ q: [Point(x,y), Point(x,y) ...], q: [...], ... }

		filter_mode : string 
			Determines the condition by which to consider a bubble "filled".
			Must be one of 'threshold', 'adaptive', 'maximum'

            'threshold': Returns all bubbles with pixel counts over the 
            			 threshold.
            'adaptive': Computes the average pixel count in a group, then 
            			threshold = avg * (1 + epsilon). 
            			Needs white suppression to detect more than half filled.
            'maximum': An Adaptive Max, returns the bubble with the highest
            	   	   pixel count over the adaptive threshold. Can't return 
            	   	   multiple bubbles

		filter_param : int or float
			Contains the threshold or epsilon value, depends on mode
			   'threshold': param is an integer representing the pixel threshold 
			   'adaptive': param is a float epsilon representing the % deviation 
			   			   from average
			   'maximum': param is a float epsilon representing the % deviation 
			   			   from average

		mask_shape : tuple, 
					(shape, [dimensions])
			Ex 1:	('rectangle', [width, height])
			Ex 2:	('circle', [radius])
			The mask_param holds shape and dimension arguments that determine
			the shape of the mask used when counting pixels in the binary
			image

		suppress_white : bool 
			Whether to exclude bubbles containing white pixels. 
			Default = True.

		white_epsilon : float
			Passed to the suppress_white() method. The fraction of whitest 
			bubble counts over which to set the exclusion threshold. 
			threshold = white_epsilon * max_white_counts
			Default = 0.5
			 		 
		show_counts : bool 
			If true, print the pixel counts of each bubble -- useful for 
			determining the threshold.
			Default = False.

		Returns
		-------
		dict 
			Key = 1, 2, 3 ... (question number)
			Value = list, int
			The indices of the filled-in bubbles for each question.
			Ex: {7:[2], 8:[None], 9:[0,2], etc.}
		"""

		# Status messages
		if show_counts:
			if suppress_white:
				print("\nWhite Suppression = ON")
			else:
				print("\nWhite Suppression = OFF")

			if filter_mode not in ('adaptive', 'threshold'):
				print("\nLight Suppression = ON")
			else:
				print("\nLight Suppression = OFF")

		indices = {}
		for q, group in sMap.items():
			counts = self.count_pixels(group, 'points', mask_shape, show_counts)

			if suppress_white:
				counts = self.suppress_white(counts, white_epsilon)
				if show_counts:
					print("Counts after white suppression")
					print(counts)

			if filter_mode not in ('adaptive', 'threshold'):
				num_filled = sum([ x > 0 for x in counts['b'] ])
				if num_filled > 1: 
					counts = self.suppress_lighter(group, counts, mode, mask_shape, False)

			indices[q] = self.extract_filled(counts['b'], filter_mode, filter_param, show_counts)

			if show_counts:
				print(f"{q}: {indices[q]}")

		return indices


	def build_sectionMap(self, bubbles, grid, num_questions, group_length):
		"""
		Wrapper method. Returns a section map from a list of bubbles and the 
		grid shape. Each P(x,y) in the list is a bubble center.

		Parameters
		----------
		bubbles : list, Bubble
			A list of Bubble objects representing all the answer bubbles in a section.

		grid : tuple, (int, int) 
			(rows, cols) -- the total num of unique bubble y-coords and x-coords
			Ex: (10, 12) = ten rows of 3 column groups of 4 answer bubbles

		num_questions : int
			The number of questions in a section.

		group_length : int 
			The number of bubbles in a single group, usually 4-5

		Returns
		-------
		dict 
			Key = (int) The question numbers
			Value = (list, Point) The coordinates of the bubble centers
			{q:[Point(x,y), Point(x,y) ...]}
		"""
		xC = self.kmeans_centers([b.center[0] for b in bubbles], grid[1])
		yC = self.kmeans_centers([b.center[1] for b in bubbles], grid[0])
		xG = self.xCoordinates_to_groups(xC, group_length)
		sMap = self.coordinates_to_points(xG, yC, num_questions)

		return sMap
		

	def generate_filled_indices(self, sectionMap, mask_shape, white_epsilon, filter_params, show_counts=False ):
		"""
		Extracts the indices of the filled-in answer bubbles and returns them
		in a dict. Assumes that the bubble elements are points -- requires a
		section map to work. Runs the adaptive, maximum, and threshold filters
		and returns all of the results.

		Note: This method is NOT able to return multiple bubbles in a group 
			  because self.suppress_lighter() is invoked by default.

		Adaptive Filter: The threshold is some percentage of the average black
						 pixel count; returns all bubbles passing the threshold.


		Maximum Filter: The threshold is some percentage of the average black
						 pixel count; returns the single bubble containing the
						 maximum number of black pixels over the threshold.
						 Returns the first maximum in the case of ties.

		Threshold Filter: The threshold is an integer number of black pixels;
						 returns all bubbles passing the threshold.

		Parameters
		----------
		sectionMap : dict 
			Key = (int) The question numbers
			Value = (list, Point) The coordinates of the bubble centers
			{q:[Point(x,y), Point(x,y) ...]}

			The section map -- dict of center points of all of the answer 
			bubbles.


		mask_shape : tuple,  (str, list[int]) 
			(shape, [dimensions])
		    ('rectangle', [width, height])
		    ('circle', [radius])

			The param holds shape and dimension arguments required when passing
			a list of Point objects (a.k.a. a section map). It is not needed
			when passing contours or Bubbles; its default value is None.
			See SheetScanner.count_pixels_at_points()


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


		show_counts : bool 
			If true, print the pixel counts of each bubble 
			-- useful for determining the threshold


		Returns
		-------
		dict
			Key = (str) 'adaptive', 'maximum', 'threshold'
			Val = dict
				K = (int)    The question numbers
				V = (list)   int/None
					The one-based index of the filled-in bubbles.
					Contains None if none of the bubbles were filled in.

			The indices of filled-in answer bubbles. Usually stored into
			ActSection.answer_indices 


		Examples
		--------
		>>> ai = self.generate_answer_indices( ('circle', [6]), 0.65, (0.1, 0.1, 90) )
		>>> ai['adaptive']

			{1:[4], 2:[None], 3:[1] . . . 75:[2]}

		"""
		shape = mask_shape[0]
		dimensions = mask_shape[1]
		adp_eps, max_eps, thresh = filter_params[0], filter_params[1], filter_params[2]

		# preallocate dicts	
		keys = sectionMap.keys()
		indices_adp = dict.fromkeys(keys, 0)
		indices_max = dict.fromkeys(keys, 0)
		indices_thr = dict.fromkeys(keys, 0)

		for q, group in sectionMap.items():
			if show_counts: print('\n', q, '\n------------------------')

			counts = self.count_pixels(group, 'points', (shape, dimensions), show_counts)
			counts = self.suppress_white(counts, white_epsilon)

			if show_counts: print("After white suppression:", counts)


			num_filled = sum([ x > 0 for x in counts['b'] ])
			if num_filled > 1:
				counts = self.suppress_lighter(group, counts, 'points', ('circle', [6])) 

			if show_counts: print("After light suppression:", counts)

			indices_adp[q] = self.extract_filled(counts['b'], 'adaptive', adp_eps, False)
			indices_max[q] = self.extract_filled(counts['b'], 'maximum', max_eps, False)
			indices_thr[q] = self.extract_filled(counts['b'], 'threshold', thresh, False)

		indices = {'adaptive':indices_max, 'maximum':indices_max, 'threshold':indices_thr}

		for method, answers in indices.items():
			for q, index in answers.items():
				if type(index) == int or index == 0:  # init dict vals are zeros
					print(f"{method}: \t {q} did not return an index.")
					sys.exit()

		return indices


	def get_points_of_filled(self, sectionMap: dict, indices: dict) -> dict:
		"""
		Returns the Point locations of the filled-in bubbles.

		Parameters
		----------
		sectionMap : dict
			Key = (int) The question numbers
			Val = (list, Point) The coordinates of all the bubble centers
			{q:[Point(x,y), Point(x,y) ...]}

		indices : dict
			Key = (int)    The question numbers
			Val = (list)   int/None
				The one-based index of the filled-in bubbles.
				Contains None if none of the bubbles were filled in.
				Ex:  {1:[4], 2:[None], 3:[1] . . . 75:[2]}

		Returns
		-------
		dict
			Key = (int) The question numbers
			Val = (list : Point, None) 
				The coordinates of all the filled bubble centers
		"""
		keys = sectionMap.keys()
		filled_points = dict.fromkeys(keys, [])

		for q, row in indices.items():
			points = sectionMap[q]

			tmp = []
			for i in row:  # i is a single index
				if i is not None:  # if the row contains a filled bubble
					tmp.append(points[i-1])
				else:
					tmp.append(None)
			filled_points[q] = tmp

		return filled_points


	def show_section_confirmation(self, image, confirmation_points: list, rect_dims: tuple, show_image: bool=False, title: str=""):
		"""
		Generates a confirmation image by drawing red rectangles around each
		filled-in bubble. Returns the confirmation image by default in BGR 
		format (3 color channels), but can also display the confirmation image
		if show_image is True.

		NOTE: The input image is copied, not modified in place.

		Parameters
		----------
		image : ndarray
			An image of the exam section showing question numbers and answer 
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
			The section image with red rectangles drawn around each filled
			bubble that was detected. 

		"""
		w, h = rect_dims[0], rect_dims[1]
		dx = int(w/2); dy = int(h/2);

		if (w%2 != 0) or (h%2 != 0):
			raise ValueError("The width and height must both be even numbers.")
		else:
			pass

		img = image.copy()
		if len(image.shape) == 2:  # if image is grayscale
			img = cv2.cvtColor(image, cv2.COLOR_GRAY2BGR)


		for b in confirmation_points:
			# Draw markers on the image
			cv2.rectangle(img, (b.x-dx, b.y-dy), (b.x+dx, b.y+dy), (0,0,255), 1)

		confirmation = img

		if show_image:
			cv2.imshow(title, confirmation)
			cv2.waitKey(0)
			cv2.destroyAllWindows()

		return confirmation


	def get_section_confirmation(self, sMap: dict, section_indices: dict) -> dict:
		"""
		Kind of a wrapper method.
		Collects the center Points of the filled-in bubble for each question. 
		This method will generate a confirmation for each filter in 
		section_indices, under the same key name. The section confirmation may 
		be passed to a draw/show method to view the confirmation image.

		NOTE: If section_indices contains multiple answers for a question,
		only the first one will be collected in this method - it can't handle
		multiple answers. 

		Parameters
		----------
		sMap : dict
			The section map
			Key = (int) The question numbers
			Val = (list, Point) The coordinates of all the bubble centers
			{q:[Point(x,y), ... Point(x,y)], q:[...], ...}

		section_indices : dict
			Key = (str)    'adaptive', 'maximum', 'threshold'
			Val = (dict)   
				K = (int) The question numbers
				V = (list : int, None)
				
			The indices of the filled-in bubbles as extracted by all 3 filters.
			Each sub-dict contains question nums as keys and lists of index
			numbers as values. See self.generate_filled_indices()
			Ex:  { 'adaptive':{1:[4], 2:[None], 3:[1] . . . 75:[2]}, ... }

		Returns
		-------
		dict 
			Key = (str)	The same keys as section_indices
			Val = (list:Point)	The center points of the filled-in bubbles

		"""
		confirmation = {}

		for filter_label in section_indices.keys():
			indices = section_indices[filter_label]

			coordinates = self.get_points_of_filled(sMap, indices)
			markers = [row[0] for row in coordinates.values() if row[0] is not None]

			confirmation[filter_label] = markers

		return confirmation


	
