from django.core.exceptions import ObjectDoesNotExist
from mitesting.render_questions import render_question

def get_question_list(assessment, seed, rng=None, thread_content=None,
                      questions_only=False):
    """
    Return list of questions for assessment, one for each question_set,
    along with additional information about each question.

    After initializing random number generator with seed
    randomly pick a question and determine question group.  
    If assessment is not set to fixed order,
    randomly order the chosen assessments, keeping questions in the same
    group together.

    Each question is randomly assigned a seed, which is to be used
    generate the question and/or solution, ensuring that question
    and solution will match.


    Return a list of dictionaries, one for each question. 
    Each dictionary contains the following:
    - question_set: the question_set from which the question was drawn
    - question: the question chosen
    - seed: the seed to use to render the question
    - relative_weight: the relative weight of the question
    - points: if have thread_content, then convert weight to points
    - group: the group of the question, if specified
    - previous_same_group: True if group is same as that of previous question
    """

    if not rng:
        import random
        rng=random.Random()

    rng.seed(seed)

    question_list = []
    
    total_weight = 0

    from mitesting.utils import get_new_seed

    for question_set in assessment.question_sets():
        questions_in_set = assessment.questionassigned_set.filter(
            question_set=question_set)

        the_question=rng.choice(questions_in_set).question

        # generate a seed for the question
        # so that can have link to this version of question and solution
        question_seed=get_new_seed(rng)

        if questions_only:
            question_list.append({'question_set': question_set,
                                  'question': the_question,
                                  'seed': question_seed,
                              })
            continue

        # find question set detail, if it exists
        try:
            question_detail=assessment.questionsetdetail_set.get(
                question_set=question_set)
        except ObjectDoesNotExist:
            question_detail = None
        
        if question_detail:
            weight=question_detail.weight
            group=question_detail.group
        else:
            weight=1
            group=""

        total_weight += weight

        question_list.append({'question_set': question_set,
                              'question': the_question,
                              'seed': question_seed,
                              'relative_weight': weight,
                              'group': group,
                              'previous_same_group': False
        })


    if questions_only:
        return question_list

    # make weight be relative weight
    # if have thread_content, then multiply by assessment points to
    # get question_points
    if total_weight:
        for q_dict in question_list:
            q_dict['relative_weight'] /= total_weight
            if thread_content and thread_content.points is not None:
                q_dict['points'] = q_dict["relative_weight"]\
                                   *thread_content.points

    if assessment.fixed_order:
        for i in range(1, len(question_list)):
            the_group = question_list[i]["group"]
            # if group is not blank and the same as previous group
            # mark as belonging to same group as previous question
            if the_group and question_list[i-1]["group"] == the_group:
                    question_list[i]["previous_same_group"] = True
        return question_list

    # if not fixed order randomly shuffle questions
    # keep questions with same group together
    # i.e., first random shuffle groups, 
    # then randomly shuffle questions within each group
    # set 'previous_same_group' if previous question is from the same group

    # create list of the groups, 
    # adding unique groups to questions with no group
    question_set_groups = {}
    for (ind,q) in enumerate(question_list):
        question_group = q['group']
        if question_group in question_set_groups:
            question_set_groups[question_group].append(ind)
        elif question_group:
            question_set_groups[question_group] = [ind]
        else:
            unique_no_group_name = '_no_group_%s' % ind
            question_set_groups[unique_no_group_name] = [ind]
            q['group']=unique_no_group_name

    # create list of randomly shuffled groups
    groups = list(question_set_groups.keys())
    rng.shuffle(groups)

    # for each group, shuffle questions,
    # creating cummulative list of the resulting question index order
    question_order =[]
    for group in groups:
        group_indices=question_set_groups[group]
        rng.shuffle(group_indices)
        question_order += group_indices

    # shuffle questions based on that order
    # also check if previous question is from same group
    question_list_shuffled =[]
    previous_group = 0
    for i in question_order:
        q=question_list[i]
        this_group = q['group']
        if this_group == previous_group:
            previous_same_group = True
        else:
            previous_same_group = False
        q['previous_same_group'] = previous_same_group
        previous_group = this_group
        question_list_shuffled.append(q)

    return question_list_shuffled


def get_question_list_from_attempt(assessment, content_attempt, question_attempts=[]):
    """
    Attempt to population question list from attempt data.

    Inputs:
    assessment
    content_attempt: should be from assessment
    question_attempts: a list of question attempts that should be from content attempt.

    If content attempt is not from assessment, return empty list.

    If question attempts are not a complete list of question attempts, 
    one per question set of assessment, then ignore questions attempt input.

    If question attempt input is not provided, use the latest question attempt from 
    content attempt for each question set.  
    If a complete set of question attempts are not available, return empty list.

    """

    # verify that content attempt is from assessment
    if content_attempt.record.content.content_object != assessment:
        return []

    question_sets=assessment.question_sets()
    question_list = []
    total_weight=0

    if question_attempts:
        ca_qs_list=[]
        total_weight=0

        for qa in question_attempts:
            ca_question_set = qa.content_attempt_question_set
            if cq_question_set.content_attempt != content_attempt:
                ca_qs_list=[]
                break

            # find question set detail, if it exists
            try:
                question_detail=assessment.questionsetdetail_set.get(
                    question_set=question_set)
            except ObjectDoesNotExist:
                question_detail = None

            if question_detail:
                weight=question_detail.weight
                group=question_detail.group
            else:
                weight=1
                group=""

            total_weight += weight

            # find latest valid response, if it exits
            try:
                latest_response=qa.responses.filter(valid=True).latest()
            except ObjectDoesNotExist:
                latest_response=None

            question_list.append(
                {'question_set': ca_question_set.question_set,
                 'question': qa.question,
                 'seed': qa.seed,
                 'question_attempt': qa,
                 'response': latest_response,
                 'relative_weight': weight,
                 'group': group,
                 'previous_same_group': False
             })

            ca_qs_list.append(ca_question_set.question_set)

    
        # if question sets don't match, then
        # ignore question attempts and treat as not having question_attempts
        if sorted(ca_qs_list) != sorted(question_sets):
            question_list=[]

    # if didn't find question attempts
    # try to use latest question attempts from content attempt
    if not question_list:

        ca_qs_list=[]
        total_weight=0
        for ca_question_set in content_attempt.question_sets.all()\
                        .prefetch_related('question_attempts'):
            try:
                qa = ca_question_set.question_attempts.latest()
            except ObjectDoesNotExist:
                ca_qs_list=[]
                break

            question_set = ca_question_set.question_set

            # find question set detail, if it exists
            try:
                question_detail=assessment.questionsetdetail_set.get(
                    question_set=question_set)
            except ObjectDoesNotExist:
                question_detail = None

            if question_detail:
                weight=question_detail.weight
                group=question_detail.group
            else:
                weight=1
                group=""

            total_weight += weight

            # find latest valid response, if it exits
            try:
                latest_response=qa.responses.filter(valid=True).latest()
            except ObjectDoesNotExist:
                latest_response=None

            question_list.append(
                {'question_set': ca_question_set.question_set,
                 'ca_question_set': ca_question_set,
                 'question': qa.question,
                 'seed': qa.seed,
                 'question_attempt': qa,
                 'response': latest_response,
                 'relative_weight': weight,
                 'group': group,
                 'previous_same_group': False
             })

            ca_qs_list.append(ca_question_set.question_set)

        # if question sets from latest question attempts don't match,
        # then return empty question list
        if sorted(ca_qs_list) != sorted(question_sets):
            return []


    # Found a valid question.  
    # Complete the data

    # make weight be relative weight
    # multiply by assessment points to
    # get question_points
    assessment_points = content_attempt.record.content.points
    if total_weight:
        for q_dict in question_list:
            q_dict['relative_weight'] /= total_weight
            if assessment_points is not None:
                q_dict['points'] = q_dict["relative_weight"]*assessment_points


    # treat just like fixed order
    for i in range(1, len(question_list)):
        the_group = question_list[i]["group"]
        # if group is not blank and the same as previous group
        # mark as belonging to same group as previous question
        if the_group and \
           question_list[i-1]["group"] == the_group:
            question_list[i]["previous_same_group"] = True

    return question_list



def render_question_list(assessment, question_list, assessment_seed, rng=None,
                         user=None, solution=False,
                         auxiliary_data=None,
                         show_post_user_errors=False,
                         show_correctness=True,
                         no_links=False,
                         allow_solution_buttons=True
                     ):

    """
    Generate list of rendered questions or solutions for assessment.

    After initializing random number generator with seed
    (or generating a new seed if seed was None),
    from each question set, randomly pick a question and a question seed,
    render the question, determine score on this attempt of assessment,
    and determine question group.  If assessment is not set to fixed order,
    randomly order the chosen assessments, keeping questions in the same
    group together.
    

    Inputs:
    - assessment: the assessment to be rendered
    - rng: instance of random number generator to use
    - seed: random number generator seed to generate assesment and questions
    - user: the logged in user
    - solution: True if rendering solution
    - current_attempt: information about score so far on computer scored
      assessments (need to fix and test)
    - auxiliary_data: dictionary for information that should be accessible 
      between questions or outside questions.  Used, for example, 
      for information about applets and hidden sections embedded in text
    - show_post_user_errors: if true, show errors in expressions that are
      flagged as post user response
    - show_correctness: if True, then should display correctness of response
      upon its submission
    - no_links: if True, then should suppress links in feedback to responses
    - allow_solution_buttons: if True, allow a solution button to be displayed
      on computer graded questions

    Outputs:
    - seed that used to generate assessment (the input seed unless it was None)
    - question_list.  List of dictionaries, one per question, giving
      information about the question.  Each dictionary contains:
      - question_set: the question_set from which the question was drawn
      - question: the question chosen
      - points: the number of points the question set is worth
      - seed: the seed to use to render the question
      - question_data: dictionary containing the information needed to
        display the question with question_body.html template.
        This dictionary is what is returned by render_question, supplemented by
        - points: copy of above points
        - current_credit: the percent credit achieved in current attempt
        - current_score: the score (points) achieved in the current attempt
        - attempt_url: url to current attempt for the question
      - group: the group the question set belongs to
      - previous_same_group: true if the previous question if from the
        same question group as the current question
        (Used as indicator for templates that questions belong together.)
    """


    """
    Question: can we move all this logic to render_question?
    Or do we need simpler version of render_question somewhere?
    
    render_question called:
    inject solution view
    
    render in question model, which is called by
    _render_question in question_tags
    question view

    I hope we can move it all over. 
    Then, here we just set the question identifier and pass in the
    question_dict from question_list.

    then just add question_data to question_dict.
    or have it automatically added...

    """

    if not rng:
        import random
        rng=random.Random()

    for (i, question_dict) in enumerate(question_list):

        # use qa for identifier since coming from assessment
        identifier="qa%s" % i


        question_data = render_question(
            question_dict,
            rng=rng, solution=solution,
            question_identifier=identifier,
            user=user, show_help=not solution,
            assessment=assessment,
            assessment_seed=assessment_seed, 
            record_response=True,
            allow_solution_buttons=allow_solution_buttons,
            auxiliary_data=auxiliary_data,
            show_post_user_errors=show_post_user_errors,
            show_correctness=show_correctness,
            no_links=no_links)
        
        question_dict['question_data']=question_data




    return question_list
