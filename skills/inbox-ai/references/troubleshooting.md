# Inbox AI Troubleshooting

Common issues and solutions.

## Connection Issues

### "Config not found"
```
ERROR: Config not found at ~/.openclaw/workspace/inbox-ai-config.env
```
**Solution:**
```bash
cp references/email-config.template.env ~/.openclaw/workspace/inbox-ai-config.env
# Edit the file with your credentials
```

### "Authentication failed"
- Check username/password
- Verify email account is active
- Disable 2FA for automation accounts
- Check for special characters in password

### "Connection timed out"
- Check firewall settings
- Verify IMAP/SMTP ports are open
- Try different network (mobile hotspot test)
- Wait 10 minutes (rate limiting)

## Processing Issues

### "No emails found"
- Check if emails are in INBOX (not subfolders)
- Verify email account actually has unread messages
- Check date filters

### "Encoding errors"
- Usually happens with special characters
- Script auto-handles UTF-8
- If persistent: check email client encoding

### "Auto-reply not sending"
- Check SMTP connection test first
- Verify AUTO_REPLY_ENABLED=true in config
- Check escalation threshold settings
- Review email categorization (spam won't auto-reply)

## Rate Limiting

### "Too many connections"
- IONOS limits connections per minute
- Wait 5-10 minutes between runs
- Consider increasing check interval

### "SMTP quota exceeded"
- Daily sending limits apply
- Check IONOS account limits
- Reduce MAX_AUTO_REPLY_PER_HOUR

## AI Behavior Issues

### "Wrong categorization"
- Add custom keywords to categorize_email() function
- Train with sample emails
- Adjust category thresholds

### "Inappropriate auto-replies"
- Switch to hybrid mode for review
- Improve templates in generate_reply()
- Add more escalation rules

### "Missing important emails"
- Lower ESCALATION_THRESHOLD
- Check spam folder regularly
- Review categorization logic

## Debug Mode

Enable verbose logging:

```python
# Add to inbox_processor.py
import logging
logging.basicConfig(level=logging.DEBUG)
```

## Getting Help

1. Check connection first:
   ```bash
   python3 scripts/test_email_connection.py
   ```

2. Review logs:
   ```bash
   cat /tmp/inbox-ai-$(date +%Y%m%d).json
   ```

3. Test in monitor mode before auto mode

## Emergency Stop

To immediately stop all auto-replies:

```bash
# Edit config
nano ~/.openclaw/workspace/inbox-ai-config.env

# Set:
AUTO_REPLY_ENABLED=false

# Or disconnect:
# Change password in email provider panel
```
