/*
  Warnings:

  - A unique constraint covering the columns `[compiledRouteId]` on the table `CodeGraph` will be added. If there are existing duplicate values, this will fail.

*/
-- CreateIndex
CREATE UNIQUE INDEX "CodeGraph_compiledRouteId_key" ON "CodeGraph"("compiledRouteId");
