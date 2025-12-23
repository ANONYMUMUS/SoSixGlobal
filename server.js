const express = require('express');
const app = express();
const PORT = process.env.PORT || 3000;

// JUST A SIMPLE PRINT TEST
const TEST_CODE = `print("SONIX CONNECTION SUCCESSFUL: DELTA IS READING RENDER")`;

app.get('/', (req, res) => {
    res.set('Content-Type', 'text/plain');
    res.send(TEST_CODE);
});

app.listen(PORT, () => console.log('Test Server Active'));
