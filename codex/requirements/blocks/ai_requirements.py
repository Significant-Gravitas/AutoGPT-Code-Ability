import logging

from codex.common.ai_block import (
    AIBlock,
    Identifiers,
    ValidatedResponse,
    ValidationError,
)
from codex.requirements.build_requirements_refinement_object import convert_requirements
from codex.requirements.model import (
    RequirementsGenResponse,
    RequirementsRefined,
    RequirementsResponse,
)

logger = logging.getLogger(__name__)


class BaseRequirementsBlock(AIBlock):
    """
    This is a block that handles, calling the LLM, validating the response,
    storing llm calls, and returning the response to the user

    """

    # The name of the prompt template folder in codex/prompts/{model}
    prompt_template_name = "requirements/requirements/base_requirements"
    # Model to use for the LLM
    model = "gpt-4-0125-preview"
    # Should we force the LLM to reply in JSON
    is_json_response = True
    # If we are using is_json_response, what is the response model
    pydantic_object = RequirementsResponse

    def validate(
        self, invoke_params: dict, response: ValidatedResponse
    ) -> ValidatedResponse:
        """
        The validation logic for the response. In this case its really simple as we
        are just validating the response is a Clarification model. However, in the other
        blocks this is much more complex. If validation failes it triggers a retry.
        """
        try:
            model: RequirementsResponse = RequirementsResponse.model_validate_json(
                response.response
            )

            requirements_q_and_a = model.answer

            # Requirements conversion
            refined_requirements: RequirementsRefined = convert_requirements(
                requirements_q_and_a
            )
            response.response = refined_requirements
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


class FuncNonFuncRequirementsBlock(AIBlock):
    """
    This is a block that handles, calling the LLM, validating the response,
    storing llm calls, and returning the response to the user

    """

    # The name of the prompt template folder in codex/prompts/{model}
    prompt_template_name = "requirements/requirements/func_nonfunc"
    # Model to use for the LLM
    model = "gpt-4-0125-preview"
    # Should we force the LLM to reply in JSON
    is_json_response = True
    # If we are using is_json_response, what is the response model
    pydantic_object = RequirementsGenResponse

    def validate(
        self, invoke_params: dict, response: ValidatedResponse
    ) -> ValidatedResponse:
        """
        The validation logic for the response. In this case its really simple as we
        are just validating the response is a Clarification model. However, in the other
        blocks this is much more complex. If validation failes it triggers a retry.
        """
        try:
            model: RequirementsGenResponse = (
                RequirementsGenResponse.model_validate_json(response.response)
            )

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

    product_description: str = """"""

    joint_q_and_a: str = """
'- "Do we need a front end for this: "The Tutor App is an application designed to help tutors manage their tutoring business and clients manage their tutoring sessions. The key users are both tutors and clients. Tutors need features to set availability, manage clients, schedule sessions, send invoices and track payments. Clients need to find tutors, book and manage appointments, communicate with tutors, and pay invoices. Core features like user accounts, authentication, notifications span both groups. But the functionality aims to let tutors run their services smoothly while giving clients control over their tutoring."": "Yes" : Reasoning: "Considering the requirements specified for the Tutor App, a front end is essential. The app aims to provide an accessible interface for two distinct user types (tutors and clients), each with specific needs and interactions with the application. Tutors need to manage various aspects of their tutoring business, including setting availability, managing clients, and handling finances. Clients, on the other hand, need to easily find tutors, book appointments, and communicate. These interactions require a user-friendly, interactive front end that makes these tasks efficient and intuitive. Moreover, features like authentication and notifications imply direct, real-time engagement with the app, reinforcing the need for a well-designed front end. Without it, achieving the application\'s goals of streamlining the business and learning experience would be impractical, if not impossible."\n- "Who is the expected user of this: "The Tutor App is an application designed to help tutors manage their tutoring business and clients manage their tutoring sessions. The key users are both tutors and clients. Tutors need features to set availability, manage clients, schedule sessions, send invoices and track payments. Clients need to find tutors, book and manage appointments, communicate with tutors, and pay invoices. Core features like user accounts, authentication, notifications span both groups. But the functionality aims to let tutors run their services smoothly while giving clients control over their tutoring."": "Tutors and clients" : Reasoning: "The Tutor App serves two main user personas: tutors and clients. For tutors, the app functions as a comprehensive business management tool, enabling features like setting availability, managing client relations, scheduling, and handling finances. It’s designed to simplify the operational aspects of tutoring, allowing tutors to focus on delivering quality education. For clients, the app acts as a bridge to access tutoring services. They can effortlessly search for tutors, book and manage sessions, and handle payments. This dual approach caters to the full lifecycle of tutoring services, from discovery and learning to payment. The inclusion of core features like user accounts, authentication, and notifications for both groups emphasizes the app’s goal to foster seamless interaction between tutors and clients, highlighting its commitment to creating a beneficial environment for teaching and learning."\n- "What is the skill level of the expected user of this: "The Tutor App is an application designed to help tutors manage their tutoring business and clients manage their tutoring sessions. The key users are both tutors and clients. Tutors need features to set availability, manage clients, schedule sessions, send invoices and track payments. Clients need to find tutors, book and manage appointments, communicate with tutors, and pay invoices. Core features like user accounts, authentication, notifications span both groups. But the functionality aims to let tutors run their services smoothly while giving clients control over their tutoring."": "Varied" : Reasoning: "Considering the description of the Tutor App, it\'s clear that the expected user base consists of two main personas: tutors and clients. Each of these personas has different roles and objectives within the app, which in turn implies different levels of technology proficiency. Tutors are expected to manage more complex tasks related to running a business such as setting their availability, managing client information, scheduling sessions, and managing finances. On the other hand, clients are primarily looking to find tutors, book and manage appointments, and make payments. Given these tasks, it’s reasonable to assume a variance in technical skill levels among the users. Tutors might possess a moderate to high level of technological proficiency, given their need to manage multiple aspects of their tutoring business through the app. Clients, however, may range from low to high technological proficiency, as their primary interaction with the app involves searching, booking, and communicating. The app should therefore be designed to be intuitive and accessible, catering to the widest possible range of user skill levels to ensure both tutors and clients can navigate and utilize its features effectively."\n- "What types of notifications should the system support for both tutors and clients, and through what channels (SMS, email, in-app)?": "Support email and in-app notifications for all users, with an optional SMS feature based on budget and user preferences." : Reasoning: "Notifications are vital for keeping users engaged and informed. Understanding the types and channels of notifications can shape the development of notification services and APIs."\n- "How should the app handle time zones for scheduling appointments, considering users might be in different regions?": "Implement functionality to adjust and display time based on the user’s local time zone, using UTC as the standard for backend storage." : Reasoning: "Properly handling time zones is crucial for a scheduling app to avoid confusion and missed appointments."\n- "What level of customization will tutors have over their profile and scheduling settings?": "Tutors can customize their profile with essential business information and manage availability settings to enhance user experience without overcomplicating the UI/UX." : Reasoning: "Enhancing tutor profiles with customization options can improve match rates but may increase complexity."\n- "What specific security measures will be implemented for authentication, especially for traditional sign-ins?": "Secure traditional sign-ins with strong password requirements, hashed password storage, SSL for data in transit, and evaluate the need for 2FA based on user feedback." : Reasoning: "With options for OAuth2 and traditional sign-ins, ensuring security for passwords and user data is imperative."\n- "How should the app facilitate communication between tutors and clients?": "Implement an in-app messaging system for real-time communication, ensuring it is secure, user-friendly, and privacy-compliant." : Reasoning: "Direct communication is a key feature for scheduling and updates. Determining the channels and mechanisms is crucial for defining the scope of development."\n- "Which payment gateways or services will the app integrate with for handling invoices and payments?": "Integrate with reputable payment services like Stripe and PayPal, ensuring the integration is secure and user-friendly." : Reasoning: "Choosing the right payment gateway is essential for simplifying financial transactions and ensuring user trust."\n- "What reporting features are essential for tutors to manage their finances within the app?": "Implement essential reporting features for financial management, including income summaries, invoice tracking, and expense reports, with room for customization." : Reasoning: "Financial management tools are key for tutors to track their business. Identifying crucial reporting features will guide the design of this functionality."\n- "Will there be a rating or feedback system for tutors and clients to assess their experiences?": "A rating and feedback system for both tutors and clients will be implemented, designed to be fair, transparent, and resistant to manipulation." : Reasoning: "A feedback system can enhance trust and quality on the platform, but it requires careful consideration to be balanced and fair."\n- "How will the app accommodate users with disabilities or those requiring assistive technologies?": "The app will be designed with accessibility in mind, complying with standard guidelines and including features that support users with various needs." : Reasoning: "Accessibility is a fundamental aspect of app design, especially for a diverse user base. Understanding these requirements early aids compliance and inclusivity."\n- "What kind of support or documentation will be provided to users to facilitate onboarding and troubleshooting?": "Provide detailed documentation, onboarding tutorials, and an easily navigable FAQ section to ensure users have all the resources they need." : Reasoning: "Effective onboarding and accessible support materials can dramatically improve user satisfaction and reduce support requests."\n'
    """

    features_str: str = """[{"name": "Dual Authentication System", "thoughts": "Balancing security with ease of use is paramount. Offering both OAuth2 for those desiring quick access and a traditional sign-in for others emphasizes this.", "description": "A flexible authentication system allowing users to sign up and log in either via OAuth2 for seamless integration with existing accounts or through a secure, traditional sign-in process.", "considerations": "The need to implement stringent security measures, especially for the traditional sign-in, to protect user data.", "risks": "Potential complexity in maintaining two parallel systems and ensuring both are secure against breaches.", "needed_external_tools": "OAuth2 integration services, Secure password storage and hashing tools", "priority": "CRITICAL"}, {"name": "Comprehensive Scheduling System", "thoughts": "The core functionality that must cater to both setting and managing appointments by tutors and clients, including modifications and cancellations.", "description": "An intuitive scheduling interface that allows for the creation, rescheduling, and cancellation of appointments. This system supports real-time updates and notifications.", "considerations": "User experience should remain a priority, ensuring the system is intuitive for both clients and tutors.", "risks": "Synchronization issues leading to double bookings or missed appointments.", "needed_external_tools": "Calendar API services, Push notification services", "priority": "CRITICAL"}, {"name": "Advanced Financial Management", "thoughts": "Providing a detailed yet easy-to-navigate financial overview, including invoicing and payment tracking, is essential for tutor's business operations.", "description": "A robust financial management module for handling invoices, tracking payments, and following up on unpaid invoices. Features include financial summary reports for various time frames.", "considerations": "Ease of understanding and interaction for users with varying financial literacy.", "risks": "Complexity of financial data handling and ensuring accuracy in reports and summaries.", "needed_external_tools": "Invoice management software integration, Payment gateway services", "priority": "HIGH"}, {"name": "Role-Based Authorization", "thoughts": "Critical for differentiating access levels between tutors and clients to ensure both parties only access relevant data and functionalities.", "description": "An authorization framework that differentiates user roles, granting access permissions according to the user's role as a tutor or client.", "considerations": "Ensuring a seamless yet secure method of identifying and authorizing users based on their roles.", "risks": "Potential security vulnerabilities if role distinctions are not properly enforced.", "needed_external_tools": "Role-based access control (RBAC) systems", "priority": "HIGH"}]"""
    requirements_q_and_a_string: str = """'- "do we need db?": "Yes" : Reasoning: "Considering the need to store a vast amount of data like user profiles, schedules, invoices, and payments securely, a database is essential for organizing and managing this information efficiently."\n- "do we need an api for talking to a front end?": "Yes" : Reasoning: "Given the separation of concerns and the necessity to communicate data between the server and the client-side application seamlessly, an API serves as an essential medium for this interaction."\n- "do we need an api for talking to other services?": "Yes" : Reasoning: "For features like OAuth2 authentication, payment processing, and possibly other third-party services, having an API that allows our app to communicate with these external services is crucial."\n- "do we need an api for other services talking to us?": "Yes" : Reasoning: "To facilitate interoperability and integration with other platforms or services that might need to access our application\'s functionalities, we would require an API."\n- "do we need to issue api keys for other services to talk to us?": "Yes" : Reasoning: "To ensure secured access and interaction with our API, issuing API keys to third-party services allows us to control and monitor the API usage."\n- "do we need monitoring?": "Yes" : Reasoning: "Monitoring is essential to ensure the health, performance, and security of the application, helping in timely detection and resolution of potential issues."\n- "do we need internationalization?": "Yes" : Reasoning: "Anticipating a global user base and aiming for a broader reach necessitates the support for multiple languages and regional settings."\n- "do we need analytics?": "Yes" : Reasoning: "To understand user behaviour, measure performance, and guide data-driven decisions for future improvements, integrating analytics is vital."\n- "is there monetization?": "Yes" : Reasoning: "Considering the financial management aspect and the invoicing feature, monetization strategies like subscription models could be implemented to support the application\'s sustainability."\n- "is the monetization via a paywall or ads?": "Paywall" : Reasoning: "Given the professional context of the application for tutors and their clients, a paywall relying on subscriptions provides a more seamless, ad-free experience."\n- "does this require a subscription or a one-time purchase?": "Subscription" : Reasoning: "A subscription model aligns with the ongoing nature of tutoring services, offering continuous access and support to the features and updates."\n- "is the whole service monetized or only part?": "Part" : Reasoning: "It\'s reasonable to keep core functionalities behind a paywall while offering certain basic features for free to attract and onboard users before they commit to a subscription."\n- "is monetization implemented through authorization?": "Yes" : Reasoning: "Utilizing authorization to manage access based on subscription status enables a segmented approach to feature availability, aligning with the monetization strategy."\n- "do we need authentication?": "Yes" : Reasoning: "Authentication is fundamental to identifying users and ensuring data security, especially when managing personal and financial information."\n- "do we need authorization?": "Yes" : Reasoning: "Authorization is crucial for differentiating between user roles and controlling access to functionalities specific to tutors, clients, and possibly admin users."\n- "what authorization roles do we need?": "["Tutor", "Client", "Admin"]" : Reasoning: "Given the nature of the application, separating users into distinct roles ensures appropriate access and functionality tailored to their needs."\n'"""

    base_requirements_block = BaseRequirementsBlock()
    func_nonfunc_requirements_block = FuncNonFuncRequirementsBlock()

    async def run_ai() -> dict[str, RequirementsRefined | RequirementsGenResponse]:
        await db_client.connect()
        base_requirement: RequirementsRefined = await base_requirements_block.invoke(
            ids=ids,
            invoke_params={
                "product_description": product_description,
                "joint_q_and_a": joint_q_and_a,
                "features": features_str,
            },
        )

        func_nonfunc_requirement: RequirementsGenResponse = (
            await func_nonfunc_requirements_block.invoke(
                ids=ids,
                invoke_params={
                    "product_description": product_description,
                    "joint_q_and_a": joint_q_and_a,
                    "features": features_str,
                    "requirements_q_and_a_string": requirements_q_and_a_string,
                },
            )
        )

        await db_client.disconnect()
        return {
            "base_requirement": base_requirement,
            "func_nonfunc_requirement": func_nonfunc_requirement,
        }

    requirements = run(run_ai())

    for key, item in requirements.items():
        if isinstance(item, RequirementsRefined):
            logger.info(f"Requirement Base {key}")
            logger.info("\tRequirementsRefined:")
            logger.info(f"\t\tneed_db: {item.need_db}")
            logger.info(f"\t\t\t{item.need_db_justification}")
            logger.info(f"\t\tneed_frontend_api: {item.need_frontend_api}")
            logger.info(f"\t\t\t{item.need_frontend_api_justification}")
            logger.info(f"\t\tneed_other_services_api: {item.need_other_services_api}")
            logger.info(f"\t\t\t{item.need_other_services_api_justification}")
            logger.info(f"\t\tneed_external_api: {item.need_external_api}")
            logger.info(f"\t\t\t{item.need_external_api_justification}")
            logger.info(f"\t\tneed_api_keys: {item.need_api_keys}")
            logger.info(f"\t\t\t{item.need_api_keys_justification}")
            logger.info(f"\t\tneed_monitoring: {item.need_monitoring}")
            logger.info(f"\t\t\t{item.need_monitoring_justification}")
            logger.info(
                f"\t\tneed_internationalization: {item.need_internationalization}"
            )
            logger.info(f"\t\t\t{item.need_internationalization_justification}")
            logger.info(f"\t\tneed_analytics: {item.need_analytics}")
            logger.info(f"\t\t\t{item.need_analytics_justification}")
            logger.info(f"\t\tneed_monetization: {item.need_monetization}")
            logger.info(f"\t\t\t{item.need_monetization_justification}")
            logger.info(f"\t\tmonetization_model: {item.monetization_model}")
            logger.info(f"\t\t\t{item.monetization_model_justification}")

            logger.info(f"\t\tmonetization_type: {item.monetization_type}")
            logger.info(f"\t\t\t{item.monetization_type_justification}")

            logger.info(f"\t\tmonetization_scope: {item.monetization_scope}")
            logger.info(f"\t\t\t{item.monetization_scope_justification}")

            logger.info(
                f"\t\tmonetization_authorization: {item.monetization_authorization}"
            )
            logger.info(f"\t\t\t{item.monetization_authorization_justification}")

            logger.info(f"\t\tneed_authentication: {item.need_authentication}")
            logger.info(f"\t\t\t{item.need_authentication_justification}")

            logger.info(f"\t\tneed_authorization: {item.need_authorization}")
            logger.info(f"\t\t\t{item.need_authorization_justification}")

            logger.info(f"\t\tauthorization_roles: {item.authorization_roles}")
            logger.info(f"\t\t\t{item.authorization_roles_justification}")
        elif isinstance(item, RequirementsGenResponse):
            logger.info(f"Requirement {key}")
            logger.info("\tRequirementsGenResponse:")
            for req in item.answer.functional:
                requirement = req
                logger.info(f"\t\tfunctional_requirement: {requirement.name}")
                logger.info(f"\t\t\t{requirement.thoughts}")
                logger.info(f"\t\t\t{requirement.description}")
            for req in item.answer.nonfunctional:
                requirement = req
                logger.info(f"\t\tnon_functional_requirement: {requirement.name}")
                logger.info(f"\t\t\t{requirement.thoughts}")
                logger.info(f"\t\t\t{requirement.description}")
        else:
            logger.info("????")

    # # If you want to test the block in an interactive environment
    # import IPython

    # IPython.embed()
