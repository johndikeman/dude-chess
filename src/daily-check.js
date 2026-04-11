import fs from 'fs';
import path from 'path';
import { fetchRecentGames } from './lichess.js';

const CONFIG_DIR = process.env.DUDE_CONFIG_DIR || process.cwd();
const TASKS_FILE = path.join(CONFIG_DIR, 'tasks.md');
const TRACKING_FILE = path.join(CONFIG_DIR, 'lichess-tracking.json');

function loadTracking() {
    if (fs.existsSync(TRACKING_FILE)) {
        return JSON.parse(fs.readFileSync(TRACKING_FILE, 'utf8'));
    }
    return { lastCheckedGameId: null };
}

function saveTracking(tracking) {
    fs.writeFileSync(TRACKING_FILE, JSON.stringify(tracking, null, 2));
}

function addTask(task) {
    let content = fs.existsSync(TASKS_FILE) ? fs.readFileSync(TASKS_FILE, 'utf8') : "# Pending Tasks\n";
    if (!content.includes("# Pending Tasks")) {
      content = "# Pending Tasks\n" + content;
    }
    content = content.replace("# Pending Tasks\n", `# Pending Tasks\n- [ ] ${task}\n`);
    fs.writeFileSync(TASKS_FILE, content);
}

export async function checkNewGames(username) {
    const tracking = loadTracking();
    const games = await fetchRecentGames(username, tracking.lastCheckedGameId);
    
    if (games.length === 0) {
        console.log("No new games found.");
        return;
    }
    
    console.log(`Found ${games.length} new games.`);
    
    // We want to process them from oldest to newest
    for (const game of games.reverse()) {
        const task = `Maintain the blog: Write a 1000-word humorous and critical blog post about my Lichess game ${game.id}. 
Use profanity and an informal writing style to tear apart my terrible play. 
Include screenshots of at least 3 important moves/positions where I blundered or missed a win. 
You can use the exported board images. 
The game URL is https://lichess.org/${game.id}. 
Put the resulting markdown file and assets in the 'blog' directory of the current workspace.`;
        
        addTask(task);
        tracking.lastCheckedGameId = game.id;
    }
    
    saveTracking(tracking);
}

// If run directly
if (import.meta.url === `file://${process.argv[1]}`) {
    const configPath = path.join(CONFIG_DIR, 'config.json');
    if (fs.existsSync(configPath)) {
        const config = JSON.parse(fs.readFileSync(configPath, 'utf8'));
        if (config.lichessUsername) {
            checkNewGames(config.lichessUsername).catch(console.error);
        } else {
            console.error("No lichessUsername found in config.json");
        }
    } else {
        console.error("config.json not found");
    }
}
