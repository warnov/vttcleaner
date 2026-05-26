
# VTTCleaner

VTTCleaner is a Python console application designed to process VTT files from Microsoft Teams, plain text transcripts copied from Word (Teams transcript format), and Zoom VTT transcripts. It extracts and simplifies speaker interactions, making transcripts much more compact and suitable for use with Large Language Models (LLMs) by drastically reducing the required number of tokens.


## Features

- Removes unnecessary metadata and timestamps from VTT files.
- Supports processing of plain text transcripts copied from Word (Teams transcript format).
- Supports processing of Zoom VTT transcript files.
- Supports processing of non-conversational closed-caption VTT files (without speaker tags).
- Simplifies speaker names to "FirstName + Initial".
- Groups consecutive lines from the same speaker.
- Outputs a clean, compact transcript.


## Why use this?

Microsoft Teams VTT transcripts and Zoom VTT transcripts contain a lot of metadata and verbose speaker tags. Teams transcripts copied from Word are also verbose and not LLM-friendly. This tool cleans up all these formats, making transcripts much easier and cheaper to process with LLMs (like GPT, Claude, etc.), as it reduces the token count significantly.


## Usage

1. Run the script:
   ```
   python vttcleaner.py
   ```
2. Choose the input format when prompted:
   - Enter `1` for a VTT file (Microsoft Teams format)
   - Enter `2` for a plain text file copied from Word (Teams transcript)
   - Enter `3` for a Zoom VTT transcript file
3. Enter the path to your file when prompted.


## Example

### Original VTT (produced by MS Teams)

```
WEBVTT

12345678-aaaa-bbbb-cccc-123456789abc/01-0
00:00:01.000 --> 00:00:05.000
<v Alice Johnson>Hello team, welcome to our weekly sync.</v>

12345678-aaaa-bbbb-cccc-123456789abc/01-1
00:00:05.000 --> 00:00:08.000
<v Alice Johnson>Let's review the project status first.</v>

12345678-aaaa-bbbb-cccc-123456789abc/02-0
00:00:08.000 --> 00:00:10.000
<v Bob Smith>Thanks Alice, I have some updates.</v>

12345678-aaaa-bbbb-cccc-123456789abc/03-0
00:00:10.000 --> 00:00:12.000
<v Charlie Brown>Looking forward to hearing them.</v>

12345678-aaaa-bbbb-cccc-123456789abc/04-0
00:00:12.000 --> 00:00:15.000
<v Alice Johnson>Great, let's get started.</v>
```

### Original Teams Transcript Copied from Word (.txt)

```
Alice Johnson   09:01
Hello team, welcome to our weekly sync.

Alice Johnson   09:05
Let's review the project status first.

Bob Smith   09:08
Thanks Alice, I have some updates.

Charlie Brown   09:10
Looking forward to hearing them.

Alice Johnson   09:12
Great, let's get started.
```

### Original Zoom VTT Transcript

```
WEBVTT

1
00:00:01.000 --> 00:00:05.000
Alice Johnson: Hello team, welcome to our weekly sync.

2
00:00:05.000 --> 00:00:08.000
Alice Johnson: Let's review the project status first.

3
00:00:08.000 --> 00:00:10.000
Bob Smith: Thanks Alice, I have some updates.

4
00:00:10.000 --> 00:00:12.000
Charlie Brown: Looking forward to hearing them.

5
00:00:12.000 --> 00:00:15.000
Alice Johnson: Great, let's get started.
```

### Original Closed-Caption VTT (non-conversational)

```
WEBVTT

dd58214a-697b-48ca-a3e5-de773d6318db-0
00:00:08.080 --> 00:00:08.240
OK.

b7d55c44-3230-40d5-b4a6-9af749db368d-0
00:00:09.040 --> 00:00:09.760
Thanks, Katie.

6fe2a765-0a70-4195-9fde-b32d02214600-0
00:00:09.840 --> 00:00:11.000
Happy Friday, everyone.

325ef10b-3e5d-426c-9179-3686ff2d077b-0
00:00:11.360 --> 00:00:15.799
I'm hoping that I can give you a
framework and some tools to understand,
```

### Cleaned Output (for all input formats)

```
AliceJ: Hello team, welcome to our weekly sync.
Let's review the project status first.
Great, let's get started.
BobS: Thanks Alice, I have some updates.
CharlieB: Looking forward to hearing them.
```

### Cleaned Output (closed-caption VTT)

```
OK. Thanks, Katie. Happy Friday, everyone. I'm hoping that I can give you a framework and some tools to understand,
```


## Installation

No installation required. Just ensure you have Python 3.x.

## Windows Context Menu

This repository includes registry files to add/remove a right-click action in File Explorer.

### Install context menu

1. Double-click `vttclean_context_menu.reg`
2. Confirm the registry prompt.
3. Right-click files in Explorer:
    - `.vtt` shows **Clean VTT**
    - `.txt` shows **Clean Transcript**

### Uninstall context menu

1. Double-click `vttclean_context_menu_uninstall.reg`
2. Confirm the registry prompt.

### Notes

- The current registry command points to:
   - `C:\Users\wnovoa\AppData\Local\Programs\Python\Python312\pythonw.exe`
   - `D:\src\vttcleaner\vttcleaner.py`
- If you clone this repo to another path or use a different Python install, edit `vttclean_context_menu.reg` before importing it.

## License

MIT

---


**Note:** This tool is tailored for Microsoft Teams VTT, Zoom VTT, Teams transcripts copied from Word, and generic closed-caption VTT (without `<v Speaker>` tags). For other formats, results may vary.
