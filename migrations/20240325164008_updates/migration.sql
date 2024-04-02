/*
  Warnings:

  - Added the required column `model` to the `LLMCallTemplate` table without a default value. This is not possible if the table is not empty.

*/
-- AlterTable
ALTER TABLE "LLMCallTemplate" ADD COLUMN "model" TEXT NOT NULL DEFAULT 'gpt-4-0125-preview';