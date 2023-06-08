import cv2
import numpy as np

class Deshadower():
	"""
	Contains methods for removing shadows and lighting artifacts from the image
	of an exam sheet.

	Attributes
	----------
	img : ndarray
		The source image to be modified.
	"""

	def __init__(self, img=None):
		"""
		"""
		self.img = img

	def deshadow(self, kernel=(7,7), ksize=21, threshold=230):
		"""
		Removes the low frequency noise & color info from an image. Returns
		a an image with color artifacts (like shadows) removed. 

		Parameters
		----------
		kernel : tuple, (int, int)
			The size of the dilation kernel
			Default = (7,7)

		ksize : int
			The aperture linear size for the median blur, must be odd and
			greater than 1.
			Default = 21

		threshold : int
			The brightness level for final thresholding. Must be between zero 
			and 255.
			Default = 230

		Returns
		-------
		ndarray
			An image with color artifacts removed.
		"""
		img = self.img

		# Convert image to grayscale if it is RGB
		if len(img.shape) > 2:
			img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

		dilated_img = cv2.dilate(img, np.ones(kernel, np.uint8)) 
		bg_img = cv2.medianBlur(dilated_img, ksize)  # The low frq color information
		# cv2.imshow("bg_image", bg_img)

		absdiff = cv2.absdiff(img, bg_img)  # Absdiff is inverted img w/ color info removed
		# cv2.imshow("absdiff", absdiff)

		diff_img = 255 - cv2.absdiff(img, bg_img)  # Img with color info removed
		# cv2.imshow("diff_img", diff_img)

		norm_img = diff_img.copy() # Needed for 3.x compatibility
		cv2.normalize(diff_img, norm_img, alpha=0, beta=255, norm_type=cv2.NORM_MINMAX, dtype=cv2.CV_8UC1)
		# cv2.imshow("norm_img", norm_img)

		_, thr_img = cv2.threshold(norm_img, 230, 0, cv2.THRESH_TRUNC)
		# cv2.imshow("thr_img", thr_img)
		# cv2.normalize(thr_img, thr_img, alpha=0, beta=255, norm_type=cv2.NORM_MINMAX, dtype=cv2.CV_8UC1)
		# cv2.imshow("Dehsadowed", thr_img)
		# cv2.waitKey(0)
		# cv2.destroyAllWindows()

		return thr_img
