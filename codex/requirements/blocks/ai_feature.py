import logging

from codex.common.ai_block import (
    AIBlock,
    Identifiers,
    ValidatedResponse,
    ValidationError,
)
from codex.common.logging_config import setup_logging
from codex.requirements.model import FeaturesSuperObject

logger = logging.getLogger(__name__)


class FeatureGenerationBlock(AIBlock):
    """
    This is a block that handles, calling the LLM, validating the response,
    storing llm calls, and returning the response to the user

    """

    # The name of the prompt template folder in codex/prompts/{model}
    prompt_template_name = "requirements/features"
    # Model to use for the LLM
    model = "gpt-4-0125-preview"
    # Should we force the LLM to reply in JSON
    is_json_response = True
    # If we are using is_json_response, what is the response model
    pydantic_object = FeaturesSuperObject

    def validate(
        self, invoke_params: dict, response: ValidatedResponse
    ) -> ValidatedResponse:
        """
        The validation logic for the response. In this case its really simple as we
        are just validating the response is a Clarification model. However, in the other
        blocks this is much more complex. If validation failes it triggers a retry.
        """
        try:
            model = FeaturesSuperObject.model_validate_json(response.response)
            response.response = model
        except Exception as e:
            raise ValidationError(f"Error validating response: {e}")

        return response

    async def create_item(
        self, ids: Identifiers, validated_response: ValidatedResponse
    ):
        """
        This is where we would store the response in the database

        Atm I don't have a database model to store QnA responses, but we can add one
        """
        pass


if __name__ == "__main__":
    """
    This is a simple test to run the block
    """
    from asyncio import run

    from openai import AsyncOpenAI
    from prisma import Prisma

    from codex.common.test_const import identifier_1

    ids = identifier_1
    db_client = Prisma(auto_register=True)
    oai = AsyncOpenAI()

    task: str = "'The Tutor App is an app designed for tutors to manage their clients, schedules, and invoices. \n\nIt must support both the client and tutor scheduling, rescheduling and canceling appointments, and sending invoices after the appointment has passed.\n\nClients can sign up with OAuth2 or with traditional sign-in authentication. If they sign up with traditional authentication, it must be safe and secure. There will need to be password reset and login capabilities. \n\nThere will need to be authorization for identifying clients vs the tutor.\n\nAdditionally, it will have proper management of financials, including invoice management and payment tracking. This includes things like paid/failed invoice notifications, unpaid invoice follow-up, summarizing d/w/m/y income, and generating reports.'"
    project_description: str = "The Tutor App is an application designed to help tutors manage their tutoring business and clients manage their tutoring sessions. The key users are both tutors and clients. Tutors need features to set availability, manage clients, schedule sessions, send invoices and track payments. Clients need to find tutors, book and manage appointments, communicate with tutors, and pay invoices. Core features like user accounts, authentication, notifications span both groups. But the functionality aims to let tutors run their services smoothly while giving clients control over their tutoring.'"
    joint_q_and_a: str = """
'- "Do we need a front end for this: "The Tutor App is an application designed to help tutors manage their tutoring business and clients manage their tutoring sessions. The key users are both tutors and clients. Tutors need features to set availability, manage clients, schedule sessions, send invoices and track payments. Clients need to find tutors, book and manage appointments, communicate with tutors, and pay invoices. Core features like user accounts, authentication, notifications span both groups. But the functionality aims to let tutors run their services smoothly while giving clients control over their tutoring."": "Yes" : Reasoning: "Considering the requirements specified for the Tutor App, a front end is essential. The app aims to provide an accessible interface for two distinct user types (tutors and clients), each with specific needs and interactions with the application. Tutors need to manage various aspects of their tutoring business, including setting availability, managing clients, and handling finances. Clients, on the other hand, need to easily find tutors, book appointments, and communicate. These interactions require a user-friendly, interactive front end that makes these tasks efficient and intuitive. Moreover, features like authentication and notifications imply direct, real-time engagement with the app, reinforcing the need for a well-designed front end. Without it, achieving the application\'s goals of streamlining the business and learning experience would be impractical, if not impossible."\n- "Who is the expected user of this: "The Tutor App is an application designed to help tutors manage their tutoring business and clients manage their tutoring sessions. The key users are both tutors and clients. Tutors need features to set availability, manage clients, schedule sessions, send invoices and track payments. Clients need to find tutors, book and manage appointments, communicate with tutors, and pay invoices. Core features like user accounts, authentication, notifications span both groups. But the functionality aims to let tutors run their services smoothly while giving clients control over their tutoring."": "Tutors and clients" : Reasoning: "The Tutor App serves two main user personas: tutors and clients. For tutors, the app functions as a comprehensive business management tool, enabling features like setting availability, managing client relations, scheduling, and handling finances. It’s designed to simplify the operational aspects of tutoring, allowing tutors to focus on delivering quality education. For clients, the app acts as a bridge to access tutoring services. They can effortlessly search for tutors, book and manage sessions, and handle payments. This dual approach caters to the full lifecycle of tutoring services, from discovery and learning to payment. The inclusion of core features like user accounts, authentication, and notifications for both groups emphasizes the app’s goal to foster seamless interaction between tutors and clients, highlighting its commitment to creating a beneficial environment for teaching and learning."\n- "What is the skill level of the expected user of this: "The Tutor App is an application designed to help tutors manage their tutoring business and clients manage their tutoring sessions. The key users are both tutors and clients. Tutors need features to set availability, manage clients, schedule sessions, send invoices and track payments. Clients need to find tutors, book and manage appointments, communicate with tutors, and pay invoices. Core features like user accounts, authentication, notifications span both groups. But the functionality aims to let tutors run their services smoothly while giving clients control over their tutoring."": "Varied" : Reasoning: "Considering the description of the Tutor App, it\'s clear that the expected user base consists of two main personas: tutors and clients. Each of these personas has different roles and objectives within the app, which in turn implies different levels of technology proficiency. Tutors are expected to manage more complex tasks related to running a business such as setting their availability, managing client information, scheduling sessions, and managing finances. On the other hand, clients are primarily looking to find tutors, book and manage appointments, and make payments. Given these tasks, it’s reasonable to assume a variance in technical skill levels among the users. Tutors might possess a moderate to high level of technological proficiency, given their need to manage multiple aspects of their tutoring business through the app. Clients, however, may range from low to high technological proficiency, as their primary interaction with the app involves searching, booking, and communicating. The app should therefore be designed to be intuitive and accessible, catering to the widest possible range of user skill levels to ensure both tutors and clients can navigate and utilize its features effectively."\n- "What types of notifications should the system support for both tutors and clients, and through what channels (SMS, email, in-app)?": "Support email and in-app notifications for all users, with an optional SMS feature based on budget and user preferences." : Reasoning: "Notifications are vital for keeping users engaged and informed. Understanding the types and channels of notifications can shape the development of notification services and APIs."\n- "How should the app handle time zones for scheduling appointments, considering users might be in different regions?": "Implement functionality to adjust and display time based on the user’s local time zone, using UTC as the standard for backend storage." : Reasoning: "Properly handling time zones is crucial for a scheduling app to avoid confusion and missed appointments."\n- "What level of customization will tutors have over their profile and scheduling settings?": "Tutors can customize their profile with essential business information and manage availability settings to enhance user experience without overcomplicating the UI/UX." : Reasoning: "Enhancing tutor profiles with customization options can improve match rates but may increase complexity."\n- "What specific security measures will be implemented for authentication, especially for traditional sign-ins?": "Secure traditional sign-ins with strong password requirements, hashed password storage, SSL for data in transit, and evaluate the need for 2FA based on user feedback." : Reasoning: "With options for OAuth2 and traditional sign-ins, ensuring security for passwords and user data is imperative."\n- "How should the app facilitate communication between tutors and clients?": "Implement an in-app messaging system for real-time communication, ensuring it is secure, user-friendly, and privacy-compliant." : Reasoning: "Direct communication is a key feature for scheduling and updates. Determining the channels and mechanisms is crucial for defining the scope of development."\n- "Which payment gateways or services will the app integrate with for handling invoices and payments?": "Integrate with reputable payment services like Stripe and PayPal, ensuring the integration is secure and user-friendly." : Reasoning: "Choosing the right payment gateway is essential for simplifying financial transactions and ensuring user trust."\n- "What reporting features are essential for tutors to manage their finances within the app?": "Implement essential reporting features for financial management, including income summaries, invoice tracking, and expense reports, with room for customization." : Reasoning: "Financial management tools are key for tutors to track their business. Identifying crucial reporting features will guide the design of this functionality."\n- "Will there be a rating or feedback system for tutors and clients to assess their experiences?": "A rating and feedback system for both tutors and clients will be implemented, designed to be fair, transparent, and resistant to manipulation." : Reasoning: "A feedback system can enhance trust and quality on the platform, but it requires careful consideration to be balanced and fair."\n- "How will the app accommodate users with disabilities or those requiring assistive technologies?": "The app will be designed with accessibility in mind, complying with standard guidelines and including features that support users with various needs." : Reasoning: "Accessibility is a fundamental aspect of app design, especially for a diverse user base. Understanding these requirements early aids compliance and inclusivity."\n- "What kind of support or documentation will be provided to users to facilitate onboarding and troubleshooting?": "Provide detailed documentation, onboarding tutorials, and an easily navigable FAQ section to ensure users have all the resources they need." : Reasoning: "Effective onboarding and accessible support materials can dramatically improve user satisfaction and reduce support requests."\n'
    """
    thoughts: str = """
'\n\nHuman: Your task is to "The Tutor App is an app designed for tutors to manage their clients, schedules, and invoices. \n\nIt must support both the client and tutor scheduling, rescheduling and canceling appointments, and sending invoices after the appointment has passed.\n\nClients can sign up with OAuth2 or with traditional sign-in authentication. If they sign up with traditional authentication, it must be safe and secure. There will need to be password reset and login capabilities. \n\nThere will need to be authorization for identifying clients vs the tutor.\n\nAdditionally, it will have proper management of financials, including invoice management and payment tracking. This includes things like paid/failed invoice notifications, unpaid invoice follow-up, summarizing d/w/m/y income, and generating reports."\n\nAnswer as an expert product owner.\n\nyour memory is based on a google like search. When you want more information send search:<query> and I\'ll send you back the reply.\n\nyou can ask the user questions by sending ask:<query> and I\'ll send you back the reply. Make sure to ask broad questions that help guide your understanding\n\nWhen you feel you have finished getting the info you need or are confident it\'s not there, summarize the memory you\'ve built and send finished:<summary>. make sure you don\'t reply anything before the "finished:<summary>" or it will confuse the human\n\nOnly reply with one message at a time so that the user isn\'t overwhelmed.\n\nOnly reply with the specified tags.\n\nAssistant: \nask: Who is the primary user for this application?\n\nHuman:Unfortunately I do not have enough context to definitively state who the primary user for a particular application would be. Applications can have different target users depending on their purpose and functionality. Some things that could help determine the primary user could be:\n\n- What is the main purpose or function of the application? Different types of apps may target different audiences (e.g. gaming apps target gamers, productivity apps target professionals, etc.)\n\n- Who is the application designed for? The UI/UX design and features may give clues as to the intended user base.\n\n- Who is the developer or company that created the application? Understanding their typical customer base could indicate who they had in mind as users.\n\n- What permissions and data does the app require or have access to? This could imply the expected user type based on what functionality is offered.\n\n- Are there any marketing materials or app descriptions that describe the target user base? Oftentimes there is explicit information on ideal users.\n\nWithout more context about which specific application you have in mind, I unfortunately cannot definitively name the expected primary user. Let me know if you can provide any additional details about the app and I\'m happy to try to make a more educated guess!\n\nAssistant:search: The Tutor App tutor schedule management clients invoices appointments OAuth2 sign-in authentication password reset login authorization identifying clients vs tutor financials invoice management payment tracking paid/failed invoice notifications unpaid invoice follow-up summarizing income reports\n\nHuman:Unfortunately I do not have enough context to provide specific feedback on features for a tutor scheduling and management app. However, some general capabilities that may be useful include:\n\n- User account management with sign-up, login, authentication, password reset, etc. Using a standard authorization protocol like OAuth 2.0 can simplify this.\n\n- Separate portals/views for tutors vs clients with appropriate functionality for each. Tutors need schedule/appointment management, client management, invoice/payment tracking, etc. Clients need to book, pay and manage appointments.\n\n- Client profiles/accounts to store info like name, contact details, billing info. This keeps client data organized and allows things like recurring appointments or billing.\n\n- Tutor calendar/availability management. Tutors need to indicate their availabilities and block off times they cannot take appointments.\n\n- Appointment management system - tutors and clients can add, edit, cancel, reschedule appointments. Notifications for upcoming sessions.\n\n- Invoicing system - automated invoice generation and tracking tied to appointments. Status indicators for paid/unpaid/failed payments. Reminders for unpaid invoices.\n\n- Payment processing and tracking against invoices. Recording payments as they come in and reconciling with invoices.\n\n- Financial/earnings reporting for tutors - reports on net earnings, paid invoices over time, appointment volume, etc. to analyze their tutoring business.\n\n- Notifications to both clients and tutors via email or SMS for unpaid invoices, appointment reminders/changes, etc. to improve engagement.\n\nLet me know if any specific features come to mind and I\'m happy to provide additional suggestions on how those could be implemented.\n\nAssistant:'
    """
    feature_block = FeatureGenerationBlock(
        oai_client=oai,
    )

    async def run_ai() -> dict[str, FeaturesSuperObject]:
        await db_client.connect()
        feature: FeaturesSuperObject = await feature_block.invoke(
            ids=ids,
            invoke_params={
                "project_description": project_description,
                "project_description_thoughts": thoughts,
                "joint_q_and_a": joint_q_and_a,
            },
        )

        await db_client.disconnect()
        return {
            "features": feature,
        }

    features = run(run_ai())

    for key, item in features.items():
        if isinstance(item, FeaturesSuperObject):
            logger.info(f"FeatureSuperObject {key}")
            logger.info(f"\tThoughts: {item.think}")
            logger.info(f"\tName: {item.project_name}")
            logger.info(f"\tDescription: {item.description}")
            logger.info(f"\tGeneral Feature Thoughts: {item.general_feature_thoughts}")
            for feature in item.features:
                f = feature.feature
                logger.info(f"\tFeature Name: {f.name}")
                logger.info(f"\t\tThoughts: {f.thoughts}")
                logger.info(f"\t\tDescription: {f.description}")
                logger.info(f"\t\tConsiderations: {f.considerations}")
                logger.info(f"\t\tRisks: {f.risks}")
                logger.info(f"\t\tNeeded external tools: {f.needed_external_tools}")
                logger.info(f"\t\tPriority: {f.priority}")

        else:
            logger.info(f"????")
            breakpoint()

    # # If you want to test the block in an interactive environment
    # import IPython

    # IPython.embed()
    breakpoint()
