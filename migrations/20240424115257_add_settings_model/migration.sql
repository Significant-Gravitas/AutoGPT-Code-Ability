-- CreateTable
CREATE TABLE "Settings" (
    "id" TEXT NOT NULL DEFAULT gen_random_uuid(),
    "zipFile" BOOLEAN NOT NULL DEFAULT true,
    "githubRepo" BOOLEAN NOT NULL DEFAULT false,
    "hosted" BOOLEAN NOT NULL DEFAULT true,
    "userId" TEXT,

    CONSTRAINT "Settings_pkey" PRIMARY KEY ("id")
);

-- CreateIndex
CREATE UNIQUE INDEX "Settings_userId_key" ON "Settings"("userId");

-- AddForeignKey
ALTER TABLE "Settings" ADD CONSTRAINT "Settings_userId_fkey" FOREIGN KEY ("userId") REFERENCES "User"("id") ON DELETE CASCADE ON UPDATE CASCADE;

