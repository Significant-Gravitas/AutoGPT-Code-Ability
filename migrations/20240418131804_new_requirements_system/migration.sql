/*
  Warnings:

  - You are about to drop the column `databaseSchemaId` on the `APIRouteSpec` table. All the data in the column will be lost.
  - You are about to drop the column `specificationId` on the `APIRouteSpec` table. All the data in the column will be lost.
  - You are about to drop the column `answer` on the `Question` table. All the data in the column will be lost.
  - You are about to drop the column `interviewId` on the `Question` table. All the data in the column will be lost.
  - You are about to drop the column `question` on the `Question` table. All the data in the column will be lost.
  - You are about to drop the column `tool` on the `Question` table. All the data in the column will be lost.
  - You are about to drop the column `context` on the `Specification` table. All the data in the column will be lost.
  - You are about to drop the column `name` on the `Specification` table. All the data in the column will be lost.

*/
-- DropForeignKey
ALTER TABLE "APIRouteSpec" DROP CONSTRAINT "APIRouteSpec_databaseSchemaId_fkey";

-- DropForeignKey
ALTER TABLE "APIRouteSpec" DROP CONSTRAINT "APIRouteSpec_specificationId_fkey";

-- DropForeignKey
ALTER TABLE "Question" DROP CONSTRAINT "Question_interviewId_fkey";

-- AlterTable
ALTER TABLE "APIRouteSpec" DROP COLUMN "databaseSchemaId",
DROP COLUMN "specificationId",
ADD COLUMN     "AllowedAccessRoles" TEXT[],
ADD COLUMN     "moduleId" TEXT,
ALTER COLUMN "AccessLevel" DROP NOT NULL;

-- AlterTable
ALTER TABLE "LLMCallAttempt" ADD COLUMN     "interviewStepId" TEXT;

-- AlterTable
ALTER TABLE "Question" DROP COLUMN "answer",
DROP COLUMN "interviewId",
DROP COLUMN "question",
DROP COLUMN "tool",
ADD COLUMN     "functionality" TEXT NOT NULL DEFAULT '',
ADD COLUMN     "interviewStepId" TEXT,
ADD COLUMN     "name" TEXT NOT NULL DEFAULT '',
ADD COLUMN     "reasoning" TEXT NOT NULL DEFAULT '',
ADD COLUMN     "specificationId" TEXT;

-- AlterTable
ALTER TABLE "Specification" DROP COLUMN "context",
DROP COLUMN "name",
ADD COLUMN     "databaseSchemaId" TEXT;

-- CreateTable
CREATE TABLE "InterviewStep" (
    "id" TEXT NOT NULL DEFAULT gen_random_uuid(),
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" TIMESTAMP(3) NOT NULL,
    "deleted" BOOLEAN NOT NULL DEFAULT false,
    "phase_complete" BOOLEAN NOT NULL DEFAULT false,
    "say" TEXT NOT NULL,
    "thoughts" TEXT NOT NULL,
    "interviewId" TEXT NOT NULL,
    "applicationId" TEXT NOT NULL,

    CONSTRAINT "InterviewStep_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "Module" (
    "id" TEXT NOT NULL DEFAULT gen_random_uuid(),
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" TIMESTAMP(3) NOT NULL,
    "deleted" BOOLEAN NOT NULL DEFAULT false,
    "name" TEXT NOT NULL,
    "description" TEXT NOT NULL,
    "applicationId" TEXT,
    "userId" TEXT,
    "specificationId" TEXT,

    CONSTRAINT "Module_pkey" PRIMARY KEY ("id")
);

-- AddForeignKey
ALTER TABLE "InterviewStep" ADD CONSTRAINT "InterviewStep_interviewId_fkey" FOREIGN KEY ("interviewId") REFERENCES "Interview"("id") ON DELETE RESTRICT ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "InterviewStep" ADD CONSTRAINT "InterviewStep_applicationId_fkey" FOREIGN KEY ("applicationId") REFERENCES "Application"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "Question" ADD CONSTRAINT "Question_interviewStepId_fkey" FOREIGN KEY ("interviewStepId") REFERENCES "InterviewStep"("id") ON DELETE SET NULL ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "Question" ADD CONSTRAINT "Question_specificationId_fkey" FOREIGN KEY ("specificationId") REFERENCES "Specification"("id") ON DELETE SET NULL ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "Specification" ADD CONSTRAINT "Specification_databaseSchemaId_fkey" FOREIGN KEY ("databaseSchemaId") REFERENCES "DatabaseSchema"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "Module" ADD CONSTRAINT "Module_applicationId_fkey" FOREIGN KEY ("applicationId") REFERENCES "Application"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "Module" ADD CONSTRAINT "Module_userId_fkey" FOREIGN KEY ("userId") REFERENCES "User"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "Module" ADD CONSTRAINT "Module_specificationId_fkey" FOREIGN KEY ("specificationId") REFERENCES "Specification"("id") ON DELETE SET NULL ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "APIRouteSpec" ADD CONSTRAINT "APIRouteSpec_moduleId_fkey" FOREIGN KEY ("moduleId") REFERENCES "Module"("id") ON DELETE SET NULL ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "LLMCallAttempt" ADD CONSTRAINT "LLMCallAttempt_interviewStepId_fkey" FOREIGN KEY ("interviewStepId") REFERENCES "InterviewStep"("id") ON DELETE SET NULL ON UPDATE CASCADE;
