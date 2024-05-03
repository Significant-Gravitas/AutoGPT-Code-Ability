/*
  Warnings:

  - Added the required column `interactions` to the `Module` table without a default value. This is not possible if the table is not empty.

*/
-- AlterTable
ALTER TABLE "InterviewStep" ADD COLUMN     "access_roles" TEXT[];

-- AlterTable
ALTER TABLE "Module" ADD COLUMN     "interactions" TEXT NOT NULL;
