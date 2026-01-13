# Bedrock Authentication Script

This script automatically fetches and exports AWS Bedrock environment variables for Claude Code.

## Setup

The script is already executable and located at:
```
/Users/alexkamer/personal_knowledge_assistant/bedrock-auth.sh
```

### Add Alias to Your Shell

Add this to your `~/.zshrc` (or `~/.bashrc` if using bash):

```bash
# Bedrock authentication alias
alias bedrock-auth='eval "$(/Users/alexkamer/personal_knowledge_assistant/bedrock-auth.sh)"'

# Optional: Add variants for different regions or users
alias bedrock-auth-west='eval "$(/Users/alexkamer/personal_knowledge_assistant/bedrock-auth.sh atiaide us-west-2)"'
```

Then reload your shell configuration:
```bash
source ~/.zshrc
```

## Usage

### Basic Usage

Simply run:
```bash
bedrock-auth
```

This will:
1. Fetch a new token from the API
2. Export all required environment variables to your current shell session
3. Show when the token expires

### Advanced Usage

You can pass custom userid and region as arguments:

```bash
# Custom userid
eval "$(/Users/alexkamer/personal_knowledge_assistant/bedrock-auth.sh myuserid us-east-2)"

# Different region
eval "$(/Users/alexkamer/personal_knowledge_assistant/bedrock-auth.sh atiaide us-west-2)"
```

### Create Custom Aliases

Add to your `~/.zshrc` for quick access to different environments:

```bash
alias bedrock-dev='eval "$(/Users/alexkamer/personal_knowledge_assistant/bedrock-auth.sh dev-user us-east-1)"'
alias bedrock-prod='eval "$(/Users/alexkamer/personal_knowledge_assistant/bedrock-auth.sh prod-user us-west-2)"'
```

## What Gets Exported

The script exports the following environment variables:
- `AWS_REGION` - AWS region
- `AWS_BEARER_TOKEN_BEDROCK` - Bearer token for Bedrock API
- `ANTHROPIC_DEFAULT_SONNET_MODEL` - ARN for Claude Sonnet 4.5
- `ANTHROPIC_DEFAULT_HAIKU_MODEL` - ARN for Claude Haiku 4.5
- `ANTHROPIC_DEFAULT_OPUS_MODEL` - ARN for Claude Opus 4.5
- `CLAUDE_CODE_USE_BEDROCK` - Flag to enable Bedrock in Claude Code

## Token Expiration

Tokens are valid for 12 hours. The script will display the expiration time when you run it.

## Requirements

- `curl` (pre-installed on macOS)
- `jq` (optional but recommended) - Install with: `brew install jq`

If `jq` is not installed, the script will use a fallback parsing method.

## Troubleshooting

### "Command not found" error
Make sure you've:
1. Added the alias to `~/.zshrc`
2. Run `source ~/.zshrc` to reload your configuration

### "Failed to fetch token" error
Check your internet connection and verify the API endpoint is accessible:
```bash
curl -s https://tokengen.aide.infra-host.com/health
```

### Variables not persisting
Remember that `eval` only sets variables for the current shell session. You'll need to run `bedrock-auth` in each new terminal window/tab, or add it to your shell startup script.

## Script Location

The script is version-controlled in your repository:
```
/Users/alexkamer/personal_knowledge_assistant/bedrock-auth.sh
```
