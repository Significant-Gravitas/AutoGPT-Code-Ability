/*
  Warnings:

  - You are about to drop the `ResumePoint` table. If the table is not empty, all the data it contains will be lost.

*/
-- DropForeignKey
ALTER TABLE "ResumePoint" DROP CONSTRAINT "ResumePoint_applicationId_fkey";

-- DropForeignKey
ALTER TABLE "ResumePoint" DROP CONSTRAINT "ResumePoint_completedAppId_fkey";

-- DropForeignKey
ALTER TABLE "ResumePoint" DROP CONSTRAINT "ResumePoint_deploymentId_fkey";

-- DropForeignKey
ALTER TABLE "ResumePoint" DROP CONSTRAINT "ResumePoint_interviewId_fkey";

-- DropForeignKey
ALTER TABLE "ResumePoint" DROP CONSTRAINT "ResumePoint_specificationId_fkey";

-- DropForeignKey
ALTER TABLE "ResumePoint" DROP CONSTRAINT "ResumePoint_userId_fkey";

-- AlterTable
ALTER TABLE "LLMCallTemplate" ALTER COLUMN "model" DROP DEFAULT;

-- AlterTable
ALTER TABLE "Specification" ADD COLUMN     "interviewId" TEXT;

-- DropTable
DROP TABLE "ResumePoint";

-- AddForeignKey
ALTER TABLE "Specification" ADD CONSTRAINT "Specification_interviewId_fkey" FOREIGN KEY ("interviewId") REFERENCES "Interview"("id") ON DELETE CASCADE ON UPDATE CASCADE;
