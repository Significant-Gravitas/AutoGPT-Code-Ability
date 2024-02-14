FEATURE_BASELINE_QUESTIONS = """
> Do we Need DB? [Yes, No]
> Do we need an API for talking to a front end? [Yes, No]
> Do we need an API for talking to other services? [Yes, No]
> Do we need an API for other services talking to us? [Yes, No]
> Do we need to issue API keys for other services to talk to us? [Yes, No, N/A]
> Do we need Monitoring? [Yes, No]
> Do we need Internationalization? [Yes, No]
> Do we need analytics? [Yes, No]
> Is there monetization? [Yes, No]
> Is the monetization via a paywall or ads? [Paywall, Ads, N/A]
> Does this require a subscription or a one-time purchase? [Subscription, One-Time Purchase, N/A]
> Is the whole service monetized or only part? [Whole, Part, N/A]
> Is monetization implemented through authorization? [Yes, No, N/A]
> Do we need Authentication?  [Yes, No]
> Do we need authorization? [Yes, No, N/A]
> What authorization roles do we need? For this question, answer an array of One Word Roles such as [UserType1, UserType2, UserType3, N/A].
"""

FEATURE_BASELINE_CHECKS = """
Human: Here's a bit of context on the project that will help us both be on the same page:
"{product_description}"

Assistant: Great, thanks for the info!

Human: Here are a few Q&As before I ask:
You already have considerations such as the following:

{joint_q_and_a}

Assistant: Okay, ask away.

Human: You are an expert product manager who works to help us ensure our MVPs are reasonable.
You should carefully think about it step by step, and share those answers in a block set off by <think>thoughts here</think>.
Each question will be in the following form: >Question? [ValidAnswer1, ValidAnswer2, ...].
You should answer with only one of the valid options next to each question.
Set the answer off by
<answer>
<wrapper>
<question>question</question>
<think>thoughts on this question. Don't answer the question here, just put the raw thoughts</think>
<answer>valid answer</answer>
</wrapper>
... other questions
</answer

{FEATURE_BASELINE_QUESTIONS}

Here are the features:

{features}

Assistant: <think>"""

# becomes requirements_q_and_a

REQUIREMENTS = """
Human: Here's a bit of context on the project that will help us both be on the same page:
"{product_description}"

Assistant: Great, thanks for the info!

Human: You already have considerations such as the following:

{joint_q_and_a}

Assistant: Okay, ask away.

Human: Also Heres a few of the general baseline requirements we've already discussed and MUST be included:

{requirements_q_and_a_string}

Assistant: I've taken note of all of these.

Human: You are an expert senior software architect and CTO. Turn the details provided into functional requirements and non-functional requirements. Start with the general baseline requirements and then add additional ones based on the product description, feature list, and Q&A.

The features are:
{features}

You should carefully think about it step by step, and share those answers in a block set off by <think>thoughts here</think>.
You should answer with only an expected non functional and functional requirements. Set the answer off by
<answer>
<functional>
<requirement>
    <thoughts>thoughts on this requirement</thoughts>
    <name>this requirements name</name>
    <description> this requirements description</description>
</requirement>
... more requirements
</functional>
<nonfunctional>
<requirement>
    <thoughts>thoughts on this requirement</thoughts>
    <name>this requirements name</name>
    <description> this requirements description</description>
</requirement>
... more requirements
</nonfunctional>
</answer>.

Assistant: <think>
Let's start by going through the baseline requirements that were already provided and categorizing them into functional and non-functional requirements."""

# becomes requirements
