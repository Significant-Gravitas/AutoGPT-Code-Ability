# This only includes Clarifications that were conclusive
CLARIFICATIONS_INTO_NAME_AND_DESC = """
Human: Here are a few Q&As before I ask:
You already have considerations such as the following:
{joint_q_and_a}

Assistant: Okay, ask away.

Human: You are an expert product owner. 

Given the basic project description and the clarification, Q&A write a detailed product description. 
The project description should be at least 750 words. Be clear and exhaustive such that it is easy to determine the functional and non-functional requirements of the product.
You should carefully think about it step by step and share those answers in a block set off by  <think>thoughts here</think>.


The project name should be short and catchy.

The format of the response should be:
<think>thoughts</think>
<project_name>short and memorable name that conveys the project's purpose.</project_name>
<description>detailed product description</description>
<general_feature_thoughts>thoughts about all the features</general_feature_thoughts>
<features>
<feature>
<name>Feature Name</name>
<thoughts>thoughts about the feature</thoughts>
<description>Feature 1 description</description>
<considerations>Feature 1 considerations</considerations>
<risks>Feature 1 risks</risks>
<needed_external_tools>Feature 1 needed external tools clearly listed</needed_external_tools>
<priority>CRITICAL/HIGH/MEDIUM/LOW/OPTIONAL</priority>
</feature>
... repeat for all features
</features>

# Project
"{project_description}"

# Project Description Thoughts
"{project_description_thoughts}

Assistant: <think>
"""
# becomes product_name, product_description, and features
