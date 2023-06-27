import { prisma } from "../../db"
import type { NextApiRequest, NextApiResponse } from "next"

export default async function handler(req: NextApiRequest, res: NextApiResponse) {
    const guilds = (await prisma.guild.findMany()).length
    const warns = (await prisma.warning.findMany()).length

    const avgwarn = warns / guilds

    return res.status(200).json({
        name: "AIMod API",
        version: "0.0.1",
        stats: {
            guilds: guilds,
            warnings: warns,
            average_warnings_per_guild: avgwarn
        }
    })
}