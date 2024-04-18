/*
  Warnings:

  - You are about to drop the column `answer` on the `Question` table. All the data in the column will be lost.
  - You are about to drop the column `interviewId` on the `Question` table. All the data in the column will be lost.
  - You are about to drop the column `question` on the `Question` table. All the data in the column will be lost.
  - You are about to drop the column `tool` on the `Question` table. All the data in the column will be lost.
  - Added the required column `functionality` to the `Question` table without a default value. This is not possible if the table is not empty.
  - Added the required column `name` to the `Question` table without a default value. This is not possible if the table is not empty.
  - Added the required column `reasoning` to the `Question` table without a default value. This is not possible if the table is not empty.

*/
-- DropForeignKey
ALTER TABLE "Question" DROP CONSTRAINT "Question_interviewId_fkey";

-- AlterTable
ALTER TABLE "LLMCallAttempt" ADD COLUMN     "interviewStepId" TEXT;

-- AlterTable
ALTER TABLE "Question" DROP COLUMN "answer",
DROP COLUMN "interviewId",
DROP COLUMN "question",
DROP COLUMN "tool",
ADD COLUMN     "functionality" TEXT NOT NULL DEFAULT '',
ADD COLUMN     "interviewStepId" TEXT DEFAULT '',
ADD COLUMN     "name" TEXT NOT NULL DEFAULT '',
ADD COLUMN     "reasoning" TEXT NOT NULL DEFAULT '',

-- CreateTable
CREATE TABLE "InterviewStep" (
    "id" TEXT NOT NULL DEFAULT gen_random_uuid(),
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "deleted" BOOLEAN NOT NULL DEFAULT false,
    "phase_complete" BOOLEAN NOT NULL DEFAULT false,
    "say" TEXT NOT NULL DEFAULT '',
    "thoughts" TEXT NOT NULL DEFAULT '',
    "interviewId" TEXT NOT NULL DEFAULT '',
    "applicationId" TEXT NOT NULL DEFAULT '',

    CONSTRAINT "InterviewStep_pkey" PRIMARY KEY ("id")
);

-- AddForeignKey
ALTER TABLE "InterviewStep" ADD CONSTRAINT "InterviewStep_interviewId_fkey" FOREIGN KEY ("interviewId") REFERENCES "Interview"("id") ON DELETE RESTRICT ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "InterviewStep" ADD CONSTRAINT "InterviewStep_applicationId_fkey" FOREIGN KEY ("applicationId") REFERENCES "Application"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "Question" ADD CONSTRAINT "Question_interviewStepId_fkey" FOREIGN KEY ("interviewStepId") REFERENCES "InterviewStep"("id") ON DELETE SET NULL ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "LLMCallAttempt" ADD CONSTRAINT "LLMCallAttempt_interviewStepId_fkey" FOREIGN KEY ("interviewStepId") REFERENCES "InterviewStep"("id") ON DELETE SET NULL ON UPDATE CASCADE;
