import argparse
import requests
from tika import parser # pip install tika
import asyncio
import tiktoken
import openai
import json
import sys
import os

from arxiv_scrape import get_daily_links

DEBUG = True

# Define the function to extract text from a PDF using pdfreader
def extract_text_from_pdf(pdf_url):
    if DEBUG:
        return f"Debug: {pdf_url}"
    response = requests.get(pdf_url)
    raw = parser.from_buffer(response.content)
    return raw['content']


def wrap_message(message, user="system"):
    return {"role": user, "content": message}


def count_tokens(message):
    """Returns the number of tokens used by a list of messages."""
    encoding = tiktoken.get_encoding("cl100k_base")
    return len(encoding.encode(message))


def split_text(text, max_tokens=12000):
    chunks = [text]
    while any([count_tokens(c)>max_tokens for c in chunks]):
        new_chunks = []
        for chunk in chunks:
            mid_point = len(chunk)//2
            # Find next space
            while chunk[mid_point] != " ":
                mid_point += 1
            new_chunks += [chunk[:mid_point], chunk[mid_point:]]
        chunks = new_chunks
    return chunks


# Define the function to prompt the LLM and receive a response from OpenAI's chatGPT model
def chat(prompt):
    if DEBUG:
        return f"Debug: {prompt}"
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo-16k",
        messages = [{"role": "system", "content": prompt},],
        temperature=0.7,
    )
    return response["choices"][0]["message"]["content"]


def summarise_from_link(link):
    # Extract the text from the PDF
    pdf_text = extract_text_from_pdf(link)
    chunks = split_text(pdf_text)
    print(f"Number of chunks: {len(chunks)}")

    if len(chunks) == 1:
        # Prompt the LLM to provide a summary
        prompt = f"You are an AI assistent designed to summarise academic papers. Your reader is a researcher, so your response should be technical and detailed. Focus on placing papers in the context of its field. The paper content is provided between triple backticks.\n\n```{pdf_text}```"
        summary = chat(prompt)

        return summary

    else:
        summaries = []
        for chunk in chunks:
            prompt = f"You are an AI assistent designed to summarise academic papers. Your reader is a researcher, so your response should be technical and detailed. Focus on placing papers in the context of its field. A subsection of the paper content is provided between triple backticks. Summarise it in a way that a larger summary can be built.\n\n```{chunk}```"

            if count_tokens(prompt) > 15000:
                print("Error: Paper is too long. Summaries exceed 15k tokens.")
                raise ValueError

            summary = chat(prompt)
            summaries.append(summary)
        
        prompt = f"You are an AI assistent designed to summarise academic papers. Your reader is a researcher, so your response should be technical and detailed. Focus on placing papers in the context of its field. Small sections of the paper have already been summarised for you, given between triple backticks in an array. Unite these summaries into a larger complete summary.\n\n"
        prompt += "[\n"
        for s in summaries:
            prompt += f"```{s}```\n\n"
        prompt += "]"
        summary = chat(prompt)
        return summary

if __name__ == "__main__":
    # Set up the OpenAI API credentials
    openai.api_key = os.getenv("OPENAI_API_KEY")
    
    # Get the links to the daily new papers
    links = get_daily_links()

    # Summarise each paper and write to file
    ofile = open("daily_summaries.txt", "w+")
    for l in links:
        print(l)
        ofile.write(l); ofile.flush()
        ofile.write("\n"); ofile.flush()
        summary = summarise_from_link(l)
        ofile.write(summary); ofile.flush()
        ofile.write("\n\n"); ofile.flush()
        ofile.write("--------------------------------------------------"); ofile.flush()
        ofile.write("\n"); ofile.flush()
    ofile.close()