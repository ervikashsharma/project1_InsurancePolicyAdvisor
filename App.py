import streamlit as st
from llmHelper import askllm
import time
from promptInjection import llm_injection_check
from guadrails import detect_pii, redact_pii
from classifier import classify_topic
from multiturn import ConversationMemory, run_chain


st.title("Insurance and Policy Advisor Co pilot")

system_prompt = 'You are an Insurance and Policy Agent. Your name is Shyaam.'

question = st.text_area("Ask your question")
Clicked = st.button("Submit")

if Clicked:
    #Check-1 : Question limit should not exceed 100
    if(len(question) > 100):
        st.write("Question exceeds limit of 100")
    else:
        progress_bar = st.progress(0)
        for progress in range(100):
            time.sleep(0.02)  # Simulate some processing time
        progress_bar.progress(progress + 1)  # Update the progress bar
        

        #Check-2 : Validate prmopt injection
        llm_injection = llm_injection_check(question)

        if llm_injection["is_injection"] == True:
            st.write("{0} and {1}".format(llm_injection["attack_type"], llm_injection["explanation"]))
        else:

            #Check-3 : Validate some personal information if found then REDACTION
            pii = detect_pii(question)
            if pii:
                question = redact_pii(question)
            
            classifier = classify_topic(question)
            if classifier["allowed"] == True:
                message = [
                    {
                        "role": "system",
                        "content": system_prompt
                    },
                    {
                        "role": "user",
                        "content": question
                    }
                ]
                #response = askllm(message)
                #st.write(response)

                mem1 = ConversationMemory()
                response = run_chain(question, mem1);
                st.write(response)
            else:
                st.write("{0}", classifier["reason"])
                progress_bar.empty()