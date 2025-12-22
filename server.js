const express = require('express');
const app = express();
app.use(express.json());
let messages = [];
app.post('/send', (req, res) => {
    messages.push(req.body);
    if (messages.length > 200) messages.shift(); 
    res.status(200).json({ success: true });
});
app.get('/get_messages', (req, res) => {
    const after = parseInt(req.query.after) || 0;
    res.json(messages.filter(m => m.Timestamp > after));
});
app.get('/', (req, res) => res.send("Sonix Global Server is Running!"));
app.listen(process.env.PORT || 3000);
