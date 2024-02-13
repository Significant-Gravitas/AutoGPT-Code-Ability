TASK_INTO_MORE_INFO = """

Human: Your task is to "{task}"

Answer as an expert product owner.

your memory is based on a google like search. When you want more information send search:<query> and I'll send you back the reply.

you can ask the user questions by sending ask:<query> and I'll send you back the reply. Make sure to ask broad questions that help guide your understanding

When you feel you have finished getting the info you need or are confident it's not there, summarize the memory you've built and send finished:<summary>. make sure you don't reply anything before the "finished:<summary>" or it will confuse the human

Only reply with one message at a time so that the user isn't overwhelmed.

Only reply with the specified tags.

Assistant: 
"""

FRONTEND_QUESTION = "Do we need a front end?"

MORE_INFO_BASE_CLARIFICATIONS_FRONTEND = """
Human: You are an expert product manager who works to help us ensure our projects are reasonable. You should carefully think about it step by step, and share those answers in a block set off by <think>thoughts here</think>. You should answer with only a yes or no. Set the answer off by <answer>Yes/No</answer>

Do we need a front end for this: 
"{project_description}"

Assistant: <think>
I would break this down into a few key questions:

1.
"""

USER_PERSONA_QUESTION = "Who is the expected user?"

# Q&As are all other clarifications gotten so far; basically clarifiying_questions_as_string running
MORE_INFO_BASE_CLARIFICATIONS_USER_PERSONA = """
Human: Here is a few Q&As before I ask:
You already have considerations such as the following:
{clarifiying_questions_so_far}

Assistant: Okay, ask away.

Human: You are an expert product manager who works to help us ensure our projects are reasonable. You should carefully think about it step by step, and share those answers in a block set off by <think>thoughts here</think>. You should answer with only an expected user persona or personas. Set the answer off by <answer>reply here</answer>. 

Who is the expected user of this: "{project_description}"

Assistant: <think>
"""

USER_SKILL_LEVEL_QUESTION = "What is the skill level of the expected user?"

MORE_INFO_BASE_CLARIFICATIONS_USER_SKILL = """
Human: Here is a few Q&As before I ask:
You already have considerations such as the following:
{clarifiying_questions_so_far}

Assistant: Okay, ask away.

Human: You are an expert product manager who works to help us ensure our projects are reasonable. You should carefully think about it step by step, and share those answers in a block set off by  <think>thoughts here</think>. You should answer with only an expected skill level of the user persona or personas. Set the answer off by <answer>reply here</answer>. 

What is the skill level of the expected user of this: 
"{project_description}"

Assistant: <think>
"""

MORE_INFO_EXPANDED_CLARIFICATIONS = """
Human: Here is a few Q&As before I ask:
You already have considerations such as the following:
{clarifiying_questions_as_string}

Assistant: Okay, ask away.

Human: 
Answer as an expert product owner.
For the following project description, ask a series of at least 10 questions that will clarify what is being requested.
Think carefully, ensuring questions do not overlap, and all ambiguities are covered. Then, generate your best guess at the answer, basing it on your knowledge and best practices. You should carefully think about it step by step and share those thoughts in a block set off by  <think>thoughts here</think>. For each reply, you should set the answer off by <answer>reply here</answer>. Pick questions that directly affect the direction of the product rather than marketing, budgets, or timeframes, stakeholders etc as those are already answered in the Q&A.

An example of that would be 
<think>your thoughts on the overall process, thinking step by step</think>
<answer>
<wrapper>
<question>concern and clarification</question>
<thoughts>your thoughts on the concern and clarification</thoughts>
<project_manager>project managers reasonable best guess answer</project_manager>
<software_architect>software architects reasonable best guess answer</software_architect>
<subject_matter_expert>subject matter expert's reasonable best guess answer</subject_matter_expert>
<team_answer>team's cohesive and combined reasonable best guess answer</team_answer>
<was_conclusive>was the team's answer conclusive? Yes/No Only</was_conclusive>
</wrapper>
<wrapper>
<question>concern and clarification</question>
<thoughts>your thoughts on the concern and clarification</thoughts>
<project_manager>project managers reasonable best guess answer</project_manager>
<software_architect>software architects reasonable best guess answer</software_architect>
<subject_matter_expert>subject matter expert's reasonable best guess answer</subject_matter_expert>
<team_answer>team's cohesive and combined reasonable best guess answer</team_answer>
<was_conclusive>was the team's answer conclusive? Yes/No Only</was_conclusive>
</wrapper>
<wrapper>
<question>concern and clarification</question>
<thoughts>your thoughts on the concern and clarification</thoughts>
<project_manager>project managers reasonable best guess answer</project_manager>
<software_architect>software architects reasonable best guess answer</software_architect>
<subject_matter_expert>subject matter expert's reasonable best guess answer</subject_matter_expert>
<team_answer>team's cohesive and combined reasonable best guess answer</team_answer>
<was_conclusive>was the team's answer conclusive? Yes/No Only</was_conclusive>
</wrapper>

repeat for each clarification
</answer>
<closing_thoughts>
any closing thoughts go here
</closing_thoughts>

# Task
"{task}"

## Project Details
"{project_description}"

Assistant: <think>
The key is understanding the core goals, target users, and key features. I will ask questions to clarify the scope, user needs, technical requirements, design, priorities, budget, and timeline. I will think through each question carefully, provide my thoughts, and give my best attempt at an answer. I will avoid questions that have already been answered by the Q&A already provided or that require input from the stakeholder. I'll approach this from the perspective of a PM, architect, SME, and overall team to cover all angles. I'll identify if the answers are conclusive or if more clarity is needed. The goal is to fully understand the problem and solution before outlining the details that the team would need to deliver the right product.
</think>
"""
# this becomes q_and_a
