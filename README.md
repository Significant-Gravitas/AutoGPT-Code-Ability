<p align="center">
    <img src="docs/codex.png" alt="Image Description" width="300">
</p>

## Introduction

The Codex System is an innovative coding agent designed to streamline the software development process. It consists of four key sub-agents, each specialized in a different aspect of software development. These sub-agents work in harmony to ensure efficient and effective delivery of software applications. This README provides an overview of the Codex System and its components.

## Components of Codex

The Codex System is an advanced software development framework comprised of various specialized sub-agents and components. Each component plays a critical role in the software development lifecycle, from conception to deployment. In addition to the primary sub-agents, the Codex System includes essential supportive components: the Common Module, Chains Module, and Prompts Module.

1. **Design (Product Owner)**: This component is pivotal in understanding and defining the product requirements. It acts as a bridge between the client's needs and the technical team, ensuring that the developed software aligns perfectly with the client's vision.

2. **Architect (Solutions Architect)**: Responsible for crafting the overall architecture of the application. This component breaks down the application into manageable modules and writes the templates that guide the development process.

3. **Coding (Junior Developer)**: The hands-on coding component. Utilizing the templates and guidelines provided by the Architect, the Coding sub-agent is responsible for writing the individual functions and pieces of the application.

4. **Delivery (Deployment Agent)**: The final phase of the software development process, this component is tasked with compiling, packaging, and deploying the completed application, ensuring its successful deployment to the designated environment.

5. **Common Module**: A fundamental component used across all stages of development. It provides shared functionalities and resources, such as libraries and tools, that are essential for the Design, Architect, Coding, and Delivery modules. This module ensures consistency and efficiency in the development process.

6. **Chains Module**: A specialized component used by all sub-agents for making Language Learning Model (LLM) calls. The Chains Module contains a seperate file for each llm call. The file must include loading the prompt templates, configuring the prompt, calling the llm, validation of resposne and retry logic.

7. **Prompts**: This component works closely with the Chains Module to generate and manage prompts for LLM interactions. It holds all the prompt templates allowing us to easily itterate prompt design without needing to modify the code.

## Mermaid Diagram

Below is a Mermaid diagram illustrating the structure of the Codex System and the interaction between its components:

```mermaid
erDiagram
    CODEX ||--o{ DESIGN : includes
    CODEX ||--o{ ARCHITECT : includes
    CODEX ||--o{ CODING : includes
    CODEX ||--o{ DELIVERY : includes
    DESIGN ||--|| COMMON-MODULE : uses
    ARCHITECT ||--|| COMMON-MODULE : uses
    CODING ||--|| COMMON-MODULE : uses
    DELIVERY ||--|| COMMON-MODULE : uses
    DESIGN ||--|| CHAINS-MODULE : "uses for LLM calls"
    ARCHITECT ||--|| CHAINS-MODULE : "uses for LLM calls"
    CODING ||--|| CHAINS-MODULE : "uses for LLM calls"
    DELIVERY ||--|| CHAINS-MODULE : "uses for LLM calls"
    DESIGN ||--|| ARCHITECT : "defines requirements for"
    ARCHITECT ||--|| CODING : "architects solution for"
    CODING ||--|| DELIVERY : "develops code for"
    DELIVERY ||--o{ CODEX : "deploys application to"
    CHAINS-MODULE ||--|| PROMPTS : "manges all prompt templates"

    CODEX {
        string name
    }
    DESIGN {
        string role "Product Owner"
    }
    ARCHITECT {
        string role "Solutions Architect"
    }
    CODING {
        string role "Junior Developer"
    }
    DELIVERY {
        string role "Build Engineer"
    }
    COMMON-MODULE {
        string function
    }
    CHAINS-MODULE {
        string purpose "LLM Calls"
    }
    PROMPTS {
        string purpose "Prompt Templates"
    }

```

## Workflow

1. **Requirement Analysis**: The Design sub-agent interacts with the client to gather and define the product requirements.

2. **Architecture Design**: Based on the requirements, the Architect sub-agent develops a solution architecture, breaking down the application into smaller, manageable modules and creating templates.

3. **Development**: The Coding sub-agent uses the templates and architecture guidelines to write the actual code for each module of the application.

4. **Deployment**: Once the coding is complete, the Delivery sub-agent takes over to package, compile, and deploy the application to the desired environment.


```mermaid
sequenceDiagram
    participant User
    participant Design
    participant Architect
    participant Coding
    participant Delivery

    User->>+Design: Request
    Design->>+User: Initial Requirements
    User->>+Design: Feedback/Corrections
    Design->>+Architect: Refined Requirements
    Architect->>+Coding: Architecture & Templates
    loop Development Iterations
        Coding->>+Architect: Request Clarification
        Architect->>+Coding: Additional Details
    end
    Coding->>+Delivery: Completed Code
    Delivery->>+User: Deploy to Production
```


##  Database Schema

The schema revolves around key models:

- CodeGraph: Represents the logic and structure of code as graphs, linked to function definitions and database schemas.
- FunctionDefinition: Defines individual functions with details like input/output types, tied to specific CodeGraphs.
- CompiledRoute: Transforms CodeGraphs into executable routes, integral for the application's runtime.
- Application: The aggregate entity that combines multiple CompiledRoutes into a complete application.
- Functions and Package: Detail the executable elements and dependencies within the application.
- DatabaseSchema and DatabaseTable: Manage database interactions within the generated code, facilitating data-driven functionalities.

This schema is pivotal for automating code generation, from defining logic in CodeGraphs to the final application assembly, enhancing our application's efficiency and scalability.

```mermaid
erDiagram

    Application ||--o{ CompiledRoute : "compiledRoutes"
    CompiledRoute ||--o{ Functions : "functions"
    CompiledRoute ||--o{ Application : "applications"
    CompiledRoute }o--|| CodeGraph : "codeGraph"
    CodeGraph ||--o{ FunctionDefinition : "functionDefs"
    CodeGraph ||--o{ CompiledRoute : "compiledRoute"
    CodeGraph }o--|| DatabaseSchema : "databaseSchema"
    FunctionDefinition }o--|| CodeGraph : "codeGraph"
    FunctionDefinition }o--|| Functions : "function"
    Functions ||--o{ FunctionDefinition : "functionDefs"
    Functions ||--o{ Package : "packages"
    Functions ||--o{ CompiledRoute : "compiledRoutes"
    Package ||--o{ Functions : "functions"
    DatabaseSchema ||--o{ DatabaseTable : "tables"
    DatabaseSchema ||--o{ CodeGraph : "codeGraphs"
    DatabaseTable ||--o{ DatabaseSchema : "schemas"
    DatabaseTable }o--o{ DatabaseTable : "relatedFromTables"
    DatabaseTable }o--o{ DatabaseTable : "relatedToTables"

    Application {
        int id PK "Primary Key"
        datetime createdAt "Creation Date"
        string name "Application Name"
        string description "Description"
    }

    CompiledRoute {
        int id PK "Primary Key"
        datetime createdAt "Creation Date"
        string embedding "Embedding (Unsupported)"
        string description "Description"
        string code "Code"
        int codeGraphId FK "Foreign Key to CodeGraph"
    }

    CodeGraph {
        int id PK "Primary Key"
        datetime createdAt "Creation Date"
        string function_name "Function Name"
        string api_route "API Route"
        string graph "Graph Representation"
        int databaseSchemaId FK "Foreign Key to DatabaseSchema"
    }

    FunctionDefinition {
        int id PK "Primary Key"
        datetime createdAt "Creation Date"
        string name "Function Name"
        string description "Description"
        string input_type "Input Type"
        string return_type "Return Type"
        int codeGraphId FK "Foreign Key to CodeGraph"
        string functionId FK "Foreign Key to Functions"
    }

    Functions {
        string id PK "Primary Key"
        datetime createdAt "Creation Date"
        string embedding "Embedding (Unsupported)"
        string name "Function Name"
        string description "Description"
        string input_type "Input Type"
        string return_type "Return Type"
        string code "Code"
    }

    Package {
        string id PK "Primary Key"
        datetime createdAt "Creation Date"
        string packageName "Package Name"
        string version "Version"
        string specifier "Specifier"
    }

    DatabaseSchema {
        int id PK "Primary Key"
        datetime createdAt "Creation Date"
        string embedding "Embedding (Unsupported)"
        string description "Description"
    }

    DatabaseTable {
        int id PK "Primary Key"
        datetime createdAt "Creation Date"
        string embedding "Embedding (Unsupported)"
        string description "Description"
        string definition "Definition"
    }
```

## Useful commands 
> docker buildx build --platform linux/amd64 -t gcr.io/agpt-dev/mvp/codegen . --push


## Prisma with Python: Quick Setup and Usage Guide

Prisma is an open-source database toolkit that simplifies database access and management. Although Prisma is traditionally associated with JavaScript and TypeScript, it can also be integrated with Python projects. This section of the README provides a quick cheat sheet for setting up Prisma in a Python environment, applying migrations, and other useful tips.

### 1. Setting Up Prisma

#### Prerequisites:
- Node.js installed (for Prisma CLI)
- Python environment setup

#### Steps:

1. **Install Prisma CLI**:
   - Use npm to install Prisma globally:
     ```bash
     npm install -g prisma
     ```

2. **Initialize Prisma in Your Project**:
   - Navigate to your Python project directory and initialize Prisma:
     ```bash
     prisma init
     ```
   - This command creates a new `prisma` directory with a default `schema.prisma` file.

3. **Configure Your Database**:
   - In `schema.prisma`, configure the `datasource` block to point to your database. For example, for PostgreSQL:
     ```prisma
     datasource db {
       provider = "postgresql"
       url      = env("DATABASE_URL")
     }
     ```
   - Replace `DATABASE_URL` with your database connection string.

### 2. Defining Your Data Model

- In the `schema.prisma` file, define your data models. For example:
  ```prisma
  model User {
    id    Int     @id @default(autoincrement())
    name  String
    email String  @unique
  }
  ```

### 3. Migrations

#### Creating Migrations:

- After defining your models, create a migration to update the database schema:
  ```bash
  prisma migrate dev --name init
  ```
- This command creates SQL files in the `prisma/migrations` directory.

#### Applying Migrations:

- Apply migrations to update your database schema:
  ```bash
  prisma migrate deploy
  ```

### 4. Generating Prisma Client

- Generate Prisma Client to interact with your database:
  ```bash
  prisma generate
  ```

### 5. Using Prisma with Python

- Since Prisma Client is native to JavaScript/TypeScript, using it in Python requires a workaround. You can execute Prisma Client through a child process. For example:
  ```python
  import subprocess
  import json

  def run_prisma_command(command):
      result = subprocess.run(["npx", "prisma", *command], capture_output=True)
      return json.loads(result.stdout)

  users = run_prisma_command(["query", "user", "--all"])
  print(users)
  ```

### 6. Useful Commands

- **Introspect Database**: To update your Prisma schema based on an existing database:
  ```bash
  prisma introspect
  ```
- **Studio**: Prisma Studio provides a GUI to view and edit data in your database:
  ```bash
  prisma studio
  ```

### Conclusion

This cheat sheet covers the basics of setting up Prisma in a Python project and performing essential database operations. Remember that using Prisma with Python is less straightforward than with JavaScript/TypeScript, and it may require additional setup and handling. For more detailed information, refer to the [Prisma Documentation](https://www.prisma.io/docs/).