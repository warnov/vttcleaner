import re
import html
import os
import argparse


def main():
    parser = argparse.ArgumentParser(description='Clean VTT/transcript files')
    parser.add_argument('file', nargs='?', help='Path to the input file')
    parser.add_argument('--type', '-t', choices=['1', '2', '3'],
                        help='File type: 1=Pure VTT, 2=Word/Teams transcript, 3=Zoom VTT')
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
        elif ext == '.txt':
            option = '2'
        else:
            print("Select the type of file to process:")
            print("1. Pure VTT")
            print("2. Text copied from Word (Teams transcript)")
            print("3. Zoom VTT transcript")
            option = input("Enter 1, 2, or 3: ").strip()
    else:
        print("Select the type of file to process:")
        print("1. Pure VTT")
        print("2. Text copied from Word (Teams transcript)")
        print("3. Zoom VTT transcript")
        option = input("Enter 1, 2, or 3: ").strip()

    # If no file was passed as argument, ask interactively
    if not file_path:
        path_prompts = {
            "1": "Enter the path to the VTT file: ",
            "2": "Enter the path to the .txt file copied from Word: ",
            "3": "Enter the path to the Zoom VTT file: ",
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
    else:
        print("Invalid option. Please try again.")


if __name__ == "__main__":
    main()
