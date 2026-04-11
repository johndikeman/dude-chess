import { execSync } from "child_process";
import fs from "fs";
import path from "path";

export async function fetchRecentGames(username, lastGameId = null) {
  const url = `https://lichess.org/api/games/user/${username}?max=10&pgn=true&evals=true&opening=true&clocks=false&range=0-9`;
  // Note: we might want to use ndjson for parsing
  
  try {
    const response = await fetch(url, {
      headers: {
        'Accept': 'application/x-ndjson'
      }
    });
    
    if (!response.ok) {
      throw new Error(`Failed to fetch games: ${response.statusText}`);
    }
    
    const text = await response.text();
    const games = text.trim().split('\n').map(line => JSON.parse(line));
    
    // Filter out games that we've already processed
    if (lastGameId) {
      const lastIndex = games.findIndex(g => g.id === lastGameId);
      if (lastIndex !== -1) {
        return games.slice(0, lastIndex);
      }
    }
    
    return games;
  } catch (error) {
    console.error(`Error fetching Lichess games: ${error.message}`);
    return [];
  }
}

export function getImportantMoves(game) {
  // Simple heuristic: moves with significant eval changes
  // Lichess evaluations are in the PGN if evals=true
  // For simplicity, we can just look for 'blunders' (??) or 'mistakes' (?) if present in PGN
  // Or just pick some representative positions.
  
  const moves = [];
  // ... parse PGN or look at analysis in game object ...
  // For now, let's just pick 3 interesting positions (start, middle, end)
  // or use the 'analysis' field if available.
  
  if (game.analysis) {
    // find biggest eval drops
    let prevEval = 0;
    for (let i = 0; i < game.analysis.length; i++) {
        const move = game.analysis[i];
        if (move.eval) {
            const currentEval = move.eval;
            const diff = Math.abs(currentEval - prevEval);
            if (diff > 200) { // 2.0 pawn advantage change
                moves.push({
                    moveIndex: i,
                    fen: move.fen,
                    eval: currentEval,
                    diff: diff
                });
            }
            prevEval = currentEval;
        }
    }
  }
  
  return moves.sort((a, b) => b.diff - a.diff).slice(0, 5);
}

export function getBoardImageUrl(fen, color = 'white') {
  return `https://lichess1.org/export/fen.png?fen=${encodeURIComponent(fen)}&color=${color}&theme=brown&piece=cburnett`;
}
