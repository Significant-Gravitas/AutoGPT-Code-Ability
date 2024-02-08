BEGIN;

-- Inserting users
INSERT INTO "CodexUser" (discord_id, email, name, role, password, deleted) VALUES
('123456789', 'joe.blogs@example.com', 'Joe Blogs', 'ADMIN', 'password123', false),
('234567890', 'jane.doe@example.com', 'Jane Doe', 'USER', 'password123', false);

COMMIT;

BEGIN;
-- Inserting applications

INSERT INTO "Application" (name, deleted, "userId", "updatedAt") VALUES
('Availability Checker', false, 1, NOW()),
('Invoice Generator', false, 1, NOW()),
('Appointment Optimization Tool', false, 1, NOW()),
('Distance Calculator', false, 1, NOW()),
('Profile Management System', false, 1, NOW()),
('Survey Tool', false, 2, NOW()),
('Scurvey Tool', true, 2, NOW());

COMMIT;
