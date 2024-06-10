import json
from time import sleep

import resend
from openai import OpenAI

from config import BaseConfig
from models import Car

settings = BaseConfig()

client = OpenAI(
    # This is the default and can be omitted
    api_key=settings.OPENAI_API_KEY
)

resend.api_key = settings.RESEND_API_KEY


def generate_prompt(brand: str, model: str, year: int) -> str:
    return f"""
    You are a helpful car sales assistant. Describe the {brand} {model} from {year} in a playful and overall positive manner.
    Also, provide five pros and five cons of the model, but formulate the cons in a positive way.
    You will respond with a JSON format consisting of the following:
    a brief description of the {brand} {model}, playful and positive, but not over the top.
    This will be called *description*. Make it at least 350 characters.
    an array of 5 brief *pros* of the car model, short and concise, maximum 12 words, slightly positive and playful
    an array of 5 brief *cons* drawbacks of the car model, short and concise, maximum 12 words
    """


def delayed_task(message: str) -> None:
    print(f"Delayed task: {message}")
    sleep(5)
    print(message)


async def create_description(brand, make, year, picture_url):
    prompt = generate_prompt(brand, make, year)

    try:
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=500,
            temperature=0.0,
        )
        content = response.choices[0].message.content
        json_part = content

        # Parsing the JSON string into a Python dictionary
        car_info = json.loads(json_part)

        await Car.find(Car.brand == brand, Car.make == make, Car.year == year).set(
            {
                "description": car_info["description"],
                "pros": car_info["pros"],
                "cons": car_info["cons"],
            }
        )

        def generate_email():
            pros_list = "\n".join([f"- {pro}" for pro in car_info["pros"]])
            cons_list = "\n".join([f"- {con}" for con in car_info["cons"]])

            return f"""
            Hello,

            We have a new car for you: {brand} {make} from {year}.
            <p>

            <img src="{picture_url}"/>

            </p>

            {car_info['description']}

            <h3>Pros</h3>

            {pros_list}

            <h3>Cons</h3>

            {cons_list}   

            
            """

        params: resend.Emails.SendParams = {
            "from": "FARM Cars  <onboarding@resend.dev>",
            "to": ["aleksendric@gmail.com"],
            "subject": "Car information updated",
            "html": generate_email(),
        }

        resend.Emails.send(params)

        return True

    except Exception as e:
        print(e)
