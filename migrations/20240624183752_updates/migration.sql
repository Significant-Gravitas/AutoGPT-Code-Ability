-- CreateExtension
CREATE EXTENSION IF NOT EXISTS "vector";

-- CreateEnum
CREATE TYPE "Role" AS ENUM ('USER', 'ADMIN');

-- CreateEnum
CREATE TYPE "InterviewPhase" AS ENUM ('FEATURES', 'ARCHITECT', 'COMPLETED');

-- CreateEnum
CREATE TYPE "AccessLevel" AS ENUM ('PUBLIC', 'PROTECTED');

-- CreateEnum
CREATE TYPE "HTTPVerb" AS ENUM ('GET', 'POST', 'PUT', 'PATCH', 'DELETE', 'OPTIONS', 'HEAD', 'CONNECT', 'TRACE');

-- CreateEnum
CREATE TYPE "FunctionState" AS ENUM ('DEFINITION', 'WRITTEN', 'VERIFIED', 'FAILED');

-- CreateEnum
CREATE TYPE "DevelopmentPhase" AS ENUM ('REQUIREMENTS', 'DEVELOPMENT', 'DEPLOYMENT');

-- CreateEnum
CREATE TYPE "Status" AS ENUM ('STARTED', 'SUCCESS', 'FAILED');

-- CreateTable
CREATE TABLE "User" (
    "id" TEXT NOT NULL DEFAULT gen_random_uuid(),
    "cloudServicesId" TEXT NOT NULL,
    "discordId" TEXT NOT NULL,
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" TIMESTAMP(3) NOT NULL,
    "lastSeen" TIMESTAMP(3),
    "role" "Role" NOT NULL DEFAULT 'USER',
    "deleted" BOOLEAN NOT NULL DEFAULT false,

    CONSTRAINT "User_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "Application" (
    "id" TEXT NOT NULL DEFAULT gen_random_uuid(),
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" TIMESTAMP(3) NOT NULL,
    "name" TEXT NOT NULL,
    "description" TEXT,
    "deleted" BOOLEAN NOT NULL DEFAULT false,
    "userId" TEXT,

    CONSTRAINT "Application_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "Interview" (
    "id" TEXT NOT NULL DEFAULT gen_random_uuid(),
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" TIMESTAMP(3) NOT NULL,
    "deleted" BOOLEAN NOT NULL DEFAULT false,
    "finished" BOOLEAN NOT NULL DEFAULT false,
    "name" TEXT NOT NULL,
    "task" TEXT NOT NULL,
    "userId" TEXT NOT NULL,
    "applicationId" TEXT NOT NULL,

    CONSTRAINT "Interview_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "InterviewStep" (
    "id" TEXT NOT NULL DEFAULT gen_random_uuid(),
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" TIMESTAMP(3) NOT NULL,
    "deleted" BOOLEAN NOT NULL DEFAULT false,
    "phase" "InterviewPhase" NOT NULL DEFAULT 'FEATURES',
    "phase_complete" BOOLEAN NOT NULL DEFAULT false,
    "say" TEXT NOT NULL,
    "thoughts" TEXT NOT NULL,
    "access_roles" TEXT[],
    "interviewId" TEXT NOT NULL,
    "applicationId" TEXT NOT NULL,

    CONSTRAINT "InterviewStep_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "Question" (
    "id" TEXT NOT NULL DEFAULT gen_random_uuid(),
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" TIMESTAMP(3) NOT NULL,
    "deleted" BOOLEAN NOT NULL DEFAULT false,
    "name" TEXT NOT NULL DEFAULT '',
    "reasoning" TEXT NOT NULL DEFAULT '',
    "functionality" TEXT NOT NULL DEFAULT '',
    "interviewStepId" TEXT,
    "specificationId" TEXT,

    CONSTRAINT "Question_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "Specification" (
    "id" TEXT NOT NULL DEFAULT gen_random_uuid(),
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" TIMESTAMP(3) NOT NULL,
    "deleted" BOOLEAN NOT NULL DEFAULT false,
    "userId" TEXT,
    "interviewId" TEXT,
    "applicationId" TEXT,
    "databaseSchemaId" TEXT,

    CONSTRAINT "Specification_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "Module" (
    "id" TEXT NOT NULL DEFAULT gen_random_uuid(),
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" TIMESTAMP(3) NOT NULL,
    "deleted" BOOLEAN NOT NULL DEFAULT false,
    "name" TEXT NOT NULL,
    "description" TEXT NOT NULL,
    "interactions" TEXT NOT NULL,
    "applicationId" TEXT,
    "userId" TEXT,
    "specificationId" TEXT,
    "interviewStepId" TEXT,

    CONSTRAINT "Module_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "APIRouteSpec" (
    "id" TEXT NOT NULL DEFAULT gen_random_uuid(),
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "functionName" TEXT NOT NULL,
    "method" "HTTPVerb" NOT NULL,
    "path" TEXT NOT NULL,
    "description" TEXT NOT NULL,
    "AccessLevel" "AccessLevel",
    "AllowedAccessRoles" TEXT[],
    "moduleId" TEXT,
    "responseObjectId" TEXT,
    "requestObjectId" TEXT,

    CONSTRAINT "APIRouteSpec_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "ObjectType" (
    "id" TEXT NOT NULL DEFAULT gen_random_uuid(),
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "name" TEXT NOT NULL,
    "description" TEXT,
    "code" TEXT,
    "isPydantic" BOOLEAN NOT NULL DEFAULT true,
    "isEnum" BOOLEAN NOT NULL DEFAULT false,
    "importStatements" TEXT[],
    "databaseTableId" TEXT,

    CONSTRAINT "ObjectType_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "ObjectField" (
    "id" TEXT NOT NULL DEFAULT gen_random_uuid(),
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "name" TEXT NOT NULL,
    "description" TEXT,
    "value" TEXT,
    "typeName" TEXT NOT NULL,
    "referredObjectTypeId" TEXT,

    CONSTRAINT "ObjectField_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "DatabaseSchema" (
    "id" TEXT NOT NULL DEFAULT gen_random_uuid(),
    "name" TEXT,
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "embedding" vector(1536),
    "description" TEXT NOT NULL,

    CONSTRAINT "DatabaseSchema_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "DatabaseTable" (
    "id" TEXT NOT NULL DEFAULT gen_random_uuid(),
    "name" TEXT,
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "embedding" vector(1536),
    "description" TEXT NOT NULL,
    "definition" TEXT NOT NULL,
    "isEnum" BOOLEAN NOT NULL DEFAULT false,
    "databaseSchemaId" TEXT,

    CONSTRAINT "DatabaseTable_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "Function" (
    "id" TEXT NOT NULL DEFAULT gen_random_uuid(),
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" TIMESTAMP(3) NOT NULL,
    "functionName" TEXT NOT NULL,
    "description" TEXT,
    "template" TEXT NOT NULL,
    "state" "FunctionState" NOT NULL,
    "rawCode" TEXT,
    "importStatements" TEXT[],
    "functionCode" TEXT,
    "functionReturnObjectId" TEXT,
    "parentFunctionId" TEXT,
    "databaseSchemaId" TEXT,
    "compiledRouteId" TEXT,

    CONSTRAINT "Function_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "Package" (
    "id" TEXT NOT NULL DEFAULT gen_random_uuid(),
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "packageName" TEXT NOT NULL,
    "version" TEXT NOT NULL,
    "specifier" TEXT NOT NULL,

    CONSTRAINT "Package_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "CompiledRoute" (
    "id" TEXT NOT NULL DEFAULT gen_random_uuid(),
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "embedding" vector(1536),
    "description" TEXT NOT NULL,
    "fileName" TEXT NOT NULL,
    "mainFunctionName" TEXT NOT NULL,
    "compiledCode" TEXT NOT NULL,
    "completedAppId" TEXT NOT NULL,
    "rootFunctionId" TEXT NOT NULL,
    "apiRouteSpecId" TEXT,

    CONSTRAINT "CompiledRoute_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "CompletedApp" (
    "id" TEXT NOT NULL DEFAULT gen_random_uuid(),
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" TIMESTAMP(3) NOT NULL,
    "deleted" BOOLEAN NOT NULL DEFAULT false,
    "name" TEXT NOT NULL,
    "description" TEXT NOT NULL,
    "userId" TEXT,
    "specificationId" TEXT,
    "applicationId" TEXT,
    "companionCompletedAppId" TEXT,

    CONSTRAINT "CompletedApp_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "Deployment" (
    "id" TEXT NOT NULL DEFAULT gen_random_uuid(),
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" TIMESTAMP(3) NOT NULL,
    "deleted" BOOLEAN NOT NULL DEFAULT false,
    "fileName" TEXT,
    "fileSize" INTEGER,
    "path" TEXT,
    "fileBytes" BYTEA,
    "repo" TEXT,
    "dbName" TEXT,
    "dbUser" TEXT,
    "zipFile" BOOLEAN NOT NULL DEFAULT false,
    "githubRepo" BOOLEAN NOT NULL DEFAULT true,
    "hosted" BOOLEAN NOT NULL DEFAULT true,
    "userId" TEXT,
    "applicationId" TEXT,
    "completedAppId" TEXT,

    CONSTRAINT "Deployment_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "LLMCallTemplate" (
    "id" TEXT NOT NULL DEFAULT gen_random_uuid(),
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "developmentPhase" "DevelopmentPhase" NOT NULL,
    "templateName" TEXT NOT NULL,
    "model" TEXT NOT NULL,
    "fileHash" TEXT NOT NULL,
    "systemPrompt" TEXT NOT NULL,
    "userPrompt" TEXT NOT NULL,
    "retryPrompt" TEXT NOT NULL,

    CONSTRAINT "LLMCallTemplate_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "LLMCallAttempt" (
    "id" TEXT NOT NULL DEFAULT gen_random_uuid(),
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "model" TEXT NOT NULL,
    "completionTokens" INTEGER NOT NULL,
    "promptTokens" INTEGER NOT NULL,
    "totalTokens" INTEGER NOT NULL,
    "firstCallId" TEXT,
    "attempt" INTEGER NOT NULL,
    "prompt" JSONB NOT NULL,
    "response" TEXT NOT NULL,
    "userId" TEXT,
    "applicationId" TEXT,
    "interviewId" TEXT,
    "specificationId" TEXT,
    "compiledRouteId" TEXT,
    "functionId" TEXT,
    "completedAppId" TEXT,
    "deploymentId" TEXT,
    "llmCallTemplateId" TEXT,
    "interviewStepId" TEXT,

    CONSTRAINT "LLMCallAttempt_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "EventLog" (
    "id" TEXT NOT NULL DEFAULT gen_random_uuid(),
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "userId" TEXT,
    "applicationId" TEXT,
    "keyType" "DevelopmentPhase" NOT NULL,
    "keyValue" TEXT NOT NULL,
    "event" TEXT NOT NULL,
    "status" "Status" NOT NULL,
    "message" TEXT,

    CONSTRAINT "EventLog_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "_ObjectFieldTypes" (
    "A" TEXT NOT NULL,
    "B" TEXT NOT NULL
);

-- CreateTable
CREATE TABLE "_TableRelations" (
    "A" TEXT NOT NULL,
    "B" TEXT NOT NULL
);

-- CreateTable
CREATE TABLE "_FunctionToPackage" (
    "A" TEXT NOT NULL,
    "B" TEXT NOT NULL
);

-- CreateTable
CREATE TABLE "_FunctionArgs" (
    "A" TEXT NOT NULL,
    "B" TEXT NOT NULL
);

-- CreateTable
CREATE TABLE "_CompiledRouteToPackage" (
    "A" TEXT NOT NULL,
    "B" TEXT NOT NULL
);

-- CreateIndex
CREATE UNIQUE INDEX "User_cloudServicesId_key" ON "User"("cloudServicesId");

-- CreateIndex
CREATE UNIQUE INDEX "User_discordId_key" ON "User"("discordId");

-- CreateIndex
CREATE UNIQUE INDEX "CompiledRoute_rootFunctionId_key" ON "CompiledRoute"("rootFunctionId");

-- CreateIndex
CREATE UNIQUE INDEX "Deployment_repo_key" ON "Deployment"("repo");

-- CreateIndex
CREATE UNIQUE INDEX "Deployment_dbName_key" ON "Deployment"("dbName");

-- CreateIndex
CREATE UNIQUE INDEX "Deployment_dbUser_key" ON "Deployment"("dbUser");

-- CreateIndex
CREATE INDEX "EventLog_userId_applicationId_idx" ON "EventLog"("userId", "applicationId");

-- CreateIndex
CREATE INDEX "EventLog_keyValue_idx" ON "EventLog"("keyValue");

-- CreateIndex
CREATE UNIQUE INDEX "_ObjectFieldTypes_AB_unique" ON "_ObjectFieldTypes"("A", "B");

-- CreateIndex
CREATE INDEX "_ObjectFieldTypes_B_index" ON "_ObjectFieldTypes"("B");

-- CreateIndex
CREATE UNIQUE INDEX "_TableRelations_AB_unique" ON "_TableRelations"("A", "B");

-- CreateIndex
CREATE INDEX "_TableRelations_B_index" ON "_TableRelations"("B");

-- CreateIndex
CREATE UNIQUE INDEX "_FunctionToPackage_AB_unique" ON "_FunctionToPackage"("A", "B");

-- CreateIndex
CREATE INDEX "_FunctionToPackage_B_index" ON "_FunctionToPackage"("B");

-- CreateIndex
CREATE UNIQUE INDEX "_FunctionArgs_AB_unique" ON "_FunctionArgs"("A", "B");

-- CreateIndex
CREATE INDEX "_FunctionArgs_B_index" ON "_FunctionArgs"("B");

-- CreateIndex
CREATE UNIQUE INDEX "_CompiledRouteToPackage_AB_unique" ON "_CompiledRouteToPackage"("A", "B");

-- CreateIndex
CREATE INDEX "_CompiledRouteToPackage_B_index" ON "_CompiledRouteToPackage"("B");

-- AddForeignKey
ALTER TABLE "Application" ADD CONSTRAINT "Application_userId_fkey" FOREIGN KEY ("userId") REFERENCES "User"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "Interview" ADD CONSTRAINT "Interview_userId_fkey" FOREIGN KEY ("userId") REFERENCES "User"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "Interview" ADD CONSTRAINT "Interview_applicationId_fkey" FOREIGN KEY ("applicationId") REFERENCES "Application"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "InterviewStep" ADD CONSTRAINT "InterviewStep_interviewId_fkey" FOREIGN KEY ("interviewId") REFERENCES "Interview"("id") ON DELETE RESTRICT ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "InterviewStep" ADD CONSTRAINT "InterviewStep_applicationId_fkey" FOREIGN KEY ("applicationId") REFERENCES "Application"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "Question" ADD CONSTRAINT "Question_interviewStepId_fkey" FOREIGN KEY ("interviewStepId") REFERENCES "InterviewStep"("id") ON DELETE SET NULL ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "Question" ADD CONSTRAINT "Question_specificationId_fkey" FOREIGN KEY ("specificationId") REFERENCES "Specification"("id") ON DELETE SET NULL ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "Specification" ADD CONSTRAINT "Specification_userId_fkey" FOREIGN KEY ("userId") REFERENCES "User"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "Specification" ADD CONSTRAINT "Specification_interviewId_fkey" FOREIGN KEY ("interviewId") REFERENCES "Interview"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "Specification" ADD CONSTRAINT "Specification_applicationId_fkey" FOREIGN KEY ("applicationId") REFERENCES "Application"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "Specification" ADD CONSTRAINT "Specification_databaseSchemaId_fkey" FOREIGN KEY ("databaseSchemaId") REFERENCES "DatabaseSchema"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "Module" ADD CONSTRAINT "Module_applicationId_fkey" FOREIGN KEY ("applicationId") REFERENCES "Application"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "Module" ADD CONSTRAINT "Module_userId_fkey" FOREIGN KEY ("userId") REFERENCES "User"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "Module" ADD CONSTRAINT "Module_specificationId_fkey" FOREIGN KEY ("specificationId") REFERENCES "Specification"("id") ON DELETE SET NULL ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "Module" ADD CONSTRAINT "Module_interviewStepId_fkey" FOREIGN KEY ("interviewStepId") REFERENCES "InterviewStep"("id") ON DELETE SET NULL ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "APIRouteSpec" ADD CONSTRAINT "APIRouteSpec_moduleId_fkey" FOREIGN KEY ("moduleId") REFERENCES "Module"("id") ON DELETE SET NULL ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "APIRouteSpec" ADD CONSTRAINT "APIRouteSpec_responseObjectId_fkey" FOREIGN KEY ("responseObjectId") REFERENCES "ObjectType"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "APIRouteSpec" ADD CONSTRAINT "APIRouteSpec_requestObjectId_fkey" FOREIGN KEY ("requestObjectId") REFERENCES "ObjectType"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "ObjectType" ADD CONSTRAINT "ObjectType_databaseTableId_fkey" FOREIGN KEY ("databaseTableId") REFERENCES "DatabaseTable"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "ObjectField" ADD CONSTRAINT "ObjectField_referredObjectTypeId_fkey" FOREIGN KEY ("referredObjectTypeId") REFERENCES "ObjectType"("id") ON DELETE SET NULL ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "DatabaseTable" ADD CONSTRAINT "DatabaseTable_databaseSchemaId_fkey" FOREIGN KEY ("databaseSchemaId") REFERENCES "DatabaseSchema"("id") ON DELETE SET NULL ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "Function" ADD CONSTRAINT "Function_functionReturnObjectId_fkey" FOREIGN KEY ("functionReturnObjectId") REFERENCES "ObjectField"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "Function" ADD CONSTRAINT "Function_parentFunctionId_fkey" FOREIGN KEY ("parentFunctionId") REFERENCES "Function"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "Function" ADD CONSTRAINT "Function_databaseSchemaId_fkey" FOREIGN KEY ("databaseSchemaId") REFERENCES "DatabaseSchema"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "Function" ADD CONSTRAINT "Function_compiledRouteId_fkey" FOREIGN KEY ("compiledRouteId") REFERENCES "CompiledRoute"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "CompiledRoute" ADD CONSTRAINT "CompiledRoute_completedAppId_fkey" FOREIGN KEY ("completedAppId") REFERENCES "CompletedApp"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "CompiledRoute" ADD CONSTRAINT "CompiledRoute_rootFunctionId_fkey" FOREIGN KEY ("rootFunctionId") REFERENCES "Function"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "CompiledRoute" ADD CONSTRAINT "CompiledRoute_apiRouteSpecId_fkey" FOREIGN KEY ("apiRouteSpecId") REFERENCES "APIRouteSpec"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "CompletedApp" ADD CONSTRAINT "CompletedApp_userId_fkey" FOREIGN KEY ("userId") REFERENCES "User"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "CompletedApp" ADD CONSTRAINT "CompletedApp_specificationId_fkey" FOREIGN KEY ("specificationId") REFERENCES "Specification"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "CompletedApp" ADD CONSTRAINT "CompletedApp_applicationId_fkey" FOREIGN KEY ("applicationId") REFERENCES "Application"("id") ON DELETE SET NULL ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "Deployment" ADD CONSTRAINT "Deployment_userId_fkey" FOREIGN KEY ("userId") REFERENCES "User"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "Deployment" ADD CONSTRAINT "Deployment_applicationId_fkey" FOREIGN KEY ("applicationId") REFERENCES "Application"("id") ON DELETE SET NULL ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "Deployment" ADD CONSTRAINT "Deployment_completedAppId_fkey" FOREIGN KEY ("completedAppId") REFERENCES "CompletedApp"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "LLMCallAttempt" ADD CONSTRAINT "LLMCallAttempt_firstCallId_fkey" FOREIGN KEY ("firstCallId") REFERENCES "LLMCallAttempt"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "LLMCallAttempt" ADD CONSTRAINT "LLMCallAttempt_userId_fkey" FOREIGN KEY ("userId") REFERENCES "User"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "LLMCallAttempt" ADD CONSTRAINT "LLMCallAttempt_applicationId_fkey" FOREIGN KEY ("applicationId") REFERENCES "Application"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "LLMCallAttempt" ADD CONSTRAINT "LLMCallAttempt_interviewId_fkey" FOREIGN KEY ("interviewId") REFERENCES "Interview"("id") ON DELETE SET NULL ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "LLMCallAttempt" ADD CONSTRAINT "LLMCallAttempt_specificationId_fkey" FOREIGN KEY ("specificationId") REFERENCES "Specification"("id") ON DELETE SET NULL ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "LLMCallAttempt" ADD CONSTRAINT "LLMCallAttempt_compiledRouteId_fkey" FOREIGN KEY ("compiledRouteId") REFERENCES "CompiledRoute"("id") ON DELETE SET NULL ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "LLMCallAttempt" ADD CONSTRAINT "LLMCallAttempt_functionId_fkey" FOREIGN KEY ("functionId") REFERENCES "Function"("id") ON DELETE SET NULL ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "LLMCallAttempt" ADD CONSTRAINT "LLMCallAttempt_completedAppId_fkey" FOREIGN KEY ("completedAppId") REFERENCES "CompletedApp"("id") ON DELETE SET NULL ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "LLMCallAttempt" ADD CONSTRAINT "LLMCallAttempt_deploymentId_fkey" FOREIGN KEY ("deploymentId") REFERENCES "Deployment"("id") ON DELETE SET NULL ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "LLMCallAttempt" ADD CONSTRAINT "LLMCallAttempt_llmCallTemplateId_fkey" FOREIGN KEY ("llmCallTemplateId") REFERENCES "LLMCallTemplate"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "LLMCallAttempt" ADD CONSTRAINT "LLMCallAttempt_interviewStepId_fkey" FOREIGN KEY ("interviewStepId") REFERENCES "InterviewStep"("id") ON DELETE SET NULL ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "_ObjectFieldTypes" ADD CONSTRAINT "_ObjectFieldTypes_A_fkey" FOREIGN KEY ("A") REFERENCES "ObjectField"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "_ObjectFieldTypes" ADD CONSTRAINT "_ObjectFieldTypes_B_fkey" FOREIGN KEY ("B") REFERENCES "ObjectType"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "_TableRelations" ADD CONSTRAINT "_TableRelations_A_fkey" FOREIGN KEY ("A") REFERENCES "DatabaseTable"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "_TableRelations" ADD CONSTRAINT "_TableRelations_B_fkey" FOREIGN KEY ("B") REFERENCES "DatabaseTable"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "_FunctionToPackage" ADD CONSTRAINT "_FunctionToPackage_A_fkey" FOREIGN KEY ("A") REFERENCES "Function"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "_FunctionToPackage" ADD CONSTRAINT "_FunctionToPackage_B_fkey" FOREIGN KEY ("B") REFERENCES "Package"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "_FunctionArgs" ADD CONSTRAINT "_FunctionArgs_A_fkey" FOREIGN KEY ("A") REFERENCES "Function"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "_FunctionArgs" ADD CONSTRAINT "_FunctionArgs_B_fkey" FOREIGN KEY ("B") REFERENCES "ObjectField"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "_CompiledRouteToPackage" ADD CONSTRAINT "_CompiledRouteToPackage_A_fkey" FOREIGN KEY ("A") REFERENCES "CompiledRoute"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "_CompiledRouteToPackage" ADD CONSTRAINT "_CompiledRouteToPackage_B_fkey" FOREIGN KEY ("B") REFERENCES "Package"("id") ON DELETE CASCADE ON UPDATE CASCADE;
