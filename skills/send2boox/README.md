# Send2Boox CLI

Quick command-line tool to send files to Boox e-readers via BooxDrop.

## Installation

This skill is already installed in your Claude Code skills directory.

## Quick Start

```bash
# 1. Start BooxDrop on your Boox device
#    (Swipe down → tap BooxDrop)

# 2. Note the IP address shown (e.g., 192.168.1.100:8080)

# 3. Save it for future use
~/.claude/skills/send2boox/scripts/send.sh --set-ip 192.168.1.100:8080

# 4. Send files
~/.claude/skills/send2boox/scripts/send.sh book.epub
```

## Optional: Add to PATH

For easier access, create an alias:

```bash
# Add to ~/.bashrc or ~/.zshrc
alias send2boox="~/.claude/skills/send2boox/scripts/send.sh"

# Then you can just run:
send2boox book.epub
```

## Usage

```bash
# Send a file
send.sh book.epub

# Send multiple files
send.sh book1.epub book2.pdf notes.txt

# Use custom IP (one-time)
send.sh book.epub --ip 192.168.1.50:8080

# Check saved IP
send.sh --show-ip

# Update saved IP
send.sh --set-ip 192.168.1.200:8080
```

## How It Works

1. **BooxDrop** on your Boox creates a local HTTP server
2. The script uploads files via HTTP POST to that server
3. Files appear in `/Download/` folder on your Boox
4. No cloud, no email, just direct LAN transfer

## Requirements

- `curl` (usually pre-installed on Linux)
- Boox and PC on same WiFi network
- BooxDrop running on Boox device

## Supported File Types

EPUB, PDF, MOBI, AZW3, TXT, HTML, RTF, CBR, CBZ, and more.

## Troubleshooting

**"Connection refused"**
- Ensure BooxDrop is running on Boox
- Check both devices are on same WiFi
- Verify IP address is correct

**"File not found"**
- Check file path
- Use absolute paths: `/full/path/to/file.epub`

**"Upload failed"**
- Large files may take time - be patient
- Try restarting BooxDrop
- Check WiFi connection

## License

Created for personal use. Based on Boox BooxDrop functionality.
