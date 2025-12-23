app.post('/send', (req, res) => {
    // This ensures UserId and PlayerName are both saved
    messages.push({
        PlayerName: req.body.PlayerName,
        UserId: req.body.UserId,
        Message: req.body.Message,
        Timestamp: req.body.Timestamp || Date.now()
    });
    if (messages.length > 200) messages.shift(); 
    res.status(200).json({ success: true });
});
