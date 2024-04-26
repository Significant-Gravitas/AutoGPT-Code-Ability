-- AlterTable
ALTER TABLE "Deployment" ADD COLUMN     "githubRepo" BOOLEAN NOT NULL DEFAULT true,
ADD COLUMN     "hosted" BOOLEAN NOT NULL DEFAULT true,
ADD COLUMN     "zipFile" BOOLEAN NOT NULL DEFAULT false;
