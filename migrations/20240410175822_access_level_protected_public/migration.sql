/*
  Warnings:

  - The values [USER,ADMIN] on the enum `AccessLevel` will be removed. If these variants are still used in the database, this will fail.

*/
-- AlterEnum
BEGIN;
CREATE TYPE "AccessLevel_new" AS ENUM ('PUBLIC', 'PROTECTED');
ALTER TABLE "APIRouteSpec" ALTER COLUMN "AccessLevel" TYPE "AccessLevel_new" USING (
  CASE "AccessLevel"
    WHEN 'PUBLIC' THEN 'PUBLIC'::text::"AccessLevel_new"
    ELSE 'PROTECTED'::text::"AccessLevel_new"
  END
);
ALTER TYPE "AccessLevel" RENAME TO "AccessLevel_old";
ALTER TYPE "AccessLevel_new" RENAME TO "AccessLevel";
DROP TYPE "AccessLevel_old";
COMMIT;
