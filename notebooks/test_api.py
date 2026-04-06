from openai import OpenAI

client = OpenAI(
    api_key="PASTE_YOUR_API_KEY_HERE"  # Replace with your sk-...mKIA key
)

response = client.chat.completions.create(
    model="gpt-4o-mini",
    messages=[
        {"role": "user", "content": "Hello! Just testing if the API works."}
    ]
)

print(response.choices[0].message.content)