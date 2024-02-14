from codex.prompts.claude.requirements.NestJSDocs import (
    NEST_JS_CRUD_GEN,
    NEST_JS_FIRST_STEPS,
    NEST_JS_MODULES,
    NEST_JS_SQL,
)

# This is a two part prompt!!!
REQUIREMENTS_INTO_MODULES = """
Human: Here is some background that is useful:

<context_first_steps>
{NEST_JS_FIRST_STEPS}
</context_first_steps>
<context_modules>
{NEST_JS_MODULES}
</context_modules>
<context_db>
{NEST_JS_SQL}
</context_db>
<context_crud_gen>
{NEST_JS_CRUD_GEN}
</context_crud_gen>

Assistant: Thank you for that.

Human: Here's a bit of context on the project that will help us both be on the same page:
"{product_description}"

Assistant: Great, thanks for the info!

Human: You already have considerations such as the following:

{joint_q_and_a}

Assistant: Okay, ask away.

Human: Also Heres a few of the general baseline requirements we've already discussed and MUST be included:

{requirements_q_and_a_string}

Assistant: I've taken note of all of these.


Human: You are an expert software architect. You aim to convert the following requirements into nestjs modules for a typescript application. Each module with be created so that services and repositories can exist within them. You should carefully think about it step by step, and share those answers in a block set off by <think>thoughts here</think>. For each reply, you should set the answer off by <answer>reply here</answer>.

List the modules required to build this app. Reply in the following format:

<think_general>
Thoughts on this general topic
</think_general>
<think_anti>
Thoughts on things that shouldn't be modules
</think_anti>
<answer> <module> <name>
name of the module </name> <description>
a description of the module </description></module>
... repeat for other modules </answer>

Here are the requirements:

{requirements}

Assistant: <think_general>

"""

# becomes part of modules

REFINING_MODULES = """

Are there any modules that were missed or seem like they would be needed for a comprehensive backend? Each module with be created so that services and repositories can exist within them. You should carefully think about it step by step, and share those answers in a block set off by <think>thoughts here</think>. For each reply, you should set the answer off by <answer>reply here</answer>.

List the modules that we missed. If there were no modules we missed, reply with NONE in your answer like this <answer>NONE</answer>.

Otherwise reply in the following format:

<think_general>
Thoughts on this general topic
</think_general>
<think_anti>
Thoughts on things that shouldn't be modules
</think_anti>
<answer> <module> <name> name of the module </name> <description> a description of the module </description> <command> command to generate the module in the following format `nest g module cats` </command> </module> ... repeat for other modules </answer> <concluding_think> thoughts </concluding_think>

Assistant:

"""
# becomes modules

REQUIREMENT_INTO_NPM_PACKAGES = """
"""
