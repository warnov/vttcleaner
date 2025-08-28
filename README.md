
# VTTCleaner

VTTCleaner is a Python console application designed to process VTT files from Microsoft Teams, plain text transcripts copied from Word (Teams transcript format), and Zoom VTT transcripts. It extracts and simplifies speaker interactions, making transcripts much more compact and suitable for use with Large Language Models (LLMs) by drastically reducing the required number of tokens.


## Features

- Removes unnecessary metadata and timestamps from VTT files.
- Supports processing of plain text transcripts copied from Word (Teams transcript format).
- Supports processing of Zoom VTT transcript files.
- Simplifies speaker names to "FirstName + Initial".
- Groups consecutive lines from the same speaker.
- Outputs a clean, compact transcript.


## Why use this?

Microsoft Teams VTT transcripts and Zoom VTT transcripts contain a lot of metadata and verbose speaker tags. Teams transcripts copied from Word are also verbose and not LLM-friendly. This tool cleans up all these formats, making transcripts much easier and cheaper to process with LLMs (like GPT, Claude, etc.), as it reduces the token count significantly.


## Usage

1. Run the script:
   ```
   python main.py
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

### Cleaned Output (for all input formats)

```
AliceJ: Hello team, welcome to our weekly sync.
Let's review the project status first.
Great, let's get started.
BobS: Thanks Alice, I have some updates.
CharlieB: Looking forward to hearing them.
```


## Installation

No installation required. Just ensure you have Python 3.x.

## License

MIT

---


**Note:** This tool is specifically tailored for VTT files from Microsoft Teams and Zoom, as well as Teams transcripts copied from Word. For other formats, results may vary.
