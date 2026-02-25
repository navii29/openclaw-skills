# Gmail Auto-Reply Agent v2.0

**Version:** 2.0.0 | **Status:** Production Ready

Professional Gmail automation with AI-powered replies, sentiment analysis, and writing style learning.

## Features

### Core Features (v2.0)
- ✅ **Gmail API Integration** - Direct integration with Gmail via OAuth2
- ✅ **Smart Categorization** - Automatically categorizes emails (urgent, meeting, follow-up, etc.)
- ✅ **Sentiment Analysis** - Detects tone to prioritize negative/urgent emails
- ✅ **Writing Style Learning** - Learns from your sent emails to match your tone
- ✅ **Template Matching** - AI-powered template selection based on email content
- ✅ **HTML + Plain-Text** - Professional multipart emails
- ✅ **Priority Scoring** - 0-1 score for intelligent routing
- ✅ **Persistent Storage** - SQLite database for tracking and analytics
- ✅ **Idempotency** - Never process the same email twice

## Quick Start

### 1. Setup Gmail API Credentials

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project
3. Enable Gmail API
4. Create OAuth2 credentials (Desktop application)
5. Download `credentials.json` to `~/.openclaw/gmail_credentials.json`

### 2. Install Dependencies

```bash
pip install google-auth google-auth-oauthlib google-auth-httplib2 google-api-python-client
```

### 3. Run the Agent

```bash
# First time: authenticate and learn from sent emails
python3 scripts/gmail_agent.py --client-name "John Doe" --learn

# Process inbox (draft mode)
python3 scripts/gmail_agent.py --max-emails 10

# Auto-send high priority replies
python3 scripts/gmail_agent.py --auto-send --max-emails 20

# View statistics
python3 scripts/gmail_agent.py --stats
```

## Email Categories

The agent automatically categorizes emails:

| Category | Description | Priority Boost |
|----------|-------------|----------------|
| `urgent` | Urgent requests, ASAP, deadlines | +0.4 |
| `meeting_request` | Meeting, call, scheduling requests | +0.2 |
| `follow_up` | Status updates, follow-ups | +0.1 |
| `question` | Questions, how-to requests | +0.1 |
| `acknowledgment` | Thank you messages | -0.1 |
| `spam` | Promotional, unwanted | -0.5 (ignored) |
| `newsletter` | Subscriptions, digests | -0.3 (ignored) |

## Sentiment Analysis

Detects email tone for prioritization:

| Sentiment | Trigger Words | Priority Impact |
|-----------|---------------|-----------------|
| Very Negative | terrible, awful, hate, angry | +0.3 |
| Negative | bad, problem, disappointed | +0.1 |
| Neutral | (default) | 0 |
| Positive | good, great, thanks | 0 |
| Very Positive | amazing, excellent, love | 0 |

## Writing Style Learning

The agent learns from your sent emails:

- **Greeting style**: Hi, Hello, Dear, Hey
- **Sign-off**: Best, Thanks, Regards, Cheers
- **Formality level**: 0-1 scale (casual to formal)
- **Sentence length**: Average words per sentence
- **Emoji usage**: Whether you use emojis
- **Reply length**: Average word count

## Template System

Built-in templates for common scenarios:

1. **Urgent Acknowledgment** - Quick response to urgent emails
2. **Meeting Request** - Respond to meeting/call requests
3. **Follow-up Response** - Reply to status check-ins
4. **Question Response** - Answer questions professionally
5. **General Acknowledgment** - Generic acknowledgment

## Auto-Send Rules

When `--auto-send` is enabled:

- Only emails with `priority_score > 0.7` are auto-sent
- Spam and newsletters are never auto-replied
- All replies are stored in database for review
- Reply content is always logged

## Database Schema

SQLite database at `~/.openclaw/gmail_auto_reply.db`:

**processed_emails table:**
- message_id (primary key)
- thread_id
- sender, subject
- category, sentiment
- priority_score
- reply_sent
- processed_at

**sent_replies table:**
- original_message_id
- reply_body
- sent_at

## Configuration Files

- `~/.openclaw/gmail_credentials.json` - Google OAuth2 credentials
- `~/.openclaw/gmail_token.pickle` - Cached authentication token
- `~/.openclaw/gmail_auto_reply.db` - Processing database
- `~/.openclaw/writing_style.json` - Learned writing style cache

## CLI Reference

```bash
python3 scripts/gmail_agent.py [options]

Options:
  --client-name NAME    Your name for signatures (default: Me)
  --max-emails N        Max emails to process (default: 20)
  --auto-send           Auto-send high priority replies
  --learn               Learn from sent emails first
  --stats               Show statistics and exit
```

## Safety Features

1. **Idempotency** - Emails tracked by message_id, never duplicated
2. **Priority Filtering** - Low priority emails can be skipped
3. **Draft Mode** - Default mode generates drafts without sending
4. **Auto-Send Threshold** - Only high priority (>0.7) auto-sent
5. **Category Exclusions** - Spam and newsletters ignored
6. **Persistent Logging** - All actions logged to database

## Example Output

```
✅ Processed 5 emails
  📝 Draft [meeting_request] Re: Project kickoff meeting...
  📤 Sent [urgent] Urgent: Server down...
  📝 Draft [question] Question about pricing...
  📝 Draft [follow_up] Following up on proposal...
  📝 Draft [acknowledgment] Thank you for the call...
```

## Use Cases

### Use Case 1: Executive Inbox Management
Process 50+ daily emails, auto-reply to urgent ones, draft responses for others.

### Use Case 2: Customer Support
Auto-acknowledge support requests, prioritize negative sentiment emails.

### Use Case 3: Meeting Coordination
Respond to meeting requests with availability questions automatically.

## Changelog

### v2.0.0 (2026-02-25) - Complete Rewrite
- Complete Python implementation with Gmail API
- Smart categorization with keyword extraction
- Sentiment analysis for prioritization
- Writing style learning from sent emails
- Template matching system
- HTML + Plain-text multipart emails
- SQLite database for tracking
- CLI interface with argparse
- Idempotency protection
- Statistics and analytics

### v1.0.0 (2026-02-18) - Initial Release
- Basic template-based reply system
- Manual draft generation
- No automation
