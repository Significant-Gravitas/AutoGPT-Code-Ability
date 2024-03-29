-- CreateEnum
CREATE TYPE "Status" AS ENUM ('STARTED', 'SUCCESS', 'FAILED');

-- CreateTable
CREATE TABLE "EventLog" (
    "id" TEXT NOT NULL DEFAULT gen_random_uuid(),
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "userId" TEXT,
    "applicationId" TEXT,
    "keyType" "DevelopmentPhase" NOT NULL,
    "keyValue" TEXT NOT NULL,
    "event" TEXT NOT NULL,
    "status" "Status" NOT NULL,
    "message" TEXT,

    CONSTRAINT "EventLog_pkey" PRIMARY KEY ("id")
);

-- CreateIndex
CREATE INDEX "EventLog_userId_applicationId_idx" ON "EventLog"("userId", "applicationId");

-- CreateIndex
CREATE INDEX "EventLog_keyValue_idx" ON "EventLog"("keyValue");
