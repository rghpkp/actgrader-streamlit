import os, sys
import pickle
from jinja2 import Environment, FileSystemLoader
from weasyprint import HTML

sys.path.append(os.path.abspath('static/grader/classes'))
from act import ACT

def pipeline(submission):
    print("\n\nPipeline Entered\n")
    print(submission)
    test_code = submission['test_code']
    first = submission['first']
    last = submission['last']


    act = ACT(test_code, first, last, submission_directory="")
    print(submission['e'].keys())
    print(type(submission['e'].keys()))
    print(type( list(submission['e'].keys())[0] ))
    
    # load the submission 
    sub = {}
    sub['e'] = act.encode_questions(submission['e'])
    sub['m'] = act.encode_questions(submission['m'])
    sub['r'] = act.encode_questions(submission['r'])
    sub['s'] = act.encode_questions(submission['s'])
    
    act.submission = sub

    # load answer key
    path_ak = os.path.abspath(f"./static/grader/answer_keys/ak_ACT_{act.test_code}.json")
    act.answer_key = act.encode_answer_key(path_ak)
    
    # load scoring table
    path_st = os.path.abspath(f"./static/grader/scoring_tables/st_ACT_{act.test_code}.pkl")
    with open( path_st, 'rb') as fil:
        act.scoring_table = pickle.load(fil)

    # grade the submission
    act.graded_submission = act.grade_submission()

    # create score report
    template_vars = act.create_template_variables(act.graded_submission)
    
    #score report string
    path_sr = os.path.abspath("./static/grader/score_report_templates")
    env = Environment(loader=FileSystemLoader(path_sr))
    template = env.get_template(f"template_ACT_{test_code}.html")
    score_report_string = template.render(template_vars)

    # score_report_pdf = HTML(string=score_report_string).render()

    return score_report_string
