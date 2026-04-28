import { Client, GatewayIntentBits } from 'discord.js';
import 'dotenv/config';

async function notify(message) {
    if (!process.env.DISCORD_TOKEN) {
        console.error('DISCORD_TOKEN not set');
        return;
    }

    const client = new Client({ intents: [GatewayIntentBits.Guilds] });

    try {
        await client.login(process.env.DISCORD_TOKEN);
        
        // Find a channel to send the message to
        // We can try to use a channel ID from env if provided, or find the first text channel
        const channelId = process.env.DISCORD_CHANNEL_ID;
        let channel;

        if (channelId) {
            channel = await client.channels.fetch(channelId);
        } else {
            // Try to find the first suitable channel in the first guild
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
            console.log(`Notification sent to #${channel.name}: ${message}`);
        } else {
            console.error('No suitable channel found for notification');
        }
    } catch (error) {
        console.error('Failed to send notification:', error);
    } finally {
        client.destroy();
    }
}

const message = process.argv.slice(2).join(' ') || 'Notification from Dude Agent!';
notify(message);
