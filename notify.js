import { Client, GatewayIntentBits } from 'discord.js';
import 'dotenv/config';
import fs from 'fs';

export async function notify(message, targetChannelId = null) {
    if (!process.env.DISCORD_TOKEN) {
        console.error('DISCORD_TOKEN not set');
        return;
    }

    const client = new Client({ intents: [GatewayIntentBits.Guilds] });

    try {
        await client.login(process.env.DISCORD_TOKEN);
        
        // Priority: parameter > env > config.json > find first
        let channelId = targetChannelId;
        
        if (!channelId) channelId = process.env.DISCORD_CHANNEL_ID;
        
        if (!channelId) {
            // Try to load from config.json
            try {
                const configPath = './config.json';
                if (fs.existsSync(configPath)) {
                    const config = JSON.parse(fs.readFileSync(configPath, 'utf8'));
                    channelId = config.lastChannelId;
                }
            } catch (e) {}
        }

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

if (import.meta.url === `file://${process.argv[1]}`) {
    // Try to find a channel ID in the arguments (e.g., --channel ID)
    let channelId = null;
    const channelIdx = process.argv.indexOf('--channel');
    if (channelIdx !== -1 && process.argv[channelIdx + 1]) {
        channelId = process.argv[channelIdx + 1];
        process.argv.splice(channelIdx, 2);
    }

    const message = process.argv.slice(2).join(' ') || 'Notification from Dude Agent!';
    notify(message, channelId);
}
