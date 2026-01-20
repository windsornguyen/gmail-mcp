# gmail-mcp

A Gmail MCP server using OAuth2 bearer token auth via the Dedalus MCP framework.

## Tools

### Messages
- `gmail_list_messages` - List messages with search queries
- `gmail_get_message` - Get a specific message by ID
- `gmail_send_message` - Send an email
- `gmail_trash_message` - Move message to trash
- `gmail_untrash_message` - Remove message from trash
- `gmail_modify_message` - Add/remove labels on a message

### Threads
- `gmail_list_threads` - List email threads (conversations)
- `gmail_get_thread` - Get a thread with all messages
- `gmail_trash_thread` - Move thread to trash

### Labels
- `gmail_list_labels` - List all labels
- `gmail_get_label` - Get label details
- `gmail_create_label` - Create a new label
- `gmail_delete_label` - Delete a user label

### Drafts
- `gmail_list_drafts` - List draft emails
- `gmail_get_draft` - Get a draft by ID
- `gmail_create_draft` - Create a draft
- `gmail_send_draft` - Send a draft
- `gmail_delete_draft` - Delete a draft

### Profile
- `gmail_get_profile` - Get user's Gmail profile

## Authentication

Gmail API requires OAuth2. The access token is provided at runtime via Dedalus credential exchange.

Required OAuth scopes (depending on operations):
- `https://www.googleapis.com/auth/gmail.readonly` - Read-only access
- `https://www.googleapis.com/auth/gmail.send` - Send emails
- `https://www.googleapis.com/auth/gmail.modify` - Modify messages/labels
- `https://www.googleapis.com/auth/gmail.compose` - Create drafts

## Local Development

```bash
cd gmail-mcp
uv sync
uv run python src/main.py
```

## API Reference

- [Gmail API Overview](https://developers.google.com/workspace/gmail/api/guides)
- [Gmail API Reference](https://developers.google.com/workspace/gmail/api/reference/rest)
