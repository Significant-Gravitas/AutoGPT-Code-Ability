-- CreateEnum
CREATE TYPE "InterviewPhase" AS ENUM ('FEATURES', 'ARCHITECT', 'COMPLETED');

-- AlterTable
ALTER TABLE "InterviewStep" ADD COLUMN     "phase" "InterviewPhase" NOT NULL DEFAULT 'FEATURES';

-- AlterTable
ALTER TABLE "Module" ADD COLUMN     "interviewStepId" TEXT;

-- AddForeignKey
ALTER TABLE "Module" ADD CONSTRAINT "Module_interviewStepId_fkey" FOREIGN KEY ("interviewStepId") REFERENCES "InterviewStep"("id") ON DELETE SET NULL ON UPDATE CASCADE;
