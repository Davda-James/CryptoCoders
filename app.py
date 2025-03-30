from flask import Flask, jsonify, request
from langchain.schema import Document
from multi_agent import chat_agent,summarize_text, extract_pagecontent
from flask_cors import CORS, cross_origin
from fetch_papers import get_research_papers
from faiss_db import load_faiss_db
from dotenv import load_dotenv
import os 
load_dotenv()

app = Flask(__name__)
CORS(app, supports_credentials=False, origins="*")  # Allow all origins
app.config['CORS_HEADERS'] = 'Content-Type'



@app.route("/",methods=["GET"])
@cross_origin()
def home():
    return jsonify("Welcome to the Research Paper Chatbot API"), 200

@app.route("/agent/chat",methods=["POST"])
@cross_origin()
def chat():
    data=request.get_json()
    chat_query=data.get("chat_query",None)
    generate_new=data.get("generate_new",None)
    k=data.get("k",None)
    pdf_url=data.get("pdf_url",None)

    if not chat_query or generate_new is None or not k or not pdf_url:
        return jsonify({"error":"chat_query and generate_new parameters are required"}), 400
    
    if generate_new not in [True,False]:
        return jsonify({"error":"generate_new parameter must be either True or False"}), 400
    
    # Perform the search
    most_similar_chunks=load_faiss_db(chat_query, k=k, generate_new=generate_new, pdf_url=pdf_url)
    
    # calling chat agent
    context = "\n\n".join([doc.page_content for doc in most_similar_chunks])

    # Construct the final prompt for the chat agent
    final_prompt = f'''Based on the following research content:\n\n{context}\n\nAnswer the question: {chat_query}
                    Tools you can use : [web_search, research_paper_search,deep_research_search and anything you want or required],
                    Act as chatbot there will be user/human asking questions or queries from this research papers.
                    Reply in a conversational manner, and provide clear and concise answers and give your best answers to it.
                    If required provide relevant links to the user. Also for reference here is the paper url : {pdf_url}, In this reply don't give any unrequired symbols or regex try to 
                    keep it human readable .
                    '''
    
    final_chatbot_reply=chat_agent(final_prompt)

    return jsonify({"response": final_chatbot_reply.content}), 200


@app.route('/agent/fetch_docs',methods=['POST'])
@cross_origin()
def fetch_documents():
    data=request.get_json()
    query = data.get("query","")
    max_papers = data.get("max_papers", 10)  # Default to 5 if not provided

    if not query or not max_papers:
        return jsonify({"error":"query ,k, max_papers and generate_new parameters are required"}), 400
    
    search_results=get_research_papers(query,max_papers)
    summary_of_search_results=summarize_text(extract_pagecontent(search_results))
    # Step 4: Attach summaries to corresponding search results
    for i, doc in enumerate(search_results):
        doc["summary"] = summary_of_search_results[i]  # Add the summary to each document

    # Format the response
    # response_data = []
    # for doc in search_results:
    #     response_data.append({
    #         "title": doc.metadata.get("title", "Unknown Title"),  # Extract title if available
    #         "abstract": doc.metadata.get("abstract", "N/A"),  # Extract abstract if available
    #         "page_content": doc.page_content,  # Extracted content from the document
    #         "full_text": doc.metadata.get("full_text",""),  # Assuming `page_content` is the full text
    #         "pdf_url": doc.metadata.get("pdf_url", "N/A"),  # Extract PDF URL if available
    #         "citations": doc.metadata.get("citations", []),  # Extract citations if available
    #         "summary": summary_of_search_results.content       # Summarized content
    #     })        

    # return jsonify(response_data), 200
    return jsonify(search_results), 200
