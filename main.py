import argparse
import youtube_transcript_api
from youtube_transcript_api.formatters import (
    JSONFormatter,
    TextFormatter,
    SRTFormatter,
)
import os
import re


def download_transcript(youtube_url, output_dir, language="en", output_format="json"):
    """
    Downloads the transcript of a YouTube video and saves it to a file.

    Args:
        youtube_url (str): The URL of the YouTube video.
        output_dir (str): The directory to save the transcript to.
        language (str, optional): The language of the transcript. Defaults to 'en'.
        output_format (str, optional): The output format of the transcript.
                                       Options are 'json', 'text', 'srt', 'vtt'. Defaults to 'json'.

    Returns:
        str: The path to the downloaded transcript file, or None if there was an error.
    """

    try:
        # Extract video ID from URL. Handle both standard and short URLs
        video_id = extract_video_id(youtube_url)
        if not video_id:
            print(f"Error: Could not extract video ID from URL: {youtube_url}")
            return None

        # Get transcript
        try:
            transcript = youtube_transcript_api.YouTubeTranscriptApi.get_transcript(
                video_id, languages=[language]
            )
        except youtube_transcript_api.TranscriptsDisabled:
            print(f"Error: Transcripts are disabled for video ID: {video_id}")
            return None
        except youtube_transcript_api.NoTranscriptFound:
            print(
                f"Error: No transcript found for video ID: {video_id} in language: {language}"
            )
            return None
        except Exception as e:
            print(f"An unexpected error occurred getting the transcript : {e}")
            return None

        # Format the transcript based on the specified format
        if output_format.lower() == "json":
            formatter = JSONFormatter()
            output_extension = "json"
        elif output_format.lower() == "text":
            formatter = TextFormatter()
            output_extension = "txt"
        elif output_format.lower() == "srt":
            formatter = SRTFormatter()
            output_extension = "srt"
        else:
            print(
                f"Error: Invalid output format: {output_format}.  Choose from 'json', 'text', 'srt', or 'vtt'."
            )
            return None

        formatted_transcript = formatter.format_transcript(transcript)

        # Create output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)

        # Sanitize filename (remove invalid characters)
        filename = re.sub(r'[\\/*?:"<>|]', "", video_id) + f".{output_extension}"
        output_path = os.path.join(output_dir, filename)

        # Write transcript to file
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(formatted_transcript)

        print(f"Transcript downloaded successfully to: {output_path}")
        return output_path

    except Exception as e:
        print(f"An error occurred: {e}")
        return None


def extract_video_id(url):
    """
    Extracts the YouTube video ID from a URL.

    Args:
        url (str): The YouTube URL.

    Returns:
        str: The video ID, or None if it cannot be extracted.
    """
    # Regex for standard YouTube URLs (e.g., https://www.youtube.com/watch?v=dQw4w9WgXcQ)
    match = re.search(r"(?:v=|\/)([0-9A-Za-z_-]{11})", url)
    if match:
        return match.group(1)

    # Regex for short YouTube URLs (e.g., https://youtu.be/dQw4w9WgXcQ)
    match = re.search(r"youtu\.be\/([0-9A-Za-z_-]{11})", url)
    if match:
        return match.group(1)

    return None


def main():
    """
    Main function to parse command-line arguments and download transcripts.
    """
    parser = argparse.ArgumentParser(
        description="Download transcripts from YouTube videos."
    )
    parser.add_argument("urls", nargs="+", help="One or more YouTube video URLs.")
    parser.add_argument(
        "-o",
        "--output-dir",
        default="transcripts",
        help="Output directory for transcript files (default: transcripts).",
    )
    parser.add_argument(
        "-l",
        "--language",
        default="en",
        help="Language of the transcript (default: en).",
    )
    parser.add_argument(
        "-f",
        "--format",
        default="text",
        choices=["json", "text", "srt", "vtt"],
        help="Output format (json, text, srt, vtt). (default: json)",
    )

    args = parser.parse_args()

    for url in args.urls:
        download_transcript(url, args.output_dir, args.language, args.format)


if __name__ == "__main__":
    main()
