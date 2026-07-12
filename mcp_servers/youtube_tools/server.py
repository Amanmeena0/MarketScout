
import sys
import os
# Add the mcp_server directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import googleapiclient.discovery
from youtube_transcript_api import YouTubeTranscriptApi, TranscriptsDisabled, NoTranscriptFound # type: ignore
from config import *
from mcp.server.fastmcp import FastMCP


mcp = FastMCP("YouTube Tools")


@mcp.tool()
def search_youtube(query: str) -> str:
    """
    Search YouTube for videos related to a specific query.
    
    Args:
        query (str): The search term to look for on YouTube
        
    Returns:
        str: Analysis of relevant YouTube content with video insights
    """
    try:
      
            
        youtube = googleapiclient.discovery.build("youtube", "v3", developerKey=google_api_key)
        
        request = youtube.search().list(
            part="snippet",
            q=query,  
            type="video",  
            videoDuration='medium', 
            maxResults=5,  
        )
        
        response = request.execute()
        
        analysis = f"YouTube Content Analysis for '{query}':\n\n"
        analysis += f"Found {len(response['items'])} relevant videos:\n\n"
        
        for i, item in enumerate(response['items'], 1):
            video_id = item['id'].get('videoId', '')
            snippet = item.get('snippet', {})
            title = snippet.get('title', 'No title')
            channel = snippet.get('channelTitle', 'Unknown channel')
            description = snippet.get('description', '')[:200] + "..." if snippet.get('description') else 'No description'
            
            analysis += f"{i}. {title}\n"
            analysis += f"   Channel: {channel}\n"
            analysis += f"   Video ID: {video_id}\n"
            analysis += f"   Description: {description}\n\n"
        
        
        
        return analysis
    except Exception as e:
        
        return f"Error searching YouTube"

@mcp.tool()
def get_youtube_comments(video_id: str) -> str:
    """
    Fetch comments from a specific YouTube video for sentiment analysis.
    
    Args:
        video_id (str): The YouTube video ID to fetch comments from
        
    Returns:
        str: Sentiment analysis of YouTube comments
    """
    try:
           
        youtube = googleapiclient.discovery.build("youtube", "v3", developerKey=google_api_key)
        
        request = youtube.commentThreads().list(
            part="snippet,replies",
            videoId=video_id,
            textFormat="plainText",
            maxResults=30
        )
        
        response = request.execute()
        comments = []

        for item in response.get('items', []):
            comment_text = item['snippet']['topLevelComment']['snippet']['textDisplay']
            if comment_text.strip():
                comments.append(comment_text)
        
        if not comments:
            return f"No comments found for video ID: {video_id}"
        
        # Basic sentiment analysis
        analysis = f"YouTube Comments Analysis for Video ID: {video_id}\n\n"
        analysis += f"Total Comments Analyzed: {len(comments)}\n\n"
       
        
        analysis += "Sample Comments:\n"
        for i, comment in enumerate(comments, 1):
            analysis += f"{i}. {comment}...\n"
        
        return analysis
    except Exception as e:
        print(f"Error fetching YouTube comments: {e}")
        return f"Error fetching YouTube comments"

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

