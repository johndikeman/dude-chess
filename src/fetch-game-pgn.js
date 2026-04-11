const gameId = process.argv[2];

if (!gameId) {
    console.error("Usage: node fetch-game-pgn.js <gameId>");
    process.exit(1);
}

fetch(`https://lichess.org/game/export/${gameId}.pgn?evals=true`)
    .then(r => r.text())
    .then(text => console.log(text))
    .catch(err => {
        console.error(`Error: ${err.message}`);
        process.exit(1);
    });
