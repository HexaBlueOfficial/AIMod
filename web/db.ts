import { PrismaClient } from '@prisma/client'

const gprisma = global as unknown as { prisma: PrismaClient }

export const prisma = gprisma.prisma || new PrismaClient({log: ["query"]})

if (process.env.NODE_ENV !== 'production') {gprisma.prisma = prisma}