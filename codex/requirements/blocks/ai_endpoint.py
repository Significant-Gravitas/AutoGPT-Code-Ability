import logging

from codex.common.ai_block import (
    AIBlock,
    Identifiers,
    ValidatedResponse,
    ValidationError,
)
from codex.common.logging_config import setup_logging
from codex.requirements.model import EndpointSchemaRefinementResponse

logger = logging.getLogger(__name__)


class EndpointSchemaRefinementBlock(AIBlock):
    """
    This is a block that handles, calling the LLM, validating the response,
    storing llm calls, and returning the response to the user

    """

    # The name of the prompt template folder in codex/prompts/{model}
    prompt_template_name = "requirements/endpoint"
    # Model to use for the LLM
    model = "gpt-4-0125-preview"
    # Should we force the LLM to reply in JSON
    is_json_response = True
    # If we are using is_json_response, what is the response model
    pydantic_object = EndpointSchemaRefinementResponse

    def validate(
        self, invoke_params: dict, response: ValidatedResponse
    ) -> ValidatedResponse:
        """
        The validation logic for the response. In this case its really simple as we
        are just validating the response is a Clarification model. However, in the other
        blocks this is much more complex. If validation failes it triggers a retry.
        """
        try:
            model: EndpointSchemaRefinementResponse = (
                EndpointSchemaRefinementResponse.model_validate_json(
                    response.response, strict=False
                )
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

    from prisma import Prisma

    from codex.common.ai_model import OpenAIChatClient
    from codex.common.test_const import identifier_1

    ids = identifier_1

    setup_logging(local=True)

    OpenAIChatClient.configure({})
    db_client = Prisma(auto_register=True)
    logging.info("Running block")

    endpoint1_repr = """Endpoint(name='OAuth2 Login', type='POST', description='Endpoint for handling OAuth2 logins, returning user tokens and session data.', path='/auth/oauth2/login', request_model=None, response_model=None, data_models=None, database_schema=None)"""

    endpoint2_repr = """Endpoint(name='Get User Permissions', type='GET', description='Retrieve the permissions associated with a user’s role.', path='/users/{id}/permissions', request_model=None, response_model=None, data_models=None, database_schema=None)"""

    module1_repr = """Module(name='Authentication', description='Manages user authentication processes, providing secure access via OAuth2 and traditional sign-in methods. Ensures data protection for user credentials and offers password reset capabilities.', requirements=[ModuleRefinementRequirement(name='OAuth2 Integration', description='Integrate with OAuth2 providers to support social logins, reducing barriers to entry for new users.'), ModuleRefinementRequirement(name='Traditional Sign-in', description='Enable a secure method for users to sign in using an email and password combo, encrypting credentials at rest.'), ModuleRefinementRequirement(name='Password Reset', description='Provide a secure, user-friendly process for users to reset forgotten passwords.'), ModuleRefinementRequirement(name='Security Compliance', description='Ensure authentication practices comply with data protection regulations and best practices.')], endpoints=[Endpoint(name='OAuth2 Login', type='POST', description='Endpoint for handling OAuth2 logins, returning user tokens and session data.', path='/auth/oauth2/login', request_model=None, response_model=None, data_models=None, database_schema=None), Endpoint(name='Login', type='POST', description='Endpoint for handling traditional logins with email and password.', path='/auth/login', request_model=None, response_model=None, data_models=None, database_schema=None), Endpoint(name='Password Reset Request', type='POST', description='Endpoint to initiate the password reset process.', path='/auth/password/reset/request', request_model=None, response_model=None, data_models=None, database_schema=None), Endpoint(name='Password Reset', type='PATCH', description='Endpoint to reset the password after verification.', path='/auth/password/reset', request_model=None, response_model=None, data_models=None, database_schema=None)], related_modules=[])"""

    module2_repr = """Module(name='Authorization', description='Manages the assignment of roles and permissions within the app, controlling access to features and information based on user roles. Ensures a secure, hierarchical access system.', requirements=[ModuleRefinementRequirement(name='Role-based Access Control', description='Define and enforce access levels based on user roles (tutor vs client), controlling what actions they can perform.'), ModuleRefinementRequirement(name='Permissions Management', description='Manage detailed permissions within user roles, allowing for granular access control.'), ModuleRefinementRequirement(name='Secure Access Implementation', description='Ensure that authorization methods adhere to security best practices, preventing unauthorized access.')], endpoints=[Endpoint(name='Set User Role', type='PATCH', description='Endpoint to assign or update a user’s role within the system.', path='/users/{id}/role', request_model=None, response_model=None, data_models=None, database_schema=None), Endpoint(name='Get User Permissions', type='GET', description='Retrieve the permissions associated with a user’s role.', path='/users/{id}/permissions', request_model=None, response_model=None, data_models=None, database_schema=None)], related_modules=[])"""
    db_names = "[User,Appointment,Invoice,Payment,Notification]"
    spec = """# TutorMaster\n\n## Task \nThe Tutor App is an app designed for tutors to manage their clients,\n schedules, and invoices.\n\nIt must support both the client and tutor scheduling, rescheduling and canceling\n appointments, and sending invoices after the appointment has passed.\n\nClients can sign up with OAuth2 or with traditional sign-in authentication. If they sign\n up with traditional authentication, it must be safe and secure. There will need to be\n password reset and login capabilities.\n\nThere will need to be authorization for identifying clients vs the tutor.\n\nAdditionally, it will have proper management of financials, including invoice management\n and payment tracking. This includes things like paid/failed invoice notifications,\n unpaid invoice follow-up, summarizing d/w/m/y income, and generating reports.\n\n### Project Description\nHuman: Your task is to "The Tutor App is an app designed for tutors to manage their clients,\n schedules, and invoices.\n\nIt must support both the client and tutor scheduling, rescheduling and canceling\n appointments, and sending invoices after the appointment has passed.\n\nClients can sign up with OAuth2 or with traditional sign-in authentication. If they sign\n up with traditional authentication, it must be safe and secure. There will need to be\n password reset and login capabilities.\n\nThere will need to be authorization for identifying clients vs the tutor.\n\nAdditionally, it will have proper management of financials, including invoice management\n and payment tracking. This includes things like paid/failed invoice notifications,\n unpaid invoice follow-up, summarizing d/w/m/y income, and generating reports."\n\nAnswer as an expert product owner.\n\nyour memory is based on a google like search. When you want more information send search:<query> and I\'ll send you back the reply.\n\nyou can ask the user questions by sending ask:<query> and I\'ll send you back the reply. Make sure to ask broad questions that help guide your understanding\n\nWhen you feel you have finished getting the info you need or are confident it\'s not there, summarize the memory you\'ve built and send finished:<summary>. make sure you don\'t reply anything before the "finished:<summary>" or it will confuse the human\n\nOnly reply with one message at a time so that the user isn\'t overwhelmed.\n\nOnly reply with the specified tags.\n\nAssistant:\n Got it, let me clarify my understanding by asking some questions.\n\nask: Who is the primary user for this app - tutors or clients? \nask: What features are most important - scheduling and financial tracking, or security and authentication?\nask: Should the app integrate with any third-party services for payments, calendars etc?\nask: What platforms should be supported - web, iOS, Android etc?\n\n### Product Description\nTutorMaster is a holistic, multi-platform application designed to serve the needs of tutors and their clients by offering a suite of tools for scheduling, payment processing, and communication. The central premise of TutorMaster is to provide an intuitive, secure, and efficient tool for managing tutorial sessions, invoicing, and financial tracking. It does so through a user-friendly interface that caters to individuals of intermediate technological proficiency, ensuring a broad range of users can navigate and utilize the app effectively. With dual authentication methods, comprehensive scheduling options, automated invoice management, and robust financial tracking and reports, TutorMaster aims to simplify the logistics of tutoring, allowing tutors more time to focus on delivering quality education.\n\n### Features\n#### User Authentication\n##### Description\nSupports OAuth2 and traditional sign-in methods, with emphasis on security for traditional authentication methods. Includes password reset and login capabilities.\n##### Considerations\nMust be compliant with data protection regulations. Should offer a straightforward password reset process.\n##### Risks\nPotential security vulnerabilities if not implemented securely.\n##### External Tools Required\nOAuth2 provider integration, secure database for traditional login credentials.\n##### Priority: CRITICAL\n#### Scheduling\n##### Description\nAllows tutors and clients to schedule, reschedule, and cancel appointments. Includes views for both parties.\n##### Considerations\nShould accommodate different time zones. Needs clean UI for ease of use.\n##### Risks\nConflicts in scheduling could arise without proper checks.\n##### External Tools Required\nPotentially, third-party calendar integration.\n##### Priority: HIGH\n#### Invoice Management\n##### Description\nAutomatic sending of invoices post-appointment, with capabilities for tracking payment status.\n##### Considerations\nMust support various payment methods and currencies.\n##### Risks\nIncorrect invoicing could lead to disputes.\n##### External Tools Required\nPayment processing integration.\n##### Priority: HIGH\n#### Financial Tracking and Reports\n##### Description\nTracks payments, generates notifications for paid/failed invoices, follows up on unpaid invoices, and provides summaries and reports of earnings over time.\n##### Considerations\nNeeds to be customizable to suit different tutoring business models.\n##### Risks\nInaccuracies in tracking could affect financial decision-making.\n##### External Tools Required\nNone beyond the internal database.\n##### Priority: HIGH\n#### Authorization\n##### Description\nDifferentiates privileges between clients and tutors, ensuring access to appropriate functionalities.\n##### Considerations\nMust be flexible to accommodate future role additions.\n##### Risks\nIncorrect access levels could expose sensitive information.\n##### External Tools Required\nInternal role-based access control system.\n##### Priority: MEDIUM\n\n### Clarifiying Questions\n- "Do we need a front end for this: "Human: Your task is to "The Tutor App is an app designed for tutors to manage their clients, schedules, and invoices. It must support both the client and tutor scheduling, rescheduling and canceling appointments, and sending invoices after the appointment has passed. Clients can sign up with OAuth2 or with traditional sign-in authentication. If they sign up with traditional authentication, it must be safe and secure. There will need to be password reset and login capabilities. There will need to be authorization for identifying clients vs the tutor. Additionally, it will have proper management of financials, including invoice management and payment tracking. This includes things like paid/failed invoice notifications, unpaid invoice follow-up, summarizing d/w/m/y income, and generating reports."": "Yes" : Reasoning: "Considering the functionalities described such as scheduling appointments, sending invoices, sign-ups via OAuth2 or traditional authentication, and financial management, it is clear that users (both tutors and clients) need an interactive platform to engage with these services. The description outlines numerous interactions that necessitate a user interface where these tasks can be performed conveniently. Therefore, a front end is essential to facilitate these user interactions efficiently."\n- "Who is the expected user of this: "Human: Your task is to "The Tutor App is an app designed for tutors to manage their clients, schedules, and invoices. It must support both the client and tutor scheduling, rescheduling and canceling appointments, and sending invoices after the appointment has passed. Clients can sign up with OAuth2 or with traditional sign-in authentication. If they sign up with traditional authentication, it must be safe and secure. There will need to be password reset and login capabilities. There will need to be authorization for identifying clients vs the tutor. Additionally, it will have proper management of financials, including invoice management and payment tracking. This includes things like paid/failed invoice notifications, unpaid invoice follow-up, summarizing d/w/m/y income, and generating reports."": "The expected users are tutors and their clients." : Reasoning: "From the provided description, it\'s clear that the app is designed to serve two main stakeholders: tutors and their clients. Tutors are the primary users, as the app\'s core functionalities cater to managing their professional activities—such as scheduling, invoice management, and financial tracking specific to their tutoring services. However, clients also play a significant role in the app\'s ecosystem. Their ability to schedule and reschedule appointments, sign up using different authentication methods (OAuth2 or traditional sign-in), and interact with invoices indicates that the app is designed with a dual-user perspective in mind, aiming to streamline the interaction between tutors and clients in a secure, efficient, and organized manner."\n- "What is the skill level of the expected user of this: "Human: Your task is to "The Tutor App is an app designed for tutors to manage their clients, schedules, and invoices. It must support both the client and tutor scheduling, rescheduling and canceling appointments, and sending invoices after the appointment has passed. Clients can sign up with OAuth2 or with traditional sign-in authentication. If they sign up with traditional authentication, it must be safe and secure. There will need to be password reset and login capabilities. There will need to be authorization for identifying clients vs the tutor. Additionally, it will have proper management of financials, including invoice management and payment tracking. This includes things like paid/failed invoice notifications, unpaid invoice follow-up, summarizing d/w/m/y income, and generating reports."": "Intermediate" : Reasoning: "Considering the functionalities and responsibilities entailed within The Tutor App, users—both tutors and clients—are expected to possess an intermediate level of technological proficiency. This skill level is necessary to navigate the various facets of the app, such as scheduling and managing appointments, handling security features like OAuth2 and traditional sign-in mechanisms, and interacting with financial tracking and invoice management systems. Tutors, specifically, need an added level of competence to efficiently manage their business aspects such as tracking payments and generating financial reports. Clients, on the other hand, require enough skill to securely sign up, schedule, and manage their appointments. This implies that the design and user experience of the app should be intuitive to those with a reasonable level of familiarity with digital platforms yet sophisticated enough to offer extensive functionalities effectively."\n\n\n### Conclusive Q&A\n- "Who is the primary user for this app - tutors or clients?": "Tutors are the primary users of the Tutor App, with features tailored to meet their specific business needs, while also accommodating clients for a seamless interaction." : Reasoning: "Identifying the primary user between tutors and clients is essential for focusing the design and development efforts. While the app serves both parties, understanding who the primary target is can influence feature prioritization and user experience design."\n- "What features are most important - scheduling and financial tracking, or security and authentication?": "Scheduling and financial tracking are deemed most important; however, a foundational level of security and authentication is necessary for these features to be effectively utilized." : Reasoning: "This question aims to assess the priority of features from a stakeholder perspective, determining whether the emphasis should be on the core functionalities (scheduling and financial tracking) or foundational aspects such as security."\n- "Should the app integrate with any third-party services for payments, calendars etc?": "The app should integrate with third-party services for payments and calendars to provide a seamless experience and trusted functionality." : Reasoning: "Integration with third-party services can enhance the app\'s functionality and user experience by enabling features such as direct payments or syncing with external calendars."\n- "What platforms should be supported - web, iOS, Android etc?": "The Tutor App should be accessible via web, iOS, and Android to ensure comprehensive coverage and user convenience." : Reasoning: "Determining the platforms to support impacts the technology choice, development process, and user reach. Given the app\'s target users, finding the right platforms is crucial for adoption."\n\n\n### Requirement Q&A\n- "do we need db?": "Yes" : Reasoning: "Given the app involves managing schedules, client and tutor profiles, invoices, and financial reports, a database is essential for storing and retrieving user and transaction data efficiently."\n- "do we need an api for talking to a front end?": "Yes" : Reasoning: "To facilitate communication between the server and the app’s frontend across different platforms (web, iOS, Android), an API is necessary. This will enable seamless data exchange and functionality use."\n- "do we need an api for talking to other services?": "Yes" : Reasoning: "Considering the need for third-party integrations for payments and calendars, an API for communicating with these services is critical to enable these functionalities."\n- "do we need an api for other services talking to us?": "Yes" : Reasoning: "For third-party services, such as payment gateways or calendar services, to push notifications or updates to our app, an API to accept incoming data is required."\n- "do we need to issue api keys for other services to talk to us?": "Yes" : Reasoning: "To ensure secure and controlled access by third-party services to our app, issuing API keys is a necessary security measure."\n- "do we need monitoring?": "Yes" : Reasoning: "Monitoring is crucial to oversee the app\'s performance, track errors, and observe user interactions. This ensures reliability and improves user experience."\n- "do we need internationalization?": "No" : Reasoning: "Given no specific mention of targeting users in multiple countries or needing to support multiple languages, it\'s reasonable to consider internationalization as a future enhancement rather than an initial necessity."\n- "do we need analytics?": "Yes" : Reasoning: "Analytics play a vital role in understanding user behavior, feature usage, and overall app performance, which is critical for driving improvements and business decisions."\n- "is there monetization?": "Yes" : Reasoning: "Considering the description mentions managing financials and invoicing, the app likely has a business model in place aimed at generating revenue, either directly or indirectly, from its user base."\n- "is the monetization via a paywall or ads?": "Paywall" : Reasoning: "Given the professional context of the app (tutor scheduling and invoicing), a paywall for accessing premium features or subscription tiers seems more appropriate and consistent than ad-supported revenue."\n- "does this require a subscription or a one-time purchase?": "Subscription" : Reasoning: "The nature of the Tutor App, providing ongoing services such as scheduling, invoicing, and financial tracking, aligns more with a subscription model, providing continuous value over time."\n- "is the whole service monetized or only part?": "Part" : Reasoning: "It\'s sensible to have basic functionalities available for free to attract users, with advanced features or enhanced services behind a subscription, thus monetizing part of the service."\n- "is monetization implemented through authorization?": "Yes" : Reasoning: "Monetization strategies such as subscriptions require controlling access to certain features based on the user’s payment status, necessitating the implementation of authorization mechanisms."\n- "do we need authentication?": "Yes" : Reasoning: "Considering the app handles sensitive user data, including financial information and personal schedules, secure authentication is fundamental to protect user accounts and data."\n- "do we need authorization?": "Yes" : Reasoning: "The app needs to distinguish between different user roles (clients vs. tutors) and their permissions, especially regarding data access and actions they can perform, which requires authorization."\n- "what authorization roles do we need?": "["Tutor", "Client"]" : Reasoning: "The core functionalities revolve around tutors managing their schedules and financials, and clients booking or managing appointments. Each set of functionalities requires different access levels."\n\n\n### Requirements\n### Functional Requirements\n#### User Authentication\n##### Thoughts\nSecurity is paramount; thoughtful consideration of potential vulnerabilities is essential to protect user data.\n##### Description\nImplement a secure authentication system supporting OAuth2 and traditional methods, with features for password resetting and login capabilities.\n#### Scheduling\n##### Thoughts\nCore functionality that impacts user experience directly, demanding an intuitive UI/UX design.\n##### Description\nFacilitate scheduling, rescheduling, and cancelling of appointments with views for both tutors and clients, including cross-time-zone support.\n#### Invoice Management\n##### Thoughts\nThis reduces administrative overhead and improves operational efficiency for tutors.\n##### Description\nAutomate the sending of invoices after appointments, and provide capabilities for tracking payment statuses including integration with payment gateways.\n#### Financial Tracking and Reports\n##### Thoughts\nEssential for tutors to manage their finances and make informed decisions regarding their tutoring business.\n##### Description\nInclude features for tracking payments, generating notifications for invoice status, summarizing and reporting income over selectable periods.\n#### Authorization\n##### Thoughts\nNecessary for operational security and privacy, ensuring users only access what\'s relevant to them.\n##### Description\nImplement role-based access control to differentiate between client and tutor functionalities and privileges.\n#### Third-Party Integrations\n##### Thoughts\nSelecting the right partners can significantly impact the app’s efficiency and user satisfaction.\n##### Description\nIncorporate third-party services for payments and calendar functionalities to enhance user experience and trustworthiness.\n#### Multi-Platform Support\n##### Thoughts\nCritical for broad user access and convenience, necessitating responsive design and cross-platform functionality.\n##### Description\nEnsure the application is accessible and fully functional across web, iOS, and Android platforms.\n\n### Nonfunctional Requirements\n#### Security\n##### Thoughts\nA foundational requirement, underpinning user trust and regulatory compliance.\n##### Description\nMaintain high security standards, especially for data protection, authentication, and transactions.\n#### Usability\n##### Thoughts\nDirectly impacts user adoption and satisfaction.\n##### Description\nDesign an intuitive and user-friendly interface suitable for users with intermediate technological proficiency.\n#### Performance\n##### Thoughts\nPoor performance can deter users, making this a crucial aspect of the user experience.\n##### Description\nEnsure quick loading times and responsive interactions within the application, optimizing for efficiency.\n#### Scalability\n##### Thoughts\nImportant for supporting the growth of the TutorMaster platform.\n##### Description\nArchitect the system to easily handle increasing numbers of users, data volume, and transaction throughput without degradation in performance.\n#### Compliance\n##### Thoughts\nNon-negotiable for operating in various jurisdictions and maintaining user trust.\n##### Description\nAdhere to legal and regulatory standards relevant to data protection (such as GDPR), financial transactions, and online security.\n#### Portability\n##### Thoughts\nEssential for reaching a broad user base and facilitating platform transitions.\n##### Description\nEnsure the system is designed to function across multiple platforms (web, iOS, Android) with consistent quality and user experience.\n#### Maintainability\n##### Thoughts\nImpacts the long-term viability and adaptability of the application.\n##### Description\nCode and system architecture should be clean and well-documented to facilitate updates and troubleshooting.\n\n\n### Modules\n### Module: Authentication\n#### Description\nManages user authentication processes, providing secure access via OAuth2 and traditional sign-in methods. Ensures data protection for user credentials and offers password reset capabilities.\n#### Requirements\n#### Requirement: OAuth2 Integration\nIntegrate with OAuth2 providers to support social logins, reducing barriers to entry for new users.\n\n#### Requirement: Traditional Sign-in\nEnable a secure method for users to sign in using an email and password combo, encrypting credentials at rest.\n\n#### Requirement: Password Reset\nProvide a secure, user-friendly process for users to reset forgotten passwords.\n\n#### Requirement: Security Compliance\nEnsure authentication practices comply with data protection regulations and best practices.\n\n#### Endpoints\n##### OAuth2 Login: `POST /auth/oauth2/login`\n\nEndpoint for handling OAuth2 logins, returning user tokens and session data.\n\n\n\n\n\n\n##### Login: `POST /auth/login`\n\nEndpoint for handling traditional logins with email and password.\n\n\n\n\n\n\n##### Password Reset Request: `POST /auth/password/reset/request`\n\nEndpoint to initiate the password reset process.\n\n\n\n\n\n\n##### Password Reset: `PATCH /auth/password/reset`\n\nEndpoint to reset the password after verification.\n\n\n\n\n\n\n\n### Module: Authorization\n#### Description\nManages the assignment of roles and permissions within the app, controlling access to features and information based on user roles. Ensures a secure, hierarchical access system.\n#### Requirements\n#### Requirement: Role-based Access Control\nDefine and enforce access levels based on user roles (tutor vs client), controlling what actions they can perform.\n\n#### Requirement: Permissions Management\nManage detailed permissions within user roles, allowing for granular access control.\n\n#### Requirement: Secure Access Implementation\nEnsure that authorization methods adhere to security best practices, preventing unauthorized access.\n\n#### Endpoints\n##### Set User Role: `PATCH /users/{id}/role`\n\nEndpoint to assign or update a user’s role within the system.\n\n\n\n\n\n\n##### Get User Permissions: `GET /users/{id}/permissions`\n\nRetrieve the permissions associated with a user’s role.\n\n\n\n\n\n\n\n### Module: Scheduling\n#### Description\nEnables tutors and clients to effectively manage appointments through scheduling, rescheduling, and cancellation functionalities. Integrates with third-party calendars for added convenience.\n#### Requirements\n#### Requirement: Appointment Creation\nAllow users to create new appointments with date, time, and participant details.\n\n#### Requirement: Appointment Modification\nUsers can reschedule appointments, updating the time and date as needed.\n\n#### Requirement: Appointment Cancellation\nEnable cancellation of appointments with appropriate notifications to affected users.\n\n#### Requirement: Conflict Resolution\nAutomatically detect and resolve scheduling conflicts to prevent double bookings.\n\n#### Requirement: Time Zone Support\nEnsure the system accommodates users in different time zones, displaying times accordingly.\n\n#### Endpoints\n##### Create Appointment: `POST /appointments`\n\nEndpoint to schedule a new appointment between a tutor and a client.\n\n\n\n\n\n\n##### Update Appointment: `PUT /appointments/{id}`\n\nEndpoint to modify details of an existing appointment.\n\n\n\n\n\n\n##### Cancel Appointment: `DELETE /appointments/{id}/cancel`\n\nEndpoint for cancelling an existing appointment.\n\n\n\n\n\n\n\n### Module: Invoice Management\n#### Description\nAutomates the generation and distribution of invoices following appointments, integrates with secure payment gateways for efficient payment processing, and enables tracking of invoice statuses.\n#### Requirements\n#### Requirement: Invoice Generation\nAutomatically generate an invoice after each appointment, detailing charges and services rendered.\n\n#### Requirement: Payment Gateway Integration\nLink with payment gateways to allow for secure, timely payment of invoices.\n\n#### Requirement: Invoice Status Tracking\nMonitor and update the status of each invoice, including paid, pending, or failed.\n\n#### Requirement: Invoice Dispute Handling\nProvide mechanisms for tutors and clients to dispute and resolve inaccuracies in invoicing.\n\n#### Endpoints\n##### Generate Invoice: `POST /invoices/generate`\n\nEndpoint to automatically generate an invoice after an appointment.\n\n\n\n\n\n\n##### Retrieve Invoice: `GET /invoices/{id}`\n\nEndpoint to get details of a specific invoice.\n\n\n\n\n\n\n##### Update Invoice Status: `PATCH /invoices/{id}/status`\n\nEndpoint to update the status of an invoice (e.g., mark as paid).\n\n\n\n\n\n\n\n### Module: Financial Tracking\n#### Description\nProvides robust tools for financial management, including tracking of payments, automated notifications for invoice statuses, and comprehensive financial analytics and reporting.\n#### Requirements\n#### Requirement: Payment Tracking\nMonitor incoming payments, associating them with the correct invoice and client.\n\n#### Requirement: Invoice Notification System\nAutomate the sending of notifications based on invoice status to both tutors and clients.\n\n#### Requirement: Financial Reporting\nGenerate detailed reports and summaries of earnings and outstanding invoices over selectable time periods.\n\n#### Requirement: Unpaid Invoice Follow-up\nImplement follow-up mechanisms for unpaid invoices, including reminder notifications.\n\n#### Endpoints\n##### Track Payment: `POST /payments/track`\n\nEndpoint to log a payment against an invoice.\n\n\n\n\n\n\n##### Financial Summary: `GET /financials/summary`\n\nProvides a summary of financial earnings over a specified period.\n\n\n\n\n\n\n\n### Module: Third-Party Integrations\n#### Description\nManages the connection and interaction with external services such as payment gateways, calendar APIs, and other third-party tools. This module serves as a centralized hub for integrating external functionalities into TutorMaster, ensuring seamless and secure interactions with trusted third-party services.\n\n### Module: UserProfile\n#### Description\nHandles user profile information for both tutors and clients. This module supports the viewing and editing of user profiles, including personal details and preferences. It serves as a support module for authentication and authorization, enriching user data beyond merely login credentials.\n\n### Module: Notification\n#### Description\nResponsible for sending notifications and alerts related to various actions and statuses within the app, such as upcoming appointments, payment confirmations, and invoice reminders. This module plays a pivotal role in enhancing user engagement and ensuring effective communication between tutors, clients, and the system.\n\n### Database Design\n## TutorMaster Schema\n**Description**: This schema defines the structure for the TutorMaster application, capturing entities like Users, Appointments, Invoices, Payments, and Notifications with relationships between them, supporting core functionalities like scheduling, financial tracking, and user interactions.\n**Tables**:\n**User**\n\n**Description**: Represents both tutors and clients, holding their login credentials, role, and relationship to appointments, invoices, and notifications.\n\n**Definition**:\n```\nmodel User {\n  id    String   @id @default(uuid())\n  email String   @unique\n  password String\n  role  UserRole\n  name  String?\n  appointments Appointment[]\n  invoices Invoice[]\n  notifications Notification[]\n  createdAt DateTime @default(now())\n  updatedAt DateTime @updatedAt\n}\n```\n\n**Appointment**\n\n**Description**: Tracks the scheduling of appointments between tutors and clients, including the date, status, and linked invoice.\n\n**Definition**:\n```\nmodel Appointment {\n  id    String   @id @default(uuid())\n  tutorId String\n  clientId String\n  date  DateTime\n  status AppointmentStatus\n  tutor User @relation(fields: [tutorId], references: [id])\n  client User @relation(fields: [clientId], references: [id])\n  invoice Invoice?\n  createdAt DateTime @default(now())\n  updatedAt DateTime @updatedAt\n}\n```\n\n**Invoice**\n\n**Description**: Manages invoicing for appointments, including amount, due date, and linked payment.\n\n**Definition**:\n```\nmodel Invoice {\n  id    String   @id @default(uuid())\n  appointmentId String\n  amount Float\n  status InvoiceStatus\n  dueDate DateTime\n  payment Payment?\n  createdAt DateTime @default(now())\n  updatedAt DateTime @updatedAt\n}\n```\n\n**Payment**\n\n**Description**: Records payments against invoices, storing the amount and date.\n\n**Definition**:\n```\nmodel Payment {\n  id    String   @id @default(uuid())\n  invoiceId String\n  amount Float\n  date DateTime\n  invoice Invoice @relation(fields: [invoiceId], references: [id])\n  createdAt DateTime @default(now())\n  updatedAt DateTime @updatedAt\n}\n```\n\n**Notification**\n\n**Description**: Handles sending of notifications to users, divided by type and containing a reference to the related user.\n\n**Definition**:\n```\nmodel Notification {\n  id    String   @id @default(uuid())\n  userId String\n  type NotificationType\n  message String\n  date DateTime\n  user User @relation(fields: [userId], references: [id])\n  createdAt DateTime @default(now())\n  updatedAt DateTime @updatedAt\n}\n```\n\n"""

    endpoint_block = EndpointSchemaRefinementBlock()

    async def run_ai() -> dict[str, EndpointSchemaRefinementResponse]:
        if not db_client.is_connected():
            await db_client.connect()
        endpoint1_ref: EndpointSchemaRefinementResponse = await endpoint_block.invoke(
            ids=ids,
            invoke_params={
                "spec": spec,
                "db_models": db_names,
                "module_repr": module1_repr,
                "endpoint_repr": endpoint1_repr,
            },
        )
        endpoint2_ref: EndpointSchemaRefinementResponse = await endpoint_block.invoke(
            ids=ids,
            invoke_params={
                "spec": spec,
                "db_models": db_names,
                "module_repr": module2_repr,
                "endpoint_repr": endpoint2_repr,
            },
        )

        await db_client.disconnect()
        return {"endpoint1": endpoint1_ref, "endpoint2": endpoint2_ref}

    endpoints = run(run_ai())

    for key, item in endpoints.items():
        if isinstance(item, EndpointSchemaRefinementResponse):
            logger.info("Endpoint:")
            logger.info(f"\tThink: {item.think}")
            logger.info(f"\tDB Models Needed: {item.db_models_needed}")
            logger.info(f"\tEnd Thoughts: {item.end_thoughts}")
            logger.info("\tAPI Endpoint Request: ")
            # Request Model
            logger.info(f"\t\t{item.api_endpoint.request_model}")
            logger.info(
                f"\t\tRequest Model Name: {item.api_endpoint.request_model.name}"
            )
            logger.info(
                f"\t\tRequest Model Description: {item.api_endpoint.request_model.description}"
            )
            logger.info(
                f"\t\tRequest Model Fields: {item.api_endpoint.request_model.Fields}"
            )
            # This shouldn't be longer than this Surely
            for i in item.api_endpoint.request_model.Fields or []:
                logger.info(f"\t\t\t{i}")
                logger.info(f"\t\t\tField Name: {i.name}")
                logger.info(f"\t\t\tField Description: {i.description}")
                logger.info(f"\t\t\tField Type: {i.type}")
                logger.info(f"\t\t\tField Related Types: {i.related_types!r}")
                for j in i.related_types or []:
                    logger.info(f"\t\t\t\t{j}")
                    logger.info(f"\t\t\t\tRelated Type Name: {j.name}")
                    logger.info(f"\t\t\t\tRelated Type Description: {j.description}")
                    logger.info(f"\t\t\t\tRelated Type Fields: {j.Fields}")
                    for k in j.Fields or []:
                        logger.info(f"\t\t\t\t\t{k}")
                        logger.info(f"\t\t\t\t\tField Name: {k.name}")
                        logger.info(f"\t\t\t\t\tField Description: {k.description}")
                        logger.info(f"\t\t\t\t\tField Type: {k.type}")
                        logger.info(
                            f"\t\t\t\t\tField Related Types: {k.related_types!r}"
                        )
                        for l in k.related_types or []:
                            logger.info(f"\t\t\t\t\t\t{l}")
                            logger.info(f"\t\t\t\t\t\tRelated Type Name: {l.name}")
                            logger.info(
                                f"\t\t\t\t\t\tRelated Type Description: {l.description}"
                            )
                            logger.info(f"\t\t\t\t\t\tRelated Type Fields: {l.Fields}")
                            for m in l.Fields or []:
                                logger.info(f"\t\t\t\t\t\t\t{m}")
                                logger.info(f"\t\t\t\t\t\t\tField Name: {m.name}")
                                logger.info(
                                    f"\t\t\t\t\t\t\tField Description: {m.description}"
                                )
                                logger.info(f"\t\t\t\t\t\t\tField Type: {m.type}")
                                logger.info(
                                    f"\t\t\t\t\t\t\tField Related Types: {m.related_types!r}"
                                )
                                if len(m.related_types or []) > 0:
                                    logger.info("This is insanely recursive")
                                    breakpoint()
            logger.info("\tAPI Endpoint Response:")
            # Response Model
            logger.info(f"\t\t{item.api_endpoint.response_model}")
            logger.info(
                f"\t\tResponse Model Name: {item.api_endpoint.response_model.name}"
            )
            logger.info(
                f"\t\tResponse Model Description: {item.api_endpoint.response_model.description}"
            )
            logger.info(
                f"\t\tResponse Model Fields: {item.api_endpoint.response_model.Fields}"
            )
            # This shouldn't be longer than this Surely
            for i in item.api_endpoint.response_model.Fields or []:
                logger.info(f"\t\t\t{i}")
                logger.info(f"\t\t\tField Name: {i.name}")
                logger.info(f"\t\t\tField Description: {i.description}")
                logger.info(f"\t\t\tField Type: {i.type}")
                logger.info(f"\t\t\tField Related Types: {i.related_types!r}")
                for j in i.related_types or []:
                    logger.info(f"\t\t\t\t{j}")
                    logger.info(f"\t\t\t\tRelated Type Name: {j.name}")
                    logger.info(f"\t\t\t\tRelated Type Description: {j.description}")
                    logger.info(f"\t\t\t\tRelated Type Fields: {j.Fields}")
                    for k in j.Fields or []:
                        logger.info(f"\t\t\t\t\t{k}")
                        logger.info(f"\t\t\t\t\tField Name: {k.name}")
                        logger.info(f"\t\t\t\t\tField Description: {k.description}")
                        logger.info(f"\t\t\t\t\tField Type: {k.type}")
                        logger.info(
                            f"\t\t\t\t\tField Related Types: {k.related_types!r}"
                        )
                        for l in k.related_types or []:
                            logger.info(f"\t\t\t\t\t\t{l}")
                            logger.info(f"\t\t\t\t\t\tRelated Type Name: {l.name}")
                            logger.info(
                                f"\t\t\t\t\t\tRelated Type Description: {l.description}"
                            )
                            logger.info(f"\t\t\t\t\t\tRelated Type Fields: {l.Fields}")
                            for m in l.Fields or []:
                                logger.info(f"\t\t\t\t\t\t\t{m}")
                                logger.info(f"\t\t\t\t\t\t\tField Name: {m.name}")
                                logger.info(
                                    f"\t\t\t\t\t\t\tField Description: {m.description}"
                                )
                                logger.info(f"\t\t\t\t\t\t\tField Type: {m.type}")
                                logger.info(
                                    f"\t\t\t\t\t\t\tField Related Types: {m.related_types!r}"
                                )
                                if len(m.related_types or []) > 0:
                                    logger.info("????")
                                    breakpoint()
            logger.info("\n\n\n")
        else:
            logger.info("????")
            breakpoint()

    # # If you want to test the block in an interactive environment
    # import IPython

    # IPython.embed()
    breakpoint()
