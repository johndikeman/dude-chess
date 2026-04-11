import { downloadBoardImage } from './blog-manager.js';

const fen = process.argv[2];
const filename = process.argv[3];

if (!fen || !filename) {
    console.error("Usage: node download-board.js <FEN> <filename>");
    process.exit(1);
}

downloadBoardImage(fen, filename)
    .then(path => console.log(`Downloaded image to: ${path}`))
    .catch(err => {
        console.error(`Error: ${err.message}`);
        process.exit(1);
    });
