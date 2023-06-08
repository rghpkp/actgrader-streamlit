import cv2 as cv 
import numpy as np
from collections import namedtuple
from matplotlib import pyplot as plt


class Dewarper():
	"""
	Contains methods for dewarping a rotated & skewed image of a sheet of 
	paper (ACT answer sheet), returning the zenithal view of the orthogonalized 
	sheet.
	"""

	Kpd = namedtuple('Kpd', ['kp', 'des']) 
	"""
	A SIFT keypoint descriptor. Contains a list of keypoints and an ndarray of
	descriptors. Each row in 'des' is the set of descriptors for a single kp
	"""


	def __init__(self, ref=None, img=None):
		"""
		The constructor

		Parameters
		----------
		ref : str or ndarray 
			path/to/the/REFERENCE.image
			or the reference image

		img : str or ndarray
			path/to/the/WARPED.image	
			or the skewed image to be dewarped
		"""

		self.MIN_MATCH_COUNT = 4
		self.MATCH_RATIO = 0.7
		self.matches = []
		self.good_matches = []
		self.transformation_matrix = None  # the transform matrix act --> ref, [ref] = M[act]
		self.homo_mask = None  # the homography mask
		self.perspective_transform = None  # the vector transform of the image bounding vectors

		self.sifter = cv.SIFT_create()  # An obj that implements the SIFT algorithm

		self.ref = None # The reference image
		self.og  = None # The skewed image to be dewarped
		self.img = None  # A copy for internal processing
		self.dewarped = None  # The dewarped/deskewed image
		self.dewarped_gray = None  # The 2D dewarped/deskewed image, used for validation

		# Handle strings or images as constructor args
		if isinstance(ref, str):
			self.ref = cv.imread(ref)  
		elif isinstance(ref, np.ndarray):
			self.ref = ref
		else:
			pass

		if isinstance(img, str):
			self.og = cv.imread(img)  
		elif isinstance(img, np.ndarray):
			self.og = img
		else:
			pass

		# Convert images to grayscale if necessary
		if isinstance(self.ref, np.ndarray):
			self.ref = cv.cvtColor(self.ref, cv.COLOR_BGR2GRAY)
		if isinstance(self.og, np.ndarray):
			self.img = cv.cvtColor(self.og, cv.COLOR_BGR2GRAY)

		self.kpd_ref = self.Kpd(None, None)  # Keypoint descriptors
		self.kpd_img = self.Kpd(None, None)

		# FANN parameters
		ALG = 1  # The Flann Index KD Tree algorithm
		index_params = dict(algorithm=ALG, trees=5)
		search_params = dict(checks=50)
		self.fanner = cv.FlannBasedMatcher(index_params, search_params)


	def load(self, path, flag):
		"""
		Loads an image file as either a reference or skewed img to be dewarped.
		Accepts PNG, JPG, TIF, converts to grayscale, & stores it in either
		self.ref or self.img

		Parameters
		----------
		path : str
			path/to/image.file

		flag : str
			Whether to store the file as the ref or img to be dewarped. 
			Accepts values of {'ref', 'r', 'img', 'i'}
		"""	
		tmp = cv.imread(path)

		if flag in ('ref', 'r'): 
			self.ref = cv.cvtColor(tmp, cv.COLOR_BGR2GRAY)
		elif flag in ('img', 'i'): 
			self.og = tmp
			self.img = cv.cvtColor(tmp, cv.COLOR_BGR2GRAY)
		else: 
			raise ValueError("The 'flag' param must be one of {'ref', 'r', 'img', 'i'}")


	def sift(self, flag=None):
		"""
		Performs the SIFT algorithm, then stores the keypoints and descriptors
		into 'self.kpd_ref' or 'self.kpd_img', depending on the flag value.

		Parameters
		----------
		flag : str
			One of {'ref' 'r' 'img' 'i'}, determines where to store the 
			keypoint descriptor.
		"""


		if flag in ('ref', 'r'): 
			kp, des = self.sifter.detectAndCompute(self.ref, mask=None)
			self.kpd_ref = self.Kpd(kp, des)
		elif flag in ('img', 'i'): 
			kp, des = self.sifter.detectAndCompute(self.img, mask=None)
			self.kpd_img = self.Kpd(kp, des)
		else: 
			raise ValueError("The 'flag' param must be one of {'ref', 'r', 'img', 'i'}")


	def fann(self, k=2):
		"""
		Finds k nearest neighbors using the FANN algorithm, then appends the
		matches to self.matches

		Parameters
		----------
		k : int
			The number of neighbors to cluster
		"""
		# Descriptors of the ref and img keypoints
		des_r, des_i = self.kpd_ref.des, self.kpd_img.des
		self.matches = self.fanner.knnMatch(des_r, des_i, k=k)


	def filter_matches(self, ratio=None): 
		"""
		Keep only the close matches

		Parameters
		----------
		ratio : float
			The upper limit of ref_match_distance/img__match_distance
		"""
		good = []
		if ratio == None:
			ratio = self.MATCH_RATIO
			
		for r,i in self.matches:
			if r.distance < ratio * i.distance:
				good.append(r)

		self.good_matches = good


	def get_homography(self):
		"""
		Uses closely matching keypoints to compute the transformation matrix M:
			img --> ref, or  [ref] = M[img]
		and the homography mask, then stores them in 
		self.transformation_matrix
		self.homo_mask
		"""
		if len(self.good_matches) < self.MIN_MATCH_COUNT:
			print(f"To find the homography, at least {MIN_MATCH_COUNT} closely matching keypoints are necessary. These images have only {len(self.good_matches)} keypoints.")
			return
		else:
			kp_ref = self.kpd_ref.kp
			kp_img = self.kpd_img.kp

			ref_pts = np.float32( [ kp_ref[m.queryIdx].pt for m in self.good_matches ] ).reshape(-1,1,2)
			img_pts = np.float32( [ kp_img[m.trainIdx].pt for m in self.good_matches ] ).reshape(-1,1,2)

			M, mask = cv.findHomography(img_pts, ref_pts, cv.RANSAC, 5.0)
			mask = mask.ravel().tolist()

			self.transformation_matrix = M
			self.homo_mask = mask


	def apply_transform(self):
		"""
		Applies the transformation matrix to the vector span bounding the image.
		Stores the resulting vector transformation in self.perspective_transformation.
		Used for computing polylines between landmarks.
		"""
		h, w = self.ref.shape
		points = np.float32( [ [0,0], [0,h-1], [w-1,h-1], [w-1,0] ] ).reshape(-1,1,2)
		dst = cv.perspectiveTransform(points, self.transformation_matrix)
		self.perspective_transform = dst


	def show_homography(self):
		"""
		Show the homography and keypoints of the reference and skewed images.
		Useful for visual inspection and parameter tuning.
		"""
		ref = self.ref
		img = self.img
		dst = self.perspective_transform
		kp_ref = self.kpd_ref.kp
		kp_img = self.kpd_img.kp
		matches = self.good_matches

		poly = cv.polylines(self.img, [np.int32(dst)], True, 255, 3, cv.LINE_AA)

		draw_params = dict(matchColor=(0,255,0),
                    singlePointColor=None,
                    matchesMask=self.homo_mask,
                    flags=2)

		comparison = cv.drawMatches(ref, kp_ref, img, kp_img, matches, None, **draw_params)
		plt.imshow(comparison, 'gray'), plt.show()


	def dewarp_image(self):
		"""
		Dewarp the skewed image by applying the img --> ref transformation
		matrix. Store the dewarped image in self.dewarped

		Returns
		-------
		ndarray
			The dewarped image
		"""
		h, w = self.ref.shape
		M = self.transformation_matrix
		dewarped = cv.warpPerspective(self.og, M, (w,h))

		self.dewarped = dewarped

		if len(dewarped.shape) == 3:
			dewarped = cv.cvtColor(dewarped, cv.COLOR_BGR2GRAY)

		self.dewarped_gray = dewarped

		return dewarped
			

	def dewarp(self, ref=None, img=None):
		"""
		Wrapper method: performs full dewarping pipeline. Passing arguments
		overwrites any images currently stored in the dewarper.

		Parameters
		----------
		ref : str or ndarray
			str - path to the reference image file
			ndarray - the reference image

		img : str or ndarray
			str - path to an image file
			ndarray - the skewed image 


		Returns
		-------
		ndarray
			The dewarped image
		"""

		# Handle strings or images as constructor args
		if isinstance(ref, str):
			self.load(ref, 'ref')
		elif isinstance(ref, np.ndarray):
			self.ref = cv.cvtColor(ref, cv.COLOR_BGR2GRAY)
		else:
			pass

		if isinstance(img, str):
			self.load(img, 'img') 
		elif isinstance(img, np.ndarray):
			self.og = img
			self.img = cv.cvtColor(self.og, cv.COLOR_BGR2GRAY)
		else:
			pass


		if self.ref is None:
			raise ValueError("The reference image is missing. Pass the file paths explicitly.")
		if self.img is None:
			raise ValueError("The warped image is missing. Pass the file paths explicitly.")

		self.sift('ref')
		self.sift('img')
		self.fann()
		self.filter_matches()
		self.get_homography()
		dewarped = self.dewarp_image()

		return dewarped












