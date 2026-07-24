import re
import html
import os
import argparse


def parse_caption_vtt(lines):
    """Parse generic VTT captions into a continuous text without metadata."""
    timestamp_re = re.compile(
        r'^\d{2}:\d{2}:\d{2}\.\d{3}\s+-->\s+\d{2}:\d{2}:\d{2}\.\d{3}'
    )
    text_chunks = []
    i = 0

    while i < len(lines):
        line = lines[i].strip()

        # Skip WEBVTT header and empty lines.
        if not line or line == 'WEBVTT':
            i += 1
            continue

        # Cues may start with an identifier line (GUID, number, or other token).
        if i + 1 < len(lines) and timestamp_re.match(lines[i + 1].strip()):
            i += 1
            line = lines[i].strip()

        if timestamp_re.match(line):
            i += 1
            cue_lines = []
            while i < len(lines):
                cue_line = lines[i].strip()
                if not cue_line:
                    break
                cue_lines.append(html.unescape(cue_line))
                i += 1

            if cue_lines:
                # Join wrapped lines inside a cue as a single sentence fragment.
                text_chunks.append(' '.join(cue_lines))
        else:
            i += 1

    cleaned_text = re.sub(r'\s+', ' ', ' '.join(text_chunks)).strip()
    return cleaned_text


def parse_teams_transcript_copy(lines):
    """Parse text copied from the Teams transcript panel (browser/client UI).

    Expected block format (repeated per utterance):
        Speaker Name (OPTCODE)
        55 minutes 18 seconds55:18
        Speaker Name (OPTCODE) 55 minutes 18 seconds
        Actual speech text.
    """
    # Matches the verbose+compact time line, e.g. "55 minutes 18 seconds55:18"
    time_line_re = re.compile(r'^\d+\s+(hour|hours|minute|minutes|second|seconds)')
    time_unit = r'(?:hour|hours|minute|minutes|second|seconds)'
    # Matches redundant accessibility repeat lines, e.g.
    # "Speaker Name (OPTCODE) 55 minutes 18 seconds".
    repeat_line_re = re.compile(
        rf'^(.+?)\s+\d+\s+{time_unit}(?:\s+\d+\s+{time_unit})*\s*$'
    )

    interactions = []
    current_speaker = None
    current_speaker_raw = None
    current_text = []

    def clean_speaker_name(speaker_name):
        return re.sub(r'\s*\([A-Z0-9]+\)\s*$', '', speaker_name).strip()

    def is_redundant_repeat_line(text):
        if not current_speaker_raw:
            return False
        match = repeat_line_re.match(text)
        return bool(match and clean_speaker_name(match.group(1)) == current_speaker_raw)

    i = 0
    while i < len(lines):
        line = lines[i].strip()

        if not line:
            i += 1
            continue

        # A speaker header is a non-empty line whose NEXT non-empty line is a time line.
        next_idx = i + 1
        while next_idx < len(lines) and not lines[next_idx].strip():
            next_idx += 1
        next_line = lines[next_idx].strip() if next_idx < len(lines) else ''

        if time_line_re.match(next_line):
            # Flush previous speaker
            if current_speaker and current_text:
                interactions.append(f"{current_speaker} {' '.join(current_text)}")

            # Clean speaker name: remove trailing account code like (WARNOV)
            speaker_raw = clean_speaker_name(line)
            parts = speaker_raw.split()
            if len(parts) >= 2:
                speaker = f"{parts[0]}{parts[1][0]}:"
            else:
                speaker = f"{parts[0]}:"

            current_speaker = speaker
            current_speaker_raw = speaker_raw
            current_text = []

            i += 1  # move to time line
            i += 1  # skip time line
            # Skip the redundant repeat line (speaker name + time text)
            if i < len(lines) and is_redundant_repeat_line(lines[i].strip()):
                i += 1
        else:
            if is_redundant_repeat_line(line):
                i += 1
                continue
            if current_speaker and line:
                current_text.append(line)
            i += 1

    # Flush last speaker
    if current_speaker and current_text:
        interactions.append(f"{current_speaker} {' '.join(current_text)}")

    return interactions


def parse_whatsapp_chat(lines):
    """Parse a WhatsApp exported chat into simplified speaker interactions.

    Expected line format (one per message):
        M/D/YY, HH:MM - Speaker Name: message text

    Notes:
    - Date/time may use 1 or 2 digit components, optional seconds and AM/PM.
    - System messages (e.g. encryption notice) have no "Speaker:" part and
      are skipped.
    - Messages can span multiple physical lines; continuation lines do not
      start with a date prefix and are appended to the current message.
    """
    # Matches the date/time prefix and captures the remaining content.
    message_re = re.compile(
        r'^\d{1,2}/\d{1,2}/\d{2,4},\s+\d{1,2}:\d{2}(?::\d{2})?'
        r'(?:\s*[APap][Mm])?\s+-\s+(.*)$'
    )
    # Within the content, separate "Speaker Name: text".
    speaker_re = re.compile(r'^([^:]+):\s(.*)$')

    interactions = []
    current_speaker = None
    current_text = []

    def flush():
        if current_speaker and current_text:
            interactions.append(f"{current_speaker} {' '.join(current_text)}")

    for raw_line in lines:
        line = raw_line.rstrip('\n')
        match = message_re.match(line.strip())

        if match:
            content = match.group(1).strip()
            speaker_match = speaker_re.match(content)

            if not speaker_match:
                # System/status message without a speaker; skip it.
                continue

            speaker_raw = speaker_match.group(1).strip()
            text = speaker_match.group(2).strip()

            # Simplify name: first word + first letter of the second word.
            parts = speaker_raw.split()
            if len(parts) >= 2:
                speaker = f"{parts[0]}{parts[1][0]}:"
            else:
                speaker = f"{parts[0]}:"

            if speaker == current_speaker:
                if text:
                    current_text.append(text)
            else:
                flush()
                current_speaker = speaker
                current_text = [text] if text else []
        else:
            # Continuation of the previous multi-line message.
            stripped = line.strip()
            if current_speaker and stripped:
                current_text.append(stripped)

    flush()
    return interactions


def detect_txt_type(file_path):
    """Inspect a .txt file content and guess the transcript format.

    Returns the option string used by main():
        '5' = WhatsApp chat export
        '4' = Teams Transcript Copy (copied from Teams UI panel)
        '2' = Text copied from Word (Teams transcript)
    Returns None if the format cannot be confidently detected.
    """
    whatsapp_re = re.compile(r'^\d{1,2}/\d{1,2}/\d{2,4},\s+\d{1,2}:\d{2}')
    teams_copy_re = re.compile(r'^\d+\s+(hour|hours|minute|minutes|second|seconds)')
    word_re = re.compile(r'^.+\s{2,}\d{1,2}:\d{2}$')

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = [ln.strip() for ln in f.read().splitlines() if ln.strip()]
    except Exception:
        return None

    sample = lines[:50]

    whatsapp_hits = sum(1 for ln in sample if whatsapp_re.match(ln))
    teams_copy_hits = sum(1 for ln in sample if teams_copy_re.match(ln))
    word_hits = sum(1 for ln in sample if word_re.match(ln))

    if whatsapp_hits and whatsapp_hits >= teams_copy_hits and whatsapp_hits >= word_hits:
        return '5'
    if teams_copy_hits and teams_copy_hits >= word_hits:
        return '4'
    if word_hits:
        return '2'
    return None


def main():
    parser = argparse.ArgumentParser(description='Clean VTT/transcript files')
    parser.add_argument('file', nargs='?', help='Path to the input file')
    parser.add_argument('--type', '-t', choices=['1', '2', '3', '4', '5'],
                        help='File type: 1=Pure VTT, 2=Word/Teams transcript, 3=Zoom VTT, 4=Teams Transcript Copy, 5=WhatsApp chat export')
    args = parser.parse_args()

    # Determine file path first (needed for extension-based auto-detection)
    if args.file:
        file_path = args.file.strip('"').strip("'")
    else:
        file_path = None

    # Determine option (file type)
    if args.type:
        option = args.type
    elif file_path:
        ext = os.path.splitext(file_path)[1].lower()
        if ext == '.vtt':
            option = '1'
        else:
            # Try to auto-detect the transcript format from the content.
            detected = detect_txt_type(file_path)
            if detected:
                names = {
                    '2': 'Word/Teams transcript',
                    '4': 'Teams Transcript Copy',
                    '5': 'WhatsApp chat export',
                }
                print(f"Auto-detected format: {names.get(detected, detected)}")
                option = detected
            else:
                print("Could not auto-detect the format.")
                print("Select the type of file to process:")
                print("1. Pure VTT")
                print("2. Text copied from Word (Teams transcript)")
                print("3. Zoom VTT transcript")
                print("4. Teams Transcript Copy (copied from Teams UI panel)")
                print("5. WhatsApp chat export")
                option = input("Enter 1, 2, 3, 4, or 5: ").strip()
    else:
        print("Select the type of file to process:")
        print("1. Pure VTT")
        print("2. Text copied from Word (Teams transcript)")
        print("3. Zoom VTT transcript")
        print("4. Teams Transcript Copy (copied from Teams UI panel)")
        print("5. WhatsApp chat export")
        option = input("Enter 1, 2, 3, 4, or 5: ").strip()

    # If no file was passed as argument, ask interactively
    if not file_path:
        path_prompts = {
            "1": "Enter the path to the VTT file: ",
            "2": "Enter the path to the .txt file copied from Word: ",
            "3": "Enter the path to the Zoom VTT file: ",
            "4": "Enter the path to the .txt file copied from Teams UI: ",
            "5": "Enter the path to the WhatsApp chat export (.txt): ",
        }
        file_path = input(path_prompts.get(option, "Enter the path to the file: ")).strip().strip('"').strip("'")

    if option == "1":
        vtt_path = file_path
        try:
            with open(vtt_path, 'r', encoding='utf-8') as file:
                VTT_content = file.read()
            print("VTT file loaded successfully.")

            # Split into lines and remove the first two lines (header and first id)
            lines = VTT_content.splitlines()
            if len(lines) > 2:
                lines = lines[2:]

            # Generic closed-caption VTTs usually do not contain speaker tags.
            # Process them as plain continuous text without speaker labels.
            if '<v ' not in VTT_content:
                cleaned_text = parse_caption_vtt(lines)
                base, ext = os.path.splitext(vtt_path)
                out_path = f"{base}_cleaned.txt"
                with open(out_path, 'w', encoding='utf-8') as out_file:
                    out_file.write(cleaned_text + '\n')
                print(f"Processed caption text saved to {out_path}")
                return

            interactions = []
            current_speaker = None
            current_text = []

            # Process all transcript lines, both with and without speaker tags
            speaker_pattern = re.compile(r'<v ([^>]+)>(.*?)</v>', re.DOTALL)
            
            i = 0
            while i < len(lines):
                line = lines[i].strip()
                
                # Skip empty lines and timestamp/ID lines
                if not line or '-->' in line or re.match(r'^[a-f0-9-]+/\d+-\d+$', line):
                    i += 1
                    continue
                
                # Check if line has speaker tag
                if '<v ' in line:
                    # Collect all lines until </v> is found
                    full_block = [line]
                    while i + 1 < len(lines) and '</v>' not in line:
                        i += 1
                        line = lines[i].strip()
                        full_block.append(line)
                    
                    # Extract speaker and text
                    block_text = ' '.join(full_block)
                    match = speaker_pattern.search(block_text)
                    if match:
                        speaker_raw = match.group(1)
                        text = match.group(2).strip()
                        
                        # Simplify speaker name
                        parts = speaker_raw.split()
                        if len(parts) >= 2:
                            first = parts[0]
                            second = parts[1][0]
                            speaker = f"{first}{second}:"
                        else:
                            speaker = f"{parts[0]}:"
                        
                        speaker = html.unescape(speaker)
                        text = html.unescape(text)
                        
                        if speaker == current_speaker:
                            current_text.append(text)
                        else:
                            if current_speaker:
                                interactions.append(f"{current_speaker} {' '.join(current_text)}")
                            current_speaker = speaker
                            current_text = [text]
                else:
                    # Line without speaker tag - treat as unknown speaker
                    text = html.unescape(line)
                    speaker = "Unknown:"
                    
                    if speaker == current_speaker:
                        current_text.append(text)
                    else:
                        if current_speaker:
                            interactions.append(f"{current_speaker} {' '.join(current_text)}")
                        current_speaker = speaker
                        current_text = [text]
                
                i += 1
            
            # Add final interaction
            if current_speaker:
                interactions.append(f"{current_speaker} {' '.join(current_text)}")

            # Save interactions to a file
            base, ext = os.path.splitext(vtt_path)
            out_path = f"{base}_cleaned.txt"
            with open(out_path, 'w', encoding='utf-8') as out_file:
                for interaction in interactions:
                    out_file.write(interaction + '\n')
            print(f"Processed interactions saved to {out_path}")

        except Exception as e:
            print(f"Error reading file: {e}")

    elif option == "2":
        txt_path = file_path
        try:
            with open(txt_path, 'r', encoding='utf-8') as file:
                txt_content = file.read()
            print("Text file loaded successfully.")

            # Process the text to extract dialogues
            lines = txt_content.splitlines()
            interactions = []
            current_speaker = None
            current_text = []

            # Regex to detect speaker line: Name Surname   HH:MM
            speaker_line_re = re.compile(r'^(.+?)\s{2,}(\d{1,2}:\d{2})$')

            for line in lines:
                line = line.strip()
                if not line:
                    continue
                match = speaker_line_re.match(line)
                if match:
                    # If new speaker, save the previous one
                    if current_speaker:
                        interactions.append(f"{current_speaker} {' '.join(current_text)}")
                    speaker_raw = match.group(1)
                    # Simplify name: only first name and first letter of the second
                    parts = speaker_raw.split()
                    if len(parts) >= 2:
                        first = parts[0]
                        second = parts[1][0]
                        speaker = f"{first}{second}:"
                    else:
                        speaker = f"{parts[0]}:"
                    current_speaker = speaker
                    current_text = []
                else:
                    # Line of text for the current speaker
                    if current_speaker:
                        current_text.append(line)
            # Save the last interaction
            if current_speaker and current_text:
                interactions.append(f"{current_speaker} {' '.join(current_text)}")

            # Save result
            base, ext = os.path.splitext(txt_path)
            out_path = f"{base}_cleaned.txt"
            with open(out_path, 'w', encoding='utf-8') as out_file:
                for interaction in interactions:
                    out_file.write(interaction + '\n')
            print(f"Processed interactions saved to {out_path}")

        except Exception as e:
            print(f"Error reading file: {e}")

    elif option == "3":
        vtt_path = file_path
        try:
            with open(vtt_path, 'r', encoding='utf-8') as file:
                VTT_content = file.read()
            print("Zoom VTT file loaded successfully.")

            # Split into lines
            lines = VTT_content.splitlines()
            
            interactions = []
            current_speaker = None
            current_text = []

            # Zoom VTT format: number, timestamp, speaker: text
            i = 0
            while i < len(lines):
                line = lines[i].strip()
                
                # Skip empty lines, WEBVTT header, numbers, and timestamp lines
                if not line or line == 'WEBVTT' or line.isdigit() or '-->' in line:
                    i += 1
                    continue
                
                # Check if line contains speaker and text (speaker: text format)
                if ':' in line:
                    parts = line.split(':', 1)
                    if len(parts) == 2:
                        speaker_raw = parts[0].strip()
                        text = parts[1].strip()
                        
                        # Simplify speaker name
                        speaker_parts = speaker_raw.split()
                        if len(speaker_parts) >= 2:
                            first = speaker_parts[0]
                            second = speaker_parts[1][0]
                            speaker = f"{first}{second}:"
                        else:
                            speaker = f"{speaker_parts[0]}:"
                        
                        speaker = html.unescape(speaker)
                        text = html.unescape(text)
                        
                        if speaker == current_speaker:
                            current_text.append(text)
                        else:
                            if current_speaker:
                                interactions.append(f"{current_speaker} {' '.join(current_text)}")
                            current_speaker = speaker
                            current_text = [text]
                
                i += 1
            
            # Add final interaction
            if current_speaker:
                interactions.append(f"{current_speaker} {' '.join(current_text)}")

            # Save interactions to a file
            base, ext = os.path.splitext(vtt_path)
            out_path = f"{base}_cleaned.txt"
            with open(out_path, 'w', encoding='utf-8') as out_file:
                for interaction in interactions:
                    out_file.write(interaction + '\n')
            print(f"Processed interactions saved to {out_path}")

        except Exception as e:
            print(f"Error reading file: {e}")
    elif option == "4":
        txt_path = file_path
        try:
            with open(txt_path, 'r', encoding='utf-8') as file:
                txt_content = file.read()
            print("Teams Transcript Copy file loaded successfully.")

            lines = txt_content.splitlines()
            interactions = parse_teams_transcript_copy(lines)

            base, ext = os.path.splitext(txt_path)
            out_path = f"{base}_cleaned.txt"
            with open(out_path, 'w', encoding='utf-8') as out_file:
                for interaction in interactions:
                    out_file.write(interaction + '\n')
            print(f"Processed interactions saved to {out_path}")

        except Exception as e:
            print(f"Error reading file: {e}")
    elif option == "5":
        txt_path = file_path
        try:
            with open(txt_path, 'r', encoding='utf-8') as file:
                txt_content = file.read()
            print("WhatsApp chat export loaded successfully.")

            lines = txt_content.splitlines()
            interactions = parse_whatsapp_chat(lines)

            base, ext = os.path.splitext(txt_path)
            out_path = f"{base}_cleaned.txt"
            with open(out_path, 'w', encoding='utf-8') as out_file:
                for interaction in interactions:
                    out_file.write(interaction + '\n')
            print(f"Processed interactions saved to {out_path}")

        except Exception as e:
            print(f"Error reading file: {e}")
    else:
        print("Invalid option. Please try again.")


if __name__ == "__main__":
    main()
