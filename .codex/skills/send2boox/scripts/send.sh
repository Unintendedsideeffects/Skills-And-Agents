#!/bin/bash
# Send files to Boox e-reader via BooxDrop

set -e

CONFIG_DIR="${HOME}/.config/send2boox"
CONFIG_FILE="${CONFIG_DIR}/config"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Create config directory if it doesn't exist
mkdir -p "${CONFIG_DIR}"

show_help() {
    cat << EOF
Send files to Boox e-reader via BooxDrop

Usage:
    send.sh [OPTIONS] <file1> [file2] [...]
    send.sh --set-ip <IP:PORT>
    send.sh --show-ip

Options:
    --ip <address>        Use specific IP for this transfer (format: IP:PORT)
    --set-ip <address>    Save IP address for future use
    --show-ip            Display currently saved IP address
    -h, --help           Show this help message

Examples:
    # Save Boox IP address
    send.sh --set-ip 192.168.1.100:8080

    # Send a file using saved IP
    send.sh book.epub

    # Send file with custom IP (one-time)
    send.sh book.epub --ip 192.168.1.50:8080

    # Send multiple files
    send.sh book1.epub book2.pdf

Setup:
    1. On Boox: Swipe down → tap BooxDrop
    2. Note the IP address shown (e.g., http://192.168.1.100:8080)
    3. Run: send.sh --set-ip <IP:PORT>
    4. Send files: send.sh <file>

EOF
    exit 0
}

# Get saved IP
get_saved_ip() {
    if [[ -f "${CONFIG_FILE}" ]]; then
        cat "${CONFIG_FILE}"
    else
        echo ""
    fi
}

# Save IP to config
save_ip() {
    local ip="$1"
    # Remove http:// or https:// prefix if present
    ip="${ip#http://}"
    ip="${ip#https://}"
    echo "${ip}" > "${CONFIG_FILE}"
    echo -e "${GREEN}✓${NC} Saved Boox IP: ${ip}"
}

# Show saved IP
show_ip() {
    local ip=$(get_saved_ip)
    if [[ -z "${ip}" ]]; then
        echo -e "${YELLOW}No IP address saved yet${NC}"
        echo "Run: send.sh --set-ip <IP:PORT>"
        exit 1
    else
        echo "Saved Boox IP: ${ip}"
    fi
    exit 0
}

# Upload file to Boox
upload_file() {
    local file="$1"
    local ip="$2"

    # Check if file exists
    if [[ ! -f "${file}" ]]; then
        echo -e "${RED}✗${NC} File not found: ${file}"
        return 1
    fi

    local filename=$(basename "${file}")
    local url="http://${ip}/upload"

    echo -n "Uploading ${filename} to Boox... "

    # Use curl to upload the file
    if curl -f -s -F "file=@${file}" "${url}" > /dev/null 2>&1; then
        echo -e "${GREEN}✓ Success${NC}"
        return 0
    else
        echo -e "${RED}✗ Failed${NC}"
        echo -e "${RED}Error:${NC} Could not upload to ${ip}"
        echo "Make sure:"
        echo "  1. BooxDrop is running on your Boox (swipe down → BooxDrop)"
        echo "  2. Both devices are on the same WiFi network"
        echo "  3. The IP address is correct (currently: ${ip})"
        return 1
    fi
}

# Parse arguments
FILES=()
CUSTOM_IP=""

while [[ $# -gt 0 ]]; do
    case $1 in
        -h|--help)
            show_help
            ;;
        --show-ip)
            show_ip
            ;;
        --set-ip)
            if [[ -z "$2" ]]; then
                echo -e "${RED}Error:${NC} --set-ip requires an IP address"
                echo "Usage: send.sh --set-ip 192.168.1.100:8080"
                exit 1
            fi
            save_ip "$2"
            exit 0
            ;;
        --ip)
            if [[ -z "$2" ]]; then
                echo -e "${RED}Error:${NC} --ip requires an IP address"
                exit 1
            fi
            CUSTOM_IP="$2"
            # Remove http:// prefix if present
            CUSTOM_IP="${CUSTOM_IP#http://}"
            CUSTOM_IP="${CUSTOM_IP#https://}"
            shift 2
            ;;
        -*)
            echo -e "${RED}Error:${NC} Unknown option: $1"
            echo "Run 'send.sh --help' for usage"
            exit 1
            ;;
        *)
            FILES+=("$1")
            shift
            ;;
    esac
done

# Check if we have files to send
if [[ ${#FILES[@]} -eq 0 ]]; then
    echo -e "${RED}Error:${NC} No files specified"
    echo "Run 'send.sh --help' for usage"
    exit 1
fi

# Determine which IP to use
BOOX_IP="${CUSTOM_IP}"
if [[ -z "${BOOX_IP}" ]]; then
    BOOX_IP=$(get_saved_ip)
fi

if [[ -z "${BOOX_IP}" ]]; then
    echo -e "${RED}Error:${NC} No Boox IP address configured"
    echo ""
    echo "Setup instructions:"
    echo "  1. On Boox: Swipe down → tap BooxDrop"
    echo "  2. Note the IP address shown (e.g., 192.168.1.100:8080)"
    echo "  3. Run: send.sh --set-ip <IP:PORT>"
    exit 1
fi

echo "Using Boox IP: ${BOOX_IP}"
echo ""

# Upload each file
SUCCESS_COUNT=0
FAIL_COUNT=0

for file in "${FILES[@]}"; do
    if upload_file "${file}" "${BOOX_IP}"; then
        ((SUCCESS_COUNT++))
    else
        ((FAIL_COUNT++))
    fi
done

echo ""
if [[ ${FAIL_COUNT} -eq 0 ]]; then
    echo -e "${GREEN}✓ All files uploaded successfully (${SUCCESS_COUNT}/${#FILES[@]})${NC}"
    exit 0
else
    echo -e "${YELLOW}⚠ Upload completed with errors${NC}"
    echo "  Success: ${SUCCESS_COUNT}"
    echo "  Failed: ${FAIL_COUNT}"
    exit 1
fi
