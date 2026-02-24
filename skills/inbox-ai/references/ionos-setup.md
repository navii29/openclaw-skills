# IONOS Email Setup Guide

Step-by-step setup for IONOS email accounts (1&1, IONOS, Strato).

## 1. Gather Credentials

From your IONOS Control Panel:
- Email address (e.g., kontakt@yourdomain.de)
- Email password
- Domain name

## 2. Configure Settings

Standard IONOS settings:

```
IMAP Server: imap.ionos.de
IMAP Port: 993 (SSL/TLS)

SMTP Server: smtp.ionos.de  
SMTP Port: 587 (STARTTLS)
```

## 3. Create Config File

```bash
# Copy template
cp references/email-config.template.env ~/.openclaw/workspace/inbox-ai-config.env

# Edit with your details
nano ~/.openclaw/workspace/inbox-ai-config.env
```

Fill in:
```env
IMAP_SERVER=imap.ionos.de
IMAP_PORT=993
SMTP_SERVER=smtp.ionos.de
SMTP_PORT=587
EMAIL_USERNAME=kontakt@yourdomain.de
EMAIL_PASSWORD=your-actual-password
FROM_NAME=Your Company
```

## 4. Test Connection

```bash
python3 scripts/test_email_connection.py
```

Expected output:
```
✅ IMAP connected! (42 total emails)
✅ SMTP connected!
✅ All tests passed! Ready for deployment.
```

## 5. Common IONOS Issues

### "Authentication failed"
- Verify password (no special characters causing issues)
- Check if 2FA is enabled (disable for automation account)
- Ensure email account is active in IONOS panel

### "Connection refused"
- IONOS sometimes blocks new connections
- Wait 10 minutes, try again
- Check firewall settings

### "SMTP policy restriction"
- Use the Python smtplib script (included)
- Avoid curl for sending

## 6. Security Recommendations

1. **Create dedicated automation email**
   - Don't use your main business email
   - Example: agent@yourdomain.de

2. **Strong password**
   - 16+ characters
   - Unique to this account

3. **Monitor access**
   - Check IONOS logs periodically
   - Watch for unauthorized access

## 7. Going Live

After successful test:

```bash
# Monitor mode first (no auto-replies)
python3 scripts/inbox_processor.py monitor

# Then auto mode (full automation)
python3 scripts/inbox_processor.py auto
```

## IONOS-Specific Features

IONOS supports:
- ✅ Standard IMAP/SMTP
- ✅ SSL/TLS encryption
- ✅ Large mailboxes (up to 50GB)
- ✅ Multiple domains per account

Limitations:
- ⚠️ Rate limits on bulk operations
- ⚠️ Some ports may be blocked on shared hosting
