/*
  Warnings:

  - A unique constraint covering the columns `[dbName]` on the table `Deployment` will be added. If there are existing duplicate values, this will fail.
  - A unique constraint covering the columns `[dbUser]` on the table `Deployment` will be added. If there are existing duplicate values, this will fail.

*/
-- AlterTable
ALTER TABLE "Deployment" ADD COLUMN     "dbName" TEXT,
ADD COLUMN     "dbUser" TEXT;

-- CreateIndex
CREATE UNIQUE INDEX "Deployment_dbName_key" ON "Deployment"("dbName");

-- CreateIndex
CREATE UNIQUE INDEX "Deployment_dbUser_key" ON "Deployment"("dbUser");
