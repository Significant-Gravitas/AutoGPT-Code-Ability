-- CreateExtension
CREATE EXTENSION IF NOT EXISTS "vector";

-- CreateEnum
CREATE TYPE "Role" AS ENUM ('USER', 'ADMIN');

-- CreateEnum
CREATE TYPE "AccessLevel" AS ENUM ('PUBLIC', 'USER', 'ADMIN');

-- CreateTable
CREATE TABLE "CodexUser" (
    "id" SERIAL NOT NULL,
    "discord_id" TEXT NOT NULL,
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "email" TEXT,
    "name" TEXT,
    "role" "Role" NOT NULL DEFAULT 'USER',
    "password" TEXT,
    "deleted" BOOLEAN NOT NULL DEFAULT false,

    CONSTRAINT "CodexUser_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "Application" (
    "id" SERIAL NOT NULL,
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" TIMESTAMP(3) NOT NULL,
    "name" TEXT NOT NULL,
    "deleted" BOOLEAN NOT NULL DEFAULT false,
    "userId" INTEGER NOT NULL,

    CONSTRAINT "Application_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "Specification" (
    "id" SERIAL NOT NULL,
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" TIMESTAMP(3) NOT NULL,
    "deleted" BOOLEAN NOT NULL DEFAULT false,
    "name" TEXT NOT NULL,
    "context" TEXT NOT NULL,
    "applicationId" INTEGER,
    "userId" INTEGER,

    CONSTRAINT "Specification_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "APIRouteSpec" (
    "id" SERIAL NOT NULL,
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "functionName" TEXT NOT NULL,
    "method" TEXT NOT NULL,
    "path" TEXT NOT NULL,
    "description" TEXT NOT NULL,
    "accessLevel" "AccessLevel" NOT NULL,
    "databaseSchemaId" INTEGER,
    "specId" INTEGER,
    "requestObjectId" INTEGER,
    "responseObjectId" INTEGER,

    CONSTRAINT "APIRouteSpec_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "ResponseObject" (
    "id" SERIAL NOT NULL,
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "name" TEXT NOT NULL,
    "description" TEXT NOT NULL,

    CONSTRAINT "ResponseObject_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "RequestObject" (
    "id" SERIAL NOT NULL,
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "name" TEXT NOT NULL,
    "description" TEXT NOT NULL,

    CONSTRAINT "RequestObject_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "Param" (
    "id" SERIAL NOT NULL,
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "name" TEXT NOT NULL,
    "description" TEXT NOT NULL,
    "param_type" TEXT NOT NULL,

    CONSTRAINT "Param_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "DatabaseSchema" (
    "id" SERIAL NOT NULL,
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "embedding" vector(1536),
    "description" TEXT NOT NULL,

    CONSTRAINT "DatabaseSchema_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "DatabaseTable" (
    "id" SERIAL NOT NULL,
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "embedding" vector(1536),
    "description" TEXT NOT NULL,
    "definition" TEXT NOT NULL,

    CONSTRAINT "DatabaseTable_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "CodeGraph" (
    "id" SERIAL NOT NULL,
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "function_name" TEXT NOT NULL,
    "apiPath" TEXT NOT NULL,
    "imports" TEXT[],
    "code_graph" TEXT NOT NULL,
    "databaseSchemaId" INTEGER,
    "routeSpecId" INTEGER,

    CONSTRAINT "CodeGraph_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "FunctionDefinition" (
    "id" SERIAL NOT NULL,
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "name" TEXT NOT NULL,
    "doc_string" TEXT NOT NULL,
    "args" TEXT NOT NULL,
    "return_type" TEXT NOT NULL,
    "function_template" TEXT NOT NULL,
    "codeGraphId" INTEGER NOT NULL,
    "functionId" INTEGER NOT NULL,

    CONSTRAINT "FunctionDefinition_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "Functions" (
    "id" SERIAL NOT NULL,
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "embedding" vector(1536),
    "name" TEXT NOT NULL,
    "doc_string" TEXT NOT NULL,
    "args" TEXT NOT NULL,
    "return_type" TEXT NOT NULL,
    "code" TEXT NOT NULL,

    CONSTRAINT "Functions_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "Package" (
    "id" SERIAL NOT NULL,
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "packageName" TEXT NOT NULL,
    "version" TEXT NOT NULL,
    "specifier" TEXT NOT NULL,

    CONSTRAINT "Package_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "CompiledRoute" (
    "id" SERIAL NOT NULL,
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "embedding" vector(1536),
    "description" TEXT NOT NULL,
    "code" TEXT NOT NULL,
    "codeGraphId" INTEGER,

    CONSTRAINT "CompiledRoute_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "CompletedApp" (
    "id" SERIAL NOT NULL,
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" TIMESTAMP(3) NOT NULL,
    "deleted" BOOLEAN NOT NULL DEFAULT false,
    "name" TEXT NOT NULL,
    "description" TEXT NOT NULL,
    "specId" INTEGER,
    "userId" INTEGER,

    CONSTRAINT "CompletedApp_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "Deployment" (
    "id" SERIAL NOT NULL,
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" TIMESTAMP(3) NOT NULL,
    "deleted" BOOLEAN NOT NULL DEFAULT false,
    "fileName" TEXT NOT NULL,
    "fileSize" INTEGER NOT NULL,
    "path" TEXT NOT NULL,
    "completedAppId" INTEGER,
    "userId" INTEGER,

    CONSTRAINT "Deployment_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "LLMCallTemplate" (
    "id" SERIAL NOT NULL,
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
    "id" SERIAL NOT NULL,
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "userId" INTEGER,
    "appId" INTEGER,
    "model" TEXT NOT NULL,
    "completionTokens" INTEGER NOT NULL,
    "promptTokens" INTEGER NOT NULL,
    "totalTokens" INTEGER NOT NULL,
    "attempt" INTEGER NOT NULL,
    "prompt" JSONB NOT NULL,
    "response" TEXT NOT NULL,
    "callTemplateId" INTEGER NOT NULL,

    CONSTRAINT "LLMCallAttempt_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "_ParamToRequestObject" (
    "A" INTEGER NOT NULL,
    "B" INTEGER NOT NULL
);

-- CreateTable
CREATE TABLE "_ParamToResponseObject" (
    "A" INTEGER NOT NULL,
    "B" INTEGER NOT NULL
);

-- CreateTable
CREATE TABLE "_DatabaseSchemaToDatabaseTable" (
    "A" INTEGER NOT NULL,
    "B" INTEGER NOT NULL
);

-- CreateTable
CREATE TABLE "_TableRelations" (
    "A" INTEGER NOT NULL,
    "B" INTEGER NOT NULL
);

-- CreateTable
CREATE TABLE "_FunctionsToPackage" (
    "A" INTEGER NOT NULL,
    "B" INTEGER NOT NULL
);

-- CreateTable
CREATE TABLE "_CompiledRouteToFunctions" (
    "A" INTEGER NOT NULL,
    "B" INTEGER NOT NULL
);

-- CreateTable
CREATE TABLE "_CompiledRouteToCompletedApp" (
    "A" INTEGER NOT NULL,
    "B" INTEGER NOT NULL
);

-- CreateIndex
CREATE UNIQUE INDEX "CodexUser_discord_id_key" ON "CodexUser"("discord_id");

-- CreateIndex
CREATE UNIQUE INDEX "CompiledRoute_codeGraphId_key" ON "CompiledRoute"("codeGraphId");

-- CreateIndex
CREATE UNIQUE INDEX "_ParamToRequestObject_AB_unique" ON "_ParamToRequestObject"("A", "B");

-- CreateIndex
CREATE INDEX "_ParamToRequestObject_B_index" ON "_ParamToRequestObject"("B");

-- CreateIndex
CREATE UNIQUE INDEX "_ParamToResponseObject_AB_unique" ON "_ParamToResponseObject"("A", "B");

-- CreateIndex
CREATE INDEX "_ParamToResponseObject_B_index" ON "_ParamToResponseObject"("B");

-- CreateIndex
CREATE UNIQUE INDEX "_DatabaseSchemaToDatabaseTable_AB_unique" ON "_DatabaseSchemaToDatabaseTable"("A", "B");

-- CreateIndex
CREATE INDEX "_DatabaseSchemaToDatabaseTable_B_index" ON "_DatabaseSchemaToDatabaseTable"("B");

-- CreateIndex
CREATE UNIQUE INDEX "_TableRelations_AB_unique" ON "_TableRelations"("A", "B");

-- CreateIndex
CREATE INDEX "_TableRelations_B_index" ON "_TableRelations"("B");

-- CreateIndex
CREATE UNIQUE INDEX "_FunctionsToPackage_AB_unique" ON "_FunctionsToPackage"("A", "B");

-- CreateIndex
CREATE INDEX "_FunctionsToPackage_B_index" ON "_FunctionsToPackage"("B");

-- CreateIndex
CREATE UNIQUE INDEX "_CompiledRouteToFunctions_AB_unique" ON "_CompiledRouteToFunctions"("A", "B");

-- CreateIndex
CREATE INDEX "_CompiledRouteToFunctions_B_index" ON "_CompiledRouteToFunctions"("B");

-- CreateIndex
CREATE UNIQUE INDEX "_CompiledRouteToCompletedApp_AB_unique" ON "_CompiledRouteToCompletedApp"("A", "B");

-- CreateIndex
CREATE INDEX "_CompiledRouteToCompletedApp_B_index" ON "_CompiledRouteToCompletedApp"("B");

-- AddForeignKey
ALTER TABLE "Application" ADD CONSTRAINT "Application_userId_fkey" FOREIGN KEY ("userId") REFERENCES "CodexUser"("id") ON DELETE RESTRICT ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "Specification" ADD CONSTRAINT "Specification_applicationId_fkey" FOREIGN KEY ("applicationId") REFERENCES "Application"("id") ON DELETE SET NULL ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "Specification" ADD CONSTRAINT "Specification_userId_fkey" FOREIGN KEY ("userId") REFERENCES "CodexUser"("id") ON DELETE SET NULL ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "APIRouteSpec" ADD CONSTRAINT "APIRouteSpec_databaseSchemaId_fkey" FOREIGN KEY ("databaseSchemaId") REFERENCES "DatabaseSchema"("id") ON DELETE SET NULL ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "APIRouteSpec" ADD CONSTRAINT "APIRouteSpec_specId_fkey" FOREIGN KEY ("specId") REFERENCES "Specification"("id") ON DELETE SET NULL ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "APIRouteSpec" ADD CONSTRAINT "APIRouteSpec_requestObjectId_fkey" FOREIGN KEY ("requestObjectId") REFERENCES "RequestObject"("id") ON DELETE SET NULL ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "APIRouteSpec" ADD CONSTRAINT "APIRouteSpec_responseObjectId_fkey" FOREIGN KEY ("responseObjectId") REFERENCES "ResponseObject"("id") ON DELETE SET NULL ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "CodeGraph" ADD CONSTRAINT "CodeGraph_databaseSchemaId_fkey" FOREIGN KEY ("databaseSchemaId") REFERENCES "DatabaseSchema"("id") ON DELETE SET NULL ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "CodeGraph" ADD CONSTRAINT "CodeGraph_routeSpecId_fkey" FOREIGN KEY ("routeSpecId") REFERENCES "APIRouteSpec"("id") ON DELETE SET NULL ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "FunctionDefinition" ADD CONSTRAINT "FunctionDefinition_codeGraphId_fkey" FOREIGN KEY ("codeGraphId") REFERENCES "CodeGraph"("id") ON DELETE RESTRICT ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "FunctionDefinition" ADD CONSTRAINT "FunctionDefinition_functionId_fkey" FOREIGN KEY ("functionId") REFERENCES "Functions"("id") ON DELETE RESTRICT ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "CompiledRoute" ADD CONSTRAINT "CompiledRoute_codeGraphId_fkey" FOREIGN KEY ("codeGraphId") REFERENCES "CodeGraph"("id") ON DELETE SET NULL ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "CompletedApp" ADD CONSTRAINT "CompletedApp_specId_fkey" FOREIGN KEY ("specId") REFERENCES "Specification"("id") ON DELETE SET NULL ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "CompletedApp" ADD CONSTRAINT "CompletedApp_userId_fkey" FOREIGN KEY ("userId") REFERENCES "CodexUser"("id") ON DELETE SET NULL ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "Deployment" ADD CONSTRAINT "Deployment_completedAppId_fkey" FOREIGN KEY ("completedAppId") REFERENCES "CompletedApp"("id") ON DELETE SET NULL ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "Deployment" ADD CONSTRAINT "Deployment_userId_fkey" FOREIGN KEY ("userId") REFERENCES "CodexUser"("id") ON DELETE SET NULL ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "LLMCallAttempt" ADD CONSTRAINT "LLMCallAttempt_userId_fkey" FOREIGN KEY ("userId") REFERENCES "CodexUser"("id") ON DELETE SET NULL ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "LLMCallAttempt" ADD CONSTRAINT "LLMCallAttempt_appId_fkey" FOREIGN KEY ("appId") REFERENCES "Application"("id") ON DELETE SET NULL ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "LLMCallAttempt" ADD CONSTRAINT "LLMCallAttempt_callTemplateId_fkey" FOREIGN KEY ("callTemplateId") REFERENCES "LLMCallTemplate"("id") ON DELETE RESTRICT ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "_ParamToRequestObject" ADD CONSTRAINT "_ParamToRequestObject_A_fkey" FOREIGN KEY ("A") REFERENCES "Param"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "_ParamToRequestObject" ADD CONSTRAINT "_ParamToRequestObject_B_fkey" FOREIGN KEY ("B") REFERENCES "RequestObject"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "_ParamToResponseObject" ADD CONSTRAINT "_ParamToResponseObject_A_fkey" FOREIGN KEY ("A") REFERENCES "Param"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "_ParamToResponseObject" ADD CONSTRAINT "_ParamToResponseObject_B_fkey" FOREIGN KEY ("B") REFERENCES "ResponseObject"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "_DatabaseSchemaToDatabaseTable" ADD CONSTRAINT "_DatabaseSchemaToDatabaseTable_A_fkey" FOREIGN KEY ("A") REFERENCES "DatabaseSchema"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "_DatabaseSchemaToDatabaseTable" ADD CONSTRAINT "_DatabaseSchemaToDatabaseTable_B_fkey" FOREIGN KEY ("B") REFERENCES "DatabaseTable"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "_TableRelations" ADD CONSTRAINT "_TableRelations_A_fkey" FOREIGN KEY ("A") REFERENCES "DatabaseTable"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "_TableRelations" ADD CONSTRAINT "_TableRelations_B_fkey" FOREIGN KEY ("B") REFERENCES "DatabaseTable"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "_FunctionsToPackage" ADD CONSTRAINT "_FunctionsToPackage_A_fkey" FOREIGN KEY ("A") REFERENCES "Functions"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "_FunctionsToPackage" ADD CONSTRAINT "_FunctionsToPackage_B_fkey" FOREIGN KEY ("B") REFERENCES "Package"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "_CompiledRouteToFunctions" ADD CONSTRAINT "_CompiledRouteToFunctions_A_fkey" FOREIGN KEY ("A") REFERENCES "CompiledRoute"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "_CompiledRouteToFunctions" ADD CONSTRAINT "_CompiledRouteToFunctions_B_fkey" FOREIGN KEY ("B") REFERENCES "Functions"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "_CompiledRouteToCompletedApp" ADD CONSTRAINT "_CompiledRouteToCompletedApp_A_fkey" FOREIGN KEY ("A") REFERENCES "CompiledRoute"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "_CompiledRouteToCompletedApp" ADD CONSTRAINT "_CompiledRouteToCompletedApp_B_fkey" FOREIGN KEY ("B") REFERENCES "CompletedApp"("id") ON DELETE CASCADE ON UPDATE CASCADE;
