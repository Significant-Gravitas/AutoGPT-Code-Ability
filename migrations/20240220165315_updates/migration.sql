-- CreateExtension
CREATE EXTENSION IF NOT EXISTS "vector";

-- CreateEnum
CREATE TYPE "Role" AS ENUM ('USER', 'ADMIN');

-- CreateEnum
CREATE TYPE "AccessLevel" AS ENUM ('PUBLIC', 'USER', 'ADMIN');

-- CreateEnum
CREATE TYPE "HTTPVerb" AS ENUM ('GET', 'POST', 'PUT', 'PATCH', 'DELETE', 'OPTIONS', 'HEAD', 'CONNECT', 'TRACE');

-- CreateTable
CREATE TABLE "User" (
    "id" TEXT NOT NULL DEFAULT gen_random_uuid(),
    "cloudServicesId" TEXT,
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
CREATE TABLE "Specification" (
    "id" TEXT NOT NULL DEFAULT gen_random_uuid(),
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" TIMESTAMP(3) NOT NULL,
    "deleted" BOOLEAN NOT NULL DEFAULT false,
    "name" TEXT NOT NULL,
    "context" TEXT NOT NULL,
    "userId" TEXT,
    "applicationId" TEXT,

    CONSTRAINT "Specification_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "APIRouteSpec" (
    "id" TEXT NOT NULL DEFAULT gen_random_uuid(),
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "functionName" TEXT NOT NULL,
    "method" "HTTPVerb" NOT NULL,
    "path" TEXT NOT NULL,
    "description" TEXT NOT NULL,
    "AccessLevel" "AccessLevel" NOT NULL,
    "specificationId" TEXT,
    "responseObjectId" TEXT,
    "requestObjectId" TEXT,
    "databaseSchemaId" TEXT,

    CONSTRAINT "APIRouteSpec_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "ResponseObject" (
    "id" TEXT NOT NULL DEFAULT gen_random_uuid(),
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "name" TEXT NOT NULL,
    "description" TEXT NOT NULL,

    CONSTRAINT "ResponseObject_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "RequestObject" (
    "id" TEXT NOT NULL DEFAULT gen_random_uuid(),
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "name" TEXT NOT NULL,
    "description" TEXT NOT NULL,

    CONSTRAINT "RequestObject_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "Param" (
    "id" TEXT NOT NULL DEFAULT gen_random_uuid(),
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "name" TEXT NOT NULL,
    "description" TEXT NOT NULL,
    "paramType" TEXT NOT NULL,
    "responseObjectId" TEXT,
    "requestObjectId" TEXT,

    CONSTRAINT "Param_pkey" PRIMARY KEY ("id")
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
    "databaseSchemaId" TEXT,

    CONSTRAINT "DatabaseTable_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "CodeGraph" (
    "id" TEXT NOT NULL DEFAULT gen_random_uuid(),
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "functionName" TEXT NOT NULL,
    "apiPath" TEXT NOT NULL,
    "imports" TEXT[],
    "codeGraph" TEXT NOT NULL,
    "apiRouteSpecId" TEXT,
    "databaseSchemaId" TEXT,
    "compiledRouteId" TEXT,

    CONSTRAINT "CodeGraph_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "FunctionDefinition" (
    "id" TEXT NOT NULL DEFAULT gen_random_uuid(),
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "name" TEXT NOT NULL,
    "docString" TEXT NOT NULL,
    "args" TEXT NOT NULL,
    "returnType" TEXT NOT NULL,
    "functionTemplate" TEXT NOT NULL,
    "codeGraphId" TEXT,
    "functionsId" TEXT,

    CONSTRAINT "FunctionDefinition_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "Function" (
    "id" TEXT NOT NULL DEFAULT gen_random_uuid(),
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "embedding" vector(1536),
    "name" TEXT NOT NULL,
    "docString" TEXT NOT NULL,
    "args" TEXT NOT NULL,
    "returnType" TEXT NOT NULL,
    "code" TEXT NOT NULL,

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
    "code" TEXT NOT NULL,
    "codeGraphId" TEXT NOT NULL,
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
    "specificationId" TEXT,

    CONSTRAINT "CompletedApp_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "Deployment" (
    "id" TEXT NOT NULL DEFAULT gen_random_uuid(),
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" TIMESTAMP(3) NOT NULL,
    "deleted" BOOLEAN NOT NULL DEFAULT false,
    "fileName" TEXT NOT NULL,
    "fileSize" INTEGER NOT NULL,
    "path" TEXT,
    "fileBytes" BYTEA,
    "userId" TEXT,
    "completedAppId" TEXT,

    CONSTRAINT "Deployment_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "LLMCallTemplate" (
    "id" TEXT NOT NULL DEFAULT gen_random_uuid(),
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "templateName" TEXT NOT NULL,
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
    "attempt" INTEGER NOT NULL,
    "prompt" JSONB NOT NULL,
    "response" TEXT NOT NULL,
    "userId" TEXT,
    "applicationId" TEXT,
    "llmCallTemplateId" TEXT,

    CONSTRAINT "LLMCallAttempt_pkey" PRIMARY KEY ("id")
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
CREATE TABLE "_CompiledRouteToFunction" (
    "A" TEXT NOT NULL,
    "B" TEXT NOT NULL
);

-- CreateTable
CREATE TABLE "_CompiledRouteToCompletedApp" (
    "A" TEXT NOT NULL,
    "B" TEXT NOT NULL
);

-- CreateIndex
CREATE UNIQUE INDEX "User_cloudServicesId_key" ON "User"("cloudServicesId");

-- CreateIndex
CREATE UNIQUE INDEX "User_discordId_key" ON "User"("discordId");

-- CreateIndex
CREATE UNIQUE INDEX "CompiledRoute_codeGraphId_key" ON "CompiledRoute"("codeGraphId");

-- CreateIndex
CREATE UNIQUE INDEX "_TableRelations_AB_unique" ON "_TableRelations"("A", "B");

-- CreateIndex
CREATE INDEX "_TableRelations_B_index" ON "_TableRelations"("B");

-- CreateIndex
CREATE UNIQUE INDEX "_FunctionToPackage_AB_unique" ON "_FunctionToPackage"("A", "B");

-- CreateIndex
CREATE INDEX "_FunctionToPackage_B_index" ON "_FunctionToPackage"("B");

-- CreateIndex
CREATE UNIQUE INDEX "_CompiledRouteToFunction_AB_unique" ON "_CompiledRouteToFunction"("A", "B");

-- CreateIndex
CREATE INDEX "_CompiledRouteToFunction_B_index" ON "_CompiledRouteToFunction"("B");

-- CreateIndex
CREATE UNIQUE INDEX "_CompiledRouteToCompletedApp_AB_unique" ON "_CompiledRouteToCompletedApp"("A", "B");

-- CreateIndex
CREATE INDEX "_CompiledRouteToCompletedApp_B_index" ON "_CompiledRouteToCompletedApp"("B");

-- AddForeignKey
ALTER TABLE "Application" ADD CONSTRAINT "Application_userId_fkey" FOREIGN KEY ("userId") REFERENCES "User"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "Specification" ADD CONSTRAINT "Specification_userId_fkey" FOREIGN KEY ("userId") REFERENCES "User"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "Specification" ADD CONSTRAINT "Specification_applicationId_fkey" FOREIGN KEY ("applicationId") REFERENCES "Application"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "APIRouteSpec" ADD CONSTRAINT "APIRouteSpec_specificationId_fkey" FOREIGN KEY ("specificationId") REFERENCES "Specification"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "APIRouteSpec" ADD CONSTRAINT "APIRouteSpec_responseObjectId_fkey" FOREIGN KEY ("responseObjectId") REFERENCES "ResponseObject"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "APIRouteSpec" ADD CONSTRAINT "APIRouteSpec_requestObjectId_fkey" FOREIGN KEY ("requestObjectId") REFERENCES "RequestObject"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "APIRouteSpec" ADD CONSTRAINT "APIRouteSpec_databaseSchemaId_fkey" FOREIGN KEY ("databaseSchemaId") REFERENCES "DatabaseSchema"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "Param" ADD CONSTRAINT "Param_responseObjectId_fkey" FOREIGN KEY ("responseObjectId") REFERENCES "ResponseObject"("id") ON DELETE SET NULL ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "Param" ADD CONSTRAINT "Param_requestObjectId_fkey" FOREIGN KEY ("requestObjectId") REFERENCES "RequestObject"("id") ON DELETE SET NULL ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "DatabaseTable" ADD CONSTRAINT "DatabaseTable_databaseSchemaId_fkey" FOREIGN KEY ("databaseSchemaId") REFERENCES "DatabaseSchema"("id") ON DELETE SET NULL ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "CodeGraph" ADD CONSTRAINT "CodeGraph_apiRouteSpecId_fkey" FOREIGN KEY ("apiRouteSpecId") REFERENCES "APIRouteSpec"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "CodeGraph" ADD CONSTRAINT "CodeGraph_databaseSchemaId_fkey" FOREIGN KEY ("databaseSchemaId") REFERENCES "DatabaseSchema"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "CodeGraph" ADD CONSTRAINT "CodeGraph_compiledRouteId_fkey" FOREIGN KEY ("compiledRouteId") REFERENCES "CompiledRoute"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "FunctionDefinition" ADD CONSTRAINT "FunctionDefinition_codeGraphId_fkey" FOREIGN KEY ("codeGraphId") REFERENCES "CodeGraph"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "FunctionDefinition" ADD CONSTRAINT "FunctionDefinition_functionsId_fkey" FOREIGN KEY ("functionsId") REFERENCES "Function"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "CompiledRoute" ADD CONSTRAINT "CompiledRoute_apiRouteSpecId_fkey" FOREIGN KEY ("apiRouteSpecId") REFERENCES "APIRouteSpec"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "CompletedApp" ADD CONSTRAINT "CompletedApp_specificationId_fkey" FOREIGN KEY ("specificationId") REFERENCES "Specification"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "Deployment" ADD CONSTRAINT "Deployment_userId_fkey" FOREIGN KEY ("userId") REFERENCES "User"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "Deployment" ADD CONSTRAINT "Deployment_completedAppId_fkey" FOREIGN KEY ("completedAppId") REFERENCES "CompletedApp"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "LLMCallAttempt" ADD CONSTRAINT "LLMCallAttempt_userId_fkey" FOREIGN KEY ("userId") REFERENCES "User"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "LLMCallAttempt" ADD CONSTRAINT "LLMCallAttempt_applicationId_fkey" FOREIGN KEY ("applicationId") REFERENCES "Application"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "LLMCallAttempt" ADD CONSTRAINT "LLMCallAttempt_llmCallTemplateId_fkey" FOREIGN KEY ("llmCallTemplateId") REFERENCES "LLMCallTemplate"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "_TableRelations" ADD CONSTRAINT "_TableRelations_A_fkey" FOREIGN KEY ("A") REFERENCES "DatabaseTable"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "_TableRelations" ADD CONSTRAINT "_TableRelations_B_fkey" FOREIGN KEY ("B") REFERENCES "DatabaseTable"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "_FunctionToPackage" ADD CONSTRAINT "_FunctionToPackage_A_fkey" FOREIGN KEY ("A") REFERENCES "Function"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "_FunctionToPackage" ADD CONSTRAINT "_FunctionToPackage_B_fkey" FOREIGN KEY ("B") REFERENCES "Package"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "_CompiledRouteToFunction" ADD CONSTRAINT "_CompiledRouteToFunction_A_fkey" FOREIGN KEY ("A") REFERENCES "CompiledRoute"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "_CompiledRouteToFunction" ADD CONSTRAINT "_CompiledRouteToFunction_B_fkey" FOREIGN KEY ("B") REFERENCES "Function"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "_CompiledRouteToCompletedApp" ADD CONSTRAINT "_CompiledRouteToCompletedApp_A_fkey" FOREIGN KEY ("A") REFERENCES "CompiledRoute"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "_CompiledRouteToCompletedApp" ADD CONSTRAINT "_CompiledRouteToCompletedApp_B_fkey" FOREIGN KEY ("B") REFERENCES "CompletedApp"("id") ON DELETE CASCADE ON UPDATE CASCADE;
