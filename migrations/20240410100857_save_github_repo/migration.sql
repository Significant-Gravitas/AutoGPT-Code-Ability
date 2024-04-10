/*
  Warnings:

  - A unique constraint covering the columns `[repo]` on the table `Deployment` will be added. If there are existing duplicate values, this will fail.

*/
-- AlterTable
ALTER TABLE "Deployment" ADD COLUMN     "repo" TEXT,
ALTER COLUMN "fileName" DROP NOT NULL,
ALTER COLUMN "fileSize" DROP NOT NULL;

-- CreateIndex
CREATE UNIQUE INDEX "Deployment_repo_key" ON "Deployment"("repo");
