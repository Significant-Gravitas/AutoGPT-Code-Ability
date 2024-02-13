-- DropForeignKey
ALTER TABLE "FunctionDefinition" DROP CONSTRAINT "FunctionDefinition_functionId_fkey";

-- AlterTable
ALTER TABLE "FunctionDefinition" ALTER COLUMN "functionId" DROP NOT NULL;

-- AddForeignKey
ALTER TABLE "FunctionDefinition" ADD CONSTRAINT "FunctionDefinition_functionId_fkey" FOREIGN KEY ("functionId") REFERENCES "Functions"("id") ON DELETE SET NULL ON UPDATE CASCADE;
