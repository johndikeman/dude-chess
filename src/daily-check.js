import fs from 'fs';
import path from 'path';
import { fetchRecentGames } from './lichess.js';

function getCONFIG_DIR() {
  return process.env.DUDE_CONFIG_DIR || process.cwd();
}
function getTASKS_FILE() {
  return path.join(getCONFIG_DIR(), "tasks.md");
}
function getTRACKING_FILE() {
  return path.join(getCONFIG_DIR(), "lichess-tracking.json");
}

function loadTracking() {
  const trackingFile = getTRACKING_FILE();
  if (fs.existsSync(trackingFile)) {
    return JSON.parse(fs.readFileSync(trackingFile, "utf8"));
  }
  return { lastCheckedGameId: null };
}

function saveTracking(tracking) {
  fs.writeFileSync(getTRACKING_FILE(), JSON.stringify(tracking, null, 2));
}

function addTask(task) {
  const tasksFile = getTASKS_FILE();
  let content = fs.existsSync(tasksFile)
    ? fs.readFileSync(tasksFile, "utf8")
    : "# Pending Tasks\n";
  if (!content.includes("# Pending Tasks")) {
    content = "# Pending Tasks\n" + content;
  }
  content = content.replace(
    "# Pending Tasks\n",
    `# Pending Tasks\n- [ ] ${task}\n`,
  );
  fs.writeFileSync(tasksFile, content);
}

async function checkNewGames(username) {
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
    const username = process.env.LICHESS_USERNAME;
    if (username) {
        checkNewGames(username).catch(console.error);
    } else {
    const configPath = path.join(getCONFIG_DIR(), "config.json");
    if (fs.existsSync(configPath)) {
      const config = JSON.parse(fs.readFileSync(configPath, "utf8"));
      if (config.lichessUsername) {
        checkNewGames(config.lichessUsername).catch(console.error);
      } else {
        console.error(
          "No LICHESS_USERNAME env var and no lichessUsername found in config.json",
        );
      }
    } else {
      console.error("No LICHESS_USERNAME env var and config.json not found");
    }
  }
}
