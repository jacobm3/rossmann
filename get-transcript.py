#!/usr/bin/env python3
import sys
from youtube_transcript_api import YouTubeTranscriptApi

def get_video_id(url):
   if "v=" in url:
       return url.split("v=")[1].split("&")[0]
   elif "youtu.be/" in url:
       return url.split("youtu.be/")[1].split("?")[0]
   raise ValueError("Could not extract video ID from URL")

def get_transcript(url):
   try:
       video_id = get_video_id(url)
       transcript = YouTubeTranscriptApi.get_transcript(video_id)
       return " ".join(entry['text'] for entry in transcript)
   except Exception as e:
       print(f"Error: {e}", file=sys.stderr)
       sys.exit(1)

if __name__ == "__main__":
   if len(sys.argv) != 2:
       print("Usage: ./script.py <youtube-url>", file=sys.stderr)
       sys.exit(1)
   
   print(get_transcript(sys.argv[1]))
