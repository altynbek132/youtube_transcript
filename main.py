import argparse
import youtube_transcript_api
from youtube_transcript_api.formatters import (
    JSONFormatter,
    TextFormatter,
    SRTFormatter,
)
import os
import re
import urllib.parse
import urllib.request
import json


def download_transcript(youtube_url, output_dir, language="en", output_format="json"):
    """
    Downloads the transcript of a YouTube video and saves it to a file.  Includes the video title in the filename.

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

        # Get video title
        try:
            video_title = get_video_title(video_id)
            if not video_title:
                print(f"Error: Could not retrieve video title for ID: {video_id}")
                video_title = video_id  # Fallback to video ID if no title is found.
        except Exception as e:
            print(
                f"Error getting video title: {e}.  Falling back to video ID for filename."
            )
            video_title = video_id

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

        # Sanitize filename (remove invalid characters) for both Title and ID to guard any illegal chars.
        sanitized_title = re.sub(r'[\\/*?:"<>|]', "", video_title)
        sanitized_id = re.sub(r'[\\/*?:"<>|]', "", video_id)  # Sanitize the ID as well.

        # Construct the filename: Title - VideoID
        filename = f"{sanitized_title} - {sanitized_id}.{output_extension}"
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


def get_video_title(video_id):
    """
    Retrieves the title of a YouTube video given its ID.

    Args:
        video_id (str): The YouTube video ID.

    Returns:
        str: The video title, or None if it cannot be retrieved.
    """
    try:
        # Use the YouTube Data API (v3) to get the video title.  This is the *correct* way to get the title.
        # You would need an API key for the YouTube Data API v3
        # Example of using the API (requires an API Key and enabling Youtube Data API V3 in Google Cloud)
        # api_key = "YOUR_YOUTUBE_API_KEY"
        # url = f"https://www.googleapis.com/youtube/v3/videos?id={video_id}&key={api_key}&part=snippet"
        # response = urllib.request.urlopen(url)
        # data = json.loads(response.read().decode())
        # if data['items']:
        #    return data['items'][0]['snippet']['title']

        # Implementing another, possibly brittle, but no-API-key solution:

        url = f"https://www.youtube.com/watch?v={video_id}"
        req = urllib.request.Request(
            url, headers={"User-Agent": "Mozilla/5.0"}
        )  # Spoof User-Agent
        response = urllib.request.urlopen(req)
        html = response.read().decode("utf-8")
        match = re.search(
            r"<title>(.*?)</title>", html
        )  # Use regex for direct title grabbing
        if match:
            title = match.group(1).replace(" - YouTube", "")  # Remove YouTube suffix
            return title.strip()
        else:
            return None

    except Exception as e:
        print(f"Error getting video title : {e}")
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
        default="json",
        choices=["json", "text", "srt", "vtt"],
        help="Output format (json, text, srt, vtt). (default: json)",
    )

    args = parser.parse_args()

    for url in args.urls:
        download_transcript(url, args.output_dir, args.language, args.format)


if __name__ == "__main__":
    main()
