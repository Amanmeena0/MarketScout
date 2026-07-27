
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
        
            
        transcript_data = None
        try:
            transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
            
            try:
                transcript_data = transcript_list.find_transcript(['en']).fetch()
            except NoTranscriptFound:
                for tx in transcript_list:
                    transcript_data = tx.translate('en').fetch()
                    break
                
                if not transcript_data:
                     return f"Error: No transcripts found for video ID: {video_id}"

        except TranscriptsDisabled:
            
            return f"Error: Transcripts are disabled for video ID: {video_id}"
        except Exception as e:
            
            return f"An unexpected error occurred: {e}"

        transcript_text = " ".join([item.text for item in transcript_data])

        
        return transcript_text

    except Exception as e:
        
        return f"Error summarizing transcript"

