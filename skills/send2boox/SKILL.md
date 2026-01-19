---
name: send2boox
description: Send files to Boox e-reader via BooxDrop over local WiFi. Use when the user wants to transfer EPUB, PDF, or other files to their Boox device quickly.
---

# Send2Boox

Quickly send files to your Boox e-reader via BooxDrop using the command line.

## Quick Start

```bash
# First time: set your Boox IP address
scripts/send.sh --set-ip 192.168.1.100:8080

# Send a file
scripts/send.sh /path/to/book.epub

# Send with custom IP (one-time)
scripts/send.sh /path/to/book.epub --ip 192.168.1.50:8080
```

## Instructions

1. Ask user to start BooxDrop on their Boox device (swipe down → tap BooxDrop)
2. Get the IP address shown on the Boox screen (e.g., `192.168.1.100:8080`)
3. If first time, save the IP: `scripts/send.sh --set-ip <IP>`
4. Send the file: `scripts/send.sh <file_path>`
5. Confirm successful upload

## Setup

**On Boox Device:**
1. Swipe down from top to open Control Center
2. Tap **BooxDrop**
3. Note the IP address displayed (e.g., `http://192.168.1.100:8080`)

**On Linux PC:**
```bash
# Save the Boox IP for future use
scripts/send.sh --set-ip 192.168.1.100:8080
```

## Usage

```bash
# Send a single file (uses saved IP)
scripts/send.sh /path/to/book.epub

# Send file with custom IP
scripts/send.sh /path/to/book.epub --ip 192.168.1.100:8080

# Send multiple files
scripts/send.sh book1.epub book2.pdf document.mobi

# Check saved IP
scripts/send.sh --show-ip

# Update saved IP
scripts/send.sh --set-ip 192.168.1.200:8080
```

## Options

| Option | Description |
|--------|-------------|
| `--ip <address>` | Use specific IP for this transfer (format: `IP:PORT`) |
| `--set-ip <address>` | Save IP address for future use |
| `--show-ip` | Display currently saved IP address |
| `-h, --help` | Show help message |

## Features

- **Fast**: Direct LAN transfer, no cloud intermediary
- **Simple**: Just drag files or use CLI
- **Persistent IP**: Saves last used IP address
- **Multiple files**: Send several files at once
- **Auto-detection**: Validates IP format and connectivity

## Supported Formats

Boox supports: EPUB, PDF, MOBI, AZW3, TXT, HTML, RTF, CBR, CBZ, and more.

## Troubleshooting

**Connection refused:**
- Ensure BooxDrop is running on your Boox (swipe down → BooxDrop)
- Check both devices are on the same WiFi network
- Verify the IP address matches what's shown on Boox

**File not found:**
- Check the file path is correct
- Use absolute paths if relative paths fail

**Upload failed:**
- Large files may take longer - wait for confirmation
- Try sending file again
- Restart BooxDrop on Boox device

## Notes

- BooxDrop must be active on the Boox device during transfer
- Files are uploaded to the `/Download/` folder on Boox
- The Boox IP address may change if it reconnects to WiFi
- Works only on local network (both devices must be on same WiFi)

## Example Workflow

```bash
# 1. User starts BooxDrop on Boox, sees IP: 192.168.1.100:8080
# 2. Assistant saves the IP
scripts/send.sh --set-ip 192.168.1.100:8080

# 3. Send newly created EPUB
scripts/send.sh "/home/user/Documents/My Book.epub"

# Output: ✓ Successfully uploaded My Book.epub to Boox
```
