import os

class ACT():
	"""
	A class for grading an ACT exam.

	Attributes
	----------
	test_code : int
		The year and month that an official exam was administered: yyyymm
		The test code serves as the unique identifier for tests, templates,
		answer keys, and scoring tables.

	first : str
		A student's first name

	last : str
		A student's last name

	submission_directory : str
		path/to/directory/containing/the/submitted/answer/file.json

	submission : dict
		Key = 'first', 'last', 'test_code', 'e', 'm', 'r', 's'
		Val = str*3, dict*4
		The emrs keys contain dict values:
			K = int  # question number
			V = str  # 'ABCDE' or '12345' representing submitted answers

	answer_key : dict
		Key = int  # question numbers
		Val = str  # 'A' 'B' 'C' 'D' 'E' an answer choice

	scoring_table : dict
		A nested dict for converting correct answers to a numeric score
		Key = 'test_code', 'table'
		Val =  int, 		dict
			K = int  # 1-36,  A numeric score 
			V = dict
				K = str  # 'e' 'm' 'r' 's', A section code
				V = range  # The number of questions corresponding to a numeric score

	graded_submission : dict
		Key = 'scores', 'e', 'm', 'r', 's'
		Val = dict
			'scores'
			K = 'e', 'm', 'r', 's'  # section code
			V = tuple, (int, int)  # (num correct, scaled score)
			'emrs'
			K = int  # question number
			V = tuple, (bool, str, str)  
			(is correct, submitted answer, correct answer)
			Ex: (True, 'A', '-'),  (False, 'A', 'C')
			The result of a specific question with entries suitable to be 
			injected into the html score report template. If a question is 
			correct, the correct answer entry will be '-'

	score_report_string : str
		A string of html containing the content and formatting for an ACT score 
		report.
	"""

	def __init__(self, test_code, name_first, name_last, submission_directory):
		"""
		The constructor

		Parameters
		----------
		test_code : int
		The year and month that an official exam was administered: yyyymm
		The test code serves as the unique identifier for tests, templates,
		answer keys, and scoring tables.

		name_first : str
			A student's first name

		name_last : str
			A student's last name

		submission_directory : str
			path/to/directory/containing/the/submitted/answer/file.json


		"""
		self.test_code = test_code
		self.first = name_first
		self.last = name_last
		self.submission_directory = os.path.abspath(submission_directory)
		self.submission = None
		self.answer_key = None
		self.scoring_table = None
		self.graded_submission = None
		self.score_report_string = None
		self.score_report_html = None
		self.score_report_pdf = None


	@staticmethod
	def compare_MC(submitted_answer, correct_answer):
		"""
		Compares one multiple choice submission (case insensitive).

		Parameters
		----------
		sa : str 
			The submitted answer

		ca : str 
			The correct answer

		Returns
		------- 
		tuple, (bool, str, str)
			(True,  sa, '-')  or 
			(False, sa, ca )
		"""
		sa = submitted_answer.upper()
		ca = correct_answer.upper()

		if sa == ca:
		    return (True, sa, '-')
		else:
		    return (False, sa, ca)


	@staticmethod
	def write_json_for_questions(num_of_questions):
		"""
		Generates a string of valid json to hold question numbers and answers.
		(Does not generate the enclosing curly braces.)

		Parameters
		----------
		num_of_questions : int
			The number of questions equals the number of json lines to write.

		Returns
		-------
		str
			A string of valid json of the form:  
			'\t   "1": "",\n\t   "2": ""\n'
		"""
		text = ""
		for q in range(1, num_of_questions):  # write all but last num_of_question
			text += f'\t   "{q}": "",\n'
		# write last questions (no trailing comma)
		text += f'\t   "{num_of_questions}": ""\n'

		return text

	@staticmethod
	def load_json(path):
		"""
		Loads a python dict from a valid json formatted file.

		Parameters
		----------
		path : str
			path/to/a/file.json

		Raises
		------
		IOError
			If file.read() fails for any reason

		Returns
		-------
		dict
		"""
		import sys
		import json

		with open(path) as f:
			try:
				data = f.read()
			except IOError:
				print("There was an error opening the file at " + path)
				sys.exit()
		return json.loads(data)


	def factory_submission(self, destination):
		"""
		Creates a blank submission file.
		Writes json representing a set of ACT answers to a file.

		Parameters
		----------
		destination : str
			path/to/the/destination/file.json

		"""
		import os
		outfile = os.path.join(destination, f'{self.last}_{self.first}_ACT_{self.test_code}_Sub.json')
		m = '{\n'
		m += f'  "first": "{self.first}",\n'
		m += f'  "last": "{self.last}",\n'
		m += f'  "test_code": "{self.test_code}",\n\n'

		# english section
		m += '  "e": {\n'
		m += self.write_json_for_questions(75)
		m += '  },\n\n'

		# math section
		m += '  "m": {\n'
		m += self.write_json_for_questions(60)
		m += '  },\n\n'

		# reading section
		m += '  "r": {\n'
		m += self.write_json_for_questions(40)
		m += '  },\n\n'

		# science section
		m += '  "s": {\n'
		m += self.write_json_for_questions(40)
		m += '  }\n\n'

		m += '}\n'

		with open(outfile, 'w') as f:
			print(m, file=f)


	def factory_answer_key(self):
		"""
		Creates a blank answer key file.
		Writes json representing an ACT answer key to the file
		./answer_keys/ak_ACT_123456.json  
		(123456 is the test code)
		"""
		outfile = f'./answer_keys/ak_ACT_{self.test_code}.json'
		m = '{\n'
		m += f'  "test_code": "{self.test_code}",\n\n'

		# english section
		m += '  "e": {\n'
		m += self.write_json_for_questions(75)
		m += '  },\n\n'

		# math section
		m += '  "m": {\n'
		m += self.write_json_for_questions(60)
		m += '  },\n\n'

		# reading section
		m += '  "r": {\n'
		m += self.write_json_for_questions(40)
		m += '  },\n\n'

		# science section
		m += '  "s": {\n'
		m += self.write_json_for_questions(40)
		m += '  }\n\n'

		m += '}\n'

		with open(outfile, 'w') as f:
			print(m, file=f)


	def factory_scoring_table(self):
		"""
		Creates a blank scoring table file.
		Writes a nested pydict in the appropriate format to a file. 
		Keys are Q numbers and scaled scores (1-36). Values are 
		range functions with empty arguments.

		Parameters
		----------
		NOT IMPLEMENTED 
		order (string): descending is 36 -> 1  (matches format on ACT)
						ascending  is 1 -> 36
		"""
		outfile = f'./scoring_tables/st_ACT_{self.test_code}.py'

		tc = self.test_code

		header = f"# st_ACT_{tc}.py\n\n"
		header += "# The blank {tc} ACT scoring table as a python dict. After filling\n"
		header += "# in the ranges, run the file in a session to load the scoring table\n"
		header += "# in a namespace:\n\n"
		header += "# exec( open('st_ACT_123456.py').read() )\n"
		header += "#\n\n"

		pydict = "scoring_table = {\n"
		pydict += f"    'test_code':{tc},\n"
		pydict += "    'table':{\n"

		for scaled_score in range(1,36):  # for all but 1 score
		    pydict += f"        {scaled_score}:{{'e':range(,), 'm':range(,), 'r':range(,), 's':range(,)}},\n"

		# add final score without trailing comma
		pydict += "        36:{'e':range(,), 'm':range(,), 'r':range(,), 's':range(,)}\n"

		pydict += "    }\n}"  # close dict

		# m = header + pydict

		with open(outfile, 'w') as f:
			print(header, file=f)
			print(pydict, file=f)


	def encode_questions(self, section):
		"""
		Convert keys from strings to integers and convert multiple-choice
		answers from integers to strings.

		Parameters
		----------
		section : dict
			Key = str  # A question number
			Val = int  # The numeric index of a multiple choice answer
					   # A = 1, B = 2, etc. 
			Questions & answers, Ex: {"1":4, "2":1, etc.}

		Returns
		-------
		dict
			Key = int  # A question number
			Val = str  # A multiple choice answer: 'ABCDE' or 'FGHJK' 
			Ex: {1:'D', 2:'F', 3:'B', 4:'K', etc.}
		"""
		# dicts to convert num submissions to char submissions
		dOdd  = {1:'A', 2:'B', 3:'C', 4:'D', 5:'E'}
		dEven = {1:'F', 2:'G', 3:'H', 4:'J', 5:'K'}

		for q in range(1, len(section)+1):
			# replace string keys with int keys
			section[q] = section.pop(str(q))

			# convert num submissions to char submissions
			d = dOdd if q%2 == 1 else dEven
			if section[q].isdigit():
				section[q] = d[ int(section[q]) ]
			else:
				pass

		return section


	def encode_submission(self, path_to_submission):
		"""
		Converts the test section portions of a submission dict as follows:
		{"1":4, "2":1, etc.}  -->   {1:'D', 2:'F', etc.}
		Keys: str num  -->  int num
		Vals: int num  -->  str letter

		Parameters
		----------
		path_to_submission : str
			path/to/submission/file.json
			The submission file contains submitted answers to all 4 ACT sections.

		Returns
		-------
		dict
			Key = 'first', 'last', 'test_code', 'emrs'
			Val = str, 		str,	str,		dict
				K = int  # A question number
				V = str  # 'ABCDE'(odd) or 'FGJHK' (even)


		Examples
		--------
		See encode_questions(...) for schema

		"""
		sub = self.load_json(path_to_submission)
		sub['e'] = self.encode_questions(sub['e'])
		sub['m'] = self.encode_questions(sub['m'])
		sub['r'] = self.encode_questions(sub['r'])
		sub['s'] = self.encode_questions(sub['s'])

		return sub


	def load_submission(self):
		"""
		Wrapper Method
		Loads and encodes a submission file. The student name and test code are
		read from the class instance attributes. The file must exist and follow 
		the naming convention  Last_First_ACT_TestCode_Sub.json
		Ex: Smith_Sam_ACT_201804_Sub.json

		Returns
		-------
		dict
			Key = 'first', 'last', 'test_code', 'emrs'
			Val = str, 		str,	str,		dict
				K = int  # A question number
				V = str  # 'ABCDE'(odd) or 'FGJHK' (even)

		Examples
		--------
		See encode_questions(...) for schema
		"""
		file_name = f'{self.last}_{self.first}_ACT_{self.test_code}_Sub.json'
		path = os.path.join( self.submission_directory, file_name )

		return self.encode_submission(path)


	def encode_answer_key(self, path_to_answer_key=None):
		"""
        Encodes answer_key.json as python dict: 'r':{..., q:(eval_fcn, ca), ...}
        Each key is a question. The first element is an evaluation function,
        the second is the correct answer.

        answer_key : str 
        	path/to/answer_key.json

        Returns
        ------- 
        dict
        	Key = 'test_code', 'emrs'
        	Val =  str,			dict
	        	K = str  # The section code, 'e', 'm', 'r', 's'
	        	V = tuple, (function, str)
        	The dict that will be passed to grade_section(..., answer_key).
        	The first tuple element is an evaluation function, the second 
        	element is the correct answer.

        Examples
        --------  
        	{..., 'e':{ q: ( eval_fcn(), ca ), etc. }, ...}
        """
		import sys

		if path_to_answer_key == None:
			path_to_answer_key = f'./answer_keys/ak_ACT_{self.test_code}.json'

		try:  # load answer key into dict
		    ak = self.load_json(path_to_answer_key)
		except IOError:
		    print("There was an error opening the file at " + path_to_answer_key)
		    sys.exit()

		# change string dict keys to integer dict keys and assign functions to 
		# evaluate multiple choice answers:
		# d[q] = 'A' --> d[q] = ( fcn(), 'A' )
		for q in range(1,76):
		    ak['e'][q] = ak['e'].pop(str(q))  # english section
		    ak['e'][q] = (self.compare_MC, ak['e'][q])

		for q in range(1,61):
		    ak['m'][q] = ak['m'].pop(str(q))  # math section
		    ak['m'][q] = (self.compare_MC, ak['m'][q])

		for q in range(1,41):
		    ak['r'][q] = ak['r'].pop(str(q))  # reading section
		    ak['r'][q] = (self.compare_MC, ak['r'][q])

		for q in range(1,41):
		    ak['s'][q] = ak['s'].pop(str(q))  # science section
		    ak['s'][q] = (self.compare_MC, ak['s'][q])

		encoded_answer_key = ak
		return encoded_answer_key


	def grade_section(self, section, answer_key):
		"""
		Checks submitted answers against answer_key (ak) for a single exam
		section (or other single-level dict). The first element of each
		answer_key value is an evaluation function. Running  ak[q][0](args)
		will apply the evaluation function to the submitted answer.

		section : dict 
			Single-level dict of submitted exam answers
			Ex: {1:'D', 2:'F', 3:'B', 4:'K', etc.}
		
		answer_key : dict
        	Key = 'test_code', 'emrs'
        	Val =  str,			dict
	        	K = str  # The section code, 'e', 'm', 'r', 's'
	        	V = tuple, (function, str)
	        The encoded answer key. The first tuple element is an evaluation 
	        function, the second element is the correct answer.
			Schema: { q: ( eval_fcn(), ca ) }
			Access:	ak[q] = ( fcn(), correct_answer )

		Returns
		-------
		dict
			Key = int  # A question number
			Val = tuple, (bool, str, str)
			One section of evaluated questions in the form 
			r[q] = (True, sa, '-') or (False, sa, ca)		

			The first element is whether the question was answered correctly.
			The second element is the submitted answer 'ABCDE' or 'FGHJK'.
			The third element is the correct answer; '-' indicates that the
			question was answered correctly.
		"""

		results = {}

		for q in range(1, len(answer_key)+1):
			compare = answer_key[q][0]  # the evaluation function
			correct_answer = answer_key[q][1]
			submitted_answer = section[q]

			results[q] = compare(submitted_answer, correct_answer)

		return results

	@staticmethod
	def count_correct_answers(graded_section):
		"""
		Counts correct answers and returns raw score. Usually applied to one
		test section at a time.

		graded_section : dict 
			Key = int  # A question number
			Val = tuple, (bool, str, str)

			One section of evaluated questions in a form ready to be injected
			into the html score report template: 
			gs[q] = (True, sa, '-') or (False, sa, ca)		

			The first element is whether the question was answered correctly.
			The second element is the submitted answer 'ABCDE' or 'FGHJK'.
			The third element is the correct answer; '-' indicates that the
			question was answered correctly.

			Ex: { 1:(False, 'D', 'B'), 2:(True, 'G', '-'), etc. }


		Returns
		-------
		int
			The number of correct answers


		Examples
		--------
		>>> gs = { 1:(False, 'D', 'B'), 2:(True, 'G', '-'), 3:(False, 'A', 'B') }
		>>> count_correct_answers(graded_section = gs)
		    1		
		"""
		raw_score = 0
		for q,v in graded_section.items():
			raw_score += v[0]

		return raw_score


	def compute_scaled_score(self, raw_score, scoring_table, section_id):
		"""
		Reads a scoring table, corelating a single raw score to a single 
		scaled score.

		Parameters
		----------
		raw_score : int
			The number of correct answers (usually in a single section).

		scoring_table : dict
			A nested dict for converting correct answers to a numeric score
			Key = 'test_code', 'table'
			Val =  int, 		dict
				K = int  # 1-36,  A numeric score 
				V = dict
					K = str  # 'e' 'm' 'r' 's', A section code
					V = range  # The number of questions corresponding to a numeric score

		section_id : str
			One of 'e', 'm', 'r', 's'. Each id corresponds to a scoring_table key.

		Returns
		-------
		int
			The scaled section score, a number from 1 to 36
		"""
		for scaled_score, raw_ranges in scoring_table['table'].items():
			if raw_score in raw_ranges[section_id]:
				return scaled_score
		print("Something went terribly wrong in act.compute_scaled_score(...). The raw_score was not found in any scoring range.")
		return False

	@staticmethod
	def round_half_up(number):
		"""
		Rounds a number according to standard rules.

		Parameters
		----------
		number : float
			The number to be rounded to a whole number.

		Returns
		-------
		int
			The rounded number

		Examples
		--------
		>>> round_half_up(1.4)
			1
		>>> round_half_up(1.5)
			2
		"""
		return int(number + 0.5)


	def grade_submission(self):
		"""
		Grades all sections of an ACT.

		Returns
		-------
		dict
			Key = 'scores', 'e', 'm', 'r', 's'
			Val = dict
				'scores':
				K = 'e', 'm', 'r', 's', 'composite'  # score code
				V = tuple, (int, int)  # (num correct, scaled score)
				'emrs':
				K = int  # question number
				V = tuple, (bool, str, str)  
				(is correct, submitted answer, correct answer)
				Ex: (True, 'A', '-'),  (False, 'A', 'C')
				The result of a specific question. If a question is 
				correct, the correct answer entry will be '-'

		Examples
		--------
		>>> act.grade_submission()
		{
			'scores': {'e': (45, 20), 'm': (35, 24), 'r': (31, 28), 's': (28, 24), 'composite': 24}, 
			'e': {1: (False, 'B', 'C'), 2: (False, 'H', 'F'), etc.},
			'm': {...},
			'r': {...},
			's': {...},
		}
		"""
		sub = self.submission
		ak = self.answer_key
		st = self.scoring_table

		scaled_score_total = 0

		r = {'scores':{}, 'e':{}, 'm':{}, 'r':{}, 's':{}}
		for section in ['e', 'm', 'r', 's']:
			r[section] = self.grade_section( sub[section], ak[section] )
			raw_score = self.count_correct_answers( r[section] )
			scaled_score = self.compute_scaled_score(raw_score, st, section)
			r['scores'][section] = (raw_score, scaled_score)
			scaled_score_total += scaled_score

		r['scores']['composite'] = self.round_half_up(scaled_score_total/4.0)
		results = r
		self.graded = results
		self.scores = results['scores']

		return results


	def load_scoring_table(self, path=None):
		"""
		Loads a serialized scoring table from a file. The file must exist, be 
		of type pickle, be written as bytes, and follow the naming convention
		st_ACT_TestCode.pkl
		Ex: st_ACT_201804.pkl

		Parameters
		----------
		path : str
			path/to/scoring/table.pkl
			If the path is None, reads from a default location.

		Returns
		-------
		dict
			A scoring table.
			A nested dict for converting correct answers to a numeric score
			Key = 'test_code', 'table'
			Val =  int, 		dict
				K = int  # 1-36,  A numeric score 
				V = dict
					K = str  # 'e' 'm' 'r' 's', A section code
					V = range  # The number of questions corresponding to a numeric score
		"""
		import pickle

		if path is None:
			path = f'scoring_tables/st_ACT_{self.test_code}.pkl'
			
		with open(path, 'rb') as f:
			scoring_table = pickle.load(f)
		return scoring_table


	def create_template_variables_for_section(self, section_id, graded_submission):
		"""
		Generates a flat dict of all elements within one section of an ACT. 
		The output dict is compatible with the template variables in the ACT 
		score report templates. Each dict key is a string corresponding to a
		unique variable in the template.
		Ex: rQ23, mSA15, eCA41

		Parameters
		----------
		section_id : str 
			The dict key for the section, options are {'e', 'm', 'r', 's'}

		graded_submission : dict
			A dict of graded ACT results and scores; each q -> (T/F, sa, ca).
			See grade_submission() for example.

		Returns
		-------
		dict 
			Key = '_Qn', '_SAn', '_CAn'  # '_' = section_id: 'emrs'
										 # 'Q' = designates a question number
										 # 'SA' = designates a submitted answer
										 # 'CA' = designates a correct answer
										 # 'n' = question number
			Val = int, str, str 	# question number, submitted answer, correct answer

			A flat dict of values compatible with the variables in the score 
			report template. These are the values that are injected into the 
			html template.

		Examples
		--------
		>>> act.create_template_variables_for_section('e', gs)
		{'eQ1':1, 'eSA1':'B', 'eCA1':'C', 'eQ2':2, 'eSA2':'H', 'eCA2':'F', etc.}
		"""

		sid = section_id
		graded_section = graded_submission[sid]
		template_vars = {}

		q = 1  # question index counter
		while q <= len(graded_section):
			tupl = graded_section[q]  # extract graded question (tuple) - see docstring
			template_vars[ f'{sid}Q{q}' ] = q  # assign question_number
			template_vars[ f'{sid}SA{q}' ] = tupl[1]
			template_vars[ f'{sid}CA{q}' ] = tupl[2]

			q += 1

		return template_vars


	def create_template_variables(self, graded_submission):
		"""
		Generates a flat dict of all elements in an entire ACT. The output dict
		is compatible with the template variables in the ACT score report 
		templates   Ex: rQ23, mSA15, eCA41

		graded_submission : dict
			A dict of graded ACT results; each q -> (T/F, sa, ca).
			See grade_submission() for example.

		Returns
		-------
		dict 
			Key = '_Qn', '_SAn', '_CAn'  # '_' = section_id: 'emrs'
										 # 'Q' = designates a question number
										 # 'SA' = designates a submitted answer
										 # 'CA' = designates a correct answer
										 # 'n' = question number
			Val = int, str, str 	# question number, submitted answer, correct answer

			A flat dict of values compatible with the variables in the score 
			report template. These are the values that are injected into the 
			html template. See create_template_variables_for_section().
		"""
		graded = graded_submission
		template_vars = {}

		template_vars['FIRST'] = self.first
		template_vars['LAST'] = self.last
		template_vars['TEST_CODE'] = self.test_code
		template_vars['SCORE_E'] = self.graded['scores']['e'][1]
		template_vars['SCORE_M'] = self.graded['scores']['m'][1]
		template_vars['SCORE_R'] = self.graded['scores']['r'][1]
		template_vars['SCORE_S'] = self.graded['scores']['s'][1]
		template_vars['COMPOSITE'] = self.graded['scores']['composite']

		# inject all template vars (Q, SA, CA) for each ACT section
		for section in ['e', 'm', 'r', 's']:
			template_vars.update( self.create_template_variables_for_section(section, graded_submission) )

		return template_vars


	def load_score_report_template(self):
		"""
		Loads a score report template from an html file. The file must exist
		and follow the naming convention: template_ACT_201804.html
		The file is loaded as a jinja2.environment.Template object. 

		Returns
		-------
		jinja2.environment.Template
			An html template
		"""
		from jinja2 import Environment, FileSystemLoader
		env = Environment(loader=FileSystemLoader('./templates'))
		template = env.get_template( f"template_ACT_{self.test_code}.html" )
		return template


	def populate_score_report_template(self, template_variables):
		"""
		Injects ACT results into the score report template by assigning values
		in the dict of graded results to unique variables in the template. The
		template_variables parameter is the dict of graded results.

		Parameters
		----------
		template_variables : dict 
			Key = '_Qn', '_SAn', '_CAn'  # '_' = section_id: 'emrs'
										 # 'Q' = designates a question number
										 # 'SA' = designates a submitted answer
										 # 'CA' = designates a correct answer
										 # 'n' = question number
			Val = int, str, str 	# question number, submitted answer, correct answer

			A flat dict of ACT results compatible with the variables in the score 
			report template. These are the values that are injected into the 
			html template. The dict is generated by create_template_variables_for_section().

		Returns
		-------
		str
			A string of valid html containing all the ACT results. The string 
			can be rendered in a web browser or converted to a pdf.
		"""
		template = self.load_score_report_template()
		score_report_string = template.render(template_variables)
		return score_report_string


	def write_score_report(self, score_report_string, score_report_directory):
		"""
		Writes the score report to both html and pdf files.
		The output files follow the naming convention
		Last_First_ACT_TestCode_Score_Report.extension
		Ex: Smith_Sam_ACT_201804_Score_Report.pdf

		Parameters
		----------
		score_report_string : str
			A string of valid html containing all the ACT results.

		score_report_directory : str
			path/to/the/score/report/directory
		"""
		from weasyprint import HTML

		score_report_directory = os.path.abspath(score_report_directory)
		file_name = f"{self.last}_{self.first}_ACT_{self.test_code}_Score_Report"
		path_html = os.path.join(score_report_directory, file_name+'.html')
		path_pdf = os.path.join(score_report_directory, file_name+'.pdf')

		self.score_report_html = path_html
		self.score_report_pdf = path_pdf

		# write the score report to an html file
		with open(path_html, 'w') as f:
			print(score_report_string, file=f)

		# write the score report to a pdf
		HTML(path_html).write_pdf(path_pdf)


	def create_score_report(self):
		"""
		Wrapper method.
		Generates the score report and writes it to html and pdf files.
		"""
		template_vars = self.create_template_variables(self.graded_submission)
		self.score_report_string = self.populate_score_report_template(template_vars)

		score_report_directory = os.path.abspath(f'../zStd/{self.last}_{self.first}')
		self.write_score_report(self.score_report_string, score_report_directory)






















