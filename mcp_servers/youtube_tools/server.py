
import sys
import os
# Add the mcp_server directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from youtube_transcript_api import YouTubeTranscriptApi, TranscriptsDisabled, NoTranscriptFound # type: ignore
from mcp.server.fastmcp import FastMCP


mcp = FastMCP("YouTube Tools")

@mcp.tool()
def summarize_youtube_transcript(video_id: str) -> str:
    """
    Fetch and summarize a YouTube video's transcript for content analysis.
    
    Args:
        video_id (str): The YouTube video ID to get transcript from
        
    Returns:
        str: Summarized transcript content
    """
    try:

        # Extract raw video ID if full URL is passed
        if "v=" in video_id:
            video_id = video_id.split("v=")[1].split("&")[0]
        elif "youtu.be/" in video_id:
            video_id = video_id.split("youtu.be/")[1].split("?")[0]

        transcript_data = None
        try:
            ytt = YouTubeTranscriptApi()
            if hasattr(ytt, "list"):
                transcript_list = ytt.list(video_id)
            elif hasattr(YouTubeTranscriptApi, "list_transcripts"):
                transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
            else:
                transcript_list = None

            if transcript_list is not None:
                try:
                    transcript_data = transcript_list.find_transcript(['en']).fetch()
                except NoTranscriptFound:
                    for tx in transcript_list:
                        try:
                            transcript_data = tx.translate('en').fetch()
                            break
                        except Exception:
                            continue

            if not transcript_data and hasattr(YouTubeTranscriptApi, "get_transcript"):
                transcript_data = YouTubeTranscriptApi.get_transcript(video_id, languages=['en'])

            if not transcript_data:
                return f"Error: No transcripts found for video ID: {video_id}"

        except TranscriptsDisabled:
            return f"Error: Transcripts are disabled for video ID: {video_id}"
        except NoTranscriptFound:
            return f"Error: No transcripts found for video ID: {video_id}"
        except Exception as e:
            return f"An unexpected error occurred: {e}"

        transcript_text = " ".join([
            item.text if hasattr(item, "text") else item.get("text", "")
            for item in transcript_data
        ])

        return transcript_text

    except Exception as e:
        return f"Error summarizing transcript: {e}"

