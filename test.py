# Install llama.cpp on Mac with: brew install llama.cpp
# Then run the llama.cpp server with: llama-server -m ./models/Qwen3-4B-Thinking-2507-UD-Q4_K_XL.gguf --port 8000

from datapizza.clients.openai_like import OpenAILikeClient
from datapizza.agents import Agent
from datapizza.tools.web_fetch import WebFetchTool
from llama_cpp import Llama
import re
import time
from llama_cpp.llama_cpp import llama_backend_free
import torch
import gc


local_client = OpenAILikeClient(
    api_key="",
    model="Qwen3-4B-Thinking-2507-UD-Q4_K_XL",
    system_prompt="You are a helpful assistant.",
    base_url="http://localhost:8000/v1",
)

def get_model() -> Llama:
    return Llama(
        model_path="./models/Qwen3-4B-Thinking-2507-UD-Q4_K_XL.gguf",
        n_gpu_layers=-1,
        n_ctx=8192,
        verbose=True,
    )

def empty_gpu_cache(model: Llama) -> None:
    model.close()
    llama_backend_free()
    gc.collect()
    torch.mps.empty_cache()

find_urls_agent = Agent(
    name="Find URLs Assistant",
    client=local_client,
    system_prompt="""You are a helpful research assistant.
        Your goal is to provide the 10 best URLs of the 10 best sources which give the best and updated news on the user's topic.

        Follow these steps:
        1.  Receive a user request where you understand the topic they are interested in.
        2.  Use the `WebFetchTool` tool to find the URLs of the best sources on the topic.
        3.  Write the 10 best URLs in a numbered list format as your final answer.
        """,
    tools=[WebFetchTool()]
)

def generate_podcast_script(duration: int, topic: str, news_content: str) -> str:
    """Creates a title for a chat session based on the first message using a LLM."""
    model = get_model()
    messages = [
        {"role": "system",
        "content": f"""
            You are a professional podcast host creating an engaging {duration}-minute episode about {topic}.

            Based on the following recent news articles, create a natural, conversational podcast script with **one person talking**, as if they are speaking directly to the audience.

            NEWS ARTICLES:
            {news_content}

            REQUIREMENTS:
            - Use a conversational, engaging tone
            - Include natural transitions and personal commentary
            - Include an introduction and conclusion
            - Optimize for text-to-speech:
            - No music cues, stage directions, or special characters
            - Natural pauses with commas and periods
            - Spell out numbers and abbreviations
            - Pronunciation should be clear and natural

            Generate the complete podcast script now:
        """}
    ]
    response = model.create_chat_completion(messages=messages)
    empty_gpu_cache(model=model)
    return response["choices"][0]["message"]["content"].strip()


def extract_text_from_html(url: str) -> str:
    import trafilatura
    
    page_content = trafilatura.fetch_url(url)
    text = trafilatura.extract(page_content, include_comments=False, include_tables=True)
    return text or ""


def extract_article_links(url: str, max_links: int = 5) -> list[str]:
    """Estrae i link agli articoli dalla homepage di un sito di news."""
    import requests
    from bs4 import BeautifulSoup
    from urllib.parse import urljoin, urlparse
    
    headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)'}
    response = requests.get(url, headers=headers, timeout=10)
    soup = BeautifulSoup(response.text, 'html.parser')
    
    base_domain = urlparse(url).netloc
    article_links = []
    
    # Cerca link in elementi tipici degli articoli
    selectors = [
        'article a[href]',
        'h2 a[href]', 'h3 a[href]',
        '.post a[href]', '.entry a[href]',
        '[class*="article"] a[href]',
        '[class*="story"] a[href]',
        '[class*="card"] a[href]',
    ]
    
    seen = set()
    for selector in selectors:
        for link in soup.select(selector):
            href = link.get('href')
            if not href:
                continue
            
            # Costruisci URL assoluto
            full_url = urljoin(url, href)
            parsed = urlparse(full_url)
            
            # Filtra: stesso dominio, path abbastanza lungo (indica articolo)
            if (parsed.netloc == base_domain and 
                len(parsed.path) > 10 and 
                full_url not in seen and
                not any(x in full_url for x in ['#', 'login', 'signup', 'subscribe', 'tag/', 'category/', 'author/'])):
                seen.add(full_url)
                article_links.append(full_url)
                
            if len(article_links) >= max_links:
                break
        if len(article_links) >= max_links:
            break
    
    return article_links


def scrape_news_site(site_url: str, max_articles: int = 3) -> list[dict]:
    """Scarica la homepage, estrae i link agli articoli e ne legge il contenuto."""
    import time
    
    print(f"\n📰 Analizzando: {site_url}")
    
    article_links = extract_article_links(site_url, max_links=max_articles)
    print(f"   Trovati {len(article_links)} articoli")
    
    articles = []
    for link in article_links:
        print(f"   → Scaricando: {link[:60]}...")
        try:
            content = extract_text_from_html(link)
            if content and len(content) > 100:
                articles.append({
                    'url': link,
                    'content': content  # Limita per il context window
                })
        except Exception as e:
            print(f"     ⚠️ Errore: {e}")
        time.sleep(1)  # Rate limiting
    
    return articles


# response = find_urls_agent.run("Give me the 10 best sources to get updated news on Artificial Intelligence.")
# print(response.text)

urls_str = """
1. https://techcrunch.com  
2. https://www.theverge.com  
3. https://www.technologyreview.com  
4. https://www.wired.com  
5. https://www.ainews.net  
6. https://deepmind.com/blog  
7. https://ai.googleblog.com  
8. https://openai.com/blog  
9. https://huggingface.co/blog  
10. https://www.nytimes.com/section/technology
"""

urls = re.findall(r'https?://[^\s]+', urls_str)
all_articles = []

for url in urls[:1]:
    articles = scrape_news_site(url, max_articles=4)
    all_articles.extend(articles)
    time.sleep(2)  # Pausa tra siti

print(f"\n✅ Totale articoli scaricati: {len(all_articles)}")

news_content = "\n\n".join([f"URL: {article['url']}\n\n{article['content']}" for article in all_articles])
podcast_script = generate_podcast_script(
    duration=10,
    topic="Artificial Intelligence",
    news_content=news_content
)

print("\n🎙️ Podcast Script:\n")
print(podcast_script)