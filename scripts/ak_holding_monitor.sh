#!/bin/bash
# AK Holding Auto-Reply Monitor
# Checks for replies from kara@ak-holding-gmbh.de and auto-responds with Calendly

GMAIL_USER="edlmairfridolin@gmail.com"
GMAIL_PASS="uwwf tlao blzj iecl"
LAST_CHECK_FILE="/tmp/ak_holding_last_check"

# Get last check timestamp
if [ -f "$LAST_CHECK_FILE" ]; then
    LAST_CHECK=$(cat "$LAST_CHECK_FILE")
else
    LAST_CHECK="21-Feb-2026"
fi

# Search for unread emails from AK Holding since last check
curl -s --url "imaps://imap.gmail.com:993/INBOX" \
  --user "$GMAIL_USER:$GMAIL_PASS" \
  --ssl-reqd \
  -X "SEARCH UNSEEN FROM kara@ak-holding-gmbh.de" 2>/dev/null | grep -o '[0-9]\+' > /tmp/ak_holding_new_emails.txt

if [ -s /tmp/ak_holding_new_emails.txt ]; then
    echo "New emails from Kara found"
    # Trigger notification for agent to reply
    echo "AK_HOLDING_REPLY_NEEDED"
else
    echo "No new emails from Kara"
fi

# Update last check
date +"%d-%b-%Y" > "$LAST_CHECK_FILE"