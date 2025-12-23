const express = require('express');
const app = express();
app.use(express.json());

let messages = [];

app.post('/send', (req, res) => {
    const newMessage = {
        PlayerName: req.body.PlayerName,
        UserId: req.body.UserId,
        Message: req.body.Message,
        Timestamp: Date.now() // Use server time to prevent sync bugs
    };
    messages.push(newMessage);
    if (messages.length > 100) messages.shift(); 
    res.status(200).json({ success: true });
});

app.get('/get_messages', (req, res) => {
    const after = parseInt(req.query.after) || 0;
    res.json(messages.filter(m => m.Timestamp > after));
});

app.get('/', (req, res) => res.send("Sonix Server Active"));
app.listen(process.env.PORT || 3000);
