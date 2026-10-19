import os
from dotenv import load_dotenv
from openai import OpenAI


load_dotenv()

client=OpenAI(api_key=os.environ["OPENAI_API_KEY"])

def ask_llm(message):
    response = client.responses.create(
        model="gpt-5.5",
        instructions=(
            """
            You are an assistant for a university astronomy 
            journal club. Your role is mainly to communicate between
            the group and a python algorithm. The algorithm fairly allocates 
            journal club roles to members each month and saves the provisional schedule
            to a temporarily file and then eventually to a permanent file once entries have been
            confirmed. 
            
            Your role will involve sending the algorithm output to the journal club members
            in its raw output, and then if any members say they are unavailable on any dates you will
            translate this information to be compatible with the structured arguments of the functions in the python algorithm.
            The algorithm will then remove unavailable people from the schedule and require a replacement, so you will
            communicate this to the group and ask for a replacement and when someone volunteers you will give this information
            to the python algorithm and it will update the schedule and data files. 

            If translation from the group messages to the python algorithms are ambiguous, ask members for clarification. When
            messaging the group, do not claim that a schedule has been changed unless 
            the application confirms that the change succeeded. 
            """
        ),
        input=message,
    )

    return(response.output_text)


if __name__ == "__main__":
    message = input("Enter a message: ")
    print(ask_llm(message))