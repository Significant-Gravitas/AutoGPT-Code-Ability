-- AlterTable
ALTER TABLE "InterviewStep" ADD COLUMN     "access_roles" TEXT[];

-- AlterTable
ALTER TABLE "Module" ADD COLUMN     "interactions" TEXT NOT NULL DEFAULT '';
