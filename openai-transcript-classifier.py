#!/usr/bin/env python3

import sys
import os
import csv
import argparse
import logging
from openai import OpenAI
from youtube_transcript_api import YouTubeTranscriptApi
from time import sleep

logger = logging.getLogger(__name__)

def setup_logging(debug):
   level = logging.DEBUG if debug else logging.INFO
   logging.basicConfig(level=level, format='%(asctime)s - %(levelname)s - %(message)s')

def get_video_id(url):
   logger.debug(f"Extracting video ID from URL: {url}")
   if "v=" in url:
       video_id = url.split("v=")[1].split("&")[0]
   elif "youtu.be/" in url:
       video_id = url.split("youtu.be/")[1].split("?")[0]
   else:
       raise ValueError("Could not extract video ID from URL")
   logger.debug(f"Extracted video ID: {video_id}")
   return video_id

def get_transcript(url):
   logger.debug(f"Getting transcript for URL: {url}")
   video_id = get_video_id(url)
   transcript = YouTubeTranscriptApi.get_transcript(video_id)
   full_text = " ".join(entry['text'] for entry in transcript)
   logger.debug(f"Retrieved transcript length: {len(full_text)} characters")
   return full_text

def get_decision(transcript):
   logger.debug("Sending request to OpenAI API")
   client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
   
   prompt = f"""Does this video cover a specific consumer rights topic that warrants a dedicated wiki page where consumers can share their experiences on this topic and collaborate on how to not get screwed by the vendor?

Examples of topics that warrant a wiki page:
"discussion of specific politician screwing right to repair bill after receiving $3300 from AT&T lobbyist"
"ford filing patent on how to use in-car-spyware to advertise to passengers during drive"

Examples of topics that DO NOT warrant a wiki page:
"cat video"
"random rant"

Video transcript: {transcript}
Please respond with a simple "yes" or "no"
"""
   logger.debug(f"Prompt length: {len(prompt)} characters")
   response = client.chat.completions.create(
       model="gpt-4",
       messages=[{"role": "user", "content": prompt}]
   )
   result = response.choices[0].message.content.strip().lower()
   logger.debug(f"OpenAI response: {result}")
   return result

def process_csv(input_file, output_file, sleep_time):
   logger.info(f"Processing CSV file: {input_file}")
   with open(input_file, 'r') as fin:
       reader = csv.DictReader(fin)
       fieldnames = ['title', 'link', 'needs_wiki_page']
       
       for i, row in enumerate(reader, 1):
           logger.info(f"Processing row {i}: {row['title']}")
           try:
               transcript = get_transcript(row['link'])
               result = get_decision(transcript)
               output_row = {
                   'title': row['title'],
                   'link': row['link'],
                   'needs_wiki_page': result
               }
           except Exception as e:
               logger.error(f"Error processing {row['link']}: {e}")
               output_row = {
                   'title': row['title'],
                   'link': row['link'],
                   'needs_wiki_page': 'error'
               }

           # Write/append current result
           write_header = not os.path.exists(output_file)
           with open(output_file, 'a', newline='') as fout:
               writer = csv.DictWriter(fout, fieldnames=fieldnames)
               if write_header:
                   writer.writeheader()
               writer.writerow(output_row)
               fout.flush()
               os.fsync(fout.fileno())
           
           logger.debug(f"Sleeping for {sleep_time} seconds...")
           sleep(sleep_time)

def main():
   parser = argparse.ArgumentParser()
   parser.add_argument("--csv", help="Process YouTube URLs from CSV file")
   parser.add_argument("--output", help="Output CSV file", default="output.csv")
   parser.add_argument("--debug", action="store_true", help="Enable debug logging")
   parser.add_argument("--sleep", type=float, default=3.0, help="Sleep time between API calls in seconds")
   parser.add_argument("url", nargs="?", help="YouTube video URL to analyze")
   args = parser.parse_args()
   
   setup_logging(args.debug)
   
   if args.csv:
       process_csv(args.csv, args.output, args.sleep)
   elif args.url:
       try:
           transcript = get_transcript(args.url)
           result = get_decision(transcript)
           print(result)
           sys.exit(0 if result == "yes" else 1)
       except Exception as e:
           logger.error(f"Error: {e}")
           sys.exit(2)
   else:
       parser.print_help()
       sys.exit(1)

if __name__ == "__main__":
   main()
