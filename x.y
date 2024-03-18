
enum Role {
  Client
  Professional
  Admin
}

model User {
  id            String               @id @default(uuid())
  email         String               @unique
  hashedPassword String
  role          Role
  clientProfile ClientProfile?
  professionalProfile ProfessionalProfile?
  messages      Message[]
  feedback      Feedback[]
  createdAt     DateTime             @default(now())
  updatedAt     DateTime             @updatedAt
}

model ClientProfile {
  id             String     @id @default(uuid())
  userId         String
  user           User       @relation(fields: [userId], references: [id])
  name           String
  contactDetails Json
  location       String
  preferences    Json
  feedback       Feedback[]
  createdAt      DateTime   @default(now())
  updatedAt      DateTime   @updatedAt
}

model ProfessionalProfile {
  id             String     @id @default(uuid())
  userId         String
  user           User       @relation(fields: [userId], references: [id])
  name           String
  contactDetails Json
  location       String
  skills         Json
  workHistory    Json
  portfolio      Json
  preferences    Json
  feedback       Feedback[]
  createdAt      DateTime   @default(now())
  updatedAt      DateTime   @updatedAt
}

model Message {
  id             String   @id @default(uuid())
  senderId       String
  sender         User     @relation(name: "MessageSender", fields: [senderId], references: [id])
  recipientId    String
  recipient      User     @relation(name: "MessageRecipient", fields: [recipientId], references: [id])
  content        String
  encrypted      Boolean
  createdAt      DateTime @default(now())
  updatedAt      DateTime @updatedAt
}

model Feedback {
  id             String   @id @default(uuid())
  authorId       String
  profileId      String
  rating         Int
  review         String?
  author         User     @relation(fields: [authorId], references: [id])
  profile        User     @relation(fields: [profileId], references: [id])
  createdAt      DateTime @default(now())
  updatedAt      DateTime @updatedAt
}
