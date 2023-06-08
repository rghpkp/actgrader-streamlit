# factory_template_ACT.py
#
# builds html template for ACT score report
#
# USAGE:  python factory_template_ACT.py -o template_ACT_123456.html

import argparse

ap = argparse.ArgumentParser()
ap.add_argument('--output', '-o', required='False', help='path/to/output_html_file')
args = ap.parse_args()

outfile = args.output if args.output else "./dummy"


def populate_row(sid, num_questions, space_breaks, row_breaks):
    """
    Builds html table row for ACT sections. Each 'row' consists of 3 <tr></tr> tags,
    and each of the 3 <tr> contains the same number of <td> {{{{var}}}} </td> tags.
    Each <td> contains a Jinja-compliant variable.

    (string) sid: the section id - will be prepended to each var name in each section
                    ex: Reading section: rQ23, rSA23, rCA23

    (int) num_questions:

    (tuple)(int) space_breaks: contains question indices after which to insert blank <td> - used to format results by passage

    (tuple)(int) row_breaks: question indices after which to start a new row - for formatting

    return (string) m: the html markup for a complete ACT section
    """

    m = "" # init a string to hold the html markup
    rq = '<tr class="question_nums"><td class="row_label">Question</td><td>&nbsp</td> {} </tr>'  # table row of question numbers
    rs = '<tr class="submitted_answers"><td class="row_label">Submitted</td><td>&nbsp</td> {} </tr>'  # table row of submitted answers
    rc = '<tr class="correct_answers"><td class="row_label">Correct</td><td>&nbsp</td> {} </tr>'  # table row of correct answers

    tdq = ""  # table division - question number
    tds = ""  # table division - submitted answer
    tdc = ""  # table division - correct answer

    q = 1  # question index counter
    while q <= num_questions:

        # for each questions index, create corresponding variables for q, sa, ca
        tdq += f"<td> {{{{ {sid}Q{q} }}}} </td>"
        tds += f"<td> {{{{ {sid}SA{q} }}}} </td>"
        tdc += f"<td> {{{{ {sid}CA{q} }}}} </td>"

        if q in space_breaks: # if at end of passage, insert <td> spacers
            tdq += "<td>&nbsp</td>"
            tds += "<td>&nbsp</td>"
            tdc += "<td>&nbsp</td>"

        if q in row_breaks:  # if time to start a new row
            # insert all the <td> into the corresponding <tr> and append to markup
            m += ("\n            " + rq.format(tdq)) 
            m += ("\n            " + rs.format(tds))
            m += ("\n            " + rc.format(tdc))

            # insert blank row
            m += ('\n            <tr class="blank"><td>&nbsp</td></tr>')

            # reset the temp td strings
            tdq = ""
            tds = ""
            tdc = ""

        q += 1

    # when loop concludes, insert all the (remaining) <td> into the corresponding <tr>
    # and append to markup
    m += ("\n            " + rq.format(tdq))
    m += ("\n            " + rs.format(tds))
    m += ("\n            " + rc.format(tdc))

    return m

def build_template(outfile):
	### begin template ###########################################

	m = "<!DOCTYPE html>" # init a string to hold the html markup

	m += """
	<html>
	<head lang="en">
	    <meta charset="UTF-8">
	    <title>ACT Score Report </title>
	    <style>
	        @page {
	          size: Legal; /* Change from the default size of A4 */
	          /* size: landscape; */
	          /* size: Letter; /* Change from the default size of A4 */
	           margin: 0.5in; /* Set margin on each page */
	        }

	        td {
	            text-align: center;
	            min-width: 20;
	            font-size: small;
	        }

	        .short_answer td :not(.row_label){
	                        border-spacing: 12px 2px;
	                        /*padding: 2px 12px 2px 2px;
	                        border: 2px 12px 2px 2px;*/
	                        text-align: center;
	                        word-wrap: break-word;
	                        min-width: 25;
	                        max-width: 50;

	        }


	        .row_label {
	                        text-align: left;
	                        border-spacing: 2px;
	                        min-width: 25;
	        }

	        .question_nums > td {
	                        /*font-size: 14px;*/
	        }
	    </style>
	</head>
	<body>
	"""

	# name and test fields
	m += """
	    <div id="meta">
	        <h1> {{LAST}}, {{FIRST}}: ACT {{ TEST_CODE }} </h1>
	        <h2> {{ NAME }} </h2>
	        <h3 style="background-color: orange;"> Score: {{ COMPOSITE }} </h3>
	        <h3> English: {{ SCORE_E }} &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; Math: {{ SCORE_M }}</h3>
	        <h3>  </h3>
	        <h3> Reading: {{ SCORE_R }} &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; Science: {{ SCORE_S }} </h3>
	        <h3> </h3>
	    </div>
	"""

	### English section results (75 questions)
	m += """
	    <div id="english" style="background-color: powderblue;">
	        <table>
	          <thead><b>English</b></thead>
	          <tbody>
	"""

	m += populate_row('e', 75, (15, 45), (30,60))

	m += """
	          </tbody>
	        </table>
	    </div>
	    <br /><br />
	"""
	### end English section


	### Math section results (60 questions)
	m += """
	    <div id="math" style="background-color: powderblue;">
	        <table>
	          <thead><b>Math</b></thead>
	          <tbody>
	"""

	m += populate_row('m', 60, (15, 45), (30,)) 

	m += """
	          </tbody>
	        </table>
	    </div>
	    <br /><br />
	"""
	### end Math section



	### reading section results (40 questions)
	m += """
	    <div id="reading" style="background-color: powderblue;">
	        <table>
	          <thead><b>Reading</b></thead>
	          <tbody>
	"""

	m += populate_row('r', 40, (10,30), (20,)) 

	m += """
	          </tbody>
	        </table>
	    </div>
	    <br /><br />
	"""
	### end reading section


	### Science section results (40 questions)
	m += """
	    <div id="science" style="background-color: powderblue;">
	        <table>
	          <thead><b>Science</b></thead>
	          <tbody>
	"""

	m += populate_row('s', 40, (6,12,26,33), (19,)) 

	m += """
	          </tbody>
	        </table>
	    </div>
	"""
	### end Science section


	# closing tags
	m += """
	</body>
	</html>
	"""

	### end template

	with open(outfile, 'w') as f:
	    print(m, file=f)

build_template(outfile)

