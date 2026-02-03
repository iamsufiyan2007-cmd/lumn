import streamlit as st
import os
import json
import google.generativeai as genai
import pandas as pd
st.markdown("""
    <style>
    /* Center all titles */
    h1 {
        text-align: center;
    }
    
    .stButton>button{
            transition:all 0.3s ease;
            border-color: #ffffff;
            }
    .stButton>button:hover{
            transform:scale(1.5);
            box-shadow: 0 5px 15px rgba(0, 0, 0, 0.3);
            }
    }
    </style>
    """, unsafe_allow_html=True)
st.title("IUMN STUDY SMART")
genai.configure(api_key=st.secrets["GOOGLE_API_KEY_1"])
model = genai.GenerativeModel("gemini-2.5-flash")

if not os.path.exists("user.json"):
    with open("user.json", "w") as f:
        json.dump({"user": {}}, f, indent=4)
if not os.path.exists("quiz.json"):
    with open("quiz.json", "w") as f:
        json.dump({"quiz": []}, f, indent=4)
if not os.path.exists("user.json"):
    with open("user.json", "w") as f:
        json.dump({"user": {}}, f, indent=4)
def load():
    with open("user.json","r") as f:
        return json.load(f)
def load_quiz():
    with open("quiz.json","r")as f:
        return json.load(f)
def add(data):
    with open("user.json","w") as f:
        json.dump(data,f,indent=4)

if "current_quiz" not in st.session_state:
    st.session_state.current_quiz = []
if "submitted" not in st.session_state:
    st.session_state.submitted = False
if "step" not in st.session_state:
    st.session_state.step=0
if "u_name" not in st.session_state:
    st.session_state.u_name=""
if "result" not in st.session_state:
    st.session_state.result={}
if "quiz" not in st.session_state:
    st.session_state.quiz=0
if "answers" not in st.session_state:
    st.session_state.answers={}
if "quiz_data" not in st.session_state:
    st.session_state.quiz_data=[]
def logged_in():
    st.session_state.step=0
def sign_in():
    st.session_state.step=1
def profile():
    st.session_state.step=2
def test():
    st.session_state.step=3
def evalu():
    st.session_state.step=4
def chat():
    st.session_state.step=5

if st.session_state.step==0:
    st.title("LOGIN")

    user=load()
    username=st.text_input("name")
    gmail=st.text_input("gmail")
    password=st.text_input("password",type="password")
    col1,col2=st.columns(2)
    
    with col1:
        if st.button("login"):
            if username in user["user"] and user["user"][username]["password"]==password:
                st.session_state.u_name=username
                evalu()
                st.rerun()
            else:
                st.warning("user dose not exist")
    with col2:
        if st.button("i dont have account"):
            sign_in()
            st.rerun()
if st.session_state.step==1:
    st.title("SIGNIN")
    data=load()
    new_user=st.text_input("name",key="new_name")
    new_age=st.number_input("age",min_value=4,step=1,key="new age")
    new_mail=st.text_input("gmail",value="example@gmail.com",key="new mail")
    new_password=st.text_input("password",type="password",key="new pass")
    new_study=st.text_input("what is your study",placeholder="college")
    new_sylabus=st.text_input("sylabus",placeholder="the sylabus must be saparated by / eg: maths/english/science/e")
    st.session_state.u_name=new_user
    if st.button("sign in"):
        if not new_user or not new_age or not new_password or not new_mail or not new_sylabus.strip() or not new_study:
            st.warning("fill the all the fields")
        elif new_user in data["user"]:
            st.warning("user name already exist")
        else:
           data["user"][new_user]={
               "gmail":new_mail,
               "password":new_password,
               "age":new_age,
               "sylabus":new_sylabus,
               "study":new_study

           }
           add(data)
           test()
           st.rerun()
if st.session_state.step==2:
    st.title("PROFILE")
    reg_info=load()
    get_user=st.session_state.u_name
    if get_user in reg_info["user"]:
        user_data=reg_info["user"][get_user]
        st.title(f"welcome {get_user}")
        st.write("your gamil is ",user_data["gmail"])
        st.write("your password is ",user_data["password"])
        st.write("your age is ",user_data["age"])
    if st.button("back"):
        logged_in()
        st.rerun()
if st.session_state.step == 3:

    st.title("TEST QUIZ")


    user = st.session_state.u_name
    data = load()
    topic = data["user"][user]["sylabus"]
    level=data["user"][user]["study"]
    if "lev" not in st.session_state:
        st.session_state.lev=level

    if st.button("Generate quiz questions"):
        prompt = f"""You are an expert in generating quiz questions.

        for the following topic - {topic}, genrate 5 quize questions in the following form and the question should be ralevent to the users subject and diffculty based on their level. this is the users study and level {level} and you should generate 5 question for each subject from topic

        {{"topic":"topic of the user "
         "question":"text" ,
        "options": [A,B,C,D],
        "correct":"correct answer",
        "explanation":"short explanation"
        }}
        For each question you generate, return a "topic" field that is **only the core subject name**, not chapter names, lesson titles, or subtopics.  
        For example:
        - If the question is about "C++ classes and objects", the topic should be "C++"
        - If the question is about "Calculus", the topic should be "Math"
        - If the question is about "Python loops", the topic should be "Python"
        - If the question is about "Shakespeare's plays", the topic should be "English"
        All strings must be valid JSON. Do not use newlines inside strings. Use plain ASCII only.
        dont add anything before or after this."""

        response = model.generate_content(
            prompt,
            generation_config={"response_mime_type": "application/json"}
        )
        
        quiz_data = json.loads(response.text)
       

        

        with open("quiz.json", "r") as f:
            saved = json.load(f)

        saved["quiz"].extend(quiz_data)

        with open("quiz.json", "w") as f:
            json.dump(saved, f, indent=4)
        st.session_state.quiz_data = quiz_data
        st.session_state.current_quiz = quiz_data


    if "quiz_data" in st.session_state:
        st.header("quiz questions")

        for i, ques in enumerate(st.session_state.quiz_data, start=1):
            st.write(f"{i}. {ques['question']}")
            st.radio("choose:", ques["options"], key=f"chosen_answer_{i}")

        if st.button("submit"):
            topic_scores = {}

           
            for i, q in enumerate(st.session_state.quiz_data, start=1):
                topic_name = q["topic"]

                if topic_name not in topic_scores:
                    topic_scores[topic_name] = {"correct": 0, "total": 0}

                topic_scores[topic_name]["total"] += 1

                if st.session_state.get(f"chosen_answer_{i}") == q["correct"]:
                    topic_scores[topic_name]["correct"] += 1

        
            with open("quiz.json", "r") as f:
                quiz_file = json.load(f)

            quiz_file.setdefault("results", [])

            quiz_file["results"].append({
                "user": user,
                "scores": topic_scores
            })

            with open("quiz.json", "w") as f:
                json.dump(quiz_file, f, indent=4)
            
            st.session_state.submitted = True
            st.success("Scores saved successfully!")


    if st.session_state.submitted:
        if st.button("evaluvate"):
            st.session_state.step = 4
            st.rerun()
 

    


        

if st.session_state.step == 4:
    if "memory" not in st.session_state:
        st.session_state.memory={}
    current_user=st.session_state.u_name
    combaind={}
    # Use the current quiz
    quiz_data = load_quiz()
    user_attempts = [r for r in quiz_data.get("results", []) if r["user"] == current_user]

    for attampt in user_attempts:
        for subject,score in attampt["scores"].items():
            if subject not in combaind:
                combaind[subject]={"correct":0,"total":0}
            combaind[subject]["correct"]+=score["correct"]
            combaind[subject]["total"]+=score["total"]
    subject_accuracy = {
        subject: round((v["correct"] / v["total"]) * 100, 2)
        for subject, v in combaind.items()
    }

    st.title("YOUR RESULT")
    st.subheader("Subject-wise Accuracy (%)")

    df = pd.DataFrame(
        list(subject_accuracy.items()),
        columns=["Subject", "Accuracy"]
    ).set_index("Subject")
   
    st.bar_chart(df)
    lowest_sub=None
    lowest_per=100
    t1,t2=st.columns(2)

    with t1:
       st.markdown("## GROSS SCORE")
       for subject, score in combaind.items():
           st.markdown(f"**{subject}** : {score['correct']} / {score['total']}")
           
    with t2:
        st.markdown("## WEAKEST SUBJECT")
        for subject, score in combaind.items():
            persent=(score["correct"] / score["total"]) * 100

            if persent<lowest_per:
                lowest_sub=subject
                lowest_per=persent
        st.markdown(f"**LOWEST PERFORMENCE:** {lowest_sub}")
        st.markdown(f"**LOWEST PERSANTAGE:** {lowest_per}")
    st.session_state.memory=combaind
    c1, c2, c3 = st.columns(3)

    with c1:
        if st.button("Close"):
            logged_in()
            st.rerun()

    with c2:
        if st.button("chat bot"):
            chat()
            st.rerun()

    with c3:
        if st.button("quiz"):
            test()


    
if st.session_state.step==5:
    lev=st.session_state.lev
    cont=st.session_state.memory
    # Configure API (use secrets in real projects)
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY_2"])

    model = genai.GenerativeModel("gemini-2.5-flash")

    st.title("💡 TALK TO LUMN")

    # Chat history
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Display previous messages
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # System instruction (hidden from user)
    SYSTEM_PROMPT = f"""
    You are Lumn, a great teacher.
    Explain any topic clearly, step by step,
    using simple words and examples and you need to give a revison plan for the user
    based on the given data of users scores and subject and you have to identify the users
    weakness. this is users scores and subject {cont}.
    if user ask anything besides studying like medical advice or anything politly refuse.
    this is the level of the user{lev} if lev is non ask the user for their level
    """

    # User input
    question = st.chat_input("Ask me anything")

    if question:
        # Show user message
        with st.chat_message("user"):
            st.markdown(question)

        st.session_state.messages.append(
            {"role": "user", "content": question}
        )

        # Properly formatted input to the API
        full_prompt = f"""
    {SYSTEM_PROMPT}

    User question:
    {question}
    """

        response = model.generate_content(full_prompt)

        answer = response.text

        # Show assistant response
        with st.chat_message("assistant"):
            st.markdown(answer)

        st.session_state.messages.append(
            {"role": "assistant", "content": answer}
        )
    if st.button("back"):
        evalu()
        st.rerun()
