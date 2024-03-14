import logging

from codex.common.ai_block import (
    AIBlock,
    Identifiers,
    ValidatedResponse,
    ValidationError,
)
from codex.common.ai_model import OpenAIChatClient
from codex.common.exec_external_tool import exec_external_on_contents
from codex.common.logging_config import setup_logging
from codex.common.parse_prisma import parse_prisma_schema
from codex.requirements.model import DatabaseEnums, DatabaseTable, DBResponse

logger = logging.getLogger(__name__)


class DatabaseGenerationBlock(AIBlock):
    """
    This is a block that handles, calling the LLM, validating the response,
    storing llm calls, and returning the response to the user

    """

    # The name of the prompt template folder in codex/prompts/{model}
    prompt_template_name = "requirements/database"
    # Model to use for the LLM
    model = "gpt-4-0125-preview"
    # Should we force the LLM to reply in JSON
    is_json_response = True
    # If we are using is_json_response, what is the response model
    pydantic_object = DBResponse

    def validate(
        self, invoke_params: dict, response: ValidatedResponse
    ) -> ValidatedResponse:
        """
        The validation logic for the response. In this case its really simple as we
        are just validating the response is a Clarification model. However, in the other
        blocks this is much more complex. If validation failes it triggers a retry.
        """
        try:
            model = DBResponse.model_validate_json(response.response, strict=False)
            text_schema = ""
            for enum in model.database_schema.enums:
                text_schema += enum.definition
            for table in model.database_schema.tables:
                text_schema += table.definition
            # parse the prisma schema back into the tables and enum definitions
            # and compare them to the original
            unparsed = exec_external_on_contents(["prisma", "format"], text_schema)
            unparsed = exec_external_on_contents(["prisma", "validate"], unparsed)

            parsed_prisma = parse_prisma_schema(unparsed)
            for enum in model.database_schema.enums:
                if enum.name not in parsed_prisma.enums:
                    raise ValidationError(
                        f"Enum {enum.name} not found in parsed prisma schema"
                    )
                # replace the definition with the parsed definition
                enum.definition = parsed_prisma.enums[enum.name].definition
            for table in model.database_schema.tables:
                if table.name not in parsed_prisma.models:
                    raise ValidationError(
                        f"Table {table.name} not found in parsed prisma schema"
                    )
                if not table.name:
                    raise ValidationError("Tables all require a name")
                # replace the definition with the parsed definition
                table.definition = parsed_prisma.models[table.name].definition

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

    from codex.common.test_const import identifier_1

    ids = identifier_1

    setup_logging(local=True)

    OpenAIChatClient.configure({})
    db_client = Prisma(auto_register=True)
    logging.info("Running block")

    # This is the input to the block
    obj = {
        "product_spec": """# TutorBridge\n\n## Task \nThe Tutor App is an app designed for tutors to manage their clients,\n schedules, and invoices.\n\nIt must support both the client and tutor scheduling, rescheduling and canceling\n appointments, and sending invoices after the appointment has passed.\n\nClients can sign up with OAuth2 or with traditional sign-in authentication. If they sign\n up with traditional authentication, it must be safe and secure. There will need to be\n password reset and login capabilities.\n\nThere will need to be authorization for identifying clients vs the tutor.\n\nAdditionally, it will have proper management of financials, including invoice management\n and payment tracking. This includes things like paid/failed invoice notifications,\n unpaid invoice follow-up, summarizing d/w/m/y income, and generating reports.\n\n### Project Description\nHuman: Your task is to "The Tutor App is an app designed for tutors to manage their clients,\n schedules, and invoices.\n\nIt must support both the client and tutor scheduling, rescheduling and canceling\n appointments, and sending invoices after the appointment has passed.\n\nClients can sign up with OAuth2 or with traditional sign-in authentication. If they sign\n up with traditional authentication, it must be safe and secure. There will need to be\n password reset and login capabilities.\n\nThere will need to be authorization for identifying clients vs the tutor.\n\nAdditionally, it will have proper management of financials, including invoice management\n and payment tracking. This includes things like paid/failed invoice notifications,\n unpaid invoice follow-up, summarizing d/w/m/y income, and generating reports."\n\nAnswer as an expert product owner.\n\nyour memory is based on a google like search. When you want more information send search:<query> and I\'ll send you back the reply.\n\nyou can ask the user questions by sending ask:<query> and I\'ll send you back the reply. Make sure to ask broad questions that help guide your understanding\n\nWhen you feel you have finished getting the info you need or are confident it\'s not there, summarize the memory you\'ve built and send finished:<summary>. make sure you don\'t reply anything before the "finished:<summary>" or it will confuse the human\n\nOnly reply with one message at a time so that the user isn\'t overwhelmed.\n\nOnly reply with the specified tags.\n\nAssistant:\n search: key features of tutor scheduling app\n\n### Product Description\nTutorBridge is an intuitive, secure, and comprehensive application designed for tutors to manage their client relationships, schedules, invoices, and financials. The app supports functionalities such as client and tutor-driven scheduling, rescheduling, cancellation of appointments, and the issuance of invoices post-appointment. To accommodate a broad user base, TutorBridge offers authentication via OAuth2 and traditional sign-in, placing a strong emphasis on security, including password resets and login features. The application distinguishes between client and tutor roles for tailored authorization and access. A robust financial management system within the app facilitates invoice processing, payment tracking, including notifications for various payment statuses, income summarization, and report generation. TutorBridge aims to provide a seamless, efficient interface for tutors to manage their business operations while ensuring data privacy and security compliance.\n\n### Features\n#### User Authentication\n##### Description\nSecure and flexible user authentication system supporting OAuth2 and traditional sign-in. Includes password reset and login capabilities.\n##### Considerations\nThe need for a user-friendly interface, landing page layouts for login/signup, and ensuring high-security standards.\n##### Risks\nFailure to properly secure user data could lead to breaches.\n##### External Tools Required\nOAuth2 providers, email services for password reset.\n##### Priority: CRITICAL\n#### Scheduling and Appointment Management\n##### Description\nAllows tutors and clients to schedule, reschedule, and cancel appointments with real-time updates. Includes calendar integration.\n##### Considerations\nReal-time synchronization, conflict resolution, user interface for easy management.\n##### Risks\nComplexities in handling overlapping schedules and time zones.\n##### External Tools Required\nCalendar Integration APIs (Google Calendar, Outlook).\n##### Priority: CRITICAL\n#### Invoice Management\n##### Description\nGenerates and manages invoices post-appointment, with tracking for paid, unpaid, and failed transactions.\n##### Considerations\nTemplate customization, automated follow-up for unpaid invoices, integration with payment gateways.\n##### Risks\nMaintaining up-to-date financial records requires consistent system availability.\n##### External Tools Required\nPayment gateway APIs, financial tracking services.\n##### Priority: HIGH\n#### Role-Based Authorization\n##### Description\nManages access rights and functionalities for clients versus tutors, optimizing the user experience for each.\n##### Considerations\nDefining clear access levels, ensuring ease of navigation for both user types.\n##### Risks\nInadvertent access control misconfigurations could expose sensitive functionalities.\n##### External Tools Required\nN/A\n##### Priority: HIGH\n#### Financial Reporting\n##### Description\nFacilitates comprehensive financial reporting, including income summaries and report generation for different periods.\n##### Considerations\nUser-friendly data visualization, customization options for report types.\n##### Risks\nComplexity in managing accurate, real-time financial data.\n##### External Tools Required\nBusiness intelligence and reporting tools.\n##### Priority: MEDIUM\n\n### Clarifiying Questions\n- "Do we need a front end for this: "Human: Your task is to "The Tutor App is an app designed for tutors to manage their clients, schedules, and invoices. It must support both the client and tutor scheduling, rescheduling and canceling appointments, and sending invoices after the appointment has passed. Clients can sign up with OAuth2 or with traditional sign-in authentication. If they sign up with traditional authentication, it must be safe and secure. There will need to be password reset and login capabilities. There will need to be authorization for identifying clients vs the tutor. Additionally, it will have proper management of financials, including invoice management and payment tracking. This includes things like paid/failed invoice notifications, unpaid invoice follow-up, summarizing d/w/m/y income, and generating reports."": "Yes" : Reasoning: "The extensive feature set described, including user authentication, scheduling, financial management, and data visualization such as reports, strongly indicates the necessity of a front-end interface. This will allow both the clients and the tutor to interact with the system effectively. A front-end is essential for delivering these functionalities in a user-friendly manner, enabling users to navigate the application, manage appointments, and access financial records among other actions. Safely managing login and password reset features, alongside providing a clear, intuitive user interface for handling schedules and invoices, highlights the need for a front-end development segment in this project."\n- "Who is the expected user of this: "Human: Your task is to "The Tutor App is an app designed for tutors to manage their clients,\n schedules, and invoices.\n\nIt must support both the client and tutor scheduling, rescheduling and canceling\n appointments, and sending invoices after the appointment has passed.\n\nClients can sign up with OAuth2 or with traditional sign-in authentication. If they sign\n up with traditional authentication, it must be safe and secure. There will need to be\n password reset and login capabilities.\n\nThere will need to be authorization for identifying clients vs the tutor.\n\nAdditionally, it will have proper management of financials, including invoice management\n and payment tracking. This includes things like paid/failed invoice notifications,\n unpaid invoice follow-up, summarizing d/w/m/y income, and generating reports."": "Tutors and their clients" : Reasoning: "The question explicitly describes the Tutor App as designed for tutors to manage their clients, schedules, and invoices, implying tutors are a primary user persona. It details functionalities such as scheduling, rescheduling, and canceling appointments, and sending invoices, which are actions performed by tutors to organize their workload and manage their business operations. Moreover, it mentions clients can sign up and authenticate, suggesting they also interact with the app for scheduling and managing appointments with their tutors. Thus, both tutors and their clients are the expected users, with tutors likely being the primary users given the app\'s focus on managing multiple aspects of tutoring operations, while clients engage with the app to manage appointments and handle invoice payments."\n- "What is the skill level of the expected user of this: "Human: Your task is to "The Tutor App is an app designed for tutors to manage their clients, schedules, and invoices. It must support both the client and tutor scheduling, rescheduling and canceling appointments, and sending invoices after the appointment has passed. Clients can sign up with OAuth2 or with traditional sign-in authentication. If they sign up with traditional authentication, it must be safe and secure. There will need to be password reset and login capabilities. There will need to be authorization for identifying clients vs the tutor. Additionally, it will have proper management of financials, including invoice management and payment tracking. This includes things like paid/failed invoice notifications, unpaid invoice follow-up, summarizing d/w/m/y income, and generating reports."": "Intermediate" : Reasoning: "Considering the functionalities required for the Tutor App, it\'s designed to accommodate both tutors and their clients, necessitating a diverse skill set. Tutors, as primary users, will manage several operational aspects like scheduling, financials, and client interactions. This requires a moderate level of technological proficiency to navigate and utilize the app\'s features effectively. The clients, on the other hand, will use the app for its scheduling capabilities and to manage their appointments, invoice payments, and communications with tutors. These tasks also demand a reasonable level of digital literacy, though potentially less technical than that required of tutors. Thus, while the app should be user-friendly and intuitive, an intermediate level of skill and comfort with technology can be expected from its user base. This encompasses the ability to interact with a digital UI, understand basic digital security practices for sign-in, and manage appointments and financial transactions through the app."\n\n\n### Conclusive Q&A\n- "What platforms will the Tutor App be developed for (Web, iOS, Android, etc.)?": "Start with a web application to ensure broad accessibility, then evaluate the need and resources for extending to mobile platforms based on user engagement and feedback." : Reasoning: "The choice of platform directly influences the technology stack, design considerations, and development process. Knowing if it\'s a mobile, web app, or both will help in selecting the right tools and technologies."\n- "Are there any specific third-party services or APIs that should be integrated for features like OAuth2 authentication, invoice management, or financial tracking?": "We will prioritize integrating with well-documented, widely used services that meet our technical requirements and budget, starting with popular OAuth2 providers and financial services with extensive API support." : Reasoning: "Integration with existing services can speed up development and enhance security. Especially for sensitive operations like authentication and financial management, leveraging proven solutions is prudent."\n- "How should the app handle data privacy and security, especially regarding client-tutor communications, financial transactions, and personal information?": "We\'ll adhere to industry best practices and legal requirements for data security and privacy, incorporating advanced encryption, secure cloud services, and regular security assessments." : Reasoning: "Data privacy and security are paramount, considering the app handles sensitive personal and financial information. We need to understand regulatory requirements and best practices to ensure compliance and user trust."\n- "What level of customization will tutors have over their scheduling system and financial reporting?": "The app will offer essential customization options around scheduling, notifications, and financial reporting, focusing on simplicity and enhancing user experience." : Reasoning: "Tutors might have diverse needs based on their teaching scale, subjects, and personal preferences. Offering some degree of customization could enhance the app\'s usability and appeal."\n- "Should the app include features for direct communication between tutors and clients within the app?": "Implementing secure, encrypted in-app communications could enhance user experience and app engagement, provided it meets user needs and complies with data protection standards." : Reasoning: "In-app communication can streamline organization and understanding between tutors and clients, potentially improving the service quality but requires careful consideration of privacy and security protocols."\n- "How detailed should the financial management and reporting features be? Is there a need for integration with accounting software?": "Focus on delivering fundamental financial tracking and reporting capabilities initially. Consider accounting software integration as a value-added feature based on user demand." : Reasoning: "While robust financial management features are crucial for tutors, the complexity and scope should align with their needs. Accounting software integration could add value but also complexity."\n- "What type of payment methods will be supported for invoice payments? And will the app process payments directly?": "We will integrate with reliable payment gateways to support essential payment methods, focusing on security, user convenience, and compliance with financial regulations." : Reasoning: "Providing multiple payment methods can enhance convenience for clients, but it raises questions about payment processing, security, and fees."\n- "Will there be different levels of access or dashboards for tutors and clients within the app?": "Distinct, role-based dashboards will be developed for tutors and clients, prioritizing ease of use and relevant functionalities for each group." : Reasoning: "Creating distinct experiences for tutors and clients is vital for usability. Understanding their unique needs will guide the features and access levels each should have."\n- "How will the app handle scheduling conflicts and availability updates in real-time?": "The app will use real-time data handling and notifications to manage schedules and conflicts efficiently, ensuring a user-friendly experience." : Reasoning: "An efficient scheduling system is crucial for an app like this. It must flawlessly handle real-time updates and conflicts to ensure reliability and user satisfaction."\n- "What metrics and data visualization options should be included in the app for tracking tutoring performance and financial health?": "The app will offer intuitive data visualization features focusing on key performance and financial metrics, with the flexibility to evolve based on user feedback." : Reasoning: "Data visualization can significantly enhance the app\'s value, offering tutors actionable insights into their teaching and financial status. Determining the most useful metrics is key."\n\n\n### Requirement Q&A\n- "do we need db?": "Yes" : Reasoning: "Given the app requires managing large amounts of dynamic data such as user profiles, schedules, invoices, and communications, a database is essential for storing and retrieving this information efficiently."\n- "do we need an api for talking to a front end?": "Yes" : Reasoning: "To facilitate communication between the front-end interface where users interact and the back-end systems that process data, an API is necessary. This ensures a decoupled architecture, enhancing maintainability and scalability."\n- "do we need an api for talking to other services?": "Yes" : Reasoning: "Considering integration with external services like OAuth2 providers for authentication and financial services for invoice management and payments, an API for communication with these services is required."\n- "do we need an api for other services talking to us?": "Yes" : Reasoning: "For functionalities like receiving notifications from payment gateways about payment statuses or integrating with external calendar services, an API that allows other services to communicate with our app is necessary."\n- "do we need to issue api keys for other services to talk to us?": "Yes" : Reasoning: "To secure and control access when external services communicate with our app, issuing API keys is a method to authenticate these services and safeguard against unauthorized access."\n- "do we need monitoring?": "Yes" : Reasoning: "Monitoring is critical for maintaining the app\'s reliability and performance, providing insights into system health, user activities, and potential security threats. It supports proactive issue resolution and optimization."\n- "do we need internationalization?": "Yes" : Reasoning: "Given the app could potentially serve tutors and clients across different regions, internationalization would enable the app to support multiple languages and regional settings, broadening its accessibility and usability."\n- "do we need analytics?": "Yes" : Reasoning: "Analytics are essential for understanding user behavior, app performance, and financial metrics. They support informed decision-making regarding app improvements, feature prioritization, and business strategy."\n- "is there monetization?": "Yes" : Reasoning: "Considering the app provides value-added services such as managing tutoring businesses, financial tracking, and client scheduling, a monetization strategy is warranted to generate revenue and support ongoing development."\n- "is the monetization via a paywall or ads?": "Paywall" : Reasoning: "A paywall aligns better with the app\'s value proposition, allowing access to premium features or functionalities, compared to ads which could detract from the user experience."\n- "does this require a subscription or a one-time purchase?": "Subscription" : Reasoning: "A subscription model suits the app\'s ongoing provision of services, updates, and support, ensuring a steady revenue stream while continuously providing value to users."\n- "is the whole service monetized or only part?": "Part" : Reasoning: "Partially monetizing the service by offering both free and premium features could increase user adoption and satisfaction, allowing users to explore basic functionalities before committing to paid upgrades."\n- "is monetization implemented through authorization?": "Yes" : Reasoning: "Implementing monetization through authorization mechanisms ensures that only subscribed or paid users can access premium features, aligning with the part-monetization strategy."\n- "do we need authentication?": "Yes" : Reasoning: "Authentication is crucial for verifying user identity, supporting secure logins, and personalizing user experiences based on roles like tutor or client, especially given the handling of sensitive data."\n- "do we need authorization?": "Yes" : Reasoning: "Authorization is required to effectively separate access levels and permissions between tutors and clients, ensuring users can only access and perform actions relevant to their roles."\n- "what authorization roles do we need?": "["Tutor", "Client"]" : Reasoning: "Considering the app\'s user base and functionality, we need to define roles that differentiate the app\'s core users and their permissions, specifically separating the functionalities available to tutors and their clients."\n\n\n### Requirements\n### Functional Requirements\n#### User Authentication\n##### Thoughts\nGiven the emphasis on security and user convenience, offering multiple, robust authentication methods is critical.\n##### Description\nProvide a secure authentication mechanism for users, including support for OAuth2 and traditional login methods, along with password recovery functionalities.\n#### Scheduling and Appointment Management\n##### Thoughts\nAs a core feature, efficient and intuitive scheduling functionality will directly impact user satisfaction and app usability.\n##### Description\nEnable users (both tutors and clients) to schedule, reschedule, and cancel appointments with immediate effect and notification, including support for calendar integration.\n#### Invoice Management\n##### Thoughts\nEnsuring financial transactions are transparent and easily managed will enhance trust and streamline operations for tutors.\n##### Description\nAutomate invoice generation following appointments, track invoice payment statuses (paid, unpaid, failed), and support for payment reminders.\n#### Role-Based Authorization\n##### Thoughts\nDifferentiating user experiences based on role will optimize usability and ensure users can access relevant functionalities effortlessly.\n##### Description\nImplement distinct access rights for tutors and clients, providing a personalized user experience based on the role.\n#### Financial Reporting\n##### Thoughts\nEnabling tutors to gain insights into their financial health is key for the business aspect of tutoring operations.\n##### Description\nOffer comprehensive financial reporting functionalities, including income summaries, payment statuses, and custom report generation for selected periods.\n#### Data Privacy and Security\n##### Thoughts\nGiven the handling of sensitive information, maintaining high standards of data privacy and security is non-negotiable.\n##### Description\nEnsure all user data, including personal information, communication, and financial transactions, are securely stored and transferred.\n#### Real-Time Updates and Notifications\n##### Thoughts\nTimeliness of information, especially concerning scheduling and financial notifications, is critical for the effectiveness of the app.\n##### Description\nImplement real-time updates for schedules and any changes therein. Include a system for automated notifications for appointments, invoices, and financial reports to users.\n\n### Nonfunctional Requirements\n#### Security Compliance\n##### Thoughts\nSecurity is a cornerstone of user trust, especially when handling personal and financial information.\n##### Description\nThe application must comply with current data protection and privacy laws, incorporating advanced encryption for data in transit and at rest.\n#### Usability\n##### Thoughts\nConsidering the varied skill levels of the user base, ensuring the platform is easily navigable is paramount.\n##### Description\nDesign a user-friendly interface that accommodates users with an intermediate level of technical skill. The interface should be intuitive, providing efficient access to all functionalities.\n#### Performance and Scalability\n##### Thoughts\nTo support a growing user base and maintain a seamless user experience, the system must be scalable and performant.\n##### Description\nEnsure the app performs efficiently under varying loads, with quick response times and the capacity to scale resources based on user demand.\n#### Device and Browser Compatibility\n##### Thoughts\nAccessibility across devices and browsers expands the app’s reach and ensures inclusivity of users.\n##### Description\nThe web application must be compatible across major browsers and responsive to different screen sizes, optimizing for both desktop and mobile viewing.\n#### Reliability\n##### Thoughts\nThe app\'s reliability directly influences user satisfaction and trust, critical for a service-oriented platform.\n##### Description\nAchieve high system availability, with robust error handling and minimal downtime, to ensure users can trust and rely on the service.\n#### Maintainability and Support\n##### Thoughts\nMaintainability ensures the application can evolve without prohibitive costs, and support is crucial for ongoing user engagement.\n##### Description\nAdopt coding best practices to ensure the application is maintainable. Additionally, provide timely support and updates based on user feedback and technological advancements.\n\n\n### Modules\n### Module: Authentication Module\n#### Description\nCentralizes user authentication logic, including OAuth2 and traditional login mechanisms, ensuring secure user access. This module will manage user sessions, handle password recovery, and safeguard routes with role-based access controls. The initiation of user authentication flows, the verification of credentials, and the generation and validation of tokens are key functionalities. By consolidating authentication responsibilities, the module supports a coherent security posture across the application.\n\n### Module: User Management Module\n#### Description\nResponsible for managing user profiles, including creation, update, and retrieval of tutor and client information. It serves as a central point for user data management, ensuring data integrity and providing a unified interface for user-related operations. This module plays a crucial role in maintaining a clean separation between user authentication (handled by the Authentication Module) and user data management, facilitating easier maintenance and enhancement of user-related functionalities.\n\n### Module: Scheduling Module\n#### Description\nHandles the creation, modification, and cancellation of appointments between tutors and clients. It encompasses functionalities such as calendar integration, real-time availability tracking, and conflict resolution to ensure a smooth scheduling process. The Scheduling Module interactively supports user-driven appointment management, promotes efficient time allocation, and mitigates scheduling conflicts, thereby enhancing the overall user experience.\n\n### Module: Invoice Management Module\n#### Description\nFacilitates invoice creation post-appointment, tracks payment statuses, and supports payment reminders. It automates financial transactions related to tutoring services, offering insights into pending, paid, and failed payments. This module streamlines financial operations for tutors, reducing administrative overhead and enabling a focus on core tutoring activities. Integrating with payment gateways and providing detailed financial reports are pivotal features.\n\n### Module: Financial Reporting Module\n#### Description\nProvides tutors with comprehensive insights into their financial performance through detailed reports and summaries of income over selectable periods. It aggregates transaction data from the Invoice Management Module to offer clarity on financial health, supporting informed decision-making for tutors. Customization options for report generation cater to diverse tutoring operations, aiding in the meticulous management of tutoring finances.\n\n### Module: Notification Module\n#### Description\nCentral hub for dispatching real-time notifications and updates to users concerning appointments, invoice statuses, and system alerts. It enhances communication efficiency within the application by automatically notifying tutors and clients about important events, such as upcoming appointments or payment confirmations. Leveraging event-driven architecture, the Notification Module ensures timely and relevant information delivery, fostering an engaged and informed user base.\n\n### Database Design\nDatabase Not Yet Generated""",
        "needed_auth_roles": ["Tutor", "Client"],
        "modules": "Authentication Module, User Management Module, Scheduling Module, Invoice Management Module, Financial Reporting Module, Notification Module",
    }

    database_block = DatabaseGenerationBlock()

    async def run_ai() -> dict[str, DBResponse]:
        await db_client.connect()
        database: DBResponse = await database_block.invoke(
            ids=ids,
            invoke_params={
                "product_spec": obj["product_spec"],
                "needed_auth_roles": obj["needed_auth_roles"],
                "modules": obj["modules"],
            },
        )

        await db_client.disconnect()
        return {
            "database": database,
        }

    modules = run(run_ai())

    for key, item in modules.items():
        if isinstance(item, DBResponse):
            logger.info(f"ModuleResponse {key}")
            logger.info(f"\tThought General: {item.think}")
            logger.info(f"\tThought Anti: {item.anti_think}")
            logger.info(f"\tPlan: {item.plan}")
            logger.info(f"\tRefine: {item.refine}")
            logger.info(f"\tPre Answer: {item.pre_answer}")
            logger.info(f"\tPre Answer Issues: {item.pre_answer_issues}")
            logger.info(f"\tFull Schema: {item.full_schema}")
            logger.info(f"\tConclusions: {item.conclusions}")

            enums: list[DatabaseEnums] = item.database_schema.enums
            for e in enums:
                logger.info(f"\t\tEnum Name: {e.name}")
                logger.info(f"\t\tEnum Values: {e.values}")
                logger.info(f"\t\tEnum Description: {e.description}")
                logger.info(f"\t\tEnum Definition: {e.definition}")
            tables: list[DatabaseTable] = item.database_schema.tables
            for t in tables:
                logger.info(f"\t\tTable Name: {t.name}")
                logger.info(f"\t\tTable Definition: {t.definition}")
                logger.info(f"\t\tTable Description: {t.description}")

        else:
            logger.info("????")
            breakpoint()

    # # If you want to test the block in an interactive environment
    # import IPython

    # IPython.embed()
    breakpoint()
