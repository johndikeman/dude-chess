import { Client, GatewayIntentBits } from 'discord.js';

export async function sendNotification(message, token, channelId) {
    if (!token) {
        console.error('DISCORD_TOKEN not set');
        return;
    }

    const client = new Client({ intents: [GatewayIntentBits.Guilds] });

    try {
        await client.login(token);
        
        let channel;
        if (channelId) {
            channel = await client.channels.fetch(channelId);
        } else {
            const guilds = await client.guilds.fetch();
            for (const [guildId, guildBase] of guilds) {
                const guild = await guildBase.fetch();
                const channels = await guild.channels.fetch();
                channel = channels.find(c => c.isTextBased());
                if (channel) break;
            }
        }

        if (channel) {
            await channel.send(message);
            console.log(`Notification sent: ${message}`);
            return true;
        } else {
            console.error('No suitable channel found for notification');
            return false;
        }
    } catch (error) {
        console.error('Failed to send notification:', error);
        return false;
    } finally {
        client.destroy();
    }
}
