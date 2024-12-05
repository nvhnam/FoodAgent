import streamlit as st
import os
import time
from dotenv import load_dotenv
from crewai import Agent, LLM, Task, Crew, Process
from crewai.tasks.conditional_task import ConditionalTask
from crewai.tasks.task_output import TaskOutput
from crewai_tools import ScrapeWebsiteTool
from crewai_tools import WebsiteSearchTool
from crewai_tools import SerperDevTool
from crewai.tools import BaseTool
# from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_community.tools import DuckDuckGoSearchRun
from langchain.agents import Tool
load_dotenv()


def chatbot_agent():
 
    if st.session_state.dish_nutrient_values and st.session_state.total_nutrient_values:
        dish_nutrient_values = st.session_state.dish_nutrient_values
        formated_dish_nutrient_values = [
            {
                "name": dish[0],
                "serving": dish[1],
                "calories": dish[3],
                "fat": dish[4],
                "saturates": dish[5],
                "sugar": dish[6],
                "salt": dish[7]
            }
            for dish in dish_nutrient_values[0] 
        ]
        # dish_names = [", ".join(dish["name"] for dish in formated_dish_nutrient_values)]
        # dish_names = ', '.join(dish_names)
        new = [
            f"{dish['name']} (serving: {dish['serving']}, calories: {dish['calories']} kcal, fat: {dish['fat']} g, saturates: {dish['saturates']} g, sugar: {dish['sugar']} g, salt: {dish['salt']} g)"
            for dish in formated_dish_nutrient_values
        ]
        dish_names = "; ".join(new)
        # st.write(dish_names)
    # else:
    #     dish_nutrient_values = None
    #     formated_dish_nutrient_values = None
    # if st.session_state.total_nutrient_values:
        total_nutrient_values = st.session_state.total_nutrient_values[0]
        total_calories = total_nutrient_values.get("Calories", 0)
        total_fat = total_nutrient_values.get("Fat", 0)
        total_saturates = total_nutrient_values.get("Saturates", 0)
        total_sugar = total_nutrient_values.get("Sugar", 0)
        total_salt = total_nutrient_values.get("Salt", 0)
        
    # else:
    #     total_nutrient_values = None
    # st.write("Total nutrient values: ", total_nutrient_values)
    # st.write("Each dish nutrient value: ", formated_dish_nutrient_values)

        gemini_api_key = os.getenv("GEMINI_API_KEY")


        # duckduckgo_search = DuckDuckGoSearchRun()

        class MyCustomDuckDuckGoTool(BaseTool):
            name: str = "DuckDuckGo Search Tool"
            description: str = "Search the web for a given query."

            def _run(self, query: str) -> str:
                duckduckgo_tool = DuckDuckGoSearchRun()
                
                response = duckduckgo_tool.invoke(query)

                return response
        

        scrape_tool = ScrapeWebsiteTool()
        # search_web = SerperDevTool(
        #     country="vn",
        #     locale="vn",
        #     location="Vietnam, Hanoi, Viet Nam, vietnam",
        #     n_results=2,
        # )

        age = 23
        gender = "male"
        height = 170
        weight = 65
        nutrition_url = "https://www.nutrition.org.uk/nutritional-information/nutrient-requirements/"
        diet_url = "https://www.nutrition.org.uk/creating-a-healthy-diet/a-healthy-balanced-diet/"


        
        if "messages" not in st.session_state:
            st.session_state.messages = []
        
        
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

        prompt = st.chat_input("Say something...")
        if prompt:
            with st.chat_message("user"):
                st.markdown(prompt)
            st.session_state.messages.append({"role": "user", "content": prompt})

        nutritionist = Agent(
            role="Nutritionist Chatbot",
            goal='Assess user’s meal and provide personalized nutritional advice',
            backstory=(
                "You are a skilled virtual nutritionist who provides dietary recommendations for a Vietnamese "
                "based on individual given health metric. You aim to optimize meal balance and variety."
            ),
            verbose=True,
            tools=[scrape_tool,MyCustomDuckDuckGoTool()],
            llm=LLM(model="gemini/gemini-1.5-flash", temperature=0.8),
            max_iter=1,
            max_rpm=10,
            memory=True,
        )

        if total_calories:
            assess_meal_task = Task(
                # description=(
                #     "Analyze the total nutrient values provided: "
                #     f"{total_calories} kcal, {total_fat} g fat, {total_salt} g salt, "
                #     f"{total_saturates} g saturated fat, and {total_sugar} g sugar. "
                #     f"Consider the following dishes nutrient values: {dish_names}. "
                #     "Evaluate the nutritional adequacy of these meals based on the Vietnamese user's profile: "
                #     f"Gender: {gender}, Age: {age} years, Height: {height} cm, Weight: {weight} kg. "
                #     f"Search for any nutrition and health-related websites, if there are no good results from those website then consider this {nutrition_url}, "
                #     "to assess if the meal meets recommended dietary guidelines. "
                #     "Specifically, determine if the meal meets protein requirements, assesses the sugar content, "
                #     "and identifies any potential nutritional deficiencies or excesses."
                # ),
                description=(
                    f"""
                        1. Extract all of the daily nutrition intake requirements for a person related-inormation from {nutrition_url} using the ScrapeWebsiteTool and DuckDuckGoSearchRun.
                        2. Based on the obtained knowledge, perform dietary assessment for a {age} years old {gender}, with a height of {height} cm and weight {weight} kg. Who is having meal consist of the following dishes with their corresponding nutrient values and serving size of each of them: {dish_names}. 
                        3. Incorporate those previous information with the total nutrient values of those dishes are: {total_calories} kcal, {total_fat} g fat, {total_salt} g salt, {total_saturates} g saturated fat, and {total_sugar} g sugar.
                        4. Finally, determine if the meal meets its required nutrient value by combining all of the provided dishes nutrient values as well as the total values, assesses the fat, protein, saturates content, and identifies any potential nutritional deficiencies or excesses.
                    """
                ),
                expected_output=(
                    "Give a precise evaluation based on the user provided dishes, nutritions and assess whether the meal meets the user's nutritional daily needs and any immediate suggestions."
                ),
                agent=nutritionist
            )

        # suggest_next_meal_task = Task(
        #     description=(
        #         "Based on the user's profile and the analysis of their previous meal, suggest options for a nutritious Vietnamese meal that "
        #         "balances the overall nutrient profile. Take into account any identified nutrient gaps and the need for variety in the diet. "
        #         f"Utilize resources, recommendation from {diet_url} to ensure that the suggestions are aligned with most of Vietnamese dietary practices. "
        #         "Also, perform additional searches using SerperDevTool to find popular Vietnamese dishes that meet the nutritional needs identified in the meal assessment."
        #     ),
        #     expected_output=(
        #         "A summary on whether the provided meals meets the user's nutritional needs and provide a detailed recommendation for the next meal, including suggested dishes, key nutrients they provide, "
        #         "and how they help fill any nutritional gaps identified in the previous meal assessment."
        #     ),
        #     agent=nutritionist
        # )

        def is_prompted(output: TaskOutput) -> bool:
            return prompt is not None

        answer_prompt = ConditionalTask(
            description=(
                "Based on the context of user nutrient level and details from previous tasks to help address in any of user needs."
                f"User said: '{prompt}'. "
                "Perform a search using DuckDuckGoSearchRun and ScrapeWebsiteTool for relevant results and summarize for a clear user instruction. Only proceed if input is provided."
            ),
            expected_output="Provide the most precise and clear answer with each idea listed as bullet point for the ease of reading regarding what user saying and their given background information.",
            agent=nutritionist,
            condition=is_prompted
        )

        crew = Crew(
            agents=[nutritionist],
            tasks=[assess_meal_task, 
                #    suggest_next_meal_task,
                    answer_prompt],
            process=Process.sequential
        )


        if total_nutrient_values and formated_dish_nutrient_values:
            crew_result = crew.kickoff(inputs={"total_calories": total_calories, "total_fat": total_fat, "total_saturates": total_saturates, "total_sugar": total_sugar, "total_salt": total_salt,  
                "dish_names": dish_names, "age": age, "gender": gender, "height": height, "weight": weight, "ntrition_url": nutrition_url,
                "diet_url": diet_url, "prompt": prompt})
            
            output = crew_result
            # def stream_message():
            #     for word in output:
            #         yield word
            #         time.sleep(0.05)
            # st.write("Type: ", type(output))
            with st.chat_message("assistant"):
                # for idx, output in enumerate(crew_result, 1):
                st.markdown(output)
                # st.write_stream(stream_message)
            st.session_state.messages.append({"role": "assistant", "content": output})

            # st.write("Bot: ", crew_result)
