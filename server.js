const express = require('express');
const app = express();
app.use(express.json());

let messages = [];
const MAX_MESSAGES = 200; // Limit set to 200

app.post('/send', (req, res) => {
    const newMessage = {
        PlayerName: req.body.PlayerName,
        UserId: req.body.UserId,
        Message: req.body.Message,
        Timestamp: Date.now() 
    };
    
    messages.push(newMessage);
    
    // If we exceed 200, remove the oldest message
    if (messages.length > MAX_MESSAGES) {
        messages.shift(); 
    }
    
    res.status(200).json({ success: true });
});

app.get('/get_messages', (req, res) => {
    const after = parseInt(req.query.after) || 0;
    // Sends only messages newer than the user's last received message
    res.json(messages.filter(m => m.Timestamp > after));
});

app.get('/', (req, res) => res.send("Sonix Global Server: Capacity 200"));
app.listen(process.env.PORT || 3000);
