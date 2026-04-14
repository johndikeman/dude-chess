import fs from 'fs';
import path from 'path';
import { fetchRecentGames, getImportantMoves, getBoardImageUrl } from './lichess.js';

const BLOG_DIR = './docs/_posts';
const ASSETS_DIR = './docs/assets/img';

export function initBlog() {
  if (!fs.existsSync(BLOG_DIR)) {
    fs.mkdirSync(BLOG_DIR, { recursive: true });
  }
  if (!fs.existsSync(ASSETS_DIR)) {
    fs.mkdirSync(ASSETS_DIR, { recursive: true });
  }
}

export async function downloadBoardImage(fen, filename) {
  const url = getBoardImageUrl(fen);
  const response = await fetch(url);
  if (response.ok) {
    const arrayBuffer = await response.arrayBuffer();
    const buffer = Buffer.from(arrayBuffer);
    const fullPath = path.join(ASSETS_DIR, filename);
    fs.writeFileSync(fullPath, buffer);
    return `/assets/img/${filename}`;
  } else {
    throw new Error(`Failed to download board image: ${response.statusText}`);
  }
}

export async function createBlogPost(game, content) {
    const slug = `${new Date(game.createdAt).toISOString().split('T')[0]}-${game.id}`;
    const filename = `${slug}.md`;
    const fullPath = path.join(BLOG_DIR, filename);

    // Prepare frontmatter
    const frontmatter = `---
layout: post
title: "I SUCK AT CHESS: ${game.id}"
date: ${new Date(game.createdAt).toISOString()}
categories: [chess, blunder]
game_url: "https://lichess.org/${game.id}"
---

${content}

[View game on Lichess](https://lichess.org/${game.id})
`;
    fs.writeFileSync(fullPath, frontmatter);
    return filename;
}
